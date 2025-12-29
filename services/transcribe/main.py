"""
Transcribe Service - Speech-to-text using Whisper
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
    HealthCheck, TranscribeTask, Transcript,
    TranscriptSegment, TaskStatus
)
from shared.database import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Rhetoric Analyzer - Transcribe Service",
    description="Service for audio transcription using Whisper",
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
        service="transcribe",
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/transcribe/{audio_id}", response_model=TranscribeTask)
async def transcribe_audio(audio_id: str):
    """
    Start transcription task for audio file
    
    Args:
        audio_id: ID of audio file in MinIO
    
    Returns:
        Transcription task with status
    """
    task_id = uuid4()
    
    # TODO: Implement actual transcription logic
    # 1. Download audio from MinIO
    # 2. Run Whisper inference
    # 3. Extract segments with timestamps
    # 4. Save to database
    # 5. Send message to Celery queue for analysis
    
    task = TranscribeTask(
        task_id=task_id,
        audio_id=audio_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    return task


@app.get("/task/{task_id}", response_model=TranscribeTask)
async def get_task_status(task_id: str):
    """
    Get transcription task status
    
    Args:
        task_id: UUID of the task
    
    Returns:
        Task status
    """
    # TODO: Query database for task status
    
    return TranscribeTask(
        task_id=task_id,
        audio_id="mock_audio_id",
        status=TaskStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        transcript_id=uuid4()
    )


@app.get("/transcript/{transcript_id}", response_model=Transcript)
async def get_transcript(transcript_id: str):
    """
    Get full transcript by ID
    
    Args:
        transcript_id: UUID of the transcript
    
    Returns:
        Complete transcript with segments
    """
    # TODO: Query database for transcript
    
    return Transcript(
        transcript_id=transcript_id,
        video_id="mock_video_id",
        language="en",
        segments=[
            TranscriptSegment(
                start_time=0.0,
                end_time=5.0,
                text="This is a mock transcript segment.",
                confidence=0.95
            )
        ],
        processing_time=10.5,
        created_at=datetime.utcnow()
    )


@app.get("/transcript/{transcript_id}/segments", response_model=list[TranscriptSegment])
async def get_transcript_segments(transcript_id: str, skip: int = 0, limit: int = 100):
    """
    Get transcript segments with pagination
    
    Args:
        transcript_id: UUID of the transcript
        skip: Number of segments to skip
        limit: Maximum number of segments to return
    
    Returns:
        List of transcript segments
    """
    # TODO: Query database for segments
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

