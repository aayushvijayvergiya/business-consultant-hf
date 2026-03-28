"""Analytics agent for data analysis and visualization."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from agents import Agent, AgentOutputSchema
from pydantic import BaseModel, Field

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = config.visualization_dpi

INSTRUCTIONS = """You are a data analytics expert. Given business data or metrics, you should:
1. Analyze the data to identify trends, patterns, and insights
2. Perform statistical analysis (mean, median, standard deviation, correlations, etc.)
3. Generate appropriate visualizations (line charts, bar charts, scatter plots, heatmaps, etc.)
4. Provide clear interpretations of the findings
5. Identify any anomalies or outliers
6. Suggest actionable insights based on the data

When creating visualizations, choose the most appropriate chart type for the data:
- Time series data: line charts
- Categorical comparisons: bar charts
- Relationships: scatter plots or correlation heatmaps
- Distributions: histograms or box plots
- Multiple variables: multi-line charts or grouped bar charts

Always ensure visualizations are clear, well-labeled, and professional."""

class AnalyticsResult(BaseModel):
    """Result from analytics agent."""
    summary: str = Field(description="A summary of the key findings from the data analysis")
    statistics: Dict[str, Any] = Field(description="Key statistical measures (mean, median, std, etc.)")
    insights: list[str] = Field(description="List of actionable insights derived from the analysis")
    visualization_paths: list[str] = Field(description="Paths to generated visualization files")
    data_summary: str = Field(description="Summary of the data structure and content")
    recommendations: list[str] = Field(description="Recommendations based on the analysis")

def analyze_data(data: str, analysis_type: str = "general") -> Dict[str, Any]:
    """
    Analyze data and return statistics.
    """
    try:
        if '\n' in data and ',' in data.split('\n')[0]:
            df = pd.read_csv(pd.io.common.StringIO(data))
        elif data.strip().startswith('{') or data.strip().startswith('['):
            df = pd.read_json(pd.io.common.StringIO(data))
        else:
            lines = data.split('\n')
            numeric_data = []
            for line in lines:
                try:
                    numbers = [float(x) for x in line.split() if x.replace('.', '').replace('-', '').isdigit()]
                    if numbers: numeric_data.extend(numbers)
                except: continue
            if numeric_data:
                df = pd.DataFrame({'value': numeric_data})
            else:
                return {"error": "Could not parse data"}
        
        stats = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "count": int(df[col].count())
            }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = df[numeric_cols].corr().to_dict() if len(numeric_cols) > 1 else None
        
        return {
            "statistics": stats,
            "correlations": correlations,
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": list(df.columns),
            "dataframe": df
        }
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def create_visualization(data: str, chart_type: str = "auto", title: str = "Data Visualization", 
                        save_path: Optional[str] = None) -> str:
    """
    Create a visualization from data.
    """
    try:
        analysis_result = analyze_data(data)
        if "error" in analysis_result: return analysis_result["error"]
        
        df = analysis_result["dataframe"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols: return "No numeric columns"
        
        viz_dir = config.visualizations_dir
        file_format = config.visualization_format
        
        import uuid
        filename = f"{title.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{file_format}"
        filepath = viz_dir / filename
        
        plt.figure(figsize=(10, 6))
        
        if chart_type == "auto":
            if len(numeric_cols) == 1:
                chart_type = "line" if df.index.dtype.name.startswith('datetime') else "histogram"
            elif len(numeric_cols) == 2:
                chart_type = "scatter"
            else:
                chart_type = "line"
        
        if chart_type == "line":
            for col in numeric_cols[:5]: plt.plot(df.index, df[col], label=col, marker='o', markersize=3)
            plt.legend()
        elif chart_type == "bar":
            for col in numeric_cols[:5]: plt.bar(range(len(df)), df[col], label=col, alpha=0.7)
            plt.legend()
        elif chart_type == "scatter" and len(numeric_cols) >= 2:
            plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
        elif chart_type == "histogram":
            for col in numeric_cols[:3]: plt.hist(df[col].dropna(), bins=30, alpha=0.7, label=col)
            plt.legend()
        elif chart_type == "heatmap" and len(numeric_cols) > 1:
            sns.heatmap(df[numeric_cols].corr(), annot=True, fmt='.2f', cmap='coolwarm', center=0)
        
        plt.title(title)
        plt.tight_layout()
        plt.savefig(filepath, format=file_format, dpi=config.visualization_dpi)
        plt.close()
        return str(filepath)
    except Exception as e:
        return f"Error: {str(e)}"

analytics_agent = Agent(
    name="AnalyticsAgent",
    instructions=INSTRUCTIONS,
    model=config.analytics_model,
    output_type=AgentOutputSchema(AnalyticsResult, strict_json_schema=False),
)
