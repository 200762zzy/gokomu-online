# ===== Stage 1: Build frontend =====
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Build context must be project root (.) — use: docker build -f backend/Dockerfile .
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Python backend =====
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/run.py .
COPY backend/app/ ./app/

# Copy built frontend from stage 1
COPY --from=frontend-builder /build/dist ./frontend_dist/

EXPOSE 8000

CMD ["python", "run.py"]
