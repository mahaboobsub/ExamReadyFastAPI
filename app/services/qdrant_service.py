from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding
from app.services.geminiservice import GeminiService
from app.config.settings import settings
import logging
from typing import List, Dict, Any
import uuid

logger = logging.getLogger("examready")

class QdrantService:
    """Unified service for hybrid search (Dense + Sparse) on Qdrant Cloud"""
    
    def __init__(self):
        # 1. Connect to Qdrant Cloud
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=60 # Increased timeout for uploads
        )
        
        # 2. Load Sparse Model (Runs locally on CPU, replaces BM25)
        self.sparse_model = SparseTextEmbedding(
            model_name="Qdrant/bm25",
            providers=["CPUExecutionProvider"]
        )
        
        # 3. Initialize Gemini Service (For Rotation-Aware Embeddings)
        self.gemini_service = GeminiService()
        
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        logger.info(f"✅ Qdrant Service initialized")

    def create_collection_if_not_exists(self):
        """Creates the collection with Hybrid (Dense+Sparse) config if missing"""
        if not self.client.collection_exists(self.collection_name):
            print(f"⚙️  Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "text-dense": models.VectorParams(
                        size=768,  # Gemini dimensions
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "text-sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                }
            )
            print("✅ Collection created successfully.")
        else:
            print(f"✅ Collection {self.collection_name} already exists.")

    def upsert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Generates Sparse Vectors and Uploads Hybrid Points to Qdrant
        Used by migration scripts.
        """
        texts = [c['text'] for c in chunks]
        
        # 1. Generate Sparse Vectors (Local CPU)
        sparse_vectors = list(self.sparse_model.embed(texts))
        
        points = []
        for i, chunk in enumerate(chunks):
            # Ensure ID is a valid UUID
            try:
                point_id = str(uuid.UUID(str(chunk['id'])))
            except:
                # Generate deterministic UUID based on content if missing/invalid
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.get('text', str(i))[:50]))

            points.append(models.PointStruct(
                id=point_id,
                vector={
                    "text-dense": embeddings[i],
                    "text-sparse": models.SparseVector(
                        indices=sparse_vectors[i].indices.tolist(),
                        values=sparse_vectors[i].values.tolist()
                    )
                },
                payload=chunk['metadata'] | {"text": chunk['text']}
            ))

        # 2. Upload Batch
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"   ☁️  Upserted {len(points)} points to Qdrant")

    def hybrid_search(self, query: str, filters: Dict[str, Any], top_k: int = 8):
        """
        Performs Hybrid Search with Confidence Threshold filtering.
        1. Dense Vector (Semantic) via GeminiService (with Rotation!)
        2. Sparse Vector (Keyword) via FastEmbed
        3. RRF Fusion (Built-in)
        """
        
        # A. Generate Dense Embedding (Using GeminiService for Rotation)
        dense_vec = self.gemini_service.embed(query)
        
        # Guard clause if embedding failed
        if not dense_vec:
             return {
                "context": "",
                "chunks": [],
                "total_results": 0
            }

        # B. Generate Sparse Embedding (BM25 replacement)
        sparse_vec = list(self.sparse_model.embed([query]))[0]

        # C. Build Filters
        must_conditions = []
        if filters:
            if filters.get('board'):
                must_conditions.append(models.FieldCondition(
                    key="board", match=models.MatchValue(value=filters['board'])
                ))
            if filters.get('class'):
                val = int(filters['class']) if str(filters['class']).isdigit() else filters['class']
                must_conditions.append(models.FieldCondition(
                    key="class", match=models.MatchValue(value=val)
                ))
            if filters.get('subject'):
                must_conditions.append(models.FieldCondition(
                    key="subject", match=models.MatchValue(value=filters['subject'])
                ))
            if filters.get('chapter'):
                # Handle list of chapters or single chapter
                chapters = filters['chapter']
                if isinstance(chapters, list):
                    must_conditions.append(models.FieldCondition(
                        key="chapter", match=models.MatchAny(any=chapters)
                    ))
                else:
                    must_conditions.append(models.FieldCondition(
                        key="chapter", match=models.MatchValue(value=chapters)
                    ))

        qdrant_filter = models.Filter(must=must_conditions) if must_conditions else None

        # D. Execute Hybrid Query
        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vec,
                    using="text-dense",
                    filter=qdrant_filter,
                    limit=settings.SEMANTIC_TOP_K
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist()
                    ),
                    using="text-sparse",
                    filter=qdrant_filter,
                    limit=settings.BM25_TOP_K
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=top_k,
            with_payload=True
        )

        # E. Format Results
        chunks = []
        for point in results.points:
            chunks.append({
                "id": point.id,
                "text": point.payload.get("text", ""),
                "metadata": {k:v for k,v in point.payload.items() if k != "text"},
                "score": point.score, 
                "rerank_score": point.score 
            })

        # Assemble Context
        context_parts = []
        for c in chunks:
            source = f"[Source: {c['metadata'].get('textbook','Book')} Page {c['metadata'].get('page',0)}]"
            context_parts.append(f"{source}\n{c['text']}")
        
        context_str = "\n\n---\n\n".join(context_parts)

        return {
            "context": context_str,
            "chunks": chunks,
            "total_results": len(chunks)
        }

# Singleton instance
qdrant_service = QdrantService()