# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Final Python environment
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (ffmpeg is required for whisper audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only version first to keep size small
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend files
COPY backend/ ./backend/

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose ports for API (8000) and Web App Frontend (5173)
EXPOSE 8000
EXPOSE 5173

# Set environment variables for model caching inside mapped volume
ENV HF_HOME=/app/data/models
ENV WHISPER_HOME=/app/data/models
ENV APPDATA=/app/data

# Create a startup script to run both services
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'python -m http.server 5173 --directory /app/frontend/dist &' >> /app/start.sh && \
    echo 'cd /app/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000' >> /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"]
