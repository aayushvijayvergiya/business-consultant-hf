"""Document agent for processing and analyzing business documents."""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agents import Agent, AgentOutputSchema

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

INSTRUCTIONS = """You are a document analysis expert specializing in processing and analyzing business documents.
Given business documents (PDFs, business plans, financial statements, etc.), you should:

1. **Document Parsing**: Extract text and structured data from documents
2. **Key Information Extraction**: Identify and extract key business information
3. **Document Summarization**: Create concise summaries of document content
4. **Data Extraction**: Extract structured data (financial figures, metrics, dates, etc.)
5. **Content Analysis**: Analyze document content for insights and patterns
6. **Business Plan Analysis**: Analyze business plans for strengths, weaknesses, and opportunities
7. **Financial Statement Analysis**: Extract and analyze financial data from statements
8. **Document Classification**: Classify documents by type and purpose
9. **Stakeholder Identification**: Identify key stakeholders, roles, and responsibilities
10. **Action Item Extraction**: Extract action items, deadlines, and responsibilities

Your analysis should be:
- Accurate and comprehensive
- Well-structured and organized
- Highlight key insights and findings
- Extract actionable information
- Identify any gaps or missing information"""

class ExtractedData(BaseModel):
    """Structured data extracted from document."""
    field_name: str = Field(description="Name of the extracted field")
    value: Any = Field(description="Extracted value")
    confidence: Optional[str] = Field(description="Confidence level in extraction")
    source_location: Optional[str] = Field(description="Location in document where data was found")

class DocumentAnalysis(BaseModel):
    """Comprehensive document analysis result."""
    document_type: str = Field(description="Type of document")
    summary: str = Field(description="Executive summary")
    key_information: Dict[str, Any] = Field(description="Key information")
    extracted_data: List[ExtractedData] = Field(description="Structured data")
    financial_data: Optional[Dict[str, Any]] = Field(description="Financial data")
    stakeholders: List[Dict[str, str]] = Field(description="Stakeholders")
    action_items: List[Dict[str, str]] = Field(description="Action items")
    strengths: List[str] = Field(description="Strengths")
    weaknesses: List[str] = Field(description="Weaknesses")
    opportunities: List[str] = Field(description="Opportunities")
    recommendations: List[str] = Field(description="Recommendations")
    full_text: Optional[str] = Field(description="Full extracted text")

document_agent = Agent(
    name="DocumentAgent",
    instructions=INSTRUCTIONS,
    model=config.document_model,
    output_type=AgentOutputSchema(DocumentAnalysis, strict_json_schema=False),
)
