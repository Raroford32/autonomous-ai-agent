#!/usr/bin/env python3
"""
Advanced Autonomous Agent with:
- Self-Healing
- Self-Learning
- Absolute Zero Reasoning
- Autonomous Tool Building
- Continuous Refactoring
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from agent import AutonomousAgent, Task
from self_healing import SelfHealer
from self_learning import SelfLearner, Experience
from zero_reasoning import ZeroReasoner
from tool_builder import ToolBuilder, ToolSpec
from refactoring_loop import RefactoringLoop
from metrics_monitor import MetricsMonitor
from resilience import ResilienceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedAgent(AutonomousAgent):
    """
    Advanced autonomous agent with self-healing, self-learning, 
    and autonomous improvement capabilities
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize advanced agent with all capabilities"""
        super().__init__(config)

        # Initialize advanced systems
        self.healer = SelfHealer(self)
        self.learner = SelfLearner(self)
        self.reasoner = ZeroReasoner(self)
        self.builder = ToolBuilder(self)
        self.refactorer = RefactoringLoop(self)
        self.metrics = MetricsMonitor(self, retention_hours=24)
        self.resilience = ResilienceManager(self)

        # Start background monitoring
        self.monitoring_task = None

        logger.info("Advanced Agent initialized with all systems")

    async def start(self):
        """Start the agent and all background processes"""
        logger.info("Starting Advanced Agent...")

        # Start health monitoring in background
        self.monitoring_task = asyncio.create_task(self.healer.start_monitoring())

        logger.info("All systems operational")

    async def stop(self):
        """Stop the agent gracefully"""
        logger.info("Stopping Advanced Agent...")

        self.healer.stop_monitoring()

        if self.monitoring_task:
            self.monitoring_task.cancel()

        # Save learned knowledge
        self.learner._save_knowledge_base()

        logger.info("Agent stopped")

    async def process_task(self, task: Task) -> Task:
        """
        Process task with advanced capabilities
        """
        logger.info(f"Processing task {task.id} with advanced agent")
        start_time = asyncio.get_event_loop().time()

        try:
            # Check if we need new tools for this task
            current_capabilities = self._get_current_capabilities()
            needed_tool = await self.builder.identify_needed_tool(
                task.description,
                current_capabilities
            )

            if needed_tool:
                logger.info(f"Building new tool: {needed_tool.name}")
                await self.builder.build_tool(needed_tool)

            # Use absolute zero reasoning for complex tasks
            if self._is_complex_task(task):
                logger.info("Applying absolute zero reasoning")
                reasoning_result = await self.reasoner.reason_from_zero(
                    task.description,
                    {'memory': self.memory}
                )

                # Use reasoning to inform task execution
                task.metadata = {'reasoning': reasoning_result}

            # Get learned strategy suggestion
            strategy = await self.learner.suggest_strategy(
                task.description,
                {'task': task}
            )

            logger.info(f"Using strategy: {strategy['strategy']} (confidence: {strategy['confidence']:.2f})")

            # Execute task with error handling
            try:
                completed_task = await super().process_task(task)
            except Exception as e:
                # Self-healing on error
                logger.warning(f"Task execution error, attempting self-healing")

                healed = await self.healer.handle_failure(
                    e,
                    'task_execution',
                    {'task': task.description}
                )

                if healed:
                    # Retry after healing
                    completed_task = await super().process_task(task)
                else:
                    raise

            # Record experience for learning
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            experience = Experience(
                timestamp=completed_task.timestamp if hasattr(completed_task, 'timestamp') else None,
                task_description=task.description,
                strategy_used=strategy['strategy'],
                actions_taken=completed_task.result if isinstance(completed_task.result, list) else [],
                outcome='success' if completed_task.status == 'completed' else 'failure',
                performance_metrics={
                    'duration': duration,
                    'memory_used': len(self.memory)
                },
                context={'task_id': task.id}
            )

            await self.learner.record_experience(experience)

            return completed_task

        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            task.error = str(e)
            task.status = "failed"

            # Try to heal and learn from failure
            await self.healer.handle_failure(e, 'advanced_agent', {'task': task.description})

            return task

    def _get_current_capabilities(self) -> List[str]:
        """Get list of current agent capabilities"""
        capabilities = [
            'web_search',
            'code_execution',
            'computer_control',
            'llm_reasoning'
        ]

        # Add dynamically built tools
        capabilities.extend(self.builder.built_tools.keys())

        return capabilities

    def _is_complex_task(self, task: Task) -> bool:
        """Determine if task requires deep reasoning"""
        complexity_keywords = [
            'analyze', 'design', 'architect', 'optimize',
            'explain', 'reason', 'prove', 'deduce'
        ]

        desc_lower = task.description.lower()
        return any(kw in desc_lower for kw in complexity_keywords)

    async def run_autonomous(self, goal: str, max_iterations: int = 20):
        """
        Run agent autonomously with advanced capabilities
        """
        logger.info(f"Starting autonomous mode (advanced) with goal: {goal}")

        iteration = 0
        while iteration < max_iterations:
            try:
                # Use zero reasoning to determine next action
                reasoning = await self.reasoner.reason_from_zero(
                    f"What is the best next action to achieve: {goal}",
                    {'memory': self.memory, 'iteration': iteration}
                )

                next_action = {
                    'action': reasoning['solution'][:100],  # Simplified
                    'description': reasoning['solution'],
                    'confidence': reasoning['confidence']
                }

                if 'goal_achieved' in next_action['action'].lower():
                    logger.info(f"Goal achieved in {iteration} iterations")
                    return {
                        'success': True,
                        'iterations': iteration,
                        'result': next_action,
                        'reasoning_used': True
                    }

                # Execute the determined action
                task = Task(
                    id=f"auto_advanced_{iteration}",
                    description=next_action['description']
                )

                await self.process_task(task)
                iteration += 1

            except Exception as e:
                logger.error(f"Autonomous iteration error: {e}")

                # Self-heal and continue
                healed = await self.healer.handle_failure(
                    e,
                    'autonomous_mode',
                    {'goal': goal, 'iteration': iteration}
                )

                if not healed:
                    break

                iteration += 1

        logger.warning(f"Max iterations ({max_iterations}) reached")
        return {
            'success': False,
            'reason': 'max_iterations_reached',
            'iterations': iteration
        }

    async def self_improve(self):
        """Trigger comprehensive self-improvement cycle"""
        logger.info("Starting comprehensive self-improvement cycle")
        
        improvements = {
            'code_refactoring': None,
            'knowledge_gaps': None,
            'healing_optimizations': None,
            'recommendations': None
        }

        # 1. Analyze and refactor codebase
        code_files = [
            'agent.py',
            'advanced_agent.py',
            'llm_interface.py',
            'code_executor.py',
            'computer_control.py',
            'web_search.py'
        ]

        analysis = await self.refactorer.analyze_codebase(code_files)
        logger.info(f"Code analysis complete: {len(analysis['issues_found'])} issues found")

        # Apply refactoring to files with issues
        refactored_files = []
        for filepath, metrics in analysis['metrics'].items():
            if any(issue['severity'] == 'high' for issue in analysis['issues_found']):
                logger.info(f"Auto-refactoring {filepath}")
                result = await self.refactorer.auto_refactor(filepath, backup=True)
                if result:
                    refactored_files.append(filepath)
        
        improvements['code_refactoring'] = {
            'analysis': analysis,
            'refactored_files': refactored_files,
            'total_refactorings': len(self.refactorer.refactoring_history)
        }

        # 2. Identify knowledge gaps
        gaps = await self.learner.identify_knowledge_gaps()
        improvements['knowledge_gaps'] = gaps
        logger.info(f"Identified {len(gaps)} knowledge gaps")

        # 3. Get learning recommendations
        recommendations = await self.learner.recommend_improvements()
        improvements['recommendations'] = recommendations
        logger.info(f"Generated {len(recommendations)} improvement recommendations")

        # 4. Predict and prevent failures
        predictions = await self.healer.predict_failures()
        improvements['healing_optimizations'] = {
            'predicted_failures': predictions,
            'preventive_actions': [p['recommended_action'] for p in predictions]
        }
        logger.info(f"Predicted {len(predictions)} potential failures")

        # 5. Optimize strategy selection based on data
        await self.learner._optimize_strategies()
        
        logger.info("Self-improvement cycle complete")
        return improvements
    
    async def continuous_evolution(self, duration_hours: int = 24):
        """Run continuous evolution loop for specified duration"""
        logger.info(f"Starting continuous evolution for {duration_hours} hours")
        
        import time
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        evolution_metrics = {
            'improvements_made': 0,
            'tasks_completed': 0,
            'failures_healed': 0,
            'new_knowledge': 0
        }
        
        while time.time() < end_time:
            try:
                # Periodic self-improvement (every 2 hours)
                if int((time.time() - start_time) / 7200) > evolution_metrics['improvements_made']:
                    logger.info("Triggering periodic self-improvement")
                    await self.self_improve()
                    evolution_metrics['improvements_made'] += 1
                
                # Monitor and optimize
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check for predicted failures and take preventive action
                predictions = await self.healer.predict_failures()
                for pred in predictions:
                    logger.warning(f"Predicted failure: {pred['metric']}, taking preventive action")
                    # Take preventive action based on recommendation
                
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
                await self.healer.handle_failure(e, 'evolution', {})
        
        logger.info(f"Evolution complete. Metrics: {evolution_metrics}")
        return evolution_metrics

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report with advanced metrics"""
        health_report = self.healer.get_health_report()
        learning_report = self.learner.get_learning_report()
        resilience_report = self.resilience.get_resilience_report()
        metrics_report = self.metrics.get_comprehensive_report()
        
        return {
            'agent_status': 'operational',
            'health_score': metrics_report['health_score'],
            'uptime_metrics': {
                'current_health': health_report['current_status'],
                'total_failures': health_report['total_failures'],
                'successful_healings': health_report['successful_healings'],
                'healing_success_rate': (
                    health_report['successful_healings'] / health_report['total_failures'] 
                    if health_report['total_failures'] > 0 else 1.0
                )
            },
            'learning_metrics': {
                'total_experiences': learning_report['total_experiences'],
                'success_rate': learning_report['overall_success_rate'],
                'knowledge_base_size': learning_report['knowledge_base_size'],
                'adaptive_learning_rate': 0.05  # Would call asyncio method
            },
            'resilience_status': resilience_report,
            'metrics_summary': metrics_report['metrics_summary'],
            'capabilities': {
                'built_tools': list(self.builder.built_tools.keys()),
                'total_tools': len(self.builder.built_tools),
                'core_capabilities': self._get_current_capabilities()
            },
            'code_quality': {
                'refactorings_applied': len(self.refactorer.refactoring_history),
                'last_refactoring': (
                    self.refactorer.refactoring_history[-1]['timestamp'].isoformat() 
                    if self.refactorer.refactoring_history else None
                )
            },
            'performance': {
                'memory_size': len(self.memory),
                'task_queue_size': len(self.task_queue),
                'strategy_performance': learning_report['strategy_performance']
            },
            'active_alerts': metrics_report['active_alerts']
        }


async def main():
    """Example usage of Advanced Agent"""
    config = {
        'llm_config': {
            'model': 'gpt-4',
            'temperature': 0.7
        },
        'search_config': {
            'engine': 'duckduckgo'
        },
        'executor_config': {
            'safe_mode': True
        },
        'computer_config': {
            'allowed_actions': ['screenshot']
        }
    }

    agent = AdvancedAgent(config)

    # Start agent
    await agent.start()

    try:
        # Example 1: Run a task with all advanced features
        result = await agent.run(
            "Research quantum computing and create a technical analysis"
        )
        print("Task result:", json.dumps(result, indent=2))

        # Example 2: Autonomous mode
        autonomous_result = await agent.run_autonomous(
            goal="Become expert at analyzing AI research papers",
            max_iterations=10
        )
        print("Autonomous result:", json.dumps(autonomous_result, indent=2))

        # Example 3: Self-improvement
        improvement = await agent.self_improve()
        print("Self-improvement:", json.dumps(improvement, indent=2))

        # Get status report
        status = agent.get_status_report()
        print("Agent status:", json.dumps(status, indent=2))

    finally:
        # Stop agent gracefully
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
