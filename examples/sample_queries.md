# Sample RAG Pipeline Queries

This document provides example queries and their responses from the RAG pipeline, demonstrating successful retrieval from both structured (CSV) and unstructured (PDF) data sources.

## Structured Data (CSV) Example

### Sample CSV Data
```csv
date,symbol,price,volume,market_cap
2024-03-15,NVDA,878.35,125.4M,2.16T
2024-03-14,NVDA,860.77,98.2M,2.11T
2024-03-13,NVDA,845.22,112.3M,2.08T
```

### Query
```json
{
    "query": "What is NVIDIA's current stock price?"
}
```

### Response
```json
{
    "answer": "NVIDIA's current stock price is $878.35 as of March 15, 2024. The stock has shown significant growth, with a market capitalization of $2.16 trillion.",
    "sources": [
        {
            "document_id": "stock_data.csv:row_1",
            "content": "2024-03-15 NVDA 878.35 125.4M 2.16T",
            "relevance_score": 0.98
        }
    ],
    "confidence": 0.98
}
```

## Unstructured Data (PDF) Example

### Sample PDF Content
Technical documentation about NVIDIA's B200 platform and its capabilities.

### Query
```json
{
    "query": "What are the key features of NVIDIA's B200 platform?"
}
```

### Response
```json
{
    "answer": "The NVIDIA B200 platform represents a significant advancement in AI computing. It features 208 billion transistors, 192GB of HBM3e memory, and delivers up to 1.4 petaflops of AI performance. The platform is designed for large language model training and inference, offering 4x faster training and 30x faster inference compared to previous generations. It also includes advanced features like dynamic programming and improved energy efficiency.",
    "sources": [
        {
            "document_id": "b200_specs.pdf:page_2",
            "content": "NVIDIA B200 Platform Specifications: The B200 features 208B transistors, 192GB HBM3e memory, and delivers 1.4 petaflops of AI performance. Key improvements include 4x faster training and 30x faster inference capabilities, along with enhanced energy efficiency and dynamic programming features.",
            "relevance_score": 0.95
        }
    ],
    "confidence": 0.95
}
```

## Combined Knowledge Query

### Query
```json
{
    "query": "How has NVIDIA's stock performance been since the B200 announcement?"
}
```

### Response
```json
{
    "answer": "NVIDIA's stock has shown significant growth following the B200 platform announcement. The stock price has increased from $845.22 on March 13 to $878.35 on March 15, with trading volume increasing to 125.4M shares. The B200 platform's impressive specifications, including 208B transistors and 192GB HBM3e memory, along with its 4x faster training and 30x faster inference capabilities, have contributed to positive market sentiment. The company's market capitalization has grown to $2.16 trillion, reflecting strong investor confidence in NVIDIA's AI leadership position.",
    "sources": [
        {
            "document_id": "stock_data.csv:row_1",
            "content": "2024-03-15 NVDA 878.35 125.4M 2.16T",
            "relevance_score": 0.97
        },
        {
            "document_id": "stock_data.csv:row_3",
            "content": "2024-03-13 NVDA 845.22 112.3M 2.08T",
            "relevance_score": 0.96
        },
        {
            "document_id": "b200_specs.pdf:page_2",
            "content": "NVIDIA B200 Platform Specifications: The B200 features 208B transistors, 192GB HBM3e memory, and delivers 1.4 petaflops of AI performance. Key improvements include 4x faster training and 30x faster inference capabilities, along with enhanced energy efficiency and dynamic programming features.",
            "relevance_score": 0.94
        }
    ],
    "confidence": 0.96
}
```

## Error Handling Example

### Invalid Query
```json
{
    "query": ""  // Empty query
}
```

### Response
```json
{
    "detail": "Query cannot be empty"
}
```

### Rate Limited Query
```json
{
    "query": "What is the historical performance of NVIDIA stock?"
}
```

### Response
```json
{
    "detail": "Rate limit exceeded. Please try again later."
}
```
