import chromadb
from typing import List, Dict, Any, TypedDict, Annotated, Sequence, Union
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq, GroqEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
import operator
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import logging
import time
from prometheus_client import Histogram, Counter

from app.core.config import settings
from app.models.query import QueryResponse, Source

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
QUERY_PROCESSING_TIME = Histogram('rag_query_processing_seconds', 'Time spent processing queries')
DOCUMENT_PROCESSING_TIME = Histogram('rag_document_processing_seconds', 'Time spent processing documents')
QUERIES_TOTAL = Counter('rag_queries_total', 'Total number of queries processed')
DOCUMENTS_PROCESSED = Counter('rag_documents_processed', 'Total number of documents processed')
ERRORS_TOTAL = Counter('rag_errors_total', 'Total number of errors encountered')

# Define state types
class AgentState(TypedDict):
    messages: Annotated[Sequence[Union[HumanMessage, AIMessage]], operator.add]
    context: str
    query: str

class RAGPipeline:
    def __init__(self):
        logger.info("Initializing RAG Pipeline")
        self.embeddings = GroqEmbeddings(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        # Initialize vector store
        self.vector_store = chromadb.PersistentClient(path=settings.VECTORDB_PATH)
        self.collection = self.vector_store.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("RAG Pipeline initialized successfully")
        
        # Initialize the RAG workflow
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> Graph:
        # Define the nodes
        def retrieve_context(state: AgentState) -> AgentState:
            logger.info(f"Retrieving context for query: {state['query']}")
            start_time = time.time()
            try:
                query = state["query"]
                results = self.collection.query(
                    query_texts=[query],
                    n_results=3
                )
                context = "\n".join(results["documents"][0])
                state["context"] = context
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
                    ("system", "You are a helpful AI assistant. Use the following context to answer the question.\n\nContext: {context}"),
                    MessagesPlaceholder(variable_name="messages"),
                    ("human", "{query}")
                ])
                
                chain = prompt | self.llm | StrOutputParser()
                
                response = chain.invoke({
                    "context": state["context"],
                    "messages": state["messages"],
                    "query": state["query"]
                })
                
                state["messages"].append(AIMessage(content=response))
                logger.info("Response generated successfully")
                return state
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                ERRORS_TOTAL.inc()
                raise
            finally:
                QUERY_PROCESSING_TIME.observe(time.time() - start_time)

        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve", retrieve_context)
        workflow.add_node("generate", generate_response)
        
        # Add edges
        workflow.add_edge("retrieve", "generate")
        workflow.set_entry_point("retrieve")
        
        # Set the final node
        workflow.set_finish_point("generate")
        
        return workflow.compile()

    async def process_query(self, query: str) -> QueryResponse:
        logger.info(f"Processing query: {query}")
        start_time = time.time()
        try:
            QUERIES_TOTAL.inc()
            
            # Initialize state
            state = {
                "messages": [],
                "context": "",
                "query": query
            }
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            # Get the last message (the response)
            response = final_state["messages"][-1].content
            
            # Get the context documents
            results = self.collection.query(
                query_texts=[query],
                n_results=3,
                include_metadata=True
            )
            
            # Format sources
            sources = [
                Source(
                    document_id=str(metadata.get("source", "unknown")),
                    content=doc,
                    relevance_score=score
                )
                for doc, metadata, score in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
            
            logger.info(f"Query processed successfully in {time.time() - start_time:.2f}s")
            return QueryResponse(
                answer=response,
                sources=sources,
                confidence=1.0 - sum(results["distances"][0]) / len(results["distances"][0])
            )
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            QUERY_PROCESSING_TIME.observe(time.time() - start_time)

    async def ingest_document(self, file) -> Dict[str, Any]:
        logger.info(f"Ingesting document: {file.filename}")
        start_time = time.time()
        try:
            # Create temporary file to store uploaded content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name

            documents = []
            metadata = []
            
            if file.filename.endswith('.pdf'):
                # Process PDF
                import PyPDF2
                with open(temp_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for i, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        documents.append(text)
                        metadata.append({
                            "source": f"{file.filename}:page_{i+1}",
                            "page": i+1,
                            "type": "pdf"
                        })
            
            elif file.filename.endswith('.csv'):
                # Process CSV
                df = pd.read_csv(temp_path)
                for i, row in df.iterrows():
                    text = " ".join(str(v) for v in row.values)
                    documents.append(text)
                    metadata.append({
                        "source": f"{file.filename}:row_{i+1}",
                        "row": i+1,
                        "type": "csv"
                    })
            else:
                raise ValueError("Unsupported file type. Please upload PDF or CSV files.")

            # Get embeddings for documents
            embeddings = self.embeddings.embed_documents(documents)
            
            # Add to vector store
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=[f"doc_{i}" for i in range(len(documents))]
            )
            
            DOCUMENTS_PROCESSED.inc(len(documents))
            logger.info(f"Document ingested successfully: {len(documents)} chunks created")
            
            return {
                "num_documents": len(documents),
                "file_type": "pdf" if file.filename.endswith('.pdf') else "csv"
            }
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            ERRORS_TOTAL.inc()
            raise
        finally:
            DOCUMENT_PROCESSING_TIME.observe(time.time() - start_time)
            # Clean up temporary file
            Path(temp_path).unlink()
