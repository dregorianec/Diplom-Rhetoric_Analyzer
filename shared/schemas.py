"""
Shared Pydantic schemas for all microservices
"""
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


# ==================== ENUMS ====================

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PatternType(str, Enum):
    FALSE_DILEMMA = "false_dilemma"
    AD_HOMINEM = "ad_hominem"
    STRAW_MAN = "straw_man"
    SLIPPERY_SLOPE = "slippery_slope"
    APPEAL_TO_FEAR = "appeal_to_fear"
    APPEAL_TO_ANGER = "appeal_to_anger"
    APPEAL_TO_PATRIOTISM = "appeal_to_patriotism"
    CHERRY_PICKING = "cherry_picking"
    FALSE_STATISTICS = "false_statistics"
    OUT_OF_CONTEXT = "out_of_context"
    LABELING = "labeling"
    ANIMAL_METAPHOR = "animal_metaphor"


class DetectionMethod(str, Enum):
    RULE = "rule"
    ML = "ml"
    ENSEMBLE = "ensemble"


# ==================== VIDEO & INGEST ====================

class VideoMetadata(BaseModel):
    """Metadata extracted from YouTube video"""
    video_id: str
    title: str
    channel: str
    upload_date: datetime
    duration: int  # seconds
    description: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None


class DownloadTask(BaseModel):
    """Download task status"""
    task_id: UUID
    video_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    audio_path: Optional[str] = None


class IngestRequest(BaseModel):
    """Request to download video"""
    video_url: str
    politician_name: str


class SearchRequest(BaseModel):
    """Request to search videos"""
    query: str
    max_results: int = Field(default=10, ge=1, le=50)


# ==================== TRANSCRIPTION ====================

class TranscriptSegment(BaseModel):
    """Single segment of transcribed speech"""
    start_time: float  # seconds
    end_time: float
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    speaker_id: Optional[int] = None


class Transcript(BaseModel):
    """Complete transcription of video"""
    transcript_id: UUID
    video_id: str
    language: str
    segments: List[TranscriptSegment]
    wer_estimate: Optional[float] = None
    processing_time: float
    created_at: datetime


class TranscribeTask(BaseModel):
    """Transcription task status"""
    task_id: UUID
    audio_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    transcript_id: Optional[UUID] = None


# ==================== ANALYSIS ====================

class RhetoricDetection(BaseModel):
    """Single rhetoric pattern detection"""
    id: UUID
    transcript_id: UUID
    timestamp_start: float
    timestamp_end: float
    text: str
    pattern_type: PatternType
    confidence: float = Field(ge=0.0, le=1.0)
    detection_method: DetectionMethod
    explanation: str
    similar_examples: List[str] = []
    human_verified: Optional[bool] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete analysis result for video"""
    analysis_id: UUID
    video_id: str
    politician_name: str
    analysis_date: datetime
    total_detections: int
    detections_by_type: Dict[str, int]
    detections: List[RhetoricDetection]
    overall_summary: str


class AnalyzeTask(BaseModel):
    """Analysis task status"""
    task_id: UUID
    transcript_id: UUID
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    analysis_id: Optional[UUID] = None


class AnalyzeRequest(BaseModel):
    """Request to analyze transcript"""
    transcript_id: UUID
    politician_name: str


# ==================== HUMAN-IN-THE-LOOP ====================

class VerificationRequest(BaseModel):
    """Human verification of detection"""
    detection_id: UUID
    verified: bool
    feedback: Optional[str] = None
    verified_by: str


# ==================== HEALTH CHECK ====================

class HealthCheck(BaseModel):
    """Health check response"""
    service: str
    status: str
    timestamp: datetime
    version: str = "1.0.0"

