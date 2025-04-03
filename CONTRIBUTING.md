# Contributing to iGenius RAG Pipeline

Thank you for your interest in contributing to the iGenius RAG Pipeline project! This document provides guidelines and instructions for contributing.

## Development Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write or update tests
5. Submit a pull request

## Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

Before submitting a PR:
1. Run unit tests: `pytest`
2. Run load tests: `python tests/load_test.py`
3. Check code coverage: `pytest --cov=app`

## Documentation

Update documentation when you:
- Add new features
- Change existing functionality
- Fix bugs that affect user interaction

## Commit Messages

Follow conventional commits:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- test: Test updates
- refactor: Code refactoring
- chore: Maintenance tasks

## Pull Request Process

1. Update README.md with details of changes
2. Update requirements.txt if adding dependencies
3. Update tests to cover new functionality
4. Ensure CI/CD pipeline passes
5. Request review from maintainers

## Setting Up Development Environment

1. Clone your fork:
```bash
git clone https://github.com/yourusername/igenius-rag.git
cd igenius-rag
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up pre-commit hooks:
```bash
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_rag_pipeline.py
```

## Code Review Process

1. All submissions require review
2. Changes must have tests
3. PR must pass CI/CD pipeline
4. Documentation must be updated

## Questions?

Open an issue or contact the maintainers.
