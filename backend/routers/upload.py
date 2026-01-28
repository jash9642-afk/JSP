"""
Upload Router
Handles file upload and initial data profiling
"""

import uuid
import os
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from models.schemas import UploadResponse, ErrorResponse
from services.data_parser import DataParser

router = APIRouter()

# Reference to main data store (injected)
def get_data_store() -> Dict[str, Any]:
    from main import get_data_store
    return get_data_store()

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 10)) * 1024 * 1024


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse}
    }
)
async def upload_file(
    file: UploadFile = File(..., description="Data file (CSV, XLSX, JSON)"),
    data_store: Dict = Depends(get_data_store)
):
    """
    Upload a data file for analysis.
    
    Accepts CSV, XLSX, XLS, and JSON files up to 10MB.
    Returns a session ID for subsequent operations and a data profile.
    """
    # Validate file type
    allowed_extensions = {'.csv', '.xlsx', '.xls', '.json'}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )
    
    try:
        # Parse the file
        df, file_type = DataParser.parse(content, file.filename)
        
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="File contains no data"
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Profile the data
        profile = DataParser.profile(df)
        
        # Get preview
        preview = DataParser.to_preview(df, rows=10)
        
        # Store in session
        data_store[session_id] = {
            "original_df": df.copy(),
            "cleaned_df": None,
            "filename": file.filename,
            "file_type": file_type,
            "cleaning_report": None
        }
        
        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            file_type=file_type,
            profile=profile,
            preview=preview,
            message=f"Successfully uploaded {file.filename}. {profile.row_count} rows, {profile.column_count} columns detected."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    data_store: Dict = Depends(get_data_store)
):
    """Get information about an existing session"""
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = data_store[session_id]
    df = session.get("cleaned_df") or session["original_df"]
    
    return {
        "session_id": session_id,
        "filename": session["filename"],
        "file_type": session["file_type"],
        "has_cleaned_data": session["cleaned_df"] is not None,
        "profile": DataParser.profile(df),
        "preview": DataParser.to_preview(df)
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    data_store: Dict = Depends(get_data_store)
):
    """Delete a session and its data"""
    if session_id not in data_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del data_store[session_id]
    return {"message": "Session deleted successfully"}
