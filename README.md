# iGenius RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline that processes both structured and unstructured data to provide contextual responses using LLMs.

## Features

- FastAPI-based REST API
- Vector database integration using ChromaDB
- Support for both structured (CSV) and unstructured (PDF) data
- Kubernetes-ready with Docker containerization
- Comprehensive monitoring and logging
- Auto-scaling with KEDA
- Load testing capabilities
- CI/CD pipeline ready
- Automatic model versioning

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
uvicorn app.main:app --reload
```

4. Visit the API documentation at `http://localhost:8000/docs`

## Project Structure

```
.
├── app/                    # Application source code
│   ├── api/               # API endpoints
│   ├── core/              # Core functionality
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── data/                  # Data storage
│   ├── raw/              # Raw input data
│   └── processed/        # Processed vector embeddings
├── k8s/                  # Kubernetes manifests
│   └── monitoring/      # Monitoring configuration
├── tests/                # Test suite
└── docker/               # Docker configuration
```

## Example Usage

See [examples/sample_queries.md](examples/sample_queries.md) for detailed examples of:
- Querying structured data (CSV)
- Querying unstructured data (PDF)
- Combined knowledge queries

## Model Versioning

The pipeline includes automatic model versioning:
- Version bumps on model changes
- Automatic releases with model archives
- Version tracking in `models/VERSION`
- GitHub releases for each model version

Access model versions:
```bash
# Get current version
cat models/VERSION

# Download specific version
gh release download model-v1.0.0
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Testing

Run unit tests:
```bash
pytest
```

Run load tests:
```bash
# Run with default parameters
python tests/load_test.py

# Run with custom parameters
python tests/load_test.py --requests 1000 --concurrent 20 --url http://localhost:8000
```

## Monitoring and Logging

The application includes comprehensive monitoring and logging:

### Metrics
- Query processing time
- Document processing time
- Total queries processed
- Documents processed
- Error rates

### Monitoring Stack
1. Prometheus for metrics collection
2. Grafana for visualization
3. Fluentd for log aggregation
4. Elasticsearch for log storage

### Dashboards
Access the Grafana dashboard at `http://grafana.your-domain/dashboards/rag-pipeline` to view:
- Query latency metrics
- Request rates
- Error rates
- System resource utilization

### Alerts
Configured alerts for:
- High error rates (>10% in 5 minutes)
- Slow query processing (95th percentile >5s)
- Resource utilization thresholds

## Load Testing

The application includes load testing capabilities using Locust.

### Running Load Tests

Run load tests with:
```bash
locust -f tests/load_test.py
```

### Load Test Configuration

Configure load test behavior in `tests/load_test.py`.

## Auto-scaling

The application uses KEDA for auto-scaling based on:
- Request rate
- Processing time
- Resource utilization

Configure scaling behavior in `k8s/keda-scaler.yaml`.

## License

MIT
