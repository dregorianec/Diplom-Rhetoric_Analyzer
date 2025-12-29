"""
Ingest Service - Video download and metadata extraction via Invidious API
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from uuid import uuid4, UUID
import sys
import os
import tempfile
import asyncio
from typing import Optional
import httpx
import yt_dlp

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.schemas import (
    HealthCheck, IngestRequest, SearchRequest,
    VideoMetadata, DownloadTask, TaskStatus
)
from shared.database import get_db
from shared.storage import storage_client
from sqlalchemy.orm import Session

app = FastAPI(
    title="Rhetoric Analyzer - Ingest Service",
    description="Service for downloading videos and extracting metadata via Invidious",
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

# Invidious instances (fallback list)
INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de", 
    "https://invidious.privacyredirect.com",
    "https://vid.puffyan.us",
    "https://invidious.lunar.icu",
]

# In-memory task storage (replace with Redis/DB in production)
tasks: dict[UUID, DownloadTask] = {}


async def get_working_instance() -> str:
    """Find a working Invidious instance"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        for instance in INVIDIOUS_INSTANCES:
            try:
                response = await client.get(f"{instance}/api/v1/stats")
                if response.status_code == 200:
                    return instance
            except Exception:
                continue
    raise HTTPException(
        status_code=503, 
        detail="No working Invidious instance found. Try again later."
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service="ingest",
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/instances")
async def list_instances():
    """List available Invidious instances and their status"""
    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for instance in INVIDIOUS_INSTANCES:
            try:
                response = await client.get(f"{instance}/api/v1/stats")
                results.append({
                    "url": instance,
                    "status": "online" if response.status_code == 200 else "error",
                })
            except Exception:
                results.append({"url": instance, "status": "offline"})
    return results


@app.post("/search", response_model=list[VideoMetadata])
async def search_videos(request: SearchRequest):
    """
    Search for videos using Invidious API
    
    Args:
        request: Search query and max results
    
    Returns:
        List of video metadata
    """
    instance = await get_working_instance()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{instance}/api/v1/search",
                params={
                    "q": request.query,
                    "type": "video",
                    "sort_by": "relevance",
                }
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Invidious API error: {str(e)}")
    
    videos = []
    for item in data[:request.max_results]:
        if item.get("type") != "video":
            continue
            
        # Parse upload date
        upload_date = datetime.utcnow()
        if item.get("published"):
            try:
                upload_date = datetime.fromtimestamp(item["published"])
            except Exception:
                pass
        
        videos.append(VideoMetadata(
            video_id=item.get("videoId", ""),
            title=item.get("title", "Unknown"),
            channel=item.get("author", "Unknown"),
            upload_date=upload_date,
            duration=item.get("lengthSeconds", 0),
            description=item.get("description", ""),
            url=f"https://www.youtube.com/watch?v={item.get('videoId', '')}",
            thumbnail_url=item.get("videoThumbnails", [{}])[0].get("url", "")
        ))
    
    return videos


@app.get("/video/{video_id}", response_model=VideoMetadata)
async def get_video_info(video_id: str):
    """
    Get detailed video information
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        Video metadata
    """
    instance = await get_working_instance()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{instance}/api/v1/videos/{video_id}")
            response.raise_for_status()
            item = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Invidious API error: {str(e)}")
    
    upload_date = datetime.utcnow()
    if item.get("published"):
        try:
            upload_date = datetime.fromtimestamp(item["published"])
        except Exception:
            pass
    
    return VideoMetadata(
        video_id=item.get("videoId", video_id),
        title=item.get("title", "Unknown"),
        channel=item.get("author", "Unknown"),
        upload_date=upload_date,
        duration=item.get("lengthSeconds", 0),
        description=item.get("description", ""),
        url=f"https://www.youtube.com/watch?v={video_id}",
        thumbnail_url=item.get("videoThumbnails", [{}])[0].get("url", "")
    )


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats"""
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Just the ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


def download_audio_sync(video_url: str, output_path: str) -> dict:
    """
    Download audio from video using yt-dlp (synchronous)
    
    Returns metadata dict
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path.replace('.mp3', ''),
        'quiet': True,
        'no_warnings': True,
        # Proxy support (uncomment if needed)
        # 'proxy': os.getenv('PROXY_URL'),
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return {
            'title': info.get('title'),
            'channel': info.get('uploader'),
            'duration': info.get('duration'),
            'video_id': info.get('id'),
        }


async def process_download(task_id: UUID, video_url: str, politician_name: str):
    """Background task to download and process video"""
    task = tasks[task_id]
    task.status = TaskStatus.PROCESSING
    
    try:
        # Extract video ID
        video_id = extract_video_id(video_url)
        task.video_id = video_id
        
        # Create temp file for download
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, f"{video_id}.mp3")
            
            # Download audio (run in thread pool to not block)
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                None, 
                download_audio_sync, 
                video_url, 
                output_path
            )
            
            # Actual output file (yt-dlp adds .mp3)
            actual_path = output_path
            if not os.path.exists(actual_path):
                actual_path = output_path.replace('.mp3', '') + '.mp3'
            
            # Upload to MinIO
            object_name = f"audio/{politician_name}/{video_id}.mp3"
            
            try:
                storage_client.upload_file(actual_path, object_name)
                task.audio_path = object_name
            except Exception as e:
                # MinIO might not be configured, save local path for now
                task.audio_path = f"local:{actual_path}"
                print(f"MinIO upload failed, using local: {e}")
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()


@app.post("/download", response_model=DownloadTask)
async def download_video(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Download video from YouTube
    
    Args:
        request: Video URL and politician name
    
    Returns:
        Download task with status
    """
    task_id = uuid4()
    
    try:
        video_id = extract_video_id(request.video_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    task = DownloadTask(
        task_id=task_id,
        video_id=video_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    tasks[task_id] = task
    
    # Start background download
    background_tasks.add_task(
        process_download, 
        task_id, 
        request.video_url, 
        request.politician_name
    )
    
    return task


@app.post("/upload", response_model=DownloadTask)
async def upload_file(
    file: UploadFile = File(...),
    politician_name: str = Form(...),
    title: str = Form(default="Uploaded file")
):
    """
    Upload audio/video file directly (alternative to YouTube download)
    
    Args:
        file: Audio or video file
        politician_name: Name of the politician
        title: Optional title for the file
    
    Returns:
        Upload task with status
    """
    task_id = uuid4()
    video_id = f"upload_{task_id.hex[:8]}"
    
    task = DownloadTask(
        task_id=task_id,
        video_id=video_id,
        status=TaskStatus.PROCESSING,
        created_at=datetime.utcnow()
    )
    tasks[task_id] = task
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Upload to MinIO
        object_name = f"audio/{politician_name}/{video_id}{os.path.splitext(file.filename)[1]}"
        
        try:
            storage_client.upload_file(tmp_path, object_name)
            task.audio_path = object_name
        except Exception as e:
            task.audio_path = f"local:{tmp_path}"
            print(f"MinIO upload failed: {e}")
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
    
    return task


@app.get("/task/{task_id}", response_model=DownloadTask)
async def get_task_status(task_id: UUID):
    """
    Get download task status
    
    Args:
        task_id: UUID of the task
    
    Returns:
        Task status
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]


@app.get("/tasks", response_model=list[DownloadTask])
async def list_tasks(status: Optional[TaskStatus] = None):
    """
    List all download tasks
    
    Args:
        status: Optional filter by status
    
    Returns:
        List of tasks
    """
    result = list(tasks.values())
    if status:
        result = [t for t in result if t.status == status]
    return sorted(result, key=lambda x: x.created_at, reverse=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
