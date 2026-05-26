"""File upload REST API endpoint (Phase 7).

POST /api/v1/upload — upload GIS data files (SHP, ZIP, GDB).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from arcgis_agent.config import CONFIG_DIR

router = APIRouter(prefix="/api/v1", tags=["Upload"])
UPLOAD_DIR = CONFIG_DIR / "uploads"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a GIS data file (.shp, .zip, .gdb).

    Returns the saved file path. ZIP archives are automatically extracted.
    """
    # Validate file extension
    allowed_ext = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".zip"}
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in allowed_ext and not (file.filename and file.filename.endswith(".gdb")):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: .shp, .shx, .dbf, .prj, .cpg, .zip, .gdb",
        )

    # Save uploaded file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename

    content = await file.read()
    dest.write_bytes(content)

    # Extract if ZIP
    if ext == ".zip":
        extract_dir = UPLOAD_DIR / file.filename.replace(".zip", "")
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(str(dest), "r") as zf:
            zf.extractall(str(extract_dir))
        return {
            "uploaded": str(dest),
            "extracted": str(extract_dir),
            "filename": file.filename,
        }

    return {
        "uploaded": str(dest),
        "filename": file.filename,
        "size": len(content),
    }
