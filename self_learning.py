"""
Self-Learning Module
Continuously learns from experiences, optimizes strategies, and improves performance
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    """Learning experience record"""
    timestamp: datetime
    task_description: str
    strategy_used: str
    actions_taken: List[Dict]
    outcome: str  # success, failure, partial
    performance_metrics: Dict[str, float]
    context: Dict
    feedback: Optional[str] = None


@dataclass
class Knowledge:
    """Knowledge base entry"""
    topic: str
    content: Any
    confidence: float
    source: str
    timestamp: datetime
    usage_count: int = 0
    success_rate: float = 0.0


class SelfLearner:
    """
    Self-learning system that improves agent performance over time
    """

    def __init__(self, agent_ref, knowledge_base_path: str = 'knowledge_base.pkl'):
        self.agent = agent_ref
        self.knowledge_base_path = knowledge_base_path
        self.experiences: List[Experience] = []
        self.knowledge_base: Dict[str, Knowledge] = {}
        self.strategy_performance: Dict[str, Dict] = defaultdict(lambda: {
            'attempts': 0,
            'successes': 0,
            'avg_duration': 0.0,
            'success_rate': 0.0
        })

        # Load existing knowledge
        self._load_knowledge_base()

        logger.info("Self-Learner initialized")

    def _load_knowledge_base(self):
        """Load knowledge base from disk"""
        try:
            with open(self.knowledge_base_path, 'rb') as f:
                data = pickle.load(f)
                self.knowledge_base = data.get('knowledge_base', {})
                self.strategy_performance = data.get('strategy_performance', defaultdict(dict))
                logger.info(f"Loaded {len(self.knowledge_base)} knowledge entries")
        except FileNotFoundError:
            logger.info("No existing knowledge base found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")

    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            with open(self.knowledge_base_path, 'wb') as f:
                pickle.dump({
                    'knowledge_base': self.knowledge_base,
                    'strategy_performance': dict(self.strategy_performance)
                }, f)
            logger.info("Knowledge base saved")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

    async def record_experience(self, experience: Experience):
        """Record a new learning experience"""
        self.experiences.append(experience)

        # Update strategy performance
        strategy = experience.strategy_used
        self.strategy_performance[strategy]['attempts'] += 1

        if experience.outcome == 'success':
            self.strategy_performance[strategy]['successes'] += 1

        attempts = self.strategy_performance[strategy]['attempts']
        successes = self.strategy_performance[strategy]['successes']
        self.strategy_performance[strategy]['success_rate'] = successes / attempts

        # Learn from experience
        await self._learn_from_experience(experience)

        logger.info(f"Recorded experience: {experience.task_description[:50]}...")

    async def _learn_from_experience(self, experience: Experience):
        """Extract learnings from an experience"""
        # Analyze what worked and what didn't
        if experience.outcome == 'success':
            # Extract successful patterns
            await self._extract_success_patterns(experience)
        else:
            # Learn from failures
            await self._extract_failure_lessons(experience)

        # Update knowledge base
        await self._update_knowledge(experience)

        # Optimize strategies
        await self._optimize_strategies()

    async def _extract_success_patterns(self, experience: Experience):
        """Extract patterns from successful experiences"""
        logger.info("Extracting success patterns")

        # Identify key success factors
        success_factors = {
            'strategy': experience.strategy_used,
            'actions': [a.get('action') for a in experience.actions_taken],
            'context_features': self._extract_context_features(experience.context)
        }

        # Store as knowledge
        knowledge_key = f"success_pattern_{experience.strategy_used}"
        if knowledge_key not in self.knowledge_base:
            self.knowledge_base[knowledge_key] = Knowledge(
                topic=knowledge_key,
                content=success_factors,
                confidence=0.7,
                source='experience',
                timestamp=experience.timestamp
            )
        else:
            # Update existing knowledge with reinforcement
            existing = self.knowledge_base[knowledge_key]
            existing.usage_count += 1
            existing.confidence = min(0.99, existing.confidence * 1.1)
            existing.timestamp = experience.timestamp

    async def _extract_failure_lessons(self, experience: Experience):
        """Extract lessons from failures"""
        logger.info("Extracting failure lessons")

        failure_lesson = {
            'strategy': experience.strategy_used,
            'failed_actions': [a for a in experience.actions_taken],
            'context': experience.context,
            'lesson': 'Avoid this strategy in similar contexts'
        }

        # Store as anti-pattern
        knowledge_key = f"failure_lesson_{experience.strategy_used}"
        if knowledge_key not in self.knowledge_base:
            self.knowledge_base[knowledge_key] = Knowledge(
                topic=knowledge_key,
                content=failure_lesson,
                confidence=0.8,
                source='failure_experience',
                timestamp=experience.timestamp
            )

    def _extract_context_features(self, context: Dict) -> List[str]:
        """Extract key features from context"""
        features = []

        if 'task_type' in context:
            features.append(f"task_type:{context['task_type']}")
        if 'complexity' in context:
            features.append(f"complexity:{context['complexity']}")
        if 'resources' in context:
            for resource in context['resources']:
                features.append(f"resource:{resource}")

        return features

    async def _update_knowledge(self, experience: Experience):
        """Update knowledge base with new information"""
        # Extract key information from the experience
        task_type = self._classify_task(experience.task_description)

        knowledge_key = f"task_solution_{task_type}"

        solution_data = {
            'task_type': task_type,
            'successful_strategy': experience.strategy_used if experience.outcome == 'success' else None,
            'actions': experience.actions_taken,
            'performance': experience.performance_metrics
        }

        if knowledge_key in self.knowledge_base:
            existing = self.knowledge_base[knowledge_key]
            existing.usage_count += 1

            # Update success rate
            if experience.outcome == 'success':
                existing.success_rate = (existing.success_rate * (existing.usage_count - 1) + 1.0) / existing.usage_count
            else:
                existing.success_rate = (existing.success_rate * (existing.usage_count - 1)) / existing.usage_count

            existing.confidence = min(0.99, existing.confidence + 0.05)
        else:
            self.knowledge_base[knowledge_key] = Knowledge(
                topic=knowledge_key,
                content=solution_data,
                confidence=0.5,
                source='experience',
                timestamp=experience.timestamp,
                usage_count=1,
                success_rate=1.0 if experience.outcome == 'success' else 0.0
            )

        # Periodically save knowledge base
        if len(self.experiences) % 10 == 0:
            self._save_knowledge_base()

    def _classify_task(self, task_description: str) -> str:
        """Classify task type from description"""
        desc_lower = task_description.lower()

        if any(word in desc_lower for word in ['search', 'find', 'look up', 'research']):
            return 'search_task'
        elif any(word in desc_lower for word in ['code', 'execute', 'run', 'program']):
            return 'code_task'
        elif any(word in desc_lower for word in ['click', 'type', 'screenshot', 'control']):
            return 'control_task'
        elif any(word in desc_lower for word in ['analyze', 'summarize', 'explain']):
            return 'analysis_task'
        else:
            return 'general_task'

    async def _optimize_strategies(self):
        """Optimize strategies based on performance data"""
        logger.info("Optimizing strategies")

        # Identify best performing strategies
        best_strategies = sorted(
            self.strategy_performance.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )[:5]

        # Store optimized strategy preferences
        self.knowledge_base['optimized_strategies'] = Knowledge(
            topic='optimized_strategies',
            content={'best_strategies': best_strategies},
            confidence=0.9,
            source='optimization',
            timestamp=datetime.utcnow()
        )

    async def suggest_strategy(self, task_description: str, context: Dict) -> Dict[str, Any]:
        """Suggest best strategy based on learned knowledge"""
        task_type = self._classify_task(task_description)

        # Look up learned knowledge
        knowledge_key = f"task_solution_{task_type}"
        if knowledge_key in self.knowledge_base:
            knowledge = self.knowledge_base[knowledge_key]

            if knowledge.success_rate > 0.6:
                logger.info(f"Found high-confidence strategy for {task_type}")
                return {
                    'strategy': knowledge.content.get('successful_strategy'),
                    'confidence': knowledge.confidence,
                    'based_on_experiences': knowledge.usage_count
                }

        # Fallback: use best performing strategies overall
        if 'optimized_strategies' in self.knowledge_base:
            best = self.knowledge_base['optimized_strategies'].content['best_strategies']
            if best:
                return {
                    'strategy': best[0][0],
                    'confidence': best[0][1]['success_rate'],
                    'based_on_experiences': best[0][1]['attempts']
                }

        # Default fallback
        return {
            'strategy': 'default_exploration',
            'confidence': 0.3,
            'based_on_experiences': 0
        }

    async def teach_self(self, topic: str, content: Any, source: str = 'self_teaching'):
        """Teach the agent new knowledge"""
        logger.info(f"Self-teaching: {topic}")

        self.knowledge_base[topic] = Knowledge(
            topic=topic,
            content=content,
            confidence=0.6,
            source=source,
            timestamp=datetime.utcnow()
        )

        self._save_knowledge_base()

    def get_learning_report(self) -> Dict:
        """Generate learning progress report"""
        total_experiences = len(self.experiences)
        successful_experiences = sum(1 for e in self.experiences if e.outcome == 'success')

        return {
            'total_experiences': total_experiences,
            'successful_experiences': successful_experiences,
            'overall_success_rate': successful_experiences / total_experiences if total_experiences > 0 else 0,
            'knowledge_base_size': len(self.knowledge_base),
            'strategy_performance': {
                k: {
                    'attempts': v['attempts'],
                    'success_rate': v['success_rate']
                }
                for k, v in sorted(
                    self.strategy_performance.items(),
                    key=lambda x: x[1]['success_rate'],
                    reverse=True
                )[:10]
            },
            'top_knowledge': [
                {
                    'topic': k,
                    'confidence': v.confidence,
                    'usage_count': v.usage_count,
                    'success_rate': v.success_rate
                }
                for k, v in sorted(
                    self.knowledge_base.items(),
                    key=lambda x: x[1].confidence * x[1].usage_count,
                    reverse=True
                )[:10]
            ]
        }
