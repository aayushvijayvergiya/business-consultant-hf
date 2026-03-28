"""Financial agent for financial analysis and modeling."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agents import Agent, AgentOutputSchema

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

INSTRUCTIONS = """You are a financial analyst and business consultant specializing in financial analysis, 
budgeting, forecasting, and investment analysis.

Given financial data, business information, or financial questions, you should:

1. **Financial Statement Analysis**: Analyze income statements, balance sheets, and cash flow statements
2. **Budget Planning**: Create comprehensive budgets and financial plans
3. **Forecasting**: Develop financial forecasts and projections
4. **ROI Calculations**: Calculate return on investment for various initiatives
5. **Cost-Benefit Analysis**: Perform cost-benefit analysis for business decisions
6. **Financial Risk Assessment**: Identify financial risks and recommend mitigation strategies
7. **Investment Recommendations**: Provide investment analysis and recommendations
8. **Financial Health Assessment**: Evaluate overall financial health and sustainability
9. **Cash Flow Management**: Analyze and recommend cash flow management strategies
10. **Financial Metrics**: Calculate and interpret key financial metrics (ROI, NPV, IRR, payback period, etc.)

Your analysis should be:
- Data-driven and accurate
- Based on sound financial principles
- Clear and actionable
- Include specific calculations and assumptions
- Consider both short-term and long-term implications
- Address financial risks and opportunities"""

class FinancialMetric(BaseModel):
    """Financial metric calculation."""
    metric_name: str = Field(description="Name of the financial metric")
    value: float = Field(description="Calculated value")
    unit: str = Field(description="Unit of measurement (e.g., percentage, dollars, ratio)")
    interpretation: str = Field(description="Interpretation of the metric")
    benchmark: Optional[str] = Field(description="Industry benchmark or target value")

class ROIAnalysis(BaseModel):
    """ROI analysis result."""
    investment_amount: float = Field(description="Total investment amount")
    expected_return: float = Field(description="Expected return over the period")
    roi_percentage: float = Field(description="Return on Investment as percentage")
    payback_period: str = Field(description="Payback period in months/years")
    npv: Optional[float] = Field(description="Net Present Value if applicable")
    irr: Optional[float] = Field(description="Internal Rate of Return if applicable")
    recommendation: str = Field(description="Recommendation based on ROI analysis")

class FinancialAnalysis(BaseModel):
    """Comprehensive financial analysis."""
    executive_summary: str = Field(description="Executive summary of financial analysis")
    financial_health: str = Field(description="Assessment of overall financial health")
    key_metrics: List[FinancialMetric] = Field(description="Key financial metrics calculated and analyzed")
    budget_recommendations: Dict[str, Any] = Field(description="Budget planning recommendations with allocations")
    forecasts: Dict[str, Any] = Field(description="Financial forecasts and projections (revenue, expenses, cash flow)")
    roi_analyses: List[ROIAnalysis] = Field(description="ROI analyses for various initiatives or investments")
    cost_benefit_analyses: List[Dict[str, Any]] = Field(description="Cost-benefit analyses for key business decisions")
    financial_risks: List[Dict[str, str]] = Field(description="Identified financial risks with mitigation strategies")
    investment_recommendations: List[str] = Field(description="Investment recommendations based on financial analysis")
    cash_flow_analysis: str = Field(description="Cash flow analysis and management recommendations")
    action_items: List[str] = Field(description="Actionable financial recommendations and next steps")

def calculate_roi(investment: float, return_amount: float, period_years: float = 1.0) -> Dict[str, Any]:
    """Calculate Return on Investment."""
    if investment == 0: return {"error": "Investment amount cannot be zero"}
    roi = ((return_amount - investment) / investment) * 100
    annualized_roi = roi / period_years if period_years > 0 else roi
    return {
        "roi_percentage": round(roi, 2),
        "annualized_roi": round(annualized_roi, 2),
        "net_profit": round(return_amount - investment, 2),
        "investment": investment,
        "return": return_amount,
        "period_years": period_years
    }

def calculate_npv(cash_flows: List[float], discount_rate: float = 0.1, initial_investment: float = 0) -> Dict[str, Any]:
    """Calculate Net Present Value."""
    npv = -initial_investment
    pv_flows = []
    for i, cash_flow in enumerate(cash_flows, start=1):
        pv = cash_flow / ((1 + discount_rate) ** i)
        npv += pv
        pv_flows.append({"period": i, "cash_flow": cash_flow, "present_value": round(pv, 2)})
    return {
        "npv": round(npv, 2),
        "discount_rate": discount_rate,
        "initial_investment": initial_investment,
        "present_value_flows": pv_flows,
        "recommendation": "Proceed" if npv > 0 else "Do not proceed"
    }

def calculate_payback_period(initial_investment: float, annual_cash_flows: List[float]) -> Dict[str, Any]:
    """Calculate payback period."""
    cumulative = 0
    payback_period = None
    for i, cash_flow in enumerate(annual_cash_flows, start=1):
        cumulative += cash_flow
        if cumulative >= initial_investment and payback_period is None:
            if i == 1: payback_period = initial_investment / cash_flow
            else:
                previous_cumulative = cumulative - cash_flow
                remaining = initial_investment - previous_cumulative
                payback_period = (i - 1) + (remaining / cash_flow)
            break
    if payback_period is None: payback_period = len(annual_cash_flows) + 1
    return {
        "payback_period_years": round(payback_period, 2),
        "payback_period_months": round(payback_period * 12, 1),
        "initial_investment": initial_investment,
        "total_cash_flows": sum(annual_cash_flows)
    }

financial_agent = Agent(
    name="FinancialAgent",
    instructions=INSTRUCTIONS,
    model=config.financial_model,
    output_type=AgentOutputSchema(FinancialAnalysis, strict_json_schema=False),
)
