from sentence_transformers import CrossEncoder
from app.config.settings import settings
from typing import List, Dict

class RerankerService:
    """Uses Cross-Encoder to refine search results with high accuracy"""

    def __init__(self):
        # We use a lightweight model designed for speed/accuracy balance
        # This will download the model (~90MB) on the first run
        print("   ⚙️  Loading Reranker Model (One-time)...")
        # ms-marco-MiniLM-L-6-v2 is highly optimized for CPU inference
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Re-sort documents based on true relevance to the query.
        Args:
            query: The user's question
            documents: List of candidate chunks (from Chroma/BM25)
            top_k: How many to keep
        """
        if not documents:
            return []

        # Prepare pairs for the model: [ [query, doc1], [query, doc2], ... ]
        # We limit doc text to 512 chars to speed up inference on CPU
        pairs = [[query, doc['text'][:512]] for doc in documents]

        # Predict scores (higher is better)
        scores = self.model.predict(pairs)

        # Attach scores to documents
        for i, doc in enumerate(documents):
            doc['rerank_score'] = float(scores[i])

        # Sort descending by score (High score = Better match)
        reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

        return reranked_docs[:top_k]