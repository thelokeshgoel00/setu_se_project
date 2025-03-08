FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build frontend
RUN npm run build

# Backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for serving the frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g serve@latest

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ ./app/
COPY .env.example ./.env

# Copy built frontend from the frontend-build stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create a script to run both services
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Expose ports for backend and frontend
EXPOSE 8000 5173

# Run the application
ENTRYPOINT ["./docker-entrypoint.sh"] 