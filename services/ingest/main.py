"""
Ingest Service - YouTube video download and metadata extraction
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from uuid import uuid4
import sys
import os

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.schemas import (
    HealthCheck, IngestRequest, SearchRequest,
    VideoMetadata, DownloadTask, TaskStatus
)
from shared.database import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Rhetoric Analyzer - Ingest Service",
    description="Service for downloading YouTube videos and extracting metadata",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service="ingest",
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/search", response_model=list[VideoMetadata])
async def search_videos(request: SearchRequest):
    """
    Search for videos on YouTube
    
    Args:
        request: Search query and max results
    
    Returns:
        List of video metadata
    """
    # TODO: Implement YouTube API search
    # For now, return mock data
    
    return [
        VideoMetadata(
            video_id="mock_video_1",
            title=f"Speech about {request.query}",
            channel="Political Channel",
            upload_date=datetime.utcnow(),
            duration=600,
            description="Mock description",
            url=f"https://youtube.com/watch?v=mock_video_1",
            thumbnail_url="https://i.ytimg.com/vi/mock_video_1/default.jpg"
        )
    ]


@app.post("/download", response_model=DownloadTask)
async def download_video(request: IngestRequest, db: Session = Depends(get_db)):
    """
    Download video from YouTube
    
    Args:
        request: Video URL and politician name
        db: Database session
    
    Returns:
        Download task with status
    """
    # Create task
    task_id = uuid4()
    
    # TODO: Implement actual download logic
    # 1. Extract video_id from URL
    # 2. Use yt-dlp to download audio
    # 3. Upload to MinIO
    # 4. Save metadata to database
    # 5. Send message to Celery queue for transcription
    
    task = DownloadTask(
        task_id=task_id,
        video_id="extracted_video_id",
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    return task


@app.get("/task/{task_id}", response_model=DownloadTask)
async def get_task_status(task_id: str):
    """
    Get download task status
    
    Args:
        task_id: UUID of the task
    
    Returns:
        Task status
    """
    # TODO: Query database for task status
    
    return DownloadTask(
        task_id=task_id,
        video_id="mock_video_id",
        status=TaskStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        audio_path="audio/mock_video_id.mp3"
    )


@app.get("/videos", response_model=list[VideoMetadata])
async def list_videos(skip: int = 0, limit: int = 10):
    """
    List all downloaded videos
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of video metadata
    """
    # TODO: Query database for videos
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

