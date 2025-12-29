"""
Analyze Service - Rhetoric pattern detection
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
    HealthCheck, AnalyzeRequest, AnalyzeTask,
    AnalysisResult, RhetoricDetection, VerificationRequest,
    TaskStatus, PatternType, DetectionMethod
)
from shared.database import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Rhetoric Analyzer - Analyze Service",
    description="Service for detecting rhetoric patterns in transcripts",
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
        service="analyze",
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/analyze", response_model=AnalyzeTask)
async def analyze_transcript(request: AnalyzeRequest):
    """
    Start analysis task for transcript
    
    Args:
        request: Transcript ID and politician name
    
    Returns:
        Analysis task with status
    """
    task_id = uuid4()
    
    # TODO: Implement actual analysis logic
    # 1. Load transcript from database
    # 2. Run rule-based detection
    # 3. Run ML classification
    # 4. Run RAG retrieval
    # 5. Generate LLM explanations
    # 6. Save results to database
    
    task = AnalyzeTask(
        task_id=task_id,
        transcript_id=request.transcript_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    return task


@app.get("/task/{task_id}", response_model=AnalyzeTask)
async def get_task_status(task_id: str):
    """
    Get analysis task status
    
    Args:
        task_id: UUID of the task
    
    Returns:
        Task status
    """
    # TODO: Query database for task status
    
    return AnalyzeTask(
        task_id=task_id,
        transcript_id=uuid4(),
        status=TaskStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        analysis_id=uuid4()
    )


@app.get("/results/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_results(analysis_id: str):
    """
    Get analysis results by ID
    
    Args:
        analysis_id: UUID of the analysis
    
    Returns:
        Complete analysis results with detections
    """
    # TODO: Query database for analysis results
    
    detection_id = uuid4()
    
    return AnalysisResult(
        analysis_id=analysis_id,
        video_id="mock_video_id",
        politician_name="Mock Politician",
        analysis_date=datetime.utcnow(),
        total_detections=1,
        detections_by_type={"false_dilemma": 1},
        detections=[
            RhetoricDetection(
                id=detection_id,
                transcript_id=uuid4(),
                timestamp_start=10.0,
                timestamp_end=15.0,
                text="You're either with us or against us.",
                pattern_type=PatternType.FALSE_DILEMMA,
                confidence=0.85,
                detection_method=DetectionMethod.ENSEMBLE,
                explanation="This statement presents a false dichotomy, limiting options to only two extremes.",
                similar_examples=["Example 1", "Example 2"]
            )
        ],
        overall_summary="Found 1 instance of false dilemma pattern."
    )


@app.post("/verify")
async def verify_detection(request: VerificationRequest):
    """
    Human verification of detection (HITL)
    
    Args:
        request: Detection ID and verification status
    
    Returns:
        Success message
    """
    # TODO: Update detection in database with verification
    
    return {
        "message": "Detection verified successfully",
        "detection_id": str(request.detection_id),
        "verified": request.verified
    }


@app.get("/patterns", response_model=list[str])
async def list_patterns():
    """
    List all available pattern types
    
    Returns:
        List of pattern names
    """
    return [pattern.value for pattern in PatternType]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

