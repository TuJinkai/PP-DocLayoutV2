# ARM-compatible Dockerfile for PaddleOCR-VL API
# Supports both x86 and ARM64 (Kunpeng)

FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

# Install runtime dependencies for OpenCV and image processing
# Use compatible package names for both x86 and ARM64
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libjpeg62-turbo \
    libpng16-16 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY api.py .

# Copy model files
COPY PP-DocLayoutV2 /app/PP-DocLayoutV2

# Environment variables
ENV DOCLAYOUT_MODEL_DIR=/app/PP-DocLayoutV2
ENV VL_REC_SERVER_URL=http://10.9.42.175:3000/v1
ENV VL_REC_API_KEY=sk-r3zC3KPb2M3NVMaduSrsjBdppFVWIqwEe6qH0QqOM6HgQ7eY
ENV VL_REC_API_MODEL_NAME=PaddleOCR-VL-0.9B
ENV PORT=5001

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Run the application
CMD ["python", "api.py"]