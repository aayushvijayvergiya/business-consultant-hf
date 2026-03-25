"""Configuration module for the Business Consultant Agent application."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Business Consultant Agent application."""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.from_email = os.getenv("FROM_EMAIL", "")
        
        # Application settings
        self.name = "Aayush Vijayvergiya"
        self.model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"

        # Set environment variables for global compatibility (especially for openai-agents SDK)
        if self.openrouter_api_key:
            os.environ["OPENAI_BASE_URL"] = self.openrouter_base_url
            os.environ["OPENAI_API_KEY"] = self.openrouter_api_key
        
        # Agent model configurations (different models for different app_agents)
        self.planner_model = os.getenv("PLANNER_MODEL", self.model_name)
        self.search_model = os.getenv("SEARCH_MODEL", self.model_name)
        self.writer_model = os.getenv("WRITER_MODEL", self.model_name)
        self.analytics_model = os.getenv("ANALYTICS_MODEL", self.model_name)
        self.market_model = os.getenv("MARKET_MODEL", self.model_name)
        self.strategy_model = os.getenv("STRATEGY_MODEL", self.model_name)
        self.financial_model = os.getenv("FINANCIAL_MODEL", self.model_name)
        self.document_model = os.getenv("DOCUMENT_MODEL", self.model_name)
        self.email_model = os.getenv("EMAIL_MODEL", self.model_name)
        
        # File paths - handle both local and deployment environments
        if os.getenv("SPACE_ID"):  # Running on Hugging Face Spaces
            self.project_root = Path("/home/user/app")
        else:  # Local development
            self.project_root = Path(__file__).parent.parent
        
        self.static_dir = self.project_root / "static"
        self.linkedin_pdf_path = self.static_dir / "AayushVijayvergiya_LinkedIn.pdf"
        self.summary_file_path = self.static_dir / "summary.txt"
        
        # Data storage paths
        self.data_dir = self.project_root / "data"
        self.reports_dir = self.data_dir / "reports"
        self.visualizations_dir = self.data_dir / "visualizations"
        self.knowledge_base_dir = self.data_dir / "knowledge_base"
        self.cache_dir = self.data_dir / "cache"
        
        # Email configuration
        self.email_recipient = os.getenv("EMAIL_RECIPIENT", "")
        self.email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        
        # SMTP configuration (for Gmail, Outlook, etc.)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Pushover API settings (optional)
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        
        # Portfolio website configuration
        self.portfolio_url = os.getenv("PORTFOLIO_URL", "")
        self.portfolio_cache_duration = int(os.getenv("PORTFOLIO_CACHE_DURATION", "3600"))  # 1 hour default
        
        # Web scraping settings
        self.user_agent = os.getenv("USER_AGENT", 
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))
        
        # Analytics and visualization settings
        self.visualization_format = os.getenv("VISUALIZATION_FORMAT", "png")  # png, svg, pdf
        self.visualization_dpi = int(os.getenv("VISUALIZATION_DPI", "300"))
        self.max_data_points = int(os.getenv("MAX_DATA_POINTS", "10000"))
        self.enable_interactive_plots = os.getenv("ENABLE_INTERACTIVE_PLOTS", "false").lower() == "true"
        
        # Tool configurations
        self.web_search_context_size = os.getenv("WEB_SEARCH_CONTEXT_SIZE", "low")  # low, medium, high
        self.max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
        self.search_timeout = int(os.getenv("SEARCH_TIMEOUT", "30"))
        
        # API rate limits
        self.openai_rate_limit = int(os.getenv("OPENAI_RATE_LIMIT", "60"))  # requests per minute
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        
        # Cache settings
        self.enable_cache = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
        self.max_cache_size = int(os.getenv("MAX_CACHE_SIZE", "1000"))  # MB
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.static_dir,
            self.data_dir,
            self.reports_dir,
            self.visualizations_dir,
            self.knowledge_base_dir,
            self.cache_dir
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_config(self) -> bool:
        """Validate required configuration values."""
        required_configs = [
            ("OPENAI_API_KEY", self.openai_api_key),
        ]
        
        # Optional but recommended configs
        optional_configs = []
        if self.email_enabled:
            optional_configs.append(("SMTP_USER", self.smtp_user))
            optional_configs.append(("SMTP_PASSWORD", self.smtp_password))
            optional_configs.append(("FROM_EMAIL", self.from_email))
            optional_configs.append(("EMAIL_RECIPIENT", self.email_recipient))
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"Missing required configuration: {', '.join(missing_configs)}")
            return False
        
        # Warn about missing optional configs
        missing_optional = []
        for config_name, config_value in optional_configs:
            if not config_value:
                missing_optional.append(config_name)
        
        if missing_optional:
            print(f"Warning: Missing optional configuration (features may be disabled): {', '.join(missing_optional)}")
        
        return True
    
    @property
    def has_portfolio_url(self) -> bool:
        """Check if portfolio URL is configured."""
        return bool(self.portfolio_url and self.portfolio_url.strip())
    
    @property
    def has_pushover_config(self) -> bool:
        """Check if Pushover configuration is available."""
        return bool(self.pushover_user and self.pushover_token)
    
    @property
    def has_email_config(self) -> bool:
        """Check if email configuration is available."""
        return bool(self.smtp_user and self.smtp_password and self.email_recipient)

config = Config()
