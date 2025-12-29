# Multi-Agent Business Consultant System

A comprehensive AI-powered business consulting system that uses multiple specialized agents to provide deep research, analysis, and strategic recommendations for business queries.

## Overview

This system employs a multi-agent architecture where specialized AI agents collaborate to:
- Clarify and refine user queries
- Plan and execute comprehensive web research
- Perform data analysis and generate visualizations
- Conduct market and competitive analysis
- Generate strategic recommendations
- Create detailed business reports
- Deliver reports via email

## Architecture

The system consists of the following agents:

1. **Interface Agent** - Handles user interaction, query clarification, and coordination
2. **Planner Agent** - Plans research strategies and search queries
3. **Search Agent** - Performs web searches and summarizes results
4. **Analytics Agent** - Analyzes data and generates visualizations
5. **Market Research Agent** - Conducts competitive and market analysis
6. **Strategy Agent** - Generates strategic planning and recommendations
7. **Financial Agent** - Performs financial analysis and forecasting
8. **Document Agent** - Processes and analyzes business documents
9. **Writer Agent** - Compiles comprehensive business reports
10. **Email Agent** - Sends formatted reports via email

## Features

- **Multi-Agent Collaboration**: Specialized agents work together to provide comprehensive analysis
- **Real-time Progress Updates**: Status updates during research and analysis
- **Data Visualization**: Automatic generation of charts and graphs
- **Market Research**: Competitive landscape and industry trend analysis
- **Strategic Planning**: Actionable recommendations and roadmaps
- **Financial Analysis**: Budget planning, ROI calculations, and forecasting
- **Document Processing**: PDF parsing and business document analysis
- **Email Delivery**: Automated report delivery with rich HTML formatting

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd business_consultant_01
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key

Email Configuration (SMTP - Free):

- `SMTP_SERVER=smtp.gmail.com` - SMTP server (Gmail: smtp.gmail.com, Outlook: smtp-mail.outlook.com)
- `SMTP_PORT=587` - SMTP port (587 for TLS, 465 for SSL)
- `SMTP_USER=your_email@gmail.com` - Your email address
- `SMTP_PASSWORD=your_app_password` - App password (see setup below)
- `SMTP_USE_TLS=true` - Use TLS encryption (default: true)
- `FROM_EMAIL=your_email@gmail.com` - Sender email
- `EMAIL_RECIPIENT=recipient@example.com` - Default recipient
- `EMAIL_ENABLED=true` - Enable email functionality

**Gmail SMTP Setup:**
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Use that 16-character password as `SMTP_PASSWORD`

See `.env.example` for all available configuration options.

## Usage

### Running Locally

```bash
python app.py
```

### Running on Hugging Face Spaces

The application is configured for deployment on Hugging Face Spaces. Use `app.py` as the entry point.

## Project Structure

```
business_consultant_01/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── consultant_manager.py
│   ├── interface_agent.py
│   ├── planner_agent.py
│   ├── search_agent.py
│   ├── writer_agent.py
│   ├── email_agent.py
│   ├── analytics_agent.py
│   ├── market_research_agent.py
│   ├── strategy_agent.py
│   ├── financial_agent.py
│   └── document_agent.py
├── src/                    # Source code
│   ├── config.py           # Configuration management
│   ├── chat_launcher.py   # Gradio interface
│   └── services/           # Service layer
│       ├── chat_service.py
│       ├── knowledge_base.py
│       └── memory_service.py
├── static/                 # Static files
├── data/                   # Data storage
│   ├── reports/
│   ├── visualizations/
│   ├── knowledge_base/
│   └── cache/
├── tests/                  # Test files
├── app.py                  # Hugging Face entry point
├── main.py                 # Local entry point
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Agents

1. Create a new agent file in `agents/`
2. Define the agent using the OpenAI Agents SDK
3. Add tools and instructions
4. Integrate with `consultant_manager.py`
5. Update `agents/__init__.py` to export the new agent

## Dependencies

- `openai` - OpenAI API client
- `gradio` - Web interface
- `pandas`, `numpy` - Data analysis
- `matplotlib`, `seaborn`, `plotly` - Visualization
- SMTP (built-in) - Email delivery via SMTP
- `pypdf` - PDF processing
- `beautifulsoup4`, `requests` - Web scraping
- `pydantic` - Data validation

See `requirements.txt` for complete list.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]

