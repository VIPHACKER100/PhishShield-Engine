"""
Vector Similarity Search Module
Uses ChromaDB and Sentence-Transformers to find semantically similar known phishing emails.
"""
import os
import chromadb
from sentence_transformers import SentenceTransformer
import logging

class VectorSearchDB:
    def __init__(self, db_path: str = "./data/chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self.client = None
        self.collection = None
        self.encoder = None

    def initialize(self):
        """Initialize ChromaDB client and SentenceTransformer model."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name="phishing_emails")
        self.encoder = SentenceTransformer(self.model_name)
        logging.info("VectorSearchDB initialized with model %s", self.model_name)

    def add_email(self, doc_id: str, text: str, label: str, metadata: dict = None):
        """Add a known email (spam or ham) to the vector database."""
        if not self.collection:
            self.initialize()
            
        embedding = self.encoder.encode(text).tolist()
        
        meta = {"label": label}
        if metadata:
            meta.update(metadata)
            
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta]
        )

    def search_similar(self, text: str, n_results: int = 3) -> list:
        """Search for the most semantically similar emails."""
        if not self.collection:
            self.initialize()
            
        if self.collection.count() == 0:
            return []
            
        embedding = self.encoder.encode(text).tolist()
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        
        matches = []
        if results and "documents" in results and len(results["documents"]) > 0:
            for idx in range(len(results["documents"][0])):
                matches.append({
                    "id": results["ids"][0][idx],
                    "document": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx]
                })
        return matches
