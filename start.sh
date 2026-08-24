#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Kill any existing processes on ports 8000 and 8501
lsof -i :8000 -t | xargs kill -9 2>/dev/null
lsof -i :8501 -t | xargs kill -9 2>/dev/null

echo "🚀 Starting FastAPI Backend..."
python3 -m uvicorn backend.app.main:app --reload --port 8000 &

echo "🎨 Starting Streamlit Frontend..."
streamlit run streamlit_app.py --server.port 8501

