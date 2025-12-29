"""
Ingest Service - Video download and metadata extraction via Invidious/Piped API
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
    description="Service for downloading videos and extracting metadata via Invidious/Piped",
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

# Proxy settings (set in environment)
PROXY_URL = os.getenv("PROXY_URL", None)  # e.g., "socks5://127.0.0.1:1080"

# Piped API instances (usually work better)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.yt",
    "https://pipedapi.in.projectsegfau.lt",
    "https://pipedapi.adminforge.de",
    "https://api.piped.privacydev.net",
]

# Invidious instances (fallback)
INVIDIOUS_INSTANCES = [
    "https://vid.puffyan.us",
    "https://yewtu.be",
    "https://invidious.snopyta.org",
    "https://invidious.kavin.rocks",
    "https://inv.riverside.rocks",
]

# In-memory task storage (replace with Redis/DB in production)
tasks: dict[UUID, DownloadTask] = {}

# Cache for working instances
_working_piped: Optional[str] = None
_working_invidious: Optional[str] = None


def get_http_client_kwargs() -> dict:
    """Get httpx client kwargs with optional proxy"""
    kwargs = {"timeout": 15.0}
    if PROXY_URL:
        kwargs["proxies"] = {"all://": PROXY_URL}
    return kwargs


async def find_working_piped() -> Optional[str]:
    """Find a working Piped instance"""
    global _working_piped
    if _working_piped:
        return _working_piped
    
    async with httpx.AsyncClient(**get_http_client_kwargs()) as client:
        for instance in PIPED_INSTANCES:
            try:
                response = await client.get(f"{instance}/healthcheck")
                if response.status_code == 200:
                    _working_piped = instance
                    print(f"Found working Piped: {instance}")
                    return instance
            except Exception as e:
                print(f"Piped {instance} failed: {e}")
                continue
    return None


async def find_working_invidious() -> Optional[str]:
    """Find a working Invidious instance"""
    global _working_invidious
    if _working_invidious:
        return _working_invidious
    
    async with httpx.AsyncClient(**get_http_client_kwargs()) as client:
        for instance in INVIDIOUS_INSTANCES:
            try:
                response = await client.get(f"{instance}/api/v1/stats")
                if response.status_code == 200:
                    _working_invidious = instance
                    print(f"Found working Invidious: {instance}")
                    return instance
            except Exception as e:
                print(f"Invidious {instance} failed: {e}")
                continue
    return None


async def search_piped(query: str, max_results: int) -> list[VideoMetadata]:
    """Search via Piped API"""
    instance = await find_working_piped()
    if not instance:
        return []
    
    async with httpx.AsyncClient(**get_http_client_kwargs()) as client:
        try:
            response = await client.get(
                f"{instance}/search",
                params={"q": query, "filter": "videos"}
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Piped search error: {e}")
            return []
    
    videos = []
    items = data.get("items", [])[:max_results]
    
    for item in items:
        video_id = item.get("url", "").replace("/watch?v=", "")
        if not video_id:
            continue
            
        videos.append(VideoMetadata(
            video_id=video_id,
            title=item.get("title", "Unknown"),
            channel=item.get("uploaderName", "Unknown"),
            upload_date=datetime.utcnow(),  # Piped doesn't return exact date
            duration=item.get("duration", 0),
            description=item.get("shortDescription", ""),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=item.get("thumbnail", "")
        ))
    
    return videos


async def search_invidious(query: str, max_results: int) -> list[VideoMetadata]:
    """Search via Invidious API"""
    instance = await find_working_invidious()
    if not instance:
        return []
    
    async with httpx.AsyncClient(**get_http_client_kwargs()) as client:
        try:
            response = await client.get(
                f"{instance}/api/v1/search",
                params={"q": query, "type": "video", "sort_by": "relevance"}
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Invidious search error: {e}")
            return []
    
    videos = []
    for item in data[:max_results]:
        if item.get("type") != "video":
            continue
            
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
    """List available API instances and their status"""
    results = {"piped": [], "invidious": [], "proxy_configured": PROXY_URL is not None}
    
    async with httpx.AsyncClient(**get_http_client_kwargs()) as client:
        # Check Piped
        for instance in PIPED_INSTANCES:
            try:
                response = await client.get(f"{instance}/healthcheck", timeout=5.0)
                results["piped"].append({
                    "url": instance,
                    "status": "online" if response.status_code == 200 else "error"
                })
            except Exception:
                results["piped"].append({"url": instance, "status": "offline"})
        
        # Check Invidious
        for instance in INVIDIOUS_INSTANCES:
            try:
                response = await client.get(f"{instance}/api/v1/stats", timeout=5.0)
                results["invidious"].append({
                    "url": instance,
                    "status": "online" if response.status_code == 200 else "error"
                })
            except Exception:
                results["invidious"].append({"url": instance, "status": "offline"})
    
    return results


@app.post("/search", response_model=list[VideoMetadata])
async def search_videos(request: SearchRequest):
    """
    Search for videos using Piped/Invidious API
    
    Tries Piped first, falls back to Invidious
    """
    # Try Piped first
    videos = await search_piped(request.query, request.max_results)
    if videos:
        return videos
    
    # Fallback to Invidious
    videos = await search_invidious(request.query, request.max_results)
    if videos:
        return videos
    
    # All APIs failed
    raise HTTPException(
        status_code=503,
        detail="All video APIs are unavailable. Try using /upload to upload files directly, or configure PROXY_URL."
    )


@app.get("/video/{video_id}", response_model=VideoMetadata)
async def get_video_info(video_id: str):
    """Get detailed video information using yt-dlp (works without API)"""
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, get_video_info_ytdlp, video_id)
        
        upload_date = datetime.utcnow()
        if info.get("upload_date"):
            try:
                upload_date = datetime.strptime(info["upload_date"], "%Y%m%d")
            except Exception:
                pass
        
        return VideoMetadata(
            video_id=video_id,
            title=info.get("title", "Unknown"),
            channel=info.get("uploader", "Unknown"),
            upload_date=upload_date,
            duration=info.get("duration", 0),
            description=info.get("description", ""),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=info.get("thumbnail", "")
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")


def get_video_info_ytdlp(video_id: str) -> dict:
    """Get video info using yt-dlp (no download)"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }
    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)


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
    """Download audio from video using yt-dlp (synchronous)"""
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
    }
    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL
    
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
        video_id = extract_video_id(video_url)
        task.video_id = video_id
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, f"{video_id}.mp3")
            
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                None, 
                download_audio_sync, 
                video_url, 
                output_path
            )
            
            actual_path = output_path
            if not os.path.exists(actual_path):
                actual_path = output_path.replace('.mp3', '') + '.mp3'
            
            object_name = f"audio/{politician_name}/{video_id}.mp3"
            
            try:
                storage_client.upload_file(actual_path, object_name)
                task.audio_path = object_name
            except Exception as e:
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
    
    Uses yt-dlp which often works even without VPN
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
    Upload audio/video file directly (best option if APIs are blocked)
    
    Supports: mp3, wav, mp4, webm, ogg, m4a
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
        ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        object_name = f"audio/{politician_name}/{video_id}{ext}"
        
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
    """Get download task status"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.get("/tasks", response_model=list[DownloadTask])
async def list_tasks(status: Optional[TaskStatus] = None):
    """List all download tasks"""
    result = list(tasks.values())
    if status:
        result = [t for t in result if t.status == status]
    return sorted(result, key=lambda x: x.created_at, reverse=True)


@app.post("/reset-cache")
async def reset_instance_cache():
    """Reset cached API instances (try finding new working ones)"""
    global _working_piped, _working_invidious
    _working_piped = None
    _working_invidious = None
    return {"message": "Cache cleared. Next request will try all instances."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
