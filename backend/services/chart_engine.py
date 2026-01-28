"""
Chart Engine Service
Natural Language to Plotly visualization using LangChain (Google Gemini)
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from models.schemas import ChartType


class ChartSpec(BaseModel):
    """LLM output for chart specification"""
    chart_type: str = Field(description="Type: bar, line, scatter, pie, histogram, box, heatmap")
    x_column: Optional[str] = Field(description="Column for X axis (if applicable)")
    y_column: Optional[str] = Field(description="Column for Y axis (if applicable)")
    color_column: Optional[str] = Field(description="Column for color grouping (optional)")
    aggregation: Optional[str] = Field(description="Aggregation: sum, mean, count, max, min (optional)")
    filter_condition: Optional[str] = Field(description="Filter expression like 'column > 100' (optional)")
    sort_by: Optional[str] = Field(description="Sort column (optional)")
    sort_order: Optional[str] = Field(description="asc or desc (optional)")
    limit: Optional[int] = Field(description="Limit number of results (optional)")
    title: str = Field(description="Chart title")
    explanation: str = Field(description="Brief explanation of what this chart shows")


class NLChartEngine:
    """
    Natural Language to Chart Engine (Google Gemini)
    
    Converts user queries like "Show top 5 products by sales" into
    interactive Plotly visualizations.
    """
    
    # Color palette for charts (modern, dark-theme friendly)
    COLORS = [
        '#6366f1',  # Indigo
        '#8b5cf6',  # Violet
        '#ec4899',  # Pink
        '#14b8a6',  # Teal
        '#f59e0b',  # Amber
        '#10b981',  # Emerald
        '#3b82f6',  # Blue
        '#ef4444',  # Red
    ]
    
    def __init__(self):
        """Initialize the chart engine"""
        self.use_llm = bool(os.getenv("GOOGLE_API_KEY"))
        
        if self.use_llm:
            self.llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-pro"),
                temperature=0.1,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        else:
            self.llm = None
    
    def _convert_to_serializable(self, obj):
        """Convert numpy arrays and other non-serializable types to Python native types"""
        if isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def generate_chart(
        self,
        df: pd.DataFrame,
        query: str,
        chart_type_override: Optional[ChartType] = None
    ) -> Tuple[Dict[str, Any], ChartType, str, List[str]]:
        """
        Generate a Plotly chart from natural language query
        
        Args:
            df: The data to visualize
            query: Natural language query
            chart_type_override: Optional forced chart type
            
        Returns:
            Tuple of (plotly_figure_dict, chart_type, explanation, suggested_queries)
        """
        # Get chart specification from LLM or rules
        if self.use_llm:
            spec = self._get_llm_chart_spec(df, query)
        else:
            spec = self._get_rule_based_spec(df, query)
        
        # Apply override if specified
        if chart_type_override:
            spec['chart_type'] = chart_type_override.value
        
        # Apply filters if specified
        filtered_df = self._apply_filters(df, spec)
        
        # Generate the chart
        fig = self._create_plotly_chart(filtered_df, spec)
        
        # Style the chart for dark theme
        fig = self._apply_dark_theme(fig)
        
        # Get chart type enum
        chart_type = ChartType(spec['chart_type']) if spec['chart_type'] in [e.value for e in ChartType] else ChartType.BAR
        
        # Generate suggested follow-up queries
        suggestions = self._generate_suggestions(df, query, spec)
        
        # Convert to dict and ensure all numpy arrays are converted to lists
        fig_dict = self._convert_to_serializable(fig.to_dict())
        
        return fig_dict, chart_type, spec.get('explanation', ''), suggestions
    
    def _get_llm_chart_spec(self, df: pd.DataFrame, query: str) -> Dict:
        """Get chart specification from LLM"""
        parser = PydanticOutputParser(pydantic_object=ChartSpec)
        
        # Build column info
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = df[col].dropna().head(3).tolist()
            columns_info.append(f"- {col} ({dtype}): {sample}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data visualization expert. Convert natural language queries into chart specifications.

Available columns:
{columns}

Row count: {row_count}

Rules:
1. Choose the most appropriate chart type for the query
2. For "top N" or "best" queries, use bar charts with sorting and limit
3. For trends over time, use line charts
4. For distributions, use histograms or pie charts
5. For comparisons, use bar charts
6. For correlations, use scatter plots
7. Always provide meaningful titles

{format_instructions}"""),
            ("user", "Query: {query}")
        ])
        
        try:
            chain = prompt | self.llm | parser
            result = chain.invoke({
                "columns": "\n".join(columns_info),
                "row_count": len(df),
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })
            
            return result.model_dump()
        except Exception as e:
            print(f"LLM chart spec failed: {e}")
            return self._get_rule_based_spec(df, query)
    
    def _get_rule_based_spec(self, df: pd.DataFrame, query: str) -> Dict:
        """Generate chart spec using keyword rules"""
        query_lower = query.lower()
        
        # Detect chart type from keywords
        chart_type = "bar"
        if any(w in query_lower for w in ["trend", "over time", "timeline", "growth", "change"]):
            chart_type = "line"
        elif any(w in query_lower for w in ["distribution", "spread", "frequency"]):
            chart_type = "histogram"
        elif any(w in query_lower for w in ["pie", "proportion", "percentage", "share"]):
            chart_type = "pie"
        elif any(w in query_lower for w in ["correlation", "relationship", "vs", "versus"]):
            chart_type = "scatter"
        
        # Find columns mentioned
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Default selections
        x_col = cat_cols[0] if cat_cols else (numeric_cols[0] if numeric_cols else df.columns[0])
        y_col = numeric_cols[0] if numeric_cols else df.columns[0]
        
        # Check for specific column mentions
        for col in df.columns:
            if col.lower() in query_lower:
                if col in numeric_cols:
                    y_col = col
                else:
                    x_col = col
        
        # Detect limit (top N)
        limit = None
        match = re.search(r'top\s*(\d+)', query_lower)
        if match:
            limit = int(match.group(1))
        
        # Detect sort order
        sort_order = "desc" if any(w in query_lower for w in ["top", "highest", "best", "most"]) else None
        
        return {
            "chart_type": chart_type,
            "x_column": x_col,
            "y_column": y_col,
            "color_column": None,
            "aggregation": "sum" if "total" in query_lower else None,
            "filter_condition": None,
            "sort_by": y_col if sort_order else None,
            "sort_order": sort_order,
            "limit": limit,
            "title": query.capitalize(),
            "explanation": f"Showing {chart_type} chart of {y_col} by {x_col}"
        }
    
    def _apply_filters(self, df: pd.DataFrame, spec: Dict) -> pd.DataFrame:
        """Apply sorting, limiting, and aggregation"""
        result = df.copy()
        
        # Apply aggregation if specified
        if spec.get('aggregation') and spec.get('x_column') and spec.get('y_column'):
            x_col = spec['x_column']
            y_col = spec['y_column']
            agg = spec['aggregation']
            
            if x_col in result.columns and y_col in result.columns:
                if agg == 'sum':
                    result = result.groupby(x_col)[y_col].sum().reset_index()
                elif agg == 'mean':
                    result = result.groupby(x_col)[y_col].mean().reset_index()
                elif agg == 'count':
                    result = result.groupby(x_col)[y_col].count().reset_index()
                elif agg == 'max':
                    result = result.groupby(x_col)[y_col].max().reset_index()
                elif agg == 'min':
                    result = result.groupby(x_col)[y_col].min().reset_index()
        
        # Apply sorting
        if spec.get('sort_by') and spec['sort_by'] in result.columns:
            ascending = spec.get('sort_order', 'desc') == 'asc'
            result = result.sort_values(spec['sort_by'], ascending=ascending)
        
        # Apply limit
        if spec.get('limit'):
            result = result.head(spec['limit'])
        
        return result
    
    def _create_plotly_chart(self, df: pd.DataFrame, spec: Dict) -> go.Figure:
        """Create the Plotly figure based on spec"""
        chart_type = spec.get('chart_type', 'bar')
        x_col = spec.get('x_column')
        y_col = spec.get('y_column')
        color_col = spec.get('color_column')
        title = spec.get('title', 'Data Visualization')
        
        # Ensure columns exist
        if x_col and x_col not in df.columns:
            x_col = df.columns[0]
        if y_col and y_col not in df.columns:
            y_col = df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else df.columns[0]
        
        try:
            if chart_type == 'bar':
                fig = px.bar(
                    df, x=x_col, y=y_col, color=color_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            elif chart_type == 'line':
                fig = px.line(
                    df, x=x_col, y=y_col, color=color_col,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    markers=True
                )
            
            elif chart_type == 'scatter':
                fig = px.scatter(
                    df, x=x_col, y=y_col, color=color_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            elif chart_type == 'pie':
                fig = px.pie(
                    df, names=x_col, values=y_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            elif chart_type == 'histogram':
                fig = px.histogram(
                    df, x=x_col if x_col else y_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            elif chart_type == 'box':
                fig = px.box(
                    df, x=x_col, y=y_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            elif chart_type == 'heatmap':
                # For heatmap, we need numeric data
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) >= 2:
                    corr = numeric_df.corr()
                    fig = px.imshow(
                        corr,
                        title=title,
                        color_continuous_scale='RdBu'
                    )
                else:
                    fig = px.bar(df, x=x_col, y=y_col, title=title)
            
            else:
                # Default to bar
                fig = px.bar(
                    df, x=x_col, y=y_col,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            
            return fig
            
        except Exception as e:
            print(f"Chart creation failed: {e}")
            # Return a simple default chart
            return px.bar(
                df.head(10), 
                x=df.columns[0], 
                y=df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else df.columns[0],
                title=f"Data Overview - {title}"
            )
    
    def _apply_dark_theme(self, fig: go.Figure) -> go.Figure:
        """Apply dark theme styling to the chart"""
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Inter, system-ui, sans-serif",
                size=12,
                color="#e5e7eb"
            ),
            title=dict(
                font=dict(size=18, color="#f9fafb"),
                x=0.5,
                xanchor='center'
            ),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(255,255,255,0.1)'
            ),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                zerolinecolor='rgba(255,255,255,0.2)'
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                zerolinecolor='rgba(255,255,255,0.2)'
            ),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def _generate_suggestions(self, df: pd.DataFrame, query: str, spec: Dict) -> List[str]:
        """Generate follow-up query suggestions"""
        suggestions = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Suggest different aggregations
        if spec.get('y_column') and len(numeric_cols) > 1:
            other_num = [c for c in numeric_cols if c != spec.get('y_column')][:1]
            if other_num:
                suggestions.append(f"Show {other_num[0]} distribution")
        
        # Suggest different chart types
        current_type = spec.get('chart_type', 'bar')
        if current_type == 'bar':
            suggestions.append("Show this as a pie chart")
        elif current_type == 'line':
            suggestions.append("Show as a bar chart instead")
        
        # Suggest filtering
        if cat_cols and len(df) > 20:
            suggestions.append(f"Show top 5 by {spec.get('y_column', 'value')}")
        
        # Suggest correlation
        if len(numeric_cols) >= 2:
            suggestions.append(f"Show correlation between {numeric_cols[0]} and {numeric_cols[1]}")
        
        return suggestions[:3]
    
    def override_chart_type(
        self,
        plotly_dict: Dict[str, Any],
        df: pd.DataFrame,
        new_type: ChartType,
        spec: Dict
    ) -> Dict[str, Any]:
        """Regenerate chart with a different type"""
        spec['chart_type'] = new_type.value
        filtered_df = self._apply_filters(df, spec)
        fig = self._create_plotly_chart(filtered_df, spec)
        fig = self._apply_dark_theme(fig)
        return self._convert_to_serializable(fig.to_dict())
