FROM python:3.11-slim
WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your files
COPY . .

# Expose the port Cloud Run expects
EXPOSE 8080

# Run BOTH servers directly from Docker (Bypasses start.sh bugs and forces Headless mode)
CMD bash -c "uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run ui.py --server.port 8080 --server.address 0.0.0.0 --server.headless true --server.enableCORS false"
