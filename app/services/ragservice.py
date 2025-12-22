# from app.services.chromaservice import ChromaService
# from app.services.bm25service import BM25Service
# from app.services.geminiservice import GeminiService
# from app.services.rerankerservice import RerankerService
# from app.config.settings import settings
# from app.utils.cache import redis_pool
# from typing import List, Dict, Any
# import time
# import redis
# import json
# import hashlib
# import math # Required for Sigmoid normalization

# class HybridRAGService:
#     """
#     Orchestrates Semantic + Keyword Search + RRF Fusion + Reranking + Caching
#     """

#     def __init__(self):
#         self.chroma = ChromaService()
#         self.bm25 = BM25Service()
#         self.gemini = GeminiService()
#         self.reranker = RerankerService()
        
#         # ✅ USE POOL: Reuses connections instead of opening new ones per request
#         self.redis_client = redis.Redis(connection_pool=redis_pool)
        
#         # Load Indexes
#         self.collection = self.chroma.create_collection("ncert_textbooks")
#         self.bm25.load_index()

#     def _generate_cache_key(self, query: str, filters: Dict) -> str:
#         """Create a deterministic hash of query + filters"""
#         # Sort keys to ensure consistency: {"a":1, "b":2} == {"b":2, "a":1}
#         key_data = f"{query}:{json.dumps(filters, sort_keys=True)}"
#         return f"rag:{hashlib.md5(key_data.encode()).hexdigest()}"

#     def _hybrid_fusion(self, semantic_results: Dict[str, Any], keyword_results: List[Dict], k: int = 60) -> List[Dict]:
#         """
#         Reciprocal Rank Fusion (RRF)
#         Combines Semantic and Keyword results by rank, not just score.
#         Formula: RRF_score = sum(1 / (k + rank))
#         """
#         scores = {}  # doc_id -> RRF score
#         doc_map = {}  # doc_id -> document object
        
#         # 1. Process Semantic Results
#         # Chroma returns structure: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
#         if semantic_results['ids']:
#             ids = semantic_results['ids'][0]
#             documents = semantic_results['documents'][0]
#             metadatas = semantic_results['metadatas'][0]
            
#             for rank, doc_id in enumerate(ids):
#                 # RRF calculation (rank starts at 0, so use rank+1)
#                 scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))
                
#                 # Store chunk data
#                 doc_map[doc_id] = {
#                     "id": doc_id,
#                     "text": documents[rank],
#                     "metadata": metadatas[rank],
#                     "source": "semantic"
#                 }

#         # 2. Process Keyword (BM25) Results
#         # BM25 returns list of dicts: [{'document': {...}, 'score': float}, ...]
#         for rank, item in enumerate(keyword_results):
#             doc = item['document']
#             doc_id = doc['id']
            
#             # RRF calculation
#             scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))
            
#             # Store if not already seen (prefer semantic metadata if collision)
#             if doc_id not in doc_map:
#                 doc_map[doc_id] = doc
#                 doc_map[doc_id]['source'] = "keyword"
        
#         # 3. Sort by final RRF score (Descending)
#         sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
#         # 4. Return merged list
#         merged_docs = []
#         for doc_id in sorted_ids:
#             doc = doc_map[doc_id]
#             doc['rrf_score'] = scores[doc_id] # Add score for debugging/analysis
#             merged_docs.append(doc)
            
#         return merged_docs

#     def search(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
#         """
#         Full Retrieval Pipeline with Caching, Fusion & Reranking
#         Returns: { 'context': str, 'chunks': List[Dict], 'latency': float }
#         """
#         start_time = time.time()
        
#         # 1. Check Cache
#         cache_key = self._generate_cache_key(query, filters)
#         try:
#             cached = self.redis_client.get(cache_key)
#             if cached:
#                 print("   ✅ RAG Cache HIT")
#                 return json.loads(cached)
#         except Exception as e:
#             print(f"   ⚠️ Cache Read Error: {e}")

#         print(f"   ❌ RAG Cache MISS - Running Search for '{query[:30]}...'")
        
#         # A. Semantic Search
#         query_embedding = self.gemini.embed(query)
#         semantic_results = self.chroma.search(
#             self.collection, 
#             query_embedding, 
#             filters=filters, 
#             top_k=50
#         )
        
#         # B. Keyword Search
#         keyword_results = self.bm25.search(query, filters=filters, top_k=50)
        
#         # C. Fusion (RRF)
#         merged_docs = self._hybrid_fusion(semantic_results, keyword_results)

#         # D. Rerank (The "Quality Filter")
#         # Rerank top 40 merged results to find the absolute best 8-10
#         top_docs = self.reranker.rerank(query, merged_docs[:40], top_k=settings.RERANK_TOP_K)
        
#         # E. Score Normalization & Filtering
#         valid_docs = []
#         for doc in top_docs:
#             raw_score = doc['rerank_score']
            
#             # ✅ FIX: Sigmoid Normalization
#             # Converts raw logits (-inf to inf) to probability (0.0 to 1.0)
#             try:
#                 normalized_score = 1 / (1 + math.exp(-raw_score))
#             except OverflowError:
#                 normalized_score = 0.0 if raw_score < 0 else 1.0
                
#             doc['rerank_score'] = round(normalized_score, 4)
            
#             # Threshold: Keep if > 1% probability (Very permissive now that we have sigmoid)
#             # This filters out absolute noise while keeping remotely relevant content
#             if normalized_score > 0.01:
#                 valid_docs.append(doc)
        
#         if not valid_docs:
#             print("   ⚠️ No relevant documents found after reranking.")
#             # Return empty structure rather than crashing
#             return {"context": "", "chunks": [], "latency": 0.0}

#         # F. Context Assembly
#         context_parts = []
#         for doc in valid_docs:
#             clean_text = doc['text'].replace("\n", " ").strip()
#             # Traceability Tag
#             source_tag = f"[Source: {doc['metadata'].get('chapter', 'Unknown')}, Page {doc['metadata'].get('page', 'N/A')}]"
#             context_parts.append(f"{source_tag}\n{clean_text}")
            
#         context_str = "\n\n---\n\n".join(context_parts)
        
#         result = {
#             "context": context_str,
#             "chunks": valid_docs, # Includes metadata and normalized rerank_score
#             "latency": round(time.time() - start_time, 2)
#         }
        
#         # 3. Store in Cache (7 Days)
#         try:
#             self.redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(result))
#         except Exception as e:
#             print(f"   ⚠️ Cache Write Error: {e}")
            
#         return result




from app.services.chromaservice import ChromaService
from app.services.bm25service import BM25Service
from app.services.geminiservice import GeminiService
from app.services.rerankerservice import RerankerService
from app.config.settings import settings
from app.utils.cache import redis_pool
from typing import List, Dict, Any
import time
import redis
import json
import hashlib
import math

class HybridRAGService:
    """
    Orchestrates Semantic + Keyword Search + RRF Fusion + Reranking + Caching
    """

    def __init__(self):
        self.chroma = ChromaService()
        self.bm25 = BM25Service()
        self.gemini = GeminiService()
        self.reranker = RerankerService()
        
        # ✅ USE POOL: Reuses connections to prevent "Too many connections" errors
        self.redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Load Indexes
        self.collection = self.chroma.create_collection("ncert_textbooks")
        self.bm25.load_index()

    def _generate_cache_key(self, query: str, filters: Dict) -> str:
        """Create a deterministic hash of query + filters"""
        # Sort keys to ensure consistency: {"a":1, "b":2} == {"b":2, "a":1}
        key_data = f"{query}:{json.dumps(filters, sort_keys=True)}"
        return f"rag:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _hybrid_fusion(self, semantic_results: Dict[str, Any], keyword_results: List[Dict], k: int = 60) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF)
        Combines Semantic and Keyword results by rank, not just score.
        Formula: RRF_score = sum(1 / (k + rank))
        """
        scores = {}  # doc_id -> RRF score
        doc_map = {}  # doc_id -> document object
        
        # 1. Process Semantic Results
        # Chroma returns structure: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
        if semantic_results['ids']:
            ids = semantic_results['ids'][0]
            documents = semantic_results['documents'][0]
            metadatas = semantic_results['metadatas'][0]
            
            for rank, doc_id in enumerate(ids):
                # RRF calculation (rank starts at 0, so use rank+1)
                scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))
                
                # Store chunk data
                doc_map[doc_id] = {
                    "id": doc_id,
                    "text": documents[rank],
                    "metadata": metadatas[rank],
                    "source": "semantic"
                }

        # 2. Process Keyword (BM25) Results
        # BM25 returns list of dicts: [{'document': {...}, 'score': float}, ...]
        for rank, item in enumerate(keyword_results):
            doc = item['document']
            doc_id = doc['id']
            
            # RRF calculation
            scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))
            
            # Store if not already seen (prefer semantic metadata if collision)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
                doc_map[doc_id]['source'] = "keyword"
        
        # 3. Sort by final RRF score (Descending)
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # 4. Return merged list
        merged_docs = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id]
            doc['rrf_score'] = scores[doc_id] # Add score for debugging/analysis
            merged_docs.append(doc)
            
        return merged_docs

    def search(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Full Retrieval Pipeline with Caching, Fusion & Reranking
        Returns: { 'context': str, 'chunks': List[Dict], 'latency': float }
        """
        start_time = time.time()
        
        # 1. Check Cache
        cache_key = self._generate_cache_key(query, filters)
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                print("   ✅ RAG Cache HIT")
                return json.loads(cached)
        except Exception as e:
            print(f"   ⚠️ Cache Read Error: {e}")

        print(f"   ❌ RAG Cache MISS - Running Search for '{query[:30]}...'")
        
        # A. Semantic Search (Chroma) - Get top 50 candidates
        query_embedding = self.gemini.embed(query)
        semantic_results = self.chroma.search(
            self.collection, 
            query_embedding, 
            filters=filters, 
            top_k=50
        )
        
        # B. Keyword Search (BM25) - Get top 50 candidates
        keyword_results = self.bm25.search(query, filters=filters, top_k=50)
        
        # C. Fusion (RRF) - Merge & Rank
        merged_docs = self._hybrid_fusion(semantic_results, keyword_results)

        # D. Rerank (The "Quality Filter")
        # Rerank top 40 merged results to find the absolute best 8-10 (RERANK_TOP_K)
        top_docs = self.reranker.rerank(query, merged_docs[:40], top_k=settings.RERANK_TOP_K)
        
        # E. Score Normalization & Filtering
        valid_docs = []
        for doc in top_docs:
            raw_score = doc['rerank_score']
            
            # ✅ FIX: Sigmoid Normalization
            # Converts raw logits (-inf to inf) to probability (0.0 to 1.0)
            try:
                normalized_score = 1 / (1 + math.exp(-raw_score))
            except OverflowError:
                normalized_score = 0.0 if raw_score < 0 else 1.0
                
            doc['rerank_score'] = round(normalized_score, 4)
            
            # Threshold: Keep if > 1% probability (Very permissive now that we have sigmoid)
            if normalized_score > 0.01:
                valid_docs.append(doc)
        
        if not valid_docs:
            print("   ⚠️ No relevant documents found after reranking.")
            # Return empty structure rather than crashing
            return {"context": "", "chunks": [], "latency": 0.0}

        # F. Context Assembly
        context_parts = []
        for doc in valid_docs:
            clean_text = doc['text'].replace("\n", " ").strip()
            # Traceability Tag
            source_tag = f"[Source: {doc['metadata'].get('chapter', 'Unknown')}, Page {doc['metadata'].get('page', 'N/A')}]"
            context_parts.append(f"{source_tag}\n{clean_text}")
            
        context_str = "\n\n---\n\n".join(context_parts)
        
        result = {
            "context": context_str,
            "chunks": valid_docs, # Includes metadata and normalized rerank_score
            "latency": round(time.time() - start_time, 2)
        }
        
        # 3. Store in Cache (7 Days)
        try:
            self.redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(result))
        except Exception as e:
            print(f"   ⚠️ Cache Write Error: {e}")
            
        return result