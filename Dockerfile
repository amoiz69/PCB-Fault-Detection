# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve backend + frontend together
FROM python:3.12-slim

# Install system packages required for OpenCV and SQLite
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face runs containers as non-root user (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install backend dependencies
COPY --chown=user:user backend/requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy backend codebase
COPY --chown=user:user backend/ ./

# Copy compiled React frontend assets from Stage 1 into backend's static directory
COPY --chown=user:user --from=frontend-builder /frontend/dist ./static

# Ensure runtime directories exist
RUN mkdir -p uploads

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
