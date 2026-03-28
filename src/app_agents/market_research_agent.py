"""Market research agent for competitive and market analysis."""

import sys
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field
from agents import Agent, WebSearchTool, ModelSettings, AgentOutputSchema

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

INSTRUCTIONS = """You are a market research expert specializing in competitive analysis and market intelligence.
Given a business query or market research request, you should:

1. Identify key competitors and market players
2. Analyze market size, growth trends, and opportunities
3. Assess competitive positioning and differentiation
4. Identify industry trends and emerging patterns
5. Evaluate market barriers and entry strategies
6. Provide SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
7. Assess market segmentation and target audiences
8. Identify key success factors in the market

Use web search to gather current market data, competitor information, industry reports, and trend analysis.
Synthesize information from multiple sources to provide comprehensive market insights.

Your analysis should be data-driven, current, and actionable."""

class MarketAnalysis(BaseModel):
    """Market analysis result."""
    market_size: str = Field(description="Estimated market size and growth rate")
    key_competitors: List[str] = Field(description="List of main competitors in the market")
    competitive_landscape: str = Field(description="Analysis of competitive positioning and market share")
    market_trends: List[str] = Field(description="Key trends affecting the market")
    opportunities: List[str] = Field(description="Market opportunities identified")
    threats: List[str] = Field(description="Market threats and challenges")
    swot_analysis: Dict[str, List[str]] = Field(description="SWOT analysis with Strengths, Weaknesses, Opportunities, Threats")
    market_segments: List[str] = Field(description="Key market segments identified")
    entry_barriers: List[str] = Field(description="Barriers to market entry")
    recommendations: List[str] = Field(description="Strategic recommendations based on market analysis")
    sources: List[str] = Field(description="Key sources and references used")

market_research_agent = Agent(
    name="MarketResearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size=config.web_search_context_size)],
    model=config.market_model,
    model_settings=ModelSettings(
        tool_choice="required"
    ),
    output_type=AgentOutputSchema(MarketAnalysis, strict_json_schema=False),
)
