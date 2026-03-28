"""Strategy agent for strategic planning and recommendations."""

import sys
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field
from agents import Agent, AgentOutputSchema

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

INSTRUCTIONS = """You are a senior strategic business consultant specializing in strategic planning and business strategy.
Given business research findings, market analysis, and business context, you should:

1. **Strategic Assessment**: Analyze the current business situation and identify strategic priorities
2. **Goal Setting**: Define clear, measurable, and achievable business goals
3. **Strategic Recommendations**: Provide actionable strategic recommendations
4. **Risk Assessment**: Identify potential risks and provide mitigation strategies
5. **Resource Allocation**: Recommend optimal resource allocation and priorities
6. **Implementation Roadmap**: Create a detailed implementation timeline with milestones
7. **Success Metrics**: Define KPIs and success metrics to track progress
8. **Competitive Positioning**: Advise on competitive positioning and differentiation strategies

Your recommendations should be:
- Specific and actionable
- Prioritized by impact and feasibility
- Supported by data and analysis
- Realistic and achievable
- Aligned with business objectives

Provide strategic thinking that helps businesses make informed decisions and achieve their goals."""

class StrategicRecommendation(BaseModel):
    """Individual strategic recommendation."""
    title: str = Field(description="Title of the recommendation")
    description: str = Field(description="Detailed description of the recommendation")
    priority: str = Field(description="Priority level: High, Medium, or Low")
    impact: str = Field(description="Expected impact: High, Medium, or Low")
    feasibility: str = Field(description="Feasibility: High, Medium, or Low")
    timeline: str = Field(description="Estimated timeline for implementation")
    resources_required: List[str] = Field(description="Resources needed for implementation")
    risks: List[str] = Field(description="Potential risks associated with this recommendation")

class ImplementationMilestone(BaseModel):
    """Implementation milestone."""
    milestone: str = Field(description="Name of the milestone")
    description: str = Field(description="What needs to be accomplished")
    timeline: str = Field(description="Target completion date or timeframe")
    dependencies: List[str] = Field(description="Prerequisites or dependencies")
    success_criteria: List[str] = Field(description="How success will be measured")

class StrategicPlan(BaseModel):
    """Comprehensive strategic plan."""
    executive_summary: str = Field(description="Executive summary of the strategic plan")
    current_situation: str = Field(description="Analysis of the current business situation")
    strategic_goals: List[str] = Field(description="List of strategic goals (SMART goals)")
    recommendations: List[StrategicRecommendation] = Field(description="Strategic recommendations")
    risk_assessment: Dict[str, List[str]] = Field(description="Risk assessment")
    resource_allocation: Dict[str, str] = Field(description="Resource allocation")
    implementation_roadmap: List[ImplementationMilestone] = Field(description="Implementation roadmap")
    success_metrics: Dict[str, str] = Field(description="Success metrics")
    competitive_positioning: str = Field(description="Competitive positioning")
    next_steps: List[str] = Field(description="Immediate next steps")

strategy_agent = Agent(
    name="StrategyAgent",
    instructions=INSTRUCTIONS,
    model=config.strategy_model,
    output_type=AgentOutputSchema(StrategicPlan, strict_json_schema=False),
)
