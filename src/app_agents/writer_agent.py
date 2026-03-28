import sys
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field
from agents import Agent, AgentOutputSchema

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

INSTRUCTIONS = (
    "You are a senior business consultant and researcher tasked with writing a comprehensive, "
    "professional business report. You will be provided with:\n"
    "- The original query\n"
    "- Research findings from web searches\n"
    "- Data analysis and visualizations (if available)\n"
    "- Market research and competitive analysis (if available)\n"
    "- Strategic recommendations (if available)\n\n"
    
    "Your report should be structured with the following sections:\n"
    "1. **Executive Summary** - High-level overview (1-2 paragraphs)\n"
    "2. **Introduction** - Context and objectives\n"
    "3. **Research Findings** - Detailed findings from web research\n"
    "4. **Data Analysis** - If data/analytics provided, include analysis with references to visualizations\n"
    "5. **Market Analysis** - Competitive landscape, market trends, opportunities (if market research provided)\n"
    "6. **Strategic Recommendations** - Actionable recommendations based on findings\n"
    "7. **Conclusion** - Summary and next steps\n"
    "8. **Appendices** - Additional data, sources, or detailed information\n\n"
    
    "When including visualizations, reference them using markdown image syntax: "
    "![Chart Title](path/to/visualization.png)\n\n"
    
    "The report should be:\n"
    "- Professional and well-structured\n"
    "- Data-driven with specific insights\n"
    "- Actionable with clear recommendations\n"
    "- Comprehensive: 5-10 pages, at least 1000 words\n"
    "- Well-formatted in markdown with proper headings, lists, and emphasis\n"
    "- Include relevant statistics, quotes, and data points\n"
    "- Cite sources when referencing external information\n\n"
    
    "**CRITICAL OUTPUT FORMAT REQUIREMENTS:**\n"
    "- Put the COMPLETE markdown report in the 'markdown_report' field\n"
    "- Put a short 1-2 paragraph summary in 'short_summary'\n"
    "- Put 3-5 follow-up questions in 'follow_up_questions' (as a list)\n"
    "- All other fields (sections, visualization_references, key_metrics, sources) are OPTIONAL\n"
    "- Do NOT nest fields inside other fields. Each field is at the top level of the output.\n"
    "- The 'sections' field, if used, should ONLY contain text content as key-value pairs, nothing else."
)

class ReportData(BaseModel):
    """Enhanced report data with multiple sections and export formats.

    IMPORTANT: All fields are at the TOP LEVEL. Do not nest fields inside 'sections'.
    The 'sections' field is ONLY for storing individual section text content as key-value pairs.
    """

    short_summary: str = Field(
        description="Executive summary of the report, 1-2 paragraphs. This is a TOP-LEVEL field."
    )

    markdown_report: str = Field(
        description="The COMPLETE report in markdown format with ALL sections combined into one document. "
        "Should be 5-10 pages, at least 1000 words. Include proper markdown headings (# ## ###). "
        "Include references to visualizations using markdown image syntax. This is a TOP-LEVEL field."
    )
    
    follow_up_questions: list[str] = Field(
        description="A list of 3-5 follow-up questions that the user may ask based on the report. "
        "This is a TOP-LEVEL field, not inside sections."
    )

    sections: Optional[dict[str, str]] = Field(
        default=None,
        description="OPTIONAL: Individual text sections as key-value pairs where key is section name "
        "(like 'executive_summary', 'introduction') and value is the TEXT CONTENT ONLY (string). "
        "Do NOT put visualization_references, key_metrics, follow_up_questions, or sources inside this field."
    )

    visualization_references: Optional[list[str]] = Field(
        default=None,
        description="OPTIONAL: List of visualization file paths referenced in the report. "
        "This is a TOP-LEVEL field, not inside sections."
    )
    
    key_metrics: Optional[dict[str, str]] = Field(
        default=None,
        description="OPTIONAL: Key metrics as simple key-value string pairs. "
        "This is a TOP-LEVEL field, not inside sections."
    )

    sources: Optional[list[str]] = Field(
        default=None,
        description="OPTIONAL: List of source URLs or citations used in the report. "
        "This is a TOP-LEVEL field, not inside sections."
    )

def export_to_html(markdown_content: str) -> str:
    """Convert markdown report to HTML format."""
    try:
        import markdown
        html = markdown.markdown(markdown_content, extensions=['extra', 'codehilite', 'tables'])
        return html
    except ImportError:
        # Fallback: simple HTML conversion
        html = markdown_content.replace('\n', '<br>\n')
        return f"<html><body>{html}</body></html>"

def export_to_pdf(markdown_content: str, output_path: str = None) -> str:
    """Convert markdown report to PDF format."""
    try:
        import markdown
        from weasyprint import HTML
        
        html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite', 'tables'])
        
        if output_path is None:
            reports_dir = config.reports_dir
            import uuid
            output_path = str(reports_dir / f"report_{uuid.uuid4().hex[:8]}.pdf")
        
        HTML(string=html_content).write_pdf(output_path)
        return output_path
    except ImportError:
        return "PDF export requires weasyprint package. Install with: pip install weasyprint"
    except Exception as e:
        return f"Error exporting to PDF: {str(e)}"

# Export functions are utilities, not agent tools
# They are called externally after the report is generated

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=config.writer_model,
    output_type=AgentOutputSchema(ReportData, strict_json_schema=False),
)
