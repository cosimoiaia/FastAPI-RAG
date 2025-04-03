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

from app.core.config import settings
from app.models.query import QueryResponse, Source

# Define state types
class AgentState(TypedDict):
    messages: Annotated[Sequence[Union[HumanMessage, AIMessage]], operator.add]
    context: str
    query: str

class RAGPipeline:
    def __init__(self):
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
        
        # Initialize the RAG workflow
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> Graph:
        # Define the nodes
        def retrieve_context(state: AgentState) -> AgentState:
            query = state["query"]
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            context = "\n".join(results["documents"][0])
            state["context"] = context
            return state

        def generate_response(state: AgentState) -> AgentState:
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
            return state

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
        
        return QueryResponse(
            answer=response,
            sources=sources,
            confidence=1.0 - sum(results["distances"][0]) / len(results["distances"][0])
        )

    async def ingest_document(self, file) -> Dict[str, Any]:
        # Create temporary file to store uploaded content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        try:
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
            
            return {
                "num_documents": len(documents),
                "file_type": "pdf" if file.filename.endswith('.pdf') else "csv"
            }
            
        finally:
            # Clean up temporary file
            Path(temp_path).unlink()
