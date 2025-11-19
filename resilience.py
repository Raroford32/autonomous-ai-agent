"""
Resilience and Fault Tolerance Module
Provides advanced resilience patterns including circuit breakers, retry logic, and failover
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import functools

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes before closing from half-open
    timeout_seconds: int = 60   # Time before trying half-open
    window_seconds: int = 300   # Rolling window for failure counting


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()
        self.failure_history: List[datetime] = []
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable[..., Awaitable], *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if datetime.utcnow() - self.last_state_change > timedelta(seconds=self.config.timeout_seconds):
                logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        # Try to execute function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"Circuit '{self.name}' success in HALF_OPEN ({self.success_count}/{self.config.success_threshold})")
            
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit '{self.name}' transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = datetime.utcnow()
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed execution"""
        self.last_failure_time = datetime.utcnow()
        self.failure_history.append(self.last_failure_time)
        
        # Clean old failures outside window
        cutoff = datetime.utcnow() - timedelta(seconds=self.config.window_seconds)
        self.failure_history = [f for f in self.failure_history if f > cutoff]
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit '{self.name}' failure in HALF_OPEN, opening circuit")
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()
        
        elif self.state == CircuitState.CLOSED:
            self.failure_count = len(self.failure_history)
            
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(f"Circuit '{self.name}' threshold exceeded, opening circuit")
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': len(self.failure_history),
            'success_count': self.success_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_state_change': self.last_state_change.isoformat()
        }


class RetryPolicy:
    """
    Configurable retry policy with exponential backoff
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = min(self.initial_delay * (self.backoff_factor ** attempt), self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())  # Add 0-50% jitter
        
        return delay
    
    async def execute(
        self,
        func: Callable[..., Awaitable],
        *args,
        **kwargs
    ):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed")
        
        raise last_exception


class Bulkhead:
    """
    Bulkhead pattern to isolate resources and prevent cascade failures
    """
    
    def __init__(self, name: str, max_concurrent: int = 10, max_queued: int = 100):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queued = max_queued
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self.queued_count = 0
        self.total_processed = 0
        self.total_rejected = 0
    
    async def execute(self, func: Callable[..., Awaitable], *args, **kwargs):
        """Execute function with bulkhead protection"""
        
        # Check if queue is full
        if self.queued_count >= self.max_queued:
            self.total_rejected += 1
            raise Exception(f"Bulkhead '{self.name}' queue is full")
        
        self.queued_count += 1
        
        try:
            async with self.semaphore:
                self.active_count += 1
                self.queued_count -= 1
                
                try:
                    result = await func(*args, **kwargs)
                    self.total_processed += 1
                    return result
                finally:
                    self.active_count -= 1
        except Exception as e:
            self.queued_count -= 1
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get bulkhead status"""
        return {
            'name': self.name,
            'active': self.active_count,
            'queued': self.queued_count,
            'max_concurrent': self.max_concurrent,
            'max_queued': self.max_queued,
            'total_processed': self.total_processed,
            'total_rejected': self.total_rejected,
            'utilization': self.active_count / self.max_concurrent
        }


class ResilienceManager:
    """
    Manages resilience patterns for the agent
    """
    
    def __init__(self, agent_ref):
        self.agent = agent_ref
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
        
        # Initialize default resilience patterns
        self._initialize_defaults()
        
        logger.info("Resilience Manager initialized")
    
    def _initialize_defaults(self):
        """Initialize default resilience patterns for common operations"""
        
        # Circuit breakers for external services
        self.circuit_breakers['llm_api'] = CircuitBreaker(
            'llm_api',
            CircuitBreakerConfig(failure_threshold=5, timeout_seconds=120)
        )
        self.circuit_breakers['web_search'] = CircuitBreaker(
            'web_search',
            CircuitBreakerConfig(failure_threshold=3, timeout_seconds=60)
        )
        self.circuit_breakers['code_execution'] = CircuitBreaker(
            'code_execution',
            CircuitBreakerConfig(failure_threshold=5, timeout_seconds=30)
        )
        
        # Bulkheads for resource isolation
        self.bulkheads['llm_requests'] = Bulkhead('llm_requests', max_concurrent=5, max_queued=20)
        self.bulkheads['code_execution'] = Bulkhead('code_execution', max_concurrent=3, max_queued=10)
        self.bulkheads['web_requests'] = Bulkhead('web_requests', max_concurrent=10, max_queued=50)
        
        # Retry policies
        self.retry_policies['api_call'] = RetryPolicy(max_attempts=3, initial_delay=1.0)
        self.retry_policies['network_request'] = RetryPolicy(max_attempts=5, initial_delay=2.0)
        self.retry_policies['critical_operation'] = RetryPolicy(max_attempts=10, initial_delay=5.0)
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name)
        return self.circuit_breakers[name]
    
    def get_bulkhead(self, name: str, max_concurrent: int = 10) -> Bulkhead:
        """Get or create bulkhead"""
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(name, max_concurrent=max_concurrent)
        return self.bulkheads[name]
    
    def get_retry_policy(self, name: str) -> RetryPolicy:
        """Get or create retry policy"""
        if name not in self.retry_policies:
            self.retry_policies[name] = RetryPolicy()
        return self.retry_policies[name]
    
    async def resilient_call(
        self,
        func: Callable[..., Awaitable],
        *args,
        circuit_breaker: str = None,
        bulkhead: str = None,
        retry_policy: str = None,
        **kwargs
    ):
        """
        Execute function with full resilience patterns
        """
        
        # Wrap function with selected patterns
        wrapped_func = func
        
        # Apply retry policy
        if retry_policy:
            policy = self.get_retry_policy(retry_policy)
            original_func = wrapped_func
            wrapped_func = lambda: policy.execute(original_func, *args, **kwargs)
            args = ()
            kwargs = {}
        
        # Apply circuit breaker
        if circuit_breaker:
            cb = self.get_circuit_breaker(circuit_breaker)
            original_func = wrapped_func
            wrapped_func = lambda: cb.call(original_func, *args, **kwargs)
            args = ()
            kwargs = {}
        
        # Apply bulkhead
        if bulkhead:
            bh = self.get_bulkhead(bulkhead)
            original_func = wrapped_func
            wrapped_func = lambda: bh.execute(original_func, *args, **kwargs)
            args = ()
            kwargs = {}
        
        # Execute with all patterns applied
        return await wrapped_func()
    
    def get_resilience_report(self) -> Dict[str, Any]:
        """Generate comprehensive resilience report"""
        return {
            'circuit_breakers': {
                name: cb.get_status()
                for name, cb in self.circuit_breakers.items()
            },
            'bulkheads': {
                name: bh.get_status()
                for name, bh in self.bulkheads.items()
            },
            'retry_policies': {
                name: {
                    'max_attempts': rp.max_attempts,
                    'initial_delay': rp.initial_delay,
                    'max_delay': rp.max_delay
                }
                for name, rp in self.retry_policies.items()
            }
        }


def resilient(
    circuit_breaker: str = None,
    bulkhead: str = None,
    retry_policy: str = None
):
    """
    Decorator to make async functions resilient
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if hasattr(self, 'resilience'):
                return await self.resilience.resilient_call(
                    func.__get__(self, type(self)),
                    *args,
                    circuit_breaker=circuit_breaker,
                    bulkhead=bulkhead,
                    retry_policy=retry_policy,
                    **kwargs
                )
            else:
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator
