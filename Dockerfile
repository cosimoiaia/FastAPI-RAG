# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser \
    && mkdir -p /app/data/raw /app/data/processed /app/data/vectordb \
    && chown -R appuser:appuser /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies in stages
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-deps fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.1 && \
    pip install --no-deps langgraph==0.0.26 langchain-core==0.1.27 langchain-groq==0.0.1 && \
    pip install --no-deps chromadb==0.4.18 pypdf==3.17.1 pandas==2.1.3 numpy==1.26.2 && \
    pip install --no-deps pytest==7.4.3 httpx==0.25.2 python-multipart==0.0.6 && \
    pip install --no-deps prometheus-client==0.19.0 prometheus-fastapi-instrumentator==6.1.0 && \
    pip install --no-deps groq==0.4.0 tiktoken==0.5.1 && \
    pip install --no-deps langchain-huggingface==0.0.8 transformers==4.37.2 && \
    pip install --no-deps torch==2.2.0 huggingface-hub==0.21.3

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
