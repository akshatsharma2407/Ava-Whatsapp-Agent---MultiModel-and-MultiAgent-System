import os
from datetime import datetime
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from ai_companion.settings import settings


class Memory:
    """Represents a memory entry in the vector store"""

    def __init__(self, text: str, metadata: dict, score: Optional[float] = None):
        self.text = text
        self.metadata = metadata
        self.score = score
    
    def get_id(self):
        return self.metadata.get('id')
    
    def get_timestamp(self):
        ts = self.metadata.get('timestamp')
        return datetime.fromisoformat(ts) if ts else None

class VectorStore:
    """A class to handle vector storeage operations using Qdrant"""

    REQUIRED_ENV_VARS = ['QDRANT_URL', 'QDRANT_API_KEY']
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = 'long_term_memory'
    SIMILARITY_THRESHOLD = 0.9

    _instance: Optional["VectorStore"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._validate_env_vars()
            self.model = SentenceTransformer(self.EMBEDDING_MODEL)
            self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            self._initialized = True
    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def _collection_exists(self):
        """Check if the memory collection exists."""
        collections = self.client.get_collections().collections
        return any(col.name == self.COLLECTION_NAME for col in collections)
    
    def _create_collection(self):
        """Create a new collection for storing memories"""
        sample_embedding = self.model.encode('sample text')
        self.client.create_collection(
            collection_name = self.COLLECTION_NAME,
            vectors_config = VectorParams(
                size=len(sample_embedding),
                distance=Distance.COSINE
            )
        )
    
    def find_similar_memory(self, text: str):
        """Find if a similar memory already exists.
        
        Args:
            text: the text to search for
        
        Returns:
            Optional Memory if a similar one is found
        """

        results = self.search_memories(text, k=1)

        if results and results[0].score > self.SIMILARITY_THRESHOLD:
            return results[0]
        return None
    
    def store_memory(self, text: str, metadata: dict):
        """store a new memory or update if similar exists in vector store
        
        Args:
            text: The text context of the memory
            metadata: Additional information about the memory (timestamp, type etc)
        """

        if not self._collection_exists():
            self._create_collection()
        
        similar_memory = self.find_similar_memory(text)

        if similar_memory and similar_memory.get_id():
            metadata['id'] = similar_memory.get_id()
        
        embedding = self.model.encode(text)
        point = PointStruct(
            id=metadata.get('id', hash(text)),
            vector=embedding.tolist(),
            payload={
                "text": text,
                **metadata
            }
        )

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point]
        )
    
    def search_memories(self, query: str, k: int = 5):
        """Search for similar memories in vector store"""
        if not self._collection_exists():
            return []
        
        query_embedding = self.model.encode(query)

        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=k
        )

        return [
            Memory(
                text=hit.payload['text'],
                metadata={key: val for key, val in hit.payload.items() if key != "text"},
                score=hit.score
            )
            for hit in results.points  
        ]

def get_vector_store():
    """Get or Create the VectorStore singleton instance"""
    return VectorStore()