from rank_bm25 import BM25Okapi
import pickle
import os
from typing import List, Dict, Any
from app.config.settings import settings

class BM25Service:
    """BM25 keyword search engine"""

    def __init__(self):
        self.index = None
        self.documents = [] # Stores metadata reference
        self.corpus = []    # Stores text tokens

    def build_index(self, chunks: List[Dict[str, Any]]):
        """Build BM25 index from chunks"""
        print("   Building BM25 index...")
        
        self.documents = chunks
        # Simple tokenization: lowercase and split by whitespace
        self.corpus = [chunk['text'].lower().split() for chunk in chunks]
        
        self.index = BM25Okapi(self.corpus)
        print(f"   BM25 built with {len(chunks)} documents.")

    def save_index(self):
        """Save index to disk"""
        os.makedirs(os.path.dirname(settings.BM25_INDEX_PATH), exist_ok=True)
        
        data = {
            "documents": self.documents,
            "corpus": self.corpus,
            "index": self.index
        }
        
        with open(settings.BM25_INDEX_PATH, "wb") as f:
            pickle.dump(data, f)
        print(f"   BM25 index saved to {settings.BM25_INDEX_PATH}")

    def load_index(self):
        """Load index from disk"""
        if not os.path.exists(settings.BM25_INDEX_PATH):
            print("   ⚠️ No BM25 index found.")
            return False
            
        with open(settings.BM25_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.corpus = data["corpus"]
            self.index = data["index"]
        print("   ✅ BM25 index loaded.")
        return True

    def search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Keyword search with metadata filtering
        """
        if not self.index:
            print("   ⚠️ BM25 index not loaded.")
            return []

        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.index.get_scores(tokenized_query)
        
        # Get top-k indices
        # Sort indices by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            score = scores[idx]
            
            # Stop if score is 0 (no match)
            if score <= 0:
                break

            # Filter by metadata
            if filters:
                meta = doc['metadata']
                # Check all filters
                is_match = True
                for key, value in filters.items():
                    if meta.get(key) != value:
                        is_match = False
                        break
                if not is_match:
                    continue

            results.append({
                'document': doc,
                'score': float(score)
            })
            
            if len(results) >= top_k:
                break
                
        return results