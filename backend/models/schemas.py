"""
Pydantic Models for Pixll API
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str


class ColumnInfo(BaseModel):
    """Information about a single column"""
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]


class DataProfile(BaseModel):
    """Data profiling result"""
    row_count: int
    column_count: int
    columns: List[ColumnInfo]
    memory_usage_mb: float


class UploadResponse(BaseModel):
    """Response after file upload"""
    session_id: str
    filename: str
    file_type: str
    profile: DataProfile
    preview: List[Dict[str, Any]]
    message: str


class CleaningAction(BaseModel):
    """A single cleaning action performed"""
    column: str
    action: str
    details: str
    rows_affected: int


class CleaningReport(BaseModel):
    """Report of all cleaning actions"""
    total_actions: int
    actions: List[CleaningAction]
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    issues_detected: List[str]
    recommendations: List[str]


class CleanResponse(BaseModel):
    """Response after data cleaning"""
    session_id: str
    report: CleaningReport
    cleaned_preview: List[Dict[str, Any]]
    message: str


class VisualizeRequest(BaseModel):
    """Request to generate visualization"""
    session_id: str
    query: str
    chart_type_override: Optional[ChartType] = None


class VisualizeResponse(BaseModel):
    """Response with Plotly figure"""
    session_id: str
    query: str
    chart_type: ChartType
    plotly_figure: Dict[str, Any]
    explanation: str
    suggested_queries: List[str]


class ExportRequest(BaseModel):
    """Request to export data"""
    session_id: str
    format: str = Field(..., pattern="^(csv|xlsx|pdf)$")
    include_report: bool = False


class ExportResponse(BaseModel):
    """Response with export file info"""
    session_id: str
    format: str
    filename: str
    download_url: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    code: int
