from agents import Runner, trace, gen_trace_id
from .search_agent import search_agent
from .planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from .writer_agent import writer_agent, ReportData
from .email_agent import email_agent
from .analytics_agent import analytics_agent, AnalyticsResult
from .market_research_agent import market_research_agent, MarketAnalysis
from .strategy_agent import strategy_agent, StrategicPlan
from .financial_agent import financial_agent, FinancialAnalysis
import asyncio
from typing import Optional, Dict, Any, List
from src.config import config


class ResearchManager:
    """Enhanced research manager with dynamic agent selection and optimization."""
    
    def __init__(self):
        """Initialize the research manager."""
        self.max_retries = config.max_retries
        self.quality_threshold = config.quality_threshold
    
    def _detect_query_type(self, query: str) -> Dict[str, bool]:
        """
        Dynamically detect query type to determine which app_agents to use.
        
        Args:
            query: The business query
            
        Returns:
            Dictionary indicating which app_agents should be used
        """
        query_lower = query.lower()
        
        # Financial keywords
        financial_keywords = ['financial', 'budget', 'roi', 'revenue', 'profit', 'cost', 'investment', 
                             'cash flow', 'forecast', 'financial statement', 'expense']
        needs_financial = any(keyword in query_lower for keyword in financial_keywords)
        
        # Strategy keywords
        strategy_keywords = ['strategy', 'strategic', 'plan', 'roadmap', 'goal', 'objective', 
                            'recommendation', 'approach', 'direction', 'vision']
        needs_strategy = any(keyword in query_lower for keyword in strategy_keywords)
        
        # Market research keywords
        market_keywords = ['market', 'competitor', 'competitive', 'industry', 'trend', 'swot', 
                          'opportunity', 'threat', 'landscape']
        needs_market = any(keyword in query_lower for keyword in market_keywords)
        
        # Analytics keywords
        analytics_keywords = ['data', 'analyze', 'analysis', 'metric', 'kpi', 'statistic', 
                             'visualization', 'chart', 'graph', 'trend']
        needs_analytics = any(keyword in query_lower for keyword in analytics_keywords)
        
        # Document processing keywords
        document_keywords = ['document', 'pdf', 'file', 'extract', 'parse', 'business plan']
        needs_document = any(keyword in query_lower for keyword in document_keywords)
        
        return {
            "financial": needs_financial,
            "strategy": needs_strategy,
            "market_research": needs_market or needs_strategy,  # Market research often needed for strategy
            "analytics": needs_analytics,
            "document": needs_document,
            "search": True,  # Always perform web search
        }
    
    def _validate_result_quality(self, result: Any, result_type: str) -> float:
        """
        Validate the quality of an agent result.
        
        Args:
            result: The result to validate
            result_type: Type of result (search, market, analytics, etc.)
            
        Returns:
            Quality score between 0 and 1
        """
        if result is None:
            return 0.0
        
        score = 0.5  # Base score
        
        if result_type == "search":
            if isinstance(result, str):
                # Check length and content
                if len(result) > 100:
                    score += 0.2
                if len(result) > 500:
                    score += 0.2
                if any(keyword in result.lower() for keyword in ['analysis', 'data', 'research', 'study']):
                    score += 0.1
        
        elif result_type == "market":
            if hasattr(result, 'market_size') and result.market_size:
                score += 0.2
            if hasattr(result, 'key_competitors') and result.key_competitors:
                score += 0.2
            if hasattr(result, 'swot_analysis') and result.swot_analysis:
                score += 0.1
        
        elif result_type == "analytics":
            if hasattr(result, 'summary') and result.summary:
                score += 0.2
            if hasattr(result, 'statistics') and result.statistics:
                score += 0.2
            if hasattr(result, 'insights') and result.insights:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _run_with_fallback(self, agent_func, *args, **kwargs) -> Optional[Any]:
        """
        Run an agent function with retry and fallback logic.
        
        Args:
            agent_func: The agent function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                result = await agent_func(*args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    print(f"All {self.max_retries} attempts failed for {agent_func.__name__}")
        return None

    async def run(
        self, 
        query: str, 
        include_analytics: bool = None,
        include_market_research: bool = None,
        include_strategy: bool = None,
        include_financial: bool = None
    ):
        """ 
        Run the deep research process with dynamic agent selection and optimization.
        """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            
            # 1. Initialization & Planning
            query_type = self._detect_query_type(query)
            if include_analytics is not None: query_type["analytics"] = include_analytics
            if include_market_research is not None: query_type["market_research"] = include_market_research
            if include_strategy is not None: query_type["strategy"] = include_strategy
            if include_financial is not None: query_type["financial"] = include_financial
            
            search_plan = await self._run_with_fallback(self.plan_searches, query)
            if not search_plan:
                yield "Error: Could not plan searches. Using default search plan."
                search_plan = type('WebSearchPlan', (), {'searches': [WebSearchItem(query=query, reason="General research")]})()
            
            yield "Searches planned, starting research..."

            # 2. Research Phase (Parallel Execution)
            research_results = await self._execute_research_phase(query, query_type, search_plan)
            # We need to yield progress from here too, but for now we'll collect and continue
            # Optimization: could make research phase a generator itself
            
            # To maintain Gradio UI progress updates, we'll keep the monolithic structure but cleaner
            # or use internal progress tracking. Let's do a semi-monolithic for now to preserve yields easily.
            
            search_tasks = [asyncio.create_task(self._run_with_fallback(self.search, item)) for item in search_plan.searches]
            search_results = []
            completed_searches = 0
            for task in asyncio.as_completed(search_tasks):
                result = await task
                if result and self._validate_result_quality(result, "search") >= self.quality_threshold:
                    search_results.append(result)
                completed_searches += 1
                yield f"Search progress: {completed_searches}/{len(search_tasks)} completed"

            # 3. Specialized Analysis Phase
            market_analysis = None
            if query_type.get("market_research"):
                yield "Performing market research..."
                market_analysis = await self._run_with_fallback(self.perform_market_research, query)
                yield "Market research complete."

            analytics_result = None
            if query_type.get("analytics") and search_results:
                yield "Performing data analysis..."
                analytics_result = await self._run_with_fallback(self.perform_analytics, search_results)
                yield "Data analysis complete."

            strategy_plan = None
            if query_type.get("strategy"):
                yield "Performing strategic analysis..."
                strategy_plan = await self._run_with_fallback(self.perform_strategy_analysis, query, search_results, market_analysis)
                yield "Strategic analysis complete."

            financial_analysis = None
            if query_type.get("financial"):
                yield "Performing financial analysis..."
                financial_analysis = await self._run_with_fallback(self.perform_financial_analysis, query, search_results)
                yield "Financial analysis complete."

            # 4. Reporting Phase
            yield "Compiling final report..."
            report = await self._run_with_fallback(
                self.write_report, query, search_results, market_analysis, analytics_result, strategy_plan, financial_analysis
            )
            
            if not report:
                yield "Error: Could not generate report."
                return
            
            yield "Report written, sending email..."
            try:
                await self._run_with_fallback(self.send_email, report)
                yield "Email sent, research complete."
            except Exception:
                yield "Email sending failed, but research complete."
            
            yield report.markdown_report

    async def _execute_research_phase(self, query, query_type, search_plan):
        # Placeholder if we want to fully modularize
        pass

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        try:
            result = await Runner.run(search_agent, f"Search term: {item.query}\nReason: {item.reason}")
            return str(result.final_output)
        except Exception:
            return None

    async def perform_market_research(self, query: str) -> Optional[MarketAnalysis]:
        """ Perform market research analysis """
        try:
            result = await Runner.run(market_research_agent, f"Market research query: {query}")
            return result.final_output_as(MarketAnalysis)
        except Exception:
            return None

    async def perform_analytics(self, data: list[str]) -> Optional[AnalyticsResult]:
        """ Perform data analytics on search results """
        try:
            result = await Runner.run(analytics_agent, f"Analyze this business data:\n" + "\n".join(data))
            return result.final_output_as(AnalyticsResult)
        except Exception:
            return None

    async def perform_strategy_analysis(self, query, search_results, market_analysis) -> Optional[StrategicPlan]:
        """Perform strategic analysis."""
        try:
            input_parts = [f"Strategic analysis query: {query}", f"Findings: {search_results}"]
            if market_analysis: input_parts.append(f"Market context: {market_analysis.market_size}")
            result = await Runner.run(strategy_agent, "\n".join(input_parts))
            return result.final_output_as(StrategicPlan)
        except Exception:
            return None
    
    async def perform_financial_analysis(self, query, search_results) -> Optional[FinancialAnalysis]:
        """Perform financial analysis."""
        try:
            result = await Runner.run(financial_agent, f"Financial analysis query: {query}\nData: {search_results}")
            return result.final_output_as(FinancialAnalysis)
        except Exception:
            return None

    async def write_report(self, query, search_results, market_analysis, analytics_result, strategy_plan, financial_analysis) -> ReportData:
        """ Write the comprehensive report """
        input_parts = [f"Original query: {query}", f"Search results: {search_results}"]
        if market_analysis: input_parts.append(f"Market: {market_analysis.model_dump_json()}")
        if analytics_result: input_parts.append(f"Analytics: {analytics_result.model_dump_json()}")
        if strategy_plan: input_parts.append(f"Strategy: {strategy_plan.model_dump_json()}")
        if financial_analysis: input_parts.append(f"Financial: {financial_analysis.model_dump_json()}")
        
        result = await Runner.run(writer_agent, "\n".join(input_parts))
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        """Send email with the report"""
        await Runner.run(email_agent, report.markdown_report)
