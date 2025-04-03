# Sample RAG Pipeline Queries

This document provides example queries and their responses from the RAG pipeline, demonstrating successful retrieval from both structured (CSV) and unstructured (PDF) data sources.

## Structured Data (CSV) Example

### Sample CSV Data
```csv
product_id,name,description,price
1,Widget Pro,Advanced widget for professional use,299.99
2,Basic Widget,Entry-level widget for beginners,99.99
```

### Query
```json
{
    "text": "What is the price of Widget Pro?"
}
```

### Response
```json
{
    "answer": "The Widget Pro costs $299.99.",
    "sources": [
        {
            "document_id": "products.csv:row_1",
            "content": "1 Widget Pro Advanced widget for professional use 299.99",
            "relevance_score": 0.92
        }
    ],
    "confidence": 0.92
}
```

## Unstructured Data (PDF) Example

### Sample PDF Content
Technical documentation about widget maintenance and best practices.

### Query
```json
{
    "text": "What are the maintenance requirements for Widget Pro?"
}
```

### Response
```json
{
    "answer": "According to the technical documentation, Widget Pro requires monthly cleaning and calibration. The maintenance schedule includes: 1) Weekly dust removal, 2) Monthly sensor calibration, 3) Quarterly software updates.",
    "sources": [
        {
            "document_id": "widget_manual.pdf:page_7",
            "content": "Widget Pro Maintenance Schedule: Perform weekly dust removal using compressed air. Monthly calibration of sensors is required to maintain accuracy. Software updates should be applied quarterly.",
            "relevance_score": 0.89
        }
    ],
    "confidence": 0.89
}
```

## Combined Knowledge Query

### Query
```json
{
    "text": "Tell me about Widget Pro's features and maintenance costs."
}
```

### Response
```json
{
    "answer": "Widget Pro is an advanced professional widget priced at $299.99. It requires regular maintenance including monthly calibration and quarterly software updates. The maintenance is designed to ensure optimal performance for professional use cases.",
    "sources": [
        {
            "document_id": "products.csv:row_1",
            "content": "1 Widget Pro Advanced widget for professional use 299.99",
            "relevance_score": 0.95
        },
        {
            "document_id": "widget_manual.pdf:page_7",
            "content": "Widget Pro Maintenance Schedule: Perform weekly dust removal using compressed air. Monthly calibration of sensors is required to maintain accuracy. Software updates should be applied quarterly.",
            "relevance_score": 0.87
        }
    ],
    "confidence": 0.91
}
