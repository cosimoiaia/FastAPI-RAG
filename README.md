# iGenius RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline that processes both structured and unstructured data to provide contextual responses using LLMs.

## Features

- FastAPI-based REST API
- Vector database integration using ChromaDB
- Support for both structured (CSV) and unstructured (PDF) data
- Kubernetes-ready with Docker containerization
- Monitoring and logging integration
- Comprehensive test suite
- CI/CD pipeline ready

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
├── tests/                # Test suite
├── k8s/                  # Kubernetes manifests
└── docker/               # Docker configuration
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Testing

Run tests with:
```bash
pytest
```

## License

MIT
