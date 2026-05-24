#!/bin/bash
# Start FastAPI backend on port 8000
uvicorn main:app --host 0.0.0.0 --port 8000 &
# Start Streamlit UI on port 8080 (which Google Cloud Run expects)
streamlit run ui.py --server.port 8080 --server.address 0.0.0.0