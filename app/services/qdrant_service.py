from qdrant_client import AsyncQdrantClient, models
from fastembed import SparseTextEmbedding
from app.services.geminiservice import GeminiService
from app.config.settings import settings
import logging
import asyncio
from typing import List, Dict, Any
import uuid

logger = logging.getLogger("examready")

class QdrantService:
    """Async Hybrid Search Service for Qdrant Cloud"""
    
    def __init__(self):
        """Initialize sync components only"""
        self.client = None  # ✅ Async client initialized later
        
        # Sync components (safe to init here)
        self.sparse_model = SparseTextEmbedding(
            model_name="Qdrant/bm25",
            providers=["CPUExecutionProvider"]
        )
        self.gemini_service = GeminiService()
        
        # Collection names
        self.questions_collection = settings.QDRANT_COLLECTION_QUESTIONS
        self.textbook_collection = settings.QDRANT_COLLECTION_NAME
    
    async def initialize(self):
        """Async initialization - call from startup event"""
        if self.client is None:
            self.client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=settings.QDRANT_TIMEOUT_SECONDS
            )
            await self._ensure_question_collection()
            logger.info("✅ Qdrant Async Service initialized")
    
    async def close(self):
        """Cleanup - call from shutdown event"""
        if self.client:
            await self.client.close()
            logger.info("🔌 Qdrant connection closed")
    
    async def _ensure_question_collection(self):
        """Ensure Questions collection exists"""
        try:
            exists = await self.client.collection_exists(self.questions_collection)
            if not exists:
                logger.info(f"Creating collection: {self.questions_collection}")
                await self.client.create_collection(
                    collection_name=self.questions_collection,
                    vectors_config={
                        "text-dense": models.VectorParams(size=768, distance=models.Distance.COSINE)
                    },
                    sparse_vectors_config={
                        "text-sparse": models.SparseVectorParams(
                            index=models.SparseIndexParams(on_disk=False)
                        )
                    }
                )
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
    
    async def create_collection_if_not_exists(self):
        """Creates the Textbook collection (used by migration script)"""
        if not self.client: await self.initialize() # Ensure client exists
        try:
            if not await self.client.collection_exists(self.textbook_collection):
                print(f"⚙️  Creating collection: {self.textbook_collection}")
                await self.client.create_collection(
                    collection_name=self.textbook_collection,
                    vectors_config={
                        "text-dense": models.VectorParams(
                            size=768,
                            distance=models.Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        "text-sparse": models.SparseVectorParams(
                            index=models.SparseIndexParams(on_disk=False)
                        )
                    }
                )
                print("✅ Collection created successfully.")
            else:
                print(f"✅ Collection {self.textbook_collection} already exists.")
        except Exception as e:
             logger.error(f"Error checking textbook collection: {e}")

    async def search_questions(self, query: str, filters: Dict, limit: int = 10) -> Dict:
        """Search exam questions"""
        return await self.hybrid_search(
            query=query,
            filters=filters,
            top_k=limit,
            collection_name=self.questions_collection
        )
    
    async def search_ncert_context(self, query: str, limit: int = 5) -> List[Dict]:
        """Search textbook context for LLM fallback"""
        res = await self.hybrid_search(
            query=query,
            filters={},
            top_k=limit,
            collection_name=self.textbook_collection
        )
        return res.get('chunks', [])
    
    async def increment_usage_count(self, question_id: str) -> bool:
        """Increment question usage count"""
        try:
            points = await self.client.retrieve(
                collection_name=self.questions_collection,
                ids=[question_id]
            )
            if not points:
                return False
            
            current = points[0].payload.get("usageCount", 0)
            await self.client.set_payload(
                collection_name=self.questions_collection,
                payload={"usageCount": current + 1},
                points=[question_id]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update usage: {e}")
            return False
    
    async def hybrid_search(
        self, 
        query: str, 
        filters: Dict[str, Any], 
        top_k: int = 8, 
        collection_name: str = None
    ) -> Dict:
        """
        Async Hybrid Search (Dense + Sparse)
        ✅ Runs blocking operations in thread pool
        """
        target_collection = collection_name or self.textbook_collection
        
        # ✅ A. Dense Embedding (I/O bound - run in thread)
        # Note: GeminiService.embed is synchronous, so we run it in a thread
        dense_vec = await asyncio.to_thread(
            self.gemini_service.embed, 
            query
        )
        if not dense_vec:
            return {"context": "", "chunks": [], "total_results": 0}
        
        # ✅ B. Sparse Embedding (CPU bound - run in thread)
        # FastEmbed is CPU intensive, good to offload
        # FIXED: Added error handling for sparse embedding failure
        sparse_vec = None
        try:
            sparse_vec = await asyncio.to_thread(
                lambda: list(self.sparse_model.embed([query]))[0]
            )
        except Exception as e:
            logger.error(f"Sparse embedding failed: {e}")
            # Continue with dense-only search
        
        # C. Build Filters
        must_conditions = []
        if filters:
            for k, v in filters.items():
                # Range queries
                if isinstance(v, dict) and any(op in v for op in ["$gte", "$lte", "$gt", "$lt"]):
                    range_config = {}
                    if "$gte" in v: range_config["gte"] = v["$gte"]
                    if "$lte" in v: range_config["lte"] = v["$lte"]
                    if "$gt" in v: range_config["gt"] = v["$gt"]
                    if "$lt" in v: range_config["lt"] = v["$lt"]
                    must_conditions.append(
                        models.FieldCondition(key=k, range=models.Range(**range_config))
                    )
                # List matching (IN clause)
                elif isinstance(v, list):
                    must_conditions.append(
                        models.FieldCondition(key=k, match=models.MatchAny(any=v))
                    )
                # Exact match
                else:
                    must_conditions.append(
                        models.FieldCondition(key=k, match=models.MatchValue(value=v))
                    )
        
        q_filter = models.Filter(must=must_conditions) if must_conditions else None
        
        # ✅ D. Build Prefetch (conditional sparse)
        prefetch = [
            models.Prefetch(
                query=dense_vec,
                using="text-dense",
                filter=q_filter,
                limit=settings.SEMANTIC_TOP_K
            )
        ]
        
        # Only add sparse prefetch if sparse embedding succeeded
        if sparse_vec is not None:
            prefetch.append(
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist()
                    ),
                    using="text-sparse",
                    filter=q_filter,
                    limit=settings.BM25_TOP_K
                )
            )
        
        # ✅ E. Execute Async Query
        results = await self.client.query_points(
            collection_name=target_collection,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=top_k,
            with_payload=True
        )
        
        # E. Format Results
        chunks = []
        for point in results.points:
            chunks.append({
                "id": str(point.id),
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                "score": point.score,
                "rerank_score": point.score
            })
        
        # Build context string
        context_parts = []
        for c in chunks[:5]:  # Top 5 for context
            source = f"Source: {c['metadata'].get('textbook', 'Book')} (Page {c['metadata'].get('page', 0)})"
            context_parts.append(f"{source}\n{c['text']}")
        
        return {
            "context": "\n---\n".join(context_parts),
            "chunks": chunks,
            "total_results": len(chunks)
        }
    
    async def upsert_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]], 
        collection_name: str = None
    ):
        """Async upsert for questions/textbooks"""
        if not self.client: await self.initialize() # Ensure client
        
        target_collection = collection_name or self.textbook_collection
        
        # Get sparse vectors
        texts = [c["text"] for c in chunks]
        sparse_vectors = await asyncio.to_thread(
            lambda: list(self.sparse_model.embed(texts))
        )
        
        # Build points
        points = []
        for i, chunk in enumerate(chunks):
            try:
                point_id = str(uuid.UUID(str(chunk["id"])))
            except:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.get("text", "")[:50] + str(i)))
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "text-dense": embeddings[i],
                        "text-sparse": models.SparseVector(
                            indices=sparse_vectors[i].indices.tolist(),
                            values=sparse_vectors[i].values.tolist()
                        )
                    },
                    payload={**chunk.get("metadata", {}), "text": chunk["text"]}
                )
            )
        
        # ✅ Async upsert
        await self.client.upsert(
            collection_name=target_collection,
            points=points
        )
        logger.info(f"✅ Upserted {len(points)} points to {target_collection}")

# Singleton (initialized in startup event)
qdrant_service = QdrantService()