#!/bin/bash
# Start script for Railway deployment
PORT=${PORT:-8501}
exec streamlit run dashboard/app.py --server.port=${PORT} --server.address=0.0.0.0
