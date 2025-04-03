import os
from typing import List, Dict, Any, Union
from fastapi import UploadFile
from langchain_groq import ChatGroq
from groq import Groq
from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage, AIMessage
from chromadb import PersistentClient
from langgraph.graph import Graph, END
import pandas as pd
import pypdf
import numpy as np
from prometheus_client import Histogram, Counter
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import operator
import tempfile
import shutil
import logging
import time
from pathlib import Path

from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
QUERY_PROCESSING_TIME = Histogram('rag_query_processing_seconds', 'Time spent processing queries')
DOCUMENT_PROCESSING_TIME = Histogram('rag_document_processing_seconds', 'Time spent processing documents')
QUERIES_TOTAL = Counter('rag_queries_total', 'Total number of queries processed')
ERRORS_TOTAL = Counter('rag_errors_total', 'Total number of errors encountered')

class GroqEmbeddings(Embeddings):
    """Custom Groq embeddings class"""
    
    def __init__(self, groq_api_key: str, model_name: str = "llama2-70b-4096"):
        self.client = Groq(api_key=groq_api_key)
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding

class AgentState(BaseModel):
    messages: List[Union[HumanMessage, AIMessage]]
    context: str
    query: str

class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        # Initialize language model
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        # Initialize embeddings
        self.embeddings = GroqEmbeddings(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        # Initialize vector store
        self.vector_store = PersistentClient(path=settings.VECTORDB_PATH)
        self.collection = self.vector_store.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Create workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Graph:
        # Define the nodes
        def retrieve_context(state: AgentState) -> AgentState:
            logger.info(f"Retrieving context for query: {state.query}")
            start_time = time.time()
            try:
                query = state.query
                results = self.collection.query(
                    query_texts=[query],
                    n_results=3
                )
                context = "\n".join(results["documents"][0])
                state.context = context
                logger.info(f"Retrieved {len(results['documents'][0])} relevant documents")
                return state
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}")
                ERRORS_TOTAL.inc()
                raise
            finally:
                QUERY_PROCESSING_TIME.observe(time.time() - start_time)

        def generate_response(state: AgentState) -> AgentState:
            logger.info("Generating response")
            start_time = time.time()
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful AI assistant. Use the following context to answer the user's question: {context}"),
                    MessagesPlaceholder(variable_name="messages"),
                    ("human", "{query}")
                ])
                
                chain = prompt | self.llm | StrOutputParser()
                
                response = chain.invoke({
                    "context": state.context,
                    "messages": state.messages,
                    "query": state.query
                })
                
                state.messages.append(AIMessage(content=response))
                logger.info("Response generated successfully")
                return state
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                ERRORS_TOTAL.inc()
                raise
            finally:
                QUERY_PROCESSING_TIME.observe(time.time() - start_time)

        # Create the graph
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("retrieve", retrieve_context)
        workflow.add_node("generate", generate_response)
        
        # Add edges
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        # Set entry point
        workflow.set_entry_point("retrieve")
        
        return workflow.compile()

    async def process_query(self, query: str) -> Dict[str, Any]:
        logger.info(f"Processing query: {query}")
        start_time = time.time()
        try:
            QUERIES_TOTAL.inc()
            
            # Initialize state
            state = AgentState(
                messages=[],
                context="",
                query=query
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            # Get the last message (the response)
            response = final_state.messages[-1].content
            
            # Get the context documents
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            # Format sources
            sources = [
                {
                    "document_id": str(metadata.get("source", "unknown")),
                    "content": doc,
                    "relevance_score": score
                }
                for doc, metadata, score in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
            
            logger.info(f"Query processed successfully in {time.time() - start_time:.2f}s")
            return {
                "answer": response,
                "sources": sources,
                "confidence": 1.0 - sum(results["distances"][0]) / len(results["distances"][0])
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            QUERY_PROCESSING_TIME.observe(time.time() - start_time)

    async def ingest_document(self, file: UploadFile) -> Dict[str, Any]:
        logger.info(f"Ingesting document: {file.filename}")
        start_time = time.time()
        try:
            # Create temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / file.filename
                
                # Save uploaded file
                with open(temp_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                # Process based on file type
                if file.filename.endswith('.pdf'):
                    # Process PDF
                    with open(temp_path, 'rb') as f:
                        pdf = pypdf.PdfReader(f)
                        texts = [page.extract_text() for page in pdf.pages]
                        metadata = [{"source": f"{file.filename}:page_{i+1}"} for i in range(len(texts))]
                elif file.filename.endswith('.csv'):
                    # Process CSV
                    df = pd.read_csv(temp_path)
                    texts = df.apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()
                    metadata = [{"source": f"{file.filename}:row_{i+1}"} for i in range(len(texts))]
                else:
                    raise ValueError(f"Unsupported file type: {file.filename}")
                
                # Get embeddings
                embeddings = self.embeddings.embed_documents(texts)
                
                # Add to vector store
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadata,
                    ids=[f"doc_{i}" for i in range(len(texts))]
                )
                
                logger.info(f"Successfully ingested {len(texts)} documents from {file.filename}")
                return {
                    "num_documents": len(texts),
                    "file_type": "pdf" if file.filename.endswith('.pdf') else "csv"
                }
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            DOCUMENT_PROCESSING_TIME.observe(time.time() - start_time)
