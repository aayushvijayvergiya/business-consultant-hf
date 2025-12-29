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


class ResearchManager:
    """Enhanced research manager with dynamic agent selection and optimization."""
    
    def __init__(self):
        """Initialize the research manager."""
        self.max_retries = 3
        self.quality_threshold = 0.7  # Minimum quality score for results
    
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
        
        Args:
            query: The business query to research
            include_analytics: Whether to include data analytics (None = auto-detect)
            include_market_research: Whether to include market research (None = auto-detect)
            include_strategy: Whether to include strategy analysis (None = auto-detect)
            include_financial: Whether to include financial analysis (None = auto-detect)
        """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            
            # Dynamic agent selection
            query_type = self._detect_query_type(query)
            print(f"Detected query type: {query_type}")
            
            # Override with explicit parameters if provided
            if include_analytics is not None:
                query_type["analytics"] = include_analytics
            if include_market_research is not None:
                query_type["market_research"] = include_market_research
            if include_strategy is not None:
                query_type["strategy"] = include_strategy
            if include_financial is not None:
                query_type["financial"] = include_financial
            
            # Plan searches
            search_plan = await self._run_with_fallback(self.plan_searches, query)
            if not search_plan:
                yield "Error: Could not plan searches. Using default search plan."
                # Fallback: create a simple search plan
                from .planner_agent import WebSearchItem
                search_plan = type('WebSearchPlan', (), {
                    'searches': [WebSearchItem(query=query, reason="General research")]
                })()
            
            yield "Searches planned, starting to search..."
            
            # Optimize parallel execution - group tasks by type
            tasks = {}
            
            # Web searches (always performed)
            tasks["searches"] = [asyncio.create_task(
                self._run_with_fallback(self.search, item)
            ) for item in search_plan.searches]
            
            # Market research (if needed)
            if query_type.get("market_research", False):
                tasks["market"] = [asyncio.create_task(
                    self._run_with_fallback(self.perform_market_research, query)
                )]
            
            # Analytics (if needed and data available)
            if query_type.get("analytics", False):
                # Will be executed after searches complete
                tasks["analytics"] = []
            
            # Strategy (if needed)
            if query_type.get("strategy", False):
                tasks["strategy"] = []
            
            # Financial (if needed)
            if query_type.get("financial", False):
                tasks["financial"] = []
            
            # Collect search results with quality check
            search_results = []
            completed_searches = 0
            for task in asyncio.as_completed(tasks["searches"]):
                result = await task
                quality = self._validate_result_quality(result, "search")
                if result is not None and quality >= self.quality_threshold:
                    search_results.append(result)
                completed_searches += 1
                yield f"Search progress: {completed_searches}/{len(tasks['searches'])} completed"
            
            yield f"Searches complete ({len(search_results)} quality results), analyzing..."
            
            # Get market research results
            market_analysis = None
            if "market" in tasks and tasks["market"]:
                try:
                    market_analysis = await tasks["market"][0]
                    quality = self._validate_result_quality(market_analysis, "market")
                    if quality < self.quality_threshold:
                        yield "Market research quality below threshold, continuing without it..."
                        market_analysis = None
                    else:
                        yield "Market research complete..."
                except Exception as e:
                    print(f"Market research error: {e}")
                    yield "Market research encountered an error, continuing..."
            
            # Perform analytics if requested and data is available
            analytics_result = None
            if query_type.get("analytics", False) and search_results:
                try:
                    yield "Performing data analysis..."
                    analytics_result = await self._run_with_fallback(
                        self.perform_analytics, search_results
                    )
                    quality = self._validate_result_quality(analytics_result, "analytics")
                    if quality < self.quality_threshold:
                        yield "Analytics quality below threshold, continuing without it..."
                        analytics_result = None
                    else:
                        yield "Data analysis complete..."
                except Exception as e:
                    print(f"Analytics error: {e}")
                    yield "Analytics encountered an error, continuing..."
            
            # Perform strategy analysis if needed
            strategy_plan = None
            if query_type.get("strategy", False):
                try:
                    yield "Performing strategic analysis..."
                    strategy_plan = await self._run_with_fallback(
                        self.perform_strategy_analysis, query, search_results, market_analysis
                    )
                    yield "Strategic analysis complete..."
                except Exception as e:
                    print(f"Strategy error: {e}")
                    yield "Strategy analysis encountered an error, continuing..."
            
            # Perform financial analysis if needed
            financial_analysis = None
            if query_type.get("financial", False):
                try:
                    yield "Performing financial analysis..."
                    financial_analysis = await self._run_with_fallback(
                        self.perform_financial_analysis, query, search_results
                    )
                    yield "Financial analysis complete..."
                except Exception as e:
                    print(f"Financial error: {e}")
                    yield "Financial analysis encountered an error, continuing..."
            
            # Write comprehensive report with all available data
            yield "Compiling report..."
            report = await self._run_with_fallback(
                self.write_report,
                query,
                search_results,
                market_analysis=market_analysis,
                analytics_result=analytics_result,
                strategy_plan=strategy_plan,
                financial_analysis=financial_analysis
            )
            
            if not report:
                yield "Error: Could not generate report. Please try again."
                return
            
            yield "Report written, sending email..."
            
            # Send email if configured (with fallback)
            try:
                await self._run_with_fallback(self.send_email, report)
                yield "Email sent, research complete"
            except Exception as e:
                print(f"Email error: {e}")
                yield "Email sending failed, but research complete"
            
            yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def perform_market_research(self, query: str) -> Optional[MarketAnalysis]:
        """ Perform market research analysis """
        print("Performing market research...")
        try:
            result = await Runner.run(
                market_research_agent,
                f"Market research query: {query}",
            )
            return result.final_output_as(MarketAnalysis)
        except Exception as e:
            print(f"Market research error: {e}")
            return None

    async def perform_analytics(self, data: list[str]) -> Optional[AnalyticsResult]:
        """ Perform data analytics on search results """
        print("Performing analytics...")
        try:
            # Combine search results into a data string
            data_str = "\n".join(data)
            result = await Runner.run(
                analytics_agent,
                f"Analyze this business data:\n{data_str}",
            )
            return result.final_output_as(AnalyticsResult)
        except Exception as e:
            print(f"Analytics error: {e}")
            return None

    async def perform_strategy_analysis(
        self,
        query: str,
        search_results: List[str],
        market_analysis: Optional[MarketAnalysis] = None
    ) -> Optional[StrategicPlan]:
        """Perform strategic analysis."""
        print("Performing strategy analysis...")
        try:
            input_parts = [f"Strategic analysis query: {query}"]
            input_parts.append(f"\nResearch findings: {search_results}")
            if market_analysis:
                input_parts.append(f"\nMarket context: {market_analysis.market_size}")
            
            result = await Runner.run(
                strategy_agent,
                "\n".join(input_parts),
            )
            return result.final_output_as(StrategicPlan)
        except Exception as e:
            print(f"Strategy analysis error: {e}")
            return None
    
    async def perform_financial_analysis(
        self,
        query: str,
        search_results: List[str]
    ) -> Optional[FinancialAnalysis]:
        """Perform financial analysis."""
        print("Performing financial analysis...")
        try:
            input_text = f"Financial analysis query: {query}\n\nAvailable data: {search_results}"
            result = await Runner.run(
                financial_agent,
                input_text,
            )
            return result.final_output_as(FinancialAnalysis)
        except Exception as e:
            print(f"Financial analysis error: {e}")
            return None

    async def write_report(
        self, 
        query: str, 
        search_results: list[str],
        market_analysis: Optional[MarketAnalysis] = None,
        analytics_result: Optional[AnalyticsResult] = None,
        strategy_plan: Optional[StrategicPlan] = None,
        financial_analysis: Optional[FinancialAnalysis] = None
    ) -> ReportData:
        """ Write the comprehensive report with all available data """
        print("Thinking about report...")
        
        # Build input with all available information
        input_parts = [f"Original query: {query}"]
        input_parts.append(f"\nSummarized search results: {search_results}")
        
        if market_analysis:
            input_parts.append(f"\nMarket Analysis:\n")
            input_parts.append(f"Market Size: {market_analysis.market_size}")
            input_parts.append(f"Key Competitors: {', '.join(market_analysis.key_competitors)}")
            input_parts.append(f"Competitive Landscape: {market_analysis.competitive_landscape}")
            input_parts.append(f"Market Trends: {', '.join(market_analysis.market_trends)}")
            input_parts.append(f"Opportunities: {', '.join(market_analysis.opportunities)}")
            input_parts.append(f"SWOT Analysis: {market_analysis.swot_analysis}")
        
        if analytics_result:
            input_parts.append(f"\nData Analytics:\n")
            input_parts.append(f"Summary: {analytics_result.summary}")
            input_parts.append(f"Statistics: {analytics_result.statistics}")
            input_parts.append(f"Insights: {', '.join(analytics_result.insights)}")
            if analytics_result.visualization_paths:
                input_parts.append(f"Visualizations available at: {', '.join(analytics_result.visualization_paths)}")
        
        if strategy_plan:
            input_parts.append(f"\nStrategic Plan:\n")
            input_parts.append(f"Executive Summary: {strategy_plan.executive_summary}")
            input_parts.append(f"Strategic Goals: {', '.join(strategy_plan.strategic_goals)}")
            input_parts.append(f"Recommendations: {len(strategy_plan.recommendations)} strategic recommendations")
            input_parts.append(f"Implementation Roadmap: {len(strategy_plan.implementation_roadmap)} milestones")
        
        if financial_analysis:
            input_parts.append(f"\nFinancial Analysis:\n")
            input_parts.append(f"Executive Summary: {financial_analysis.executive_summary}")
            input_parts.append(f"Financial Health: {financial_analysis.financial_health}")
            input_parts.append(f"Key Metrics: {len(financial_analysis.key_metrics)} metrics calculated")
            if financial_analysis.roi_analyses:
                input_parts.append(f"ROI Analyses: {len(financial_analysis.roi_analyses)} analyses")
        
        input_text = "\n".join(input_parts)
        
        result = await Runner.run(
            writer_agent,
            input_text,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        """Send email with the report"""
        print("Writing email...")
        try:
            result = await Runner.run(
                email_agent,
                report.markdown_report,
            )
            print("Email sent")
        except Exception as e:
            print(f"Email sending error: {e}")
            raise
        return report