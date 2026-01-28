"""
Visualize Router
Natural language to chart generation endpoints
"""

import io
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import plotly.io as pio

from models.schemas import VisualizeRequest, VisualizeResponse, ChartType
from services.chart_engine import NLChartEngine
from services.data_parser import DataParser

router = APIRouter()

def get_data_store() -> Dict[str, Any]:
    from main import get_data_store
    return get_data_store()


@router.post("/visualize", response_model=VisualizeResponse)
async def generate_visualization(
    request: VisualizeRequest,
    data_store: Dict = Depends(get_data_store)
):
    """
    Generate an interactive chart from a natural language query.
    
    Example queries:
    - "Show me the top 5 products by sales"
    - "Compare revenue across regions"
    - "Show the distribution of ages"
    - "What's the trend of orders over time?"
    
    Returns a Plotly figure in JSON format for rendering.
    """
    if request.session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a file first.")
    
    session = data_store[request.session_id]
    
    # Use cleaned data if available, otherwise original
    df = session.get("cleaned_df") or session["original_df"]
    
    if df.empty:
        raise HTTPException(status_code=400, detail="No data available for visualization")
    
    try:
        engine = NLChartEngine()
        
        plotly_dict, chart_type, explanation, suggestions = engine.generate_chart(
            df=df,
            query=request.query,
            chart_type_override=request.chart_type_override
        )
        
        # Store last query in session for override functionality
        session["last_query"] = request.query
        session["last_chart_spec"] = {
            "chart_type": chart_type.value,
            "plotly_dict": plotly_dict
        }
        
        return VisualizeResponse(
            session_id=request.session_id,
            query=request.query,
            chart_type=chart_type,
            plotly_figure=plotly_dict,
            explanation=explanation,
            suggested_queries=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Visualization failed: {str(e)}"
        )


@router.post("/visualize/override")
async def override_chart_type(
    session_id: str,
    chart_type: ChartType,
    data_store: Dict = Depends(get_data_store)
):
    """
    Change the chart type for the last visualization.
    
    This allows users to switch between Bar, Line, Pie, etc.
    without re-running the query.
    """
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    
    if not session.get("last_query"):
        raise HTTPException(status_code=400, detail="No previous visualization to override")
    
    df = session.get("cleaned_df") or session["original_df"]
    
    try:
        engine = NLChartEngine()
        
        plotly_dict, new_chart_type, explanation, suggestions = engine.generate_chart(
            df=df,
            query=session["last_query"],
            chart_type_override=chart_type
        )
        
        # Update session
        session["last_chart_spec"]["chart_type"] = new_chart_type.value
        session["last_chart_spec"]["plotly_dict"] = plotly_dict
        
        return VisualizeResponse(
            session_id=session_id,
            query=session["last_query"],
            chart_type=new_chart_type,
            plotly_figure=plotly_dict,
            explanation=f"Chart type changed to {chart_type.value}. {explanation}",
            suggested_queries=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")


@router.get("/visualize/{session_id}/export/{format}")
async def export_chart(
    session_id: str,
    format: str,
    data_store: Dict = Depends(get_data_store)
):
    """
    Export the current chart as an image.
    
    Formats: png, pdf, svg
    """
    if format not in ['png', 'pdf', 'svg']:
        raise HTTPException(status_code=400, detail="Format must be png, pdf, or svg")
    
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    
    if not session.get("last_chart_spec"):
        raise HTTPException(status_code=400, detail="No chart to export. Generate a visualization first.")
    
    try:
        import plotly.graph_objects as go
        
        # Reconstruct figure from dict
        fig_dict = session["last_chart_spec"]["plotly_dict"]
        fig = go.Figure(fig_dict)
        
        # Set better resolution for export
        width = 1200
        height = 800
        scale = 2
        
        if format == 'png':
            img_bytes = pio.to_image(fig, format='png', width=width, height=height, scale=scale)
            media_type = "image/png"
            ext = "png"
        elif format == 'pdf':
            img_bytes = pio.to_image(fig, format='pdf', width=width, height=height, scale=scale)
            media_type = "application/pdf"
            ext = "pdf"
        elif format == 'svg':
            img_bytes = pio.to_image(fig, format='svg', width=width, height=height)
            media_type = "image/svg+xml"
            ext = "svg"
        
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=pixll_chart.{ext}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}. Make sure kaleido is installed.")


@router.get("/visualize/{session_id}/columns")
async def get_available_columns(
    session_id: str,
    data_store: Dict = Depends(get_data_store)
):
    """Get column information for manual chart configuration"""
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    df = session.get("cleaned_df") or session["original_df"]
    
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        is_numeric = dtype in ['int64', 'float64', 'int32', 'float32']
        is_datetime = 'datetime' in dtype
        
        columns.append({
            "name": col,
            "dtype": dtype,
            "is_numeric": is_numeric,
            "is_datetime": is_datetime,
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(5).tolist()
        })
    
    return {
        "session_id": session_id,
        "columns": columns,
        "chart_types": [ct.value for ct in ChartType]
    }
