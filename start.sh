#!/bin/bash
# Start script for Railway deployment
# Runs both FastAPI (for API endpoints) and Streamlit (for dashboard UI)

# Railway sets PORT env var - use it for Streamlit, FastAPI runs on internal port 8000
STREAMLIT_PORT=${PORT:-8501}
API_PORT=8000

echo "Starting Portal IQ services..."
echo "- FastAPI API on internal port ${API_PORT}"
echo "- Streamlit Dashboard on port ${STREAMLIT_PORT}"

# Start FastAPI in the background
cd /app/dashboard
uvicorn api.main:app --host 0.0.0.0 --port ${API_PORT} &
FASTAPI_PID=$!
echo "FastAPI started with PID ${FASTAPI_PID}"

# Wait for FastAPI to be ready
sleep 2

# Start Streamlit in the foreground
exec streamlit run app.py --server.port=${STREAMLIT_PORT} --server.address=0.0.0.0
