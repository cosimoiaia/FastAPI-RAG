import os
from typing import List, Dict, Any, Union
from fastapi import UploadFile
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from chromadb import PersistentClient
from langgraph.graph import Graph, END
import pandas as pd
import pypdf
from prometheus_client import Histogram, Counter
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import shutil
import logging
import time
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
QUERY_PROCESSING_TIME = Histogram('rag_query_processing_seconds', 'Time spent processing queries')
DOCUMENT_PROCESSING_TIME = Histogram('rag_document_processing_seconds', 'Time spent processing documents')
QUERIES_TOTAL = Counter('rag_queries_total', 'Total number of queries processed')
ERRORS_TOTAL = Counter('rag_errors_total', 'Total number of errors encountered')

class AgentState(BaseModel):
    messages: List[Union[HumanMessage, AIMessage]]
    context: str = ""
    query: str = ""

class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        # Initialize language model
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize vector store
        os.makedirs(settings.VECTORDB_PATH, exist_ok=True)
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
                query_embedding = self.embeddings.embed_query(state.query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3
                )
                context = "\n".join(results["documents"][0]) if results["documents"] and results["documents"][0] else ""
                state.context = context
                logger.info(f"Retrieved {len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0} relevant documents")
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
                query=query
            )
            
            # Get query embedding and retrieve documents
            query_embedding = self.embeddings.embed_query(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            # Set context in state
            state.context = "\n".join(results["documents"][0]) if results["documents"] and results["documents"][0] else ""
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            # Get the last message (the response)
            response = final_state.messages[-1].content
            
            # Format sources
            sources = [
                {
                    "document_id": str(metadata.get("source", "unknown")),
                    "content": doc,
                    "relevance_score": score
                }
                for doc, metadata, score in zip(
                    results["documents"][0] if results["documents"] and results["documents"][0] else [],
                    results["metadatas"][0] if results["metadatas"] and results["metadatas"][0] else [],
                    results["distances"][0] if results["distances"] and results["distances"][0] else []
                )
            ]
            
            logger.info(f"Query processed successfully in {time.time() - start_time:.2f}s")
            return {
                "answer": response,
                "sources": sources,
                "confidence": 1.0 - sum(results["distances"][0]) / len(results["distances"][0]) if results["distances"] and results["distances"][0] else 0.0
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            QUERY_PROCESSING_TIME.observe(time.time() - start_time)

    async def ingest_document(self, file: UploadFile) -> Dict[str, Any]:
        """
        Ingest a document into the RAG pipeline.
        """
        start_time = time.time()
        logger.info(f"Ingesting document: {file.filename}")

        try:
            # Create data directories if they don't exist
            Path(settings.RAW_DATA_PATH).mkdir(parents=True, exist_ok=True)
            Path(settings.PROCESSED_DATA_PATH).mkdir(parents=True, exist_ok=True)

            # Save file temporarily
            temp_path = os.path.join(settings.RAW_DATA_PATH, file.filename)
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Process based on file type
            file_extension = os.path.splitext(file.filename)[1].lower()
            documents = []

            if file_extension == '.csv':
                df = pd.read_csv(temp_path)
                for _, row in df.iterrows():
                    documents.append(row.to_string())
            elif file_extension == '.pdf':
                with open(temp_path, "rb") as f:
                    pdf = pypdf.PdfReader(f)
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text.strip():
                            documents.append(text)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

            # Generate embeddings and store in vector database
            embeddings = self.embeddings.embed_documents(documents)
            for i, (doc, emb) in enumerate(zip(documents, embeddings)):
                self.collection.add(
                    embeddings=[emb],
                    documents=[doc],
                    ids=[f"doc_{i}"],
                    metadatas=[{"source": file.filename}]
                )

            elapsed_time = time.time() - start_time
            logger.info(f"Successfully ingested {len(documents)} documents from {file.filename}")
            DOCUMENT_PROCESSING_TIME.observe(elapsed_time)

            return {
                "message": f"Successfully ingested {len(documents)} documents",
                "details": {
                    "file_type": file_extension[1:],  # Remove the leading dot
                    "num_documents": len(documents),
                    "processing_time": f"{elapsed_time:.2f}s"
                }
            }

        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            DOCUMENT_PROCESSING_TIME.observe(time.time() - start_time)
