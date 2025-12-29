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

try:
    from src.config import config
except ImportError:
    config = None

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 300 if config and hasattr(config, 'visualization_dpi') else 150

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
    
    Args:
        data: Data in CSV, JSON, or text format
        analysis_type: Type of analysis to perform
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Try to parse as CSV first
        if '\n' in data and ',' in data.split('\n')[0]:
            df = pd.read_csv(pd.io.common.StringIO(data))
        # Try JSON
        elif data.strip().startswith('{') or data.strip().startswith('['):
            df = pd.read_json(pd.io.common.StringIO(data))
        else:
            # Treat as text data, try to extract numbers
            lines = data.split('\n')
            numeric_data = []
            for line in lines:
                try:
                    # Try to extract numbers from each line
                    numbers = [float(x) for x in line.split() if x.replace('.', '').replace('-', '').isdigit()]
                    if numbers:
                        numeric_data.extend(numbers)
                except:
                    continue
            if numeric_data:
                df = pd.DataFrame({'value': numeric_data})
            else:
                return {"error": "Could not parse data into a structured format"}
        
        # Basic statistics
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
        
        # Correlation matrix if multiple numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = None
        if len(numeric_cols) > 1:
            correlations = df[numeric_cols].corr().to_dict()
        
        return {
            "statistics": stats,
            "correlations": correlations,
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": list(df.columns),
            "dataframe": df
        }
    except Exception as e:
        return {"error": f"Error analyzing data: {str(e)}"}

def create_visualization(data: str, chart_type: str = "auto", title: str = "Data Visualization", 
                        save_path: Optional[str] = None) -> str:
    """
    Create a visualization from data.
    
    Args:
        data: Data to visualize
        chart_type: Type of chart (auto, line, bar, scatter, histogram, heatmap)
        title: Title for the chart
        save_path: Path to save the visualization
        
    Returns:
        Path to saved visualization file
    """
    try:
        analysis_result = analyze_data(data)
        if "error" in analysis_result:
            return analysis_result["error"]
        
        df = analysis_result["dataframe"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return "No numeric columns found for visualization"
        
        # Determine visualization directory
        if config and hasattr(config, 'visualizations_dir'):
            viz_dir = config.visualizations_dir
        else:
            viz_dir = Path(project_root) / "data" / "visualizations"
            viz_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file format
        file_format = "png"
        if config and hasattr(config, 'visualization_format'):
            file_format = config.visualization_format
        
        # Generate filename
        import uuid
        filename = f"{title.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{file_format}"
        filepath = viz_dir / filename
        
        plt.figure(figsize=(10, 6))
        
        # Auto-detect chart type if needed
        if chart_type == "auto":
            if len(numeric_cols) == 1:
                if df.index.dtype.name.startswith('datetime') or 'date' in str(df.index.dtype).lower():
                    chart_type = "line"
                else:
                    chart_type = "histogram"
            elif len(numeric_cols) == 2:
                chart_type = "scatter"
            else:
                chart_type = "line"
        
        # Create appropriate visualization
        if chart_type == "line":
            for col in numeric_cols[:5]:  # Limit to 5 columns
                plt.plot(df.index, df[col], label=col, marker='o', markersize=3)
            plt.legend()
            plt.xlabel("Index")
            plt.ylabel("Value")
        elif chart_type == "bar":
            for col in numeric_cols[:5]:
                plt.bar(range(len(df)), df[col], label=col, alpha=0.7)
            plt.legend()
            plt.xlabel("Index")
            plt.ylabel("Value")
        elif chart_type == "scatter" and len(numeric_cols) >= 2:
            plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
            plt.xlabel(numeric_cols[0])
            plt.ylabel(numeric_cols[1])
        elif chart_type == "histogram":
            for col in numeric_cols[:3]:
                plt.hist(df[col].dropna(), bins=30, alpha=0.7, label=col)
            plt.legend()
            plt.xlabel("Value")
            plt.ylabel("Frequency")
        elif chart_type == "heatmap" and len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
        else:
            # Default: line chart
            for col in numeric_cols[:5]:
                plt.plot(df.index, df[col], label=col)
            plt.legend()
        
        plt.title(title)
        plt.tight_layout()
        plt.savefig(filepath, format=file_format, dpi=300 if config and hasattr(config, 'visualization_dpi') else 150)
        plt.close()
        
        return str(filepath)
    except Exception as e:
        return f"Error creating visualization: {str(e)}"

def generate_insights(data: str, statistics: Dict[str, Any]) -> list[str]:
    """Generate insights from data and statistics."""
    insights = []
    try:
        analysis_result = analyze_data(data)
        if "error" in analysis_result:
            return [f"Analysis error: {analysis_result['error']}"]
        
        stats = analysis_result.get("statistics", {})
        
        for col, col_stats in stats.items():
            mean = col_stats.get("mean", 0)
            std = col_stats.get("std", 0)
            min_val = col_stats.get("min", 0)
            max_val = col_stats.get("max", 0)
            
            # Identify outliers (values beyond 2 standard deviations)
            if std > 0:
                insights.append(f"{col}: Mean value is {mean:.2f} with standard deviation of {std:.2f}")
                if max_val > mean + 2 * std:
                    insights.append(f"{col}: High outliers detected (max: {max_val:.2f})")
                if min_val < mean - 2 * std:
                    insights.append(f"{col}: Low outliers detected (min: {min_val:.2f})")
        
        # Correlation insights
        if analysis_result.get("correlations"):
            insights.append("Multiple variables detected - correlation analysis available")
        
    except Exception as e:
        insights.append(f"Error generating insights: {str(e)}")
    
    return insights

# Analytics tools are utilities, not agent tools
# They are called externally or by the system, not by the agent itself

analytics_agent = Agent(
    name="AnalyticsAgent",
    instructions=INSTRUCTIONS,
    model=config.analytics_model if config and hasattr(config, 'analytics_model') else "gpt-4o-mini",
    output_type=AgentOutputSchema(AnalyticsResult, strict_json_schema=False),
)

