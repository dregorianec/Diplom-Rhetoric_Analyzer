"""
Celery tasks for async video processing
"""
import os
import sys
from celery import Celery

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
)


@app.task(bind=True, name="tasks.download_video")
def download_video_task(self, video_url: str, politician_name: str):
    """
    Background task to download video
    """
    import tempfile
    import yt_dlp
    from shared.storage import storage_client
    
    task_id = self.request.id
    
    try:
        # Extract video ID
        video_id = extract_video_id(video_url)
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'video_id': video_id})
        
        # Download
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, f"{video_id}.mp3")
            
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
            
            proxy = os.getenv("PROXY_URL")
            if proxy:
                ydl_opts['proxy'] = proxy
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
            
            # Find actual file
            actual_path = output_path
            if not os.path.exists(actual_path):
                actual_path = output_path.replace('.mp3', '') + '.mp3'
            
            # Upload to storage
            object_name = f"audio/{politician_name}/{video_id}.mp3"
            try:
                storage_client.upload_file(actual_path, object_name)
            except Exception as e:
                print(f"Storage upload failed: {e}")
                object_name = f"local:{actual_path}"
            
            return {
                'status': 'completed',
                'video_id': video_id,
                'audio_path': object_name,
                'title': info.get('title'),
            }
            
    except Exception as e:
        self.update_state(state='FAILED', meta={'error': str(e)})
        raise


@app.task(name="tasks.transcribe_audio")
def transcribe_audio_task(audio_path: str, video_id: str):
    """
    Background task to transcribe audio
    """
    # This will be handled by transcribe service
    # Just a placeholder for task routing
    return {"status": "pending", "audio_path": audio_path}


def extract_video_id(url: str) -> str:
    """Extract video ID from URL"""
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")

