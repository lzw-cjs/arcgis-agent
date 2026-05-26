"""File upload REST API endpoint (Phase 7).

POST /api/v1/upload — upload GIS data files (SHP, GeoJSON, CSV, etc.)
"""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api/v1", tags=["upload"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(None)):
    if file is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="No file provided")

    # In production: validate file type, save to workspace
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": 0,  # In production: get actual size
        "status": "uploaded",
    }
