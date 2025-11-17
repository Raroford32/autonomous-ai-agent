# Autonomous AI Agent

A general-purpose AI agent with computer control, web search, and code execution capabilities.

## Features

🖥️ **Computer Control**
- Mouse and keyboard control
- Screen capture and image recognition
- System command execution
- Safe mode with permission controls

🔍 **Web Search**
- DuckDuckGo and Google search support
- Web scraping capabilities
- Structured result extraction

💻 **Code Execution**
- Multi-language support (Python, JavaScript, Bash, Ruby, Go)
- Safe sandboxed execution
- Docker container isolation (optional)
- Timeout and resource limits

🧠 **LLM Integration**
- OpenAI GPT-4 support
- Anthropic Claude support
- Intelligent task planning
- Autonomous goal-directed behavior

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- (Optional) Docker for isolated code execution

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.json` file with your API keys:

```json
{
  "llm_config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "openai_api_key": "your-openai-key",
    "anthropic_api_key": "your-anthropic-key"
  },
  "search_config": {
    "engine": "duckduckgo",
    "max_results": 10
  },
  "executor_config": {
    "safe_mode": true,
    "timeout": 30,
    "use_docker": false
  },
  "computer_config": {
    "allowed_actions": ["screenshot", "mouse", "keyboard"],
    "safe_mode": true
  }
}
```

## Usage

### Basic Usage

```python
import asyncio
from agent import AutonomousAgent

async def main():
    # Load configuration
    with open('config.json') as f:
        config = json.load(f)

    # Initialize agent
    agent = AutonomousAgent(config)

    # Run a task
    result = await agent.run("Search for the latest AI news and summarize")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Autonomous Mode

```python
# Run agent autonomously towards a goal
result = await agent.run_autonomous(
    goal="Find the top 5 Python libraries for data science and create a comparison",
    max_iterations=10
)
```

### Individual Capabilities

#### Web Search
```python
searcher = WebSearcher(config['search_config'])
results = await searcher.search("artificial intelligence trends")
```

#### Code Execution
```python
executor = CodeExecutor(config['executor_config'])
result = await executor.execute(
    code="print('Hello, World!')",
    language="python"
)
```

#### Computer Control
```python
controller = ComputerController(config['computer_config'])
screenshot = await controller.take_screenshot()
```

## Architecture

```
┌─────────────────────────────────────┐
│      Autonomous Agent Core          │
│  (Task Planning & Orchestration)    │
└───────────┬─────────────────────────┘
            │
   ┌────────┼────────────────┐
   │        │                │
   ▼        ▼                ▼
┌──────┐ ┌──────┐ ┌────────────┐
│ LLM  │ │Search│ │  Computer  │
│Inter-│ │ API  │ │  Control   │
│face  │ └──────┘ └────────────┘
└──────┘      │           │
   │          ▼           ▼
   │    ┌─────────┐ ┌─────────┐
   │    │   Web   │ │  System │
   │    │Scraping │ │   API   │
   │    └─────────┘ └─────────┘
   │
   ▼
┌──────────────┐
│Code Executor │
│  (Sandbox)   │
└──────────────┘
```

## Safety Features

- **Safe Mode**: Simulates dangerous operations instead of executing them
- **Permission Controls**: Whitelist allowed actions
- **Sandboxing**: Execute code in isolated environments
- **Timeouts**: Prevent infinite loops and hangs
- **Resource Limits**: Memory and CPU constraints
- **Code Validation**: Check for dangerous operations

## Examples

### Example 1: Research Assistant
```python
result = await agent.run(
    "Research the latest developments in quantum computing and create a summary"
)
```

### Example 2: Data Analysis
```python
result = await agent.run(
    "Download data from example.com/data.csv, analyze it, and create visualizations"
)
```

### Example 3: Automation
```python
result = await agent.run(
    "Take a screenshot, find all buttons on screen, and document their positions"
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Considerations

⚠️ **Important**: This agent can execute arbitrary code and control your computer. Always:

- Run in a virtual machine or container for testing
- Review all code before execution
- Use safe mode for untrusted operations
- Keep API keys secure
- Monitor agent actions
- Set appropriate permission limits

## Roadmap

- [ ] Add more LLM providers (Llama, Mistral, etc.)
- [ ] Implement multi-agent collaboration
- [ ] Add visual understanding capabilities
- [ ] Create web UI for agent control
- [ ] Add memory persistence and learning
- [ ] Implement plugin system for extensions
- [ ] Add more programming language support
- [ ] Improve autonomous decision-making

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

Built with:
- [PyAutoGUI](https://pyautogui.readthedocs.io/) for computer control
- [OpenAI API](https://openai.com/) for language models
- [Anthropic API](https://www.anthropic.com/) for Claude
- [Docker](https://www.docker.com/) for code sandboxing
- [aiohttp](https://docs.aiohttp.org/) for async HTTP
