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

try:
    from src.config import config
except ImportError:
    config = None

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
    document_type: str = Field(description="Type of document (business plan, financial statement, etc.)")
    
    summary: str = Field(description="Executive summary of the document content")
    
    key_information: Dict[str, Any] = Field(
        description="Key information extracted from the document"
    )
    
    extracted_data: List[ExtractedData] = Field(
        description="Structured data extracted from the document"
    )
    
    financial_data: Optional[Dict[str, Any]] = Field(
        description="Financial data extracted if applicable"
    )
    
    stakeholders: List[Dict[str, str]] = Field(
        description="Stakeholders identified in the document"
    )
    
    action_items: List[Dict[str, str]] = Field(
        description="Action items, deadlines, and responsibilities extracted"
    )
    
    strengths: List[str] = Field(
        description="Strengths identified in the document (for business plans)"
    )
    
    weaknesses: List[str] = Field(
        description="Weaknesses or gaps identified in the document"
    )
    
    opportunities: List[str] = Field(
        description="Opportunities identified in the document"
    )
    
    recommendations: List[str] = Field(
        description="Recommendations based on document analysis"
    )
    
    full_text: Optional[str] = Field(
        description="Full extracted text from the document (if requested)"
    )

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        from pypdf import PdfReader
        
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at {pdf_path}"
        
        reader = PdfReader(pdf_path)
        text_content = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {page_num} ---\n{text}")
            except Exception as e:
                text_content.append(f"--- Page {page_num} ---\n[Error extracting text: {str(e)}]")
        
        return "\n\n".join(text_content)
    except ImportError:
        return "Error: pypdf package not installed. Install with: pip install pypdf"
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"

def extract_financial_data(text: str) -> Dict[str, Any]:
    """
    Extract financial data from text.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Dictionary with extracted financial data
    """
    import re
    
    financial_data = {}
    
    # Extract currency amounts
    currency_pattern = r'\$[\d,]+(?:\.\d{2})?'
    amounts = re.findall(currency_pattern, text)
    if amounts:
        financial_data["currency_amounts"] = amounts[:20]  # Limit to 20
    
    # Extract percentages
    percentage_pattern = r'\d+\.?\d*\s*%'
    percentages = re.findall(percentage_pattern, text)
    if percentages:
        financial_data["percentages"] = percentages[:20]
    
    # Extract dates
    date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
    dates = re.findall(date_pattern, text)
    if dates:
        financial_data["dates"] = list(set(dates))[:20]
    
    # Look for common financial terms
    financial_terms = [
        "revenue", "profit", "loss", "expense", "income", "budget",
        "investment", "ROI", "cash flow", "assets", "liabilities", "equity"
    ]
    found_terms = []
    for term in financial_terms:
        if term.lower() in text.lower():
            found_terms.append(term)
    financial_data["financial_terms_found"] = found_terms
    
    return financial_data

def summarize_document(text: str, max_length: int = 500) -> str:
    """
    Create a summary of document content.
    
    Args:
        text: Document text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Document summary
    """
    # Simple extraction-based summarization
    sentences = text.split('.')
    
    # Filter out very short sentences
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Take first few meaningful sentences
    summary_sentences = meaningful_sentences[:5]
    summary = '. '.join(summary_sentences)
    
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    
    return summary

# Document processing tools are utilities, not agent tools
# They are called externally or by the system, not by the agent itself

document_agent = Agent(
    name="DocumentAgent",
    instructions=INSTRUCTIONS,
    model=config.document_model if config and hasattr(config, 'document_model') else "gpt-4o-mini",
    output_type=AgentOutputSchema(DocumentAnalysis, strict_json_schema=False),
)

