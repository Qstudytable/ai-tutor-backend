FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Force Streamlit into production mode (No email prompts, no analytics)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8080

# Run FastAPI in the background, and Streamlit in the foreground
CMD uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run ui.py
