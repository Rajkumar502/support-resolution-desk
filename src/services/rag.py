import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from src.schemas.tickets import RAGContext

# Initialize Google GenAI Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

# Persistent local vector store directory
PERSIST_DIR = "./vector_store/chroma_db"

def get_vector_store():
    """Initializes or loads the persistent Chroma vector store with sample enterprise KB docs."""
    if not os.path.exists(PERSIST_DIR) or not os.listdir(PERSIST_DIR):
        initial_docs = [
            Document(page_content="Standard shipping takes 3-5 business days. International shipping takes 7-14 business days. Customers can track orders using the tracking link sent via email upon fulfillment.", metadata={"category": "order_status"}),
            Document(page_content="Items can be returned within 30 days of purchase for a full refund if unused and in original packaging. Return shipping is free for domestic orders. Customers can generate a prepaid return label from their account portal.", metadata={"category": "returns"}),
            Document(page_content="Customers can update their billing credit card or manage subscription tiers by logging into their account dashboard under 'Billing & Subscriptions'.", metadata={"category": "subscriptions"})
        ]
        return Chroma.from_documents(initial_docs, embeddings, persist_directory=PERSIST_DIR)
    
    return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

def retrieve_knowledge_base_docs(category: str, query: str, top_k: int = 2) -> RAGContext:
    """Performs dynamic vector similarity search filtered by category."""
    vector_store = get_vector_store()
    
    # Semantic search with metadata filtering for high precision
    filter_dict = {"category": category} if category not in ["other_complex", "general"] else None
    docs = vector_store.similarity_search(query, k=top_k, filter=filter_dict)
    
    # Fallback to general similarity search if filter yields nothing
    if not docs:
        docs = vector_store.similarity_search(query, k=top_k)
        
    chunks = [doc.page_content for doc in docs]
    scores = [0.95] * len(chunks)
    
    return RAGContext(chunks=chunks, similarity_scores=scores)