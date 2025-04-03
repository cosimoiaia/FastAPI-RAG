# Running the RAG Pipeline

This guide explains how to run and test the RAG pipeline project step by step.

## Prerequisites

1. Python 3.10 or higher
2. Docker and Docker Compose
3. kubectl (for Kubernetes deployment)
4. GitHub CLI (optional, for model version management)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/igenius-rag.git
cd igenius-rag
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration:
# - GROQ_API_KEY: Your Groq API key
# - GROQ_MODEL: Model name (e.g., mixtral-8x7b-32768)
# - VECTORDB_PATH: Path for vector database storage
```

## Running the Application

### Local Development Server

1. Start the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

2. Visit the API documentation:
```
http://localhost:8000/docs
```

### Docker Container

1. Build and run with Docker:
```bash
# Build the image
docker build -t rag-api .

# Run the container
docker run -p 8000:8000 --env-file .env rag-api
```

## Running Tests

### Unit Tests

1. Install test dependencies:
```bash
pip install pytest pytest-cov
```

2. Run unit tests with coverage:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

### Load Tests

1. Run load tests:
```bash
# Run with default parameters
python tests/load_test.py

# Run with custom parameters
python tests/load_test.py --requests 1000 --concurrent 20 --url http://localhost:8000
```

## Kubernetes Deployment

1. Apply Kubernetes configurations:
```bash
# Apply base deployment
kubectl apply -f k8s/deployment.yaml

# Apply monitoring stack
kubectl apply -f k8s/monitoring/

# Apply KEDA scaler
kubectl apply -f k8s/keda-scaler.yaml
```

2. Verify deployment:
```bash
kubectl get pods -l app=rag-api
kubectl get services -l app=rag-api
```

3. Access monitoring:
```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3000:3000

# Visit Grafana dashboard
http://localhost:3000
```

## Model Version Management

1. Check current model version:
```bash
cat models/VERSION
```

2. Download specific model version:
```bash
gh release download model-v1.0.0
```

## Troubleshooting

### Common Issues

1. API Connection Issues:
   - Check GROQ_API_KEY in .env
   - Verify network connectivity

2. Vector Database Issues:
   - Ensure VECTORDB_PATH is writable
   - Check disk space

3. Test Failures:
   - Verify Python version (3.10+)
   - Check all dependencies are installed
   - Ensure .env is properly configured

### Logs

1. View application logs:
```bash
# Local
tail -f logs/app.log

# Kubernetes
kubectl logs -f deployment/rag-api
```

2. View monitoring metrics:
```bash
# Prometheus metrics
curl http://localhost:8000/metrics
```

## CI/CD Pipeline

The project includes GitHub Actions workflows for:
- Automated testing
- Docker image building
- Kubernetes deployment
- Model versioning

To use them:
1. Fork the repository
2. Add required secrets:
   - `KUBE_CONFIG`: Kubernetes configuration
   - `GROQ_API_KEY`: Groq API key
3. Push to main branch or create a PR

The pipelines will automatically run tests, build images, and deploy to your cluster.
