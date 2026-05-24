FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Make the startup script executable
RUN chmod +x start.sh
# Cloud Run exposes port 8080
EXPOSE 8080
CMD ["./start.sh"]