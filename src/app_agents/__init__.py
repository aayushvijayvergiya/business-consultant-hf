"""Agents package for the Business Consultant Agent system."""

# Note: The 'app_agents' package import (Runner, trace, gen_trace_id, Agent, etc.)
# appears to be from OpenAI's Agents SDK or a similar package.
# If this is a separate package, it should be added to requirements.txt.
# For now, we'll export the agent classes for easier imports.

from .consultant_manager import ResearchManager
from .interface_agent import InterfaceAgent, get_interface_agent, run as interface_agent_run
from .planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from .search_agent import search_agent
from .writer_agent import writer_agent, ReportData, export_to_pdf, export_to_html
from .email_agent import email_agent
from .analytics_agent import analytics_agent, AnalyticsResult
from .market_research_agent import market_research_agent, MarketAnalysis
from .strategy_agent import strategy_agent, StrategicPlan
from .financial_agent import financial_agent, FinancialAnalysis
from .document_agent import document_agent, DocumentAnalysis

__all__ = [
    "ResearchManager",
    "InterfaceAgent",
    "get_interface_agent",
    "interface_agent_run",
    "planner_agent",
    "WebSearchItem",
    "WebSearchPlan",
    "search_agent",
    "writer_agent",
    "ReportData",
    "export_to_pdf",
    "export_to_html",
    "email_agent",
    "analytics_agent",
    "AnalyticsResult",
    "market_research_agent",
    "MarketAnalysis",
    "strategy_agent",
    "StrategicPlan",
    "financial_agent",
    "FinancialAnalysis",
    "document_agent",
    "DocumentAnalysis",
]

