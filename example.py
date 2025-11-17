#!/usr/bin/env python3
"""
Example usage of the Autonomous AI Agent
"""

import asyncio
import json
from agent import AutonomousAgent


async def example_web_search():
    """Example: Web search and summarization"""
    print("\n=== Example 1: Web Search ===")

    config = {
        'llm_config': {'model': 'gpt-4', 'temperature': 0.7},
        'search_config': {'engine': 'duckduckgo'},
        'executor_config': {'safe_mode': True},
        'computer_config': {'allowed_actions': ['screenshot']}
    }

    agent = AutonomousAgent(config)
    result = await agent.run("Search for 'Python asyncio tutorial' and summarize the top result")

    print(f"Status: {result['status']}")
    print(f"Result: {json.dumps(result['result'], indent=2)}")


async def example_code_execution():
    """Example: Execute code to analyze data"""
    print("\n=== Example 2: Code Execution ===")

    config = {
        'llm_config': {'model': 'gpt-4', 'temperature': 0.7},
        'search_config': {'engine': 'duckduckgo'},
        'executor_config': {'safe_mode': True},
        'computer_config': {'allowed_actions': ['screenshot']}
    }

    agent = AutonomousAgent(config)

    task = """
    Write and execute Python code to:
    1. Generate a list of prime numbers up to 100
    2. Calculate their sum
    3. Return the result
    """

    result = await agent.run(task)
    print(f"Status: {result['status']}")
    print(f"Result: {json.dumps(result['result'], indent=2)}")


async def example_autonomous_mode():
    """Example: Run agent in autonomous mode"""
    print("\n=== Example 3: Autonomous Mode ===")

    config = {
        'llm_config': {'model': 'gpt-4', 'temperature': 0.7},
        'search_config': {'engine': 'duckduckgo'},
        'executor_config': {'safe_mode': True},
        'computer_config': {'allowed_actions': ['screenshot']}
    }

    agent = AutonomousAgent(config)

    goal = "Research the top 3 programming languages in 2024 and explain why they're popular"
    result = await agent.run_autonomous(goal, max_iterations=5)

    print(f"Success: {result['success']}")
    print(f"Iterations: {result['iterations']}")


async def example_computer_control():
    """Example: Computer control operations"""
    print("\n=== Example 4: Computer Control ===")

    config = {
        'llm_config': {'model': 'gpt-4', 'temperature': 0.7},
        'search_config': {'engine': 'duckduckgo'},
        'executor_config': {'safe_mode': True},
        'computer_config': {
            'allowed_actions': ['screenshot', 'mouse_move'],
            'safe_mode': True  # Safe mode for demo
        }
    }

    agent = AutonomousAgent(config)
    result = await agent.run("Take a screenshot and describe what you see")

    print(f"Status: {result['status']}")


async def main():
    """Run all examples"""
    print("Autonomous AI Agent - Examples")
    print("=" * 50)

    # Note: These examples require proper API keys in config
    print("\nNote: Update config with your API keys to run these examples")

    try:
        await example_web_search()
        await example_code_execution()
        await example_autonomous_mode()
        await example_computer_control()
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure to configure API keys in config.json")


if __name__ == "__main__":
    asyncio.run(main())
