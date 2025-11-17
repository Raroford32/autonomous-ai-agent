#!/usr/bin/env python3
"""
Autonomous AI Agent - Main Controller
A general-purpose AI agent with computer control, web search, and code execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from computer_control import ComputerController
from web_search import WebSearcher
from code_executor import CodeExecutor
from llm_interface import LLMInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task for the agent to complete"""
    id: str
    description: str
    priority: int = 1
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class AutonomousAgent:
    """
    Main AI Agent class that orchestrates computer control, web search, and code execution
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the autonomous agent with all capabilities

        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config
        self.llm = LLMInterface(config.get('llm_config', {}))
        self.computer = ComputerController(config.get('computer_config', {}))
        self.searcher = WebSearcher(config.get('search_config', {}))
        self.executor = CodeExecutor(config.get('executor_config', {}))
        self.task_queue: List[Task] = []
        self.memory: List[Dict] = []

        logger.info("Autonomous Agent initialized successfully")

    async def process_task(self, task: Task) -> Task:
        """
        Process a single task using available capabilities

        Args:
            task: Task object to process

        Returns:
            Updated task with results or errors
        """
        logger.info(f"Processing task {task.id}: {task.description}")

        try:
            # Use LLM to determine which capabilities to use
            plan = await self.llm.create_plan(task.description, self.memory)
            logger.info(f"Execution plan created: {plan['steps']}")

            results = []
            for step in plan['steps']:
                step_result = await self._execute_step(step)
                results.append(step_result)

                # Update memory with step results
                self.memory.append({
                    'task_id': task.id,
                    'step': step,
                    'result': step_result
                })

            task.result = results
            task.status = "completed"
            logger.info(f"Task {task.id} completed successfully")

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            logger.error(f"Task {task.id} failed: {e}")

        return task

    async def _execute_step(self, step: Dict) -> Any:
        """
        Execute a single step using the appropriate capability

        Args:
            step: Step dictionary with action and parameters

        Returns:
            Result of the step execution
        """
        action = step['action']
        params = step.get('parameters', {})

        if action == 'search_web':
            return await self.searcher.search(params['query'])

        elif action == 'execute_code':
            return await self.executor.execute(params['code'], params.get('language', 'python'))

        elif action == 'control_computer':
            return await self.computer.execute_action(params['action_type'], params)

        elif action == 'llm_query':
            return await self.llm.query(params['prompt'])

        else:
            raise ValueError(f"Unknown action type: {action}")

    async def run(self, task_description: str) -> Dict[str, Any]:
        """
        Main entry point to run the agent with a task

        Args:
            task_description: Natural language description of the task

        Returns:
            Task results dictionary
        """
        task = Task(
            id=f"task_{len(self.task_queue)}",
            description=task_description
        )

        self.task_queue.append(task)
        completed_task = await self.process_task(task)

        return {
            'task_id': completed_task.id,
            'status': completed_task.status,
            'result': completed_task.result,
            'error': completed_task.error
        }

    async def run_autonomous(self, goal: str, max_iterations: int = 10):
        """
        Run the agent autonomously towards a goal

        Args:
            goal: High-level goal to achieve
            max_iterations: Maximum number of iterations
        """
        logger.info(f"Starting autonomous mode with goal: {goal}")

        iteration = 0
        while iteration < max_iterations:
            # Ask LLM for next action based on goal and memory
            next_action = await self.llm.determine_next_action(goal, self.memory)

            if next_action['action'] == 'goal_achieved':
                logger.info(f"Goal achieved in {iteration} iterations")
                return {
                    'success': True,
                    'iterations': iteration,
                    'result': next_action.get('result')
                }

            # Execute the determined action
            task = Task(
                id=f"auto_task_{iteration}",
                description=next_action['description']
            )

            await self.process_task(task)
            iteration += 1

        logger.warning(f"Max iterations ({max_iterations}) reached")
        return {
            'success': False,
            'reason': 'max_iterations_reached',
            'iterations': iteration
        }


async def main():
    """Example usage of the autonomous agent"""
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
            'allowed_actions': ['mouse', 'keyboard', 'screenshot']
        }
    }

    agent = AutonomousAgent(config)

    # Example task
    result = await agent.run("Search for the latest AI news and summarize the top 3 articles")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
