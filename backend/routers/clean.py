"""
Clean Router
Data cleaning endpoints with AI-powered processing
"""

import io
import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from models.schemas import CleanResponse, ExportRequest, ExportResponse
from services.ai_cleaner import AIDataCleaner
from services.data_parser import DataParser

router = APIRouter()

def get_data_store() -> Dict[str, Any]:
    from main import get_data_store
    return get_data_store()


@router.post("/clean/{session_id}", response_model=CleanResponse)
async def clean_data(
    session_id: str,
    data_store: Dict = Depends(get_data_store)
):
    """
    Run AI-powered data cleaning on the uploaded dataset.
    
    This will:
    - Profile the data for quality issues
    - Use LLM to make intelligent cleaning decisions
    - Handle missing values, fix types, standardize dates
    - Return a detailed report of all actions taken
    """
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a file first.")
    
    session = data_store[session_id]
    original_df = session["original_df"]
    
    try:
        # Initialize cleaner
        cleaner = AIDataCleaner(use_llm=True)
        
        # Run cleaning
        cleaned_df, report = cleaner.clean(original_df)
        
        # Store cleaned data
        session["cleaned_df"] = cleaned_df
        session["cleaning_report"] = report
        
        # Get preview of cleaned data
        preview = DataParser.to_preview(cleaned_df, rows=10)
        
        return CleanResponse(
            session_id=session_id,
            report=report,
            cleaned_preview=preview,
            message=f"Cleaning complete! {report.total_actions} actions performed."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleaning failed: {str(e)}"
        )


@router.get("/clean/{session_id}/report")
async def get_cleaning_report(
    session_id: str,
    data_store: Dict = Depends(get_data_store)
):
    """Get the cleaning report for a session"""
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    
    if not session.get("cleaning_report"):
        raise HTTPException(status_code=400, detail="Data has not been cleaned yet")
    
    return session["cleaning_report"]


@router.get("/export/{session_id}/{format}")
async def export_data(
    session_id: str,
    format: str,
    cleaned: bool = True,
    data_store: Dict = Depends(get_data_store)
):
    """
    Export data in various formats.
    
    Formats: csv, xlsx, pdf
    Use cleaned=false to export original data.
    """
    if format not in ['csv', 'xlsx', 'pdf']:
        raise HTTPException(status_code=400, detail="Format must be csv, xlsx, or pdf")
    
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    
    # Get the appropriate dataframe
    if cleaned and session.get("cleaned_df") is not None:
        df = session["cleaned_df"]
        suffix = "_cleaned"
    else:
        df = session["original_df"]
        suffix = "_original"
    
    filename = os.path.splitext(session["filename"])[0] + suffix
    
    try:
        if format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
            )
        
        elif format == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
                
                # Add cleaning report if available
                if cleaned and session.get("cleaning_report"):
                    report = session["cleaning_report"]
                    report_df = pd.DataFrame([{
                        "Metric": "Rows Before",
                        "Value": report.rows_before
                    }, {
                        "Metric": "Rows After", 
                        "Value": report.rows_after
                    }, {
                        "Metric": "Actions Performed",
                        "Value": report.total_actions
                    }])
                    report_df.to_excel(writer, index=False, sheet_name='Summary')
                    
                    if report.actions:
                        actions_df = pd.DataFrame([{
                            "Column": a.column,
                            "Action": a.action,
                            "Details": a.details,
                            "Rows Affected": a.rows_affected
                        } for a in report.actions])
                        actions_df.to_excel(writer, index=False, sheet_name='Actions')
            
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
            )
        
        elif format == 'pdf':
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30
            )
            elements.append(Paragraph(f"Pixll Data Report: {session['filename']}", title_style))
            
            # Summary
            if cleaned and session.get("cleaning_report"):
                report = session["cleaning_report"]
                elements.append(Paragraph("Cleaning Summary", styles['Heading2']))
                summary_data = [
                    ["Metric", "Value"],
                    ["Rows Before", str(report.rows_before)],
                    ["Rows After", str(report.rows_after)],
                    ["Columns", str(report.columns_after)],
                    ["Actions Performed", str(report.total_actions)]
                ]
                summary_table = Table(summary_data, colWidths=[200, 150])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 20))
            
            # Data preview
            elements.append(Paragraph("Data Preview (First 20 Rows)", styles['Heading2']))
            preview_df = df.head(20)
            
            # Create table data
            table_data = [preview_df.columns.tolist()]
            for _, row in preview_df.iterrows():
                table_data.append([str(v)[:30] for v in row.values])  # Truncate long values
            
            # Calculate column widths based on number of columns
            col_width = min(80, 550 / len(preview_df.columns))
            data_table = Table(table_data, colWidths=[col_width] * len(preview_df.columns))
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
            ]))
            elements.append(data_table)
            
            doc.build(elements)
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/data/{session_id}")
async def get_data(
    session_id: str,
    cleaned: bool = True,
    page: int = 1,
    page_size: int = 50,
    data_store: Dict = Depends(get_data_store)
):
    """Get paginated data from a session"""
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    
    if cleaned and session.get("cleaned_df") is not None:
        df = session["cleaned_df"]
    else:
        df = session["original_df"]
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]
    
    return {
        "data": DataParser.to_preview(page_df, rows=page_size),
        "total_rows": len(df),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(df) + page_size - 1) // page_size
    }
