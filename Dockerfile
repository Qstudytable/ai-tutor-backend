FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Force Streamlit into production mode
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Google Cloud Run expects the app to listen on the environment variable $PORT
EXPOSE 8080

# Run FastAPI and Streamlit, explicitly passing the $PORT variable
CMD uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run ui.py --server.port $PORT --server.address 0.0.0.0
