"""
Dashboard Service - Streamlit UI
"""
import streamlit as st
import requests
import os
from datetime import datetime

# API endpoints
INGEST_API = os.getenv("INGEST_API", "http://localhost:8001")
TRANSCRIBE_API = os.getenv("TRANSCRIBE_API", "http://localhost:8002")
ANALYZE_API = os.getenv("ANALYZE_API", "http://localhost:8003")

st.set_page_config(
    page_title="Rhetoric Analyzer",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Political Rhetoric Analyzer")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["Search & Submit", "Analysis Results", "Verification"]
    )

# Search & Submit Page
if page == "Search & Submit":
    st.header("🔍 Search Videos")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Search for politician or topic", placeholder="e.g. Donald Trump")
    
    with col2:
        max_results = st.number_input("Max results", min_value=1, max_value=50, value=10)
    
    if st.button("🔍 Search", type="primary"):
        if query:
            with st.spinner("Searching YouTube..."):
                try:
                    response = requests.post(
                        f"{INGEST_API}/search",
                        json={"query": query, "max_results": max_results}
                    )
                    
                    if response.status_code == 200:
                        videos = response.json()
                        st.success(f"Found {len(videos)} videos")
                        
                        for video in videos:
                            with st.expander(f"📹 {video['title']}"):
                                st.write(f"**Channel:** {video['channel']}")
                                st.write(f"**Duration:** {video['duration']} seconds")
                                st.write(f"**URL:** {video['url']}")
                                
                                if st.button(f"Download & Analyze", key=video['video_id']):
                                    st.info("Download started! Check Analysis Results page.")
                    else:
                        st.error("Search failed")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a search query")
    
    st.markdown("---")
    st.header("📥 Direct URL Submit")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        video_url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
    
    with col2:
        politician_name = st.text_input("Politician name", placeholder="e.g. Joe Biden")
    
    if st.button("▶️ Submit for Analysis", type="primary"):
        if video_url and politician_name:
            with st.spinner("Submitting..."):
                try:
                    response = requests.post(
                        f"{INGEST_API}/download",
                        json={"video_url": video_url, "politician_name": politician_name}
                    )
                    
                    if response.status_code == 200:
                        task = response.json()
                        st.success(f"✅ Task created: {task['task_id']}")
                        st.info("Processing started. Check Analysis Results page in a few minutes.")
                    else:
                        st.error("Submission failed")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please provide both URL and politician name")

# Analysis Results Page
elif page == "Analysis Results":
    st.header("📊 Analysis Results")
    
    # Mock data for now
    st.info("This page will show analysis results. Implementation pending.")
    
    # TODO: List all analyzed videos
    # TODO: Show timeline with detections
    # TODO: Display detection details
    # TODO: Export functionality

# Verification Page
elif page == "Verification":
    st.header("✅ Human Verification (HITL)")
    
    st.info("This page will show detections requiring human verification. Implementation pending.")
    
    # TODO: List unverified detections
    # TODO: Show detection details
    # TODO: Approve/Reject buttons
    # TODO: Feedback form

