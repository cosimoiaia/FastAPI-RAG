# Design and Implement a RAG (Retrieval-Augmented Generation) Pipeline for Contextual Query Handling


## Objective:
The goal of this assignment is to design, implement, and deploy a Retrieval-Augmented Generation (RAG) pipeline for processing contextual queries, where a the system retrieves relevant external knowledge from a database or document corpus and a model uses that information to generates a more accurate response.

The candidate will also be in charge of populating the vector database with structured and unstructured data, such as PDFs and tabular data, and ensuring the retrieval system is optimized for both types of data.

The candidate should focus on:
	•	Data Retrieval: Fetching relevant context from a vector database.
	•	Model Interaction: Using the retrieved context to generate high-quality, coherent responses with a generative language model.
	•	Scalability & Automation: Automating the entire pipeline with a focus on modularity, scalability, and reproducibility in a cloud-native MLOps environment.


## Requirements
The RAG pipeline will execute the following steps:

	1.	Populate the vector database with both structured data (e.g., CSV or database records) and unstructured data (e.g., PDFs, text files).
    It's required to use both types of data
	2.	Retrieve relevant data from the vector database based on an input query.
	3.	Generate a response using a generative language model that incorporates the retrieved information.
	4.	Deploy and automate the pipeline for querying and response generation.
	5.	Implement logging, monitoring, and testing to ensure reliability and performance.

### API
Expose the RAG pipeline as a RESTful API for inference.

	•	Framework: Use FastAPI as web framework for implementing the API.
	•	API Design: Create endpoints for:
        •	Accepting a user query.
        •	Retrieving the context and generating a response.
	•	Containerization: Containerize the service using Docker to ensure portability.
	•	Deployment: Deploy the service to a Kubernetes cluster, ensuring it is easily scalable and fault-tolerant.
	•	Use K-Native/Keda for autoscaling (scale-to-zero when idle).
	•	Ensure the system can handle varying loads efficiently.

### CICD
Automate the pipeline and deployment process:

    •	Docker image builds.
    •	Deployment to the Kubernetes cluster.
	•	Use a tool like GitHub Actions or GitLab CI for the CI/CD pipeline.
	•	Implement automatic versioning for the model and its updates.

### [OPTIONAL] Monitoring and Logging
Ensure the system is observable in production.

	•	Monitoring: Integrate monitoring tools to track system performance and health (e.g., Prometheus, Grafana).
	•	Logging: Use a logging solution to capture important events (e.g., Fluentd, Loki).
	•	Monitor:
        	•	Request rates, response times.
        	•	Model performance (e.g., accuracy or quality of generated responses).
	        •	System health (e.g., errors, resource utilization).

### Testing and Validation
Implement tests to validate the entire RAG pipeline.

	•	Unit Tests: Write unit tests for the retrieval and generation components.
	•	Integration Tests: Ensure the entire pipeline (querying + generation) works as expected in a real-world scenario.
	•	Load Testing: Simulate query loads to validate the system’s scalability and response under stress.


## Deliverables:
	•	Code to extract and vectorize both structured and unstructured data.
	•	A snapshot populated vector database with both types of data.
	•	Sample queries demonstrating successful retrieval from both structured and unstructured data sources.
	•	Code for the retrieval logic to handle both structured and unstructured data.
	•	Example query results demonstrating successful retrieval of both data types.
	•	FastAPI API code.
	•	Dockerfile for containerization.
	•	Kubernetes deployment manifests (including any K-Native configurations).
    	•	A .github/workflows (or similar) file that automates the deployment.
	•	A brief explanation of the CI/CD setup and how it works.
    	•	Prometheus/Grafana setup for monitoring.
	•	Logs for query processing, retrieval, and generation.
	•	Example dashboard or screenshots showing system health and performance metrics.
	•	Unit and integration test code.
	•	Results from load tests, with a description of any optimizations made.

Use groq cloud api for LLM queries or text generation
UV as package/environment manager for python
Qdrant in a docker instance as vector database
