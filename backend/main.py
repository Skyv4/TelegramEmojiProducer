from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pathlib import Path
import shutil
import tempfile
import os
from typing import List, Dict
import sys
import uuid
import requests

# Add the src directory to the path so we can import telegramemojis and database
sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegramemojis.main import convert_to_telegram_sticker, is_gif_or_video, setup_directories
from telegramemojis.database import add_conversion_request, get_all_conversion_requests, update_conversion_request_status, get_conversion_request_by_id

app = FastAPI(
    title="Telegram Sticker Converter API",
    description="Convert GIFs and videos to Telegram-compliant animated WebM stickers",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
BASE_PATH = Path(__file__).parent
DIRS = setup_directories(BASE_PATH)

# Admin authentication
security = HTTPBasic()
ADMIN_PASSWORD = "hamilton jacobi bellman" # This should be stored securely, e.g., in environment variables

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == "admin" and credentials.password == ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Telegram Sticker Converter API",
        "version": "1.0.0"
    }

@app.post("/api/convert")
async def convert_file(file: UploadFile = File(...)):
    """
    Convert a single GIF or video file to Telegram sticker format
    
    Returns:
        - id: Unique ID of the conversion request
        - filename: Name of the converted file
        - original_size: Size of the original file in bytes
        - converted_size: Size of the converted file in bytes
        - download_url: URL to download the converted file
        - status: Status of the conversion ('pending', 'completed', 'failed')
        - error: Error message if conversion failed
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    request_id = str(uuid.uuid4())
    original_filename = file.filename
    
    request_data = {
        "id": request_id,
        "type": "file",
        "original_filename": original_filename,
        "status": "pending",
        "original_size": 0,
        "converted_size": 0,
        "compression_ratio": 0,
        "download_url": None,
        "error": None
    }
    add_conversion_request(request_data)

    # Create a temporary file to save the upload
    temp_dir = Path(tempfile.mkdtemp())
    temp_input = temp_dir / original_filename
    
    try:
        # Save uploaded file
        with temp_input.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verify it's a valid GIF or video
        if not is_gif_or_video(temp_input):
            update_conversion_request_status(request_id, "failed", error="Invalid file type. Please upload a GIF or video file.")
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a GIF or video file."
            )
        
        # Get original file size
        original_size = temp_input.stat().st_size
        request_data["original_size"] = original_size
        
        # Convert the file
        output_dir = DIRS["output_webm"]
        converted_path = convert_to_telegram_sticker(temp_input, output_dir)
        
        if not converted_path or not converted_path.exists():
            update_conversion_request_status(request_id, "failed", error="Conversion failed. Please try again.")
            raise HTTPException(
                status_code=500,
                detail="Conversion failed. Please try again."
            )
        
        # Get converted file size
        converted_size = converted_path.stat().st_size
        
        # Calculate compression ratio
        compression_ratio = ((original_size - converted_size) / original_size) * 100
        download_url = f"/api/download/{converted_path.name}"

        update_conversion_request_status(
            request_id,
            "completed",
            converted_filename=converted_path.name,
            download_url=download_url
        )
        
        return {
            "id": request_id,
            "original_filename": original_filename,
            "original_size": original_size,
            "converted_filename": converted_path.name,
            "converted_size": converted_size,
            "compression_ratio": round(compression_ratio, 2),
            "download_url": download_url,
            "status": "completed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        update_conversion_request_status(request_id, "failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@app.post("/api/convert-url")
async def convert_url(url: str):
    """
    Convert a GIF or video file from a URL to Telegram sticker format
    """
    request_id = str(uuid.uuid4())
    original_url = url
    
    request_data = {
        "id": request_id,
        "type": "url",
        "original_url": original_url,
        "status": "pending",
        "original_size": 0,
        "converted_size": 0,
        "compression_ratio": 0,
        "download_url": None,
        "error": None
    }
    add_conversion_request(request_data)

    temp_dir = Path(tempfile.mkdtemp())
    downloaded_file_path = None

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        content_type = response.headers.get("Content-Type", "")
        if not (content_type.startswith("image/gif") or content_type.startswith("video/")):
            update_conversion_request_status(request_id, "failed", error="Invalid content type from URL. Expected GIF or video.")
            raise HTTPException(status_code=400, detail="Invalid content type from URL. Expected GIF or video.")

        original_filename = Path(url).name if Path(url).name != '' else f"downloaded_file_{request_id}.{content_type.split('/')[-1].split(';')[0]}"
        downloaded_file_path = temp_dir / original_filename

        with open(downloaded_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if not is_gif_or_video(downloaded_file_path):
            update_conversion_request_status(request_id, "failed", error="Downloaded file is not a GIF or video.")
            raise HTTPException(status_code=400, detail="Downloaded file is not a GIF or video.")
        
        original_size = downloaded_file_path.stat().st_size
        request_data["original_size"] = original_size

        output_dir = DIRS["output_webm"]
        converted_path = convert_to_telegram_sticker(downloaded_file_path, output_dir)

        if not converted_path or not converted_path.exists():
            update_conversion_request_status(request_id, "failed", error="Conversion failed. Please try again.")
            raise HTTPException(status_code=500, detail="Conversion failed. Please try again.")
        
        converted_size = converted_path.stat().st_size
        compression_ratio = ((original_size - converted_size) / original_size) * 100
        download_url = f"/api/download/{converted_path.name}"

        update_conversion_request_status(
            request_id,
            "completed",
            converted_filename=converted_path.name,
            download_url=download_url
        )

        return {
            "id": request_id,
            "original_url": original_url,
            "original_filename": original_filename,
            "original_size": original_size,
            "converted_filename": converted_path.name,
            "converted_size": converted_size,
            "compression_ratio": round(compression_ratio, 2),
            "download_url": download_url,
            "status": "completed"
        }

    except requests.exceptions.RequestException as e:
        update_conversion_request_status(request_id, "failed", error=f"Failed to download URL: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download URL: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        update_conversion_request_status(request_id, "failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@app.post("/api/convert-batch")
async def convert_batch(files: List[UploadFile] = File(...)):
    """
    Convert multiple GIF or video files to Telegram sticker format
    
    Returns a list of conversion results
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        try:
            # Call the single file conversion endpoint for each file
            # This will handle logging to the database automatically
            result = await convert_file(file)
            results.append(result)
        except HTTPException as e:
            results.append({
                "id": str(uuid.uuid4()), # Generate a new ID for failed batch items
                "type": "file",
                "original_filename": file.filename or "unknown",
                "status": "failed",
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "id": str(uuid.uuid4()), # Generate a new ID for failed batch items
                "type": "file",
                "original_filename": file.filename or "unknown",
                "status": "failed",
                "error": str(e)
            })
    
    return {"results": results}

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    Download a converted sticker file
    """
    file_path = DIRS["output_webm"] / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="video/webm"
    )

@app.get("/api/stats")
async def get_stats():
    """
    Get statistics about conversions
    """
    output_files = list(DIRS["output_webm"].glob("*.webm"))
    archive_files = list(DIRS["archive_webm"].glob("*")) + list(DIRS["archive_gif"].glob("*"))
    
    total_output_size = sum(f.stat().st_size for f in output_files if f.is_file())
    
    return {
        "total_conversions": len(archive_files),
        "available_downloads": len(output_files),
        "total_output_size": total_output_size,
        "total_output_size_mb": round(total_output_size / (1024 * 1024), 2)
    }

@app.get("/api/admin/requests", dependencies=[Depends(authenticate_admin)])
async def get_all_requests():
    """
    Admin endpoint to get all conversion requests.
    Requires basic authentication with username 'admin' and the admin password.
    """
    return {"requests": get_all_conversion_requests()}

@app.post("/api/admin/requests/{request_id}/complete", dependencies=[Depends(authenticate_admin)])
async def complete_request(request_id: str):
    """
    Admin endpoint to mark a conversion request as completed.
    Requires basic authentication with username 'admin' and the admin password.
    """
    if update_conversion_request_status(request_id, "admin_completed"):
        return {"message": f"Request {request_id} marked as admin_completed."}
    raise HTTPException(status_code=404, detail="Conversion request not found.")

@app.get("/api/admin/requests/{request_id}", dependencies=[Depends(authenticate_admin)])
async def get_single_request(request_id: str):
    """
    Admin endpoint to get a single conversion request by ID.
    Requires basic authentication with username 'admin' and the admin password.
    """
    request = get_conversion_request_by_id(request_id)
    if request:
        return request
    raise HTTPException(status_code=404, detail="Conversion request not found.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
