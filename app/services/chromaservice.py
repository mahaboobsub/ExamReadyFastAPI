import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config.settings import settings
from typing import List, Dict, Any
import os

class ChromaService:
    """Chroma Vector Database operations"""

    def __init__(self):
        # Ensure directory exists
        os.makedirs(settings.CHROMA_PATH, exist_ok=True)
        
        # Create persistent client
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

    def create_collection(self, name: str = "ncert_textbooks"):
        """Create or get collection"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"description": "NCERT textbooks for ExamReady"}
            )

    def add_documents(self, collection, chunks: List[Dict[str, Any]]):
        """
        Add chunks to Chroma collection
        """
        if not chunks:
            return

        ids = [c['id'] for c in chunks]
        documents = [c['text'] for c in chunks]
        embeddings = [c['embedding'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]

        # Add in batches of 500
        batch_size = 500
        for i in range(0, len(chunks), batch_size):
            end = i + batch_size
            collection.add(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end]
            )
            print(f"   Stored batch {i}-{min(end, len(chunks))} in Chroma")

    def search(self, collection, query_embedding: List[float], filters: Dict[str, Any] = None, top_k: int = 20) -> Dict[str, Any]:
        """
        Semantic search with strict metadata filtering
        """
        # Build where clause with explicit $and for multiple conditions
        where_conditions = []
        
        if filters:
            if filters.get('board'): 
                where_conditions.append({"board": filters['board']})
            if filters.get('class'): 
                where_conditions.append({"class": filters['class']})
            if filters.get('subject'): 
                where_conditions.append({"subject": filters['subject']})
            if filters.get('chapter'): 
                where_conditions.append({"chapter": filters['chapter']})
            if filters.get('bloomsLevel'): 
                where_conditions.append({"bloomsLevel": filters['bloomsLevel']})

        # Construct final where clause
        where = None
        if len(where_conditions) > 1:
            where = {"$and": where_conditions}
        elif len(where_conditions) == 1:
            where = where_conditions[0]

        # Execute query
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        return results