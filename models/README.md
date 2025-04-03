# Model Directory

This directory contains versioned model artifacts for the RAG pipeline:

## Structure

```
models/
├── VERSION             # Current model version
├── embeddings/        # Embedding model configurations
└── rag/              # RAG model configurations and weights
```

## Versioning

Model versions are automatically managed by GitHub Actions. When changes are made to models or the RAG pipeline implementation, a new version is created and released.

### Version Format

We use semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

### Accessing Versions

```bash
# Get current version
cat VERSION

# Download specific version
gh release download model-v1.0.0
```

## Model Updates

When updating models:
1. Make changes to model files
2. Commit and push changes
3. GitHub Actions will automatically:
   - Bump version number
   - Create model archive
   - Create GitHub release
   - Update VERSION file
