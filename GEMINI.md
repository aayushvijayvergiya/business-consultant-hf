# Business Consultant Agent Project Overview

This project is a multi-agent business consulting system designed to provide deep research, analysis, and strategic recommendations. It leverages a collaborative agentic pattern using the OpenAI Agents SDK (or OpenRouter via OpenAI-compatible settings).

## Project Overview

- **Purpose**: An AI-powered business consultant that uses specialized agents to answer complex business queries.
- **Core Architecture**: A multi-agent system where a `ResearchManager` orchestrates various specialized agents (Search, Planner, Writer, Analytics, Market Research, Strategy, Financial, Document, and Email).
- **Interface**: Built with Gradio, providing a chat-based UI with report previews and data visualizations.
- **Key Technologies**:
    - **LLM Interaction**: `openai-agents` (configured for OpenRouter/OpenAI).
    - **Web Search**: `duckduckgo-search` (via `WebSearchTool`).
    - **Data Processing & Viz**: `pandas`, `numpy`, `matplotlib`, `seaborn`, `plotly`.
    - **Document Processing**: `pypdf`.
    - **Reporting**: `markdown`, `weasyprint` (for PDF generation).
    - **Communication**: SMTP for email delivery.

## Building and Running

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)
- API Keys: `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`)

### Setup
1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
2. **Configure Environment**:
   Create a `.env` file based on `.env.example` (or the existing `.env`):
   ```env
   OPENROUTER_API_KEY=your_key
   OPENROUTER_MODEL=openai/gpt-4o-mini
   # Optional SMTP settings for email delivery
   ```

### Running the Application
To start the Gradio interface:
```powershell
python app.py
```
This is the entry point for both local development and Hugging Face Spaces deployment.

### Running Tests
```powershell
pytest tests/
```

## Project Structure & Architecture

- **`app.py`**: Main entry point for the Gradio application.
- **`src/`**:
    - **`app_agents/`**: Contains the logic for all specialized agents.
        - `consultant_manager.py`: The `ResearchManager` class that orchestrates the research flow.
        - `interface_agent.py`: Handles initial user interaction and prompt refinement.
        - Specialized agents: `planner_agent.py`, `search_agent.py`, `writer_agent.py`, `analytics_agent.py`, etc.
    - **`services/`**: Supporting services.
        - `chat_service.py`: High-level chat orchestration.
        - `config.py`: Centralized configuration management and environment variable handling.
- **`data/`**: Persistent storage for reports, visualizations, and cache.

## Development Conventions

- **Agent Definition**: Agents are defined using the `agents.Agent` class from the `openai-agents` SDK.
- **Tooling**: Most agents use custom tools or built-in tools like `WebSearchTool`.
- **Data Flow**: The `ResearchManager` uses `asyncio` to run independent tasks (like multiple web searches) in parallel.
- **Output Schemas**: Specialized agents often use `Pydantic` models with `AgentOutputSchema` to ensure structured output.
- **Configuration**: All API keys and model names should be accessed via the `config` object in `src/config.py`.
- **Documentation**: All docmentation goes in docs folder(create if not already there). Divided into subfolders for each category of documentation. Plan goes into plan folder with format plan-<idea in 2/3 words>-<current date>.md. Fixes plan goes into fixes folder with format fixes-<fixes in 2/3 words>-<current date>.md. Reviews goes into reviews folder with format review-<review in 2/3 words>-<current date>.md. 

## Future Extensions
- **Knowledge Base**: The project has placeholders for a RAG-based knowledge base in `src/services/knowledge_base.py`.
- **Memory**: Conversation memory service is structured in `src/services/memory_service.py`.
