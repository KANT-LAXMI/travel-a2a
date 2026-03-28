import logging
import os
import pickle
import numpy as np
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Local vector database using FAISS and SentenceTransformers
    - Creates embeddings using all-MiniLM-L6-v2 (free, offline)
    - Stores vectors in FAISS index (fast similarity search)
    - Saves to disk for persistence
    """

    def __init__(self, db_path: str = "backend/data/vector_db"):
        self.db_path = db_path
        self.index = None
        self.documents = []
        self.embeddings_model = None
        self.dimension = 384  # MiniLM-L6-v2 embedding size

        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)

        # Paths for saving
        self.index_path = os.path.join(db_path, "faiss_index.bin")
        self.docs_path = os.path.join(db_path, "documents.pkl")

    def _load_embedding_model(self):
        """Load SentenceTransformer model (free, runs locally)"""
        if self.embeddings_model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. "
                "Install it with: pip install sentence-transformers --break-system-packages"
            )

        logger.info("📥 Loading embedding model (all-MiniLM-L6-v2)...")
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded")

    def _create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts"""
        if self.embeddings_model is None:
            self._load_embedding_model()

        logger.info(f"🔄 Creating embeddings for {len(texts)} texts...")
        embeddings = self.embeddings_model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32
        )
        logger.info("✅ Embeddings created")
        return embeddings

    def add_documents(self, documents: List[Dict]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
        """
        if not documents:
            logger.warning("⚠️ No documents to add")
            return

        # Extract texts
        texts = [doc['text'] for doc in documents]

        # Create embeddings
        embeddings = self._create_embeddings(texts)

        # Create or update FAISS index
        if self.index is None:
            try:
                import faiss
            except ImportError:
                raise ImportError(
                    "faiss-cpu is required. "
                    "Install it with: pip install faiss-cpu --break-system-packages"
                )

            # Create new index
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"✅ Created new FAISS index (dimension={self.dimension})")

        # Add vectors to index
        self.index.add(embeddings.astype('float32'))

        # Store documents
        self.documents.extend(documents)

        logger.info(f"✅ Added {len(documents)} documents to vector store")
        logger.info(f"📊 Total documents: {len(self.documents)}")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dicts with 'text', 'metadata', and 'score' keys
        """
        logger.info("5️⃣ FAISS SEARCH EXECUTION (REAL VECTOR MATH)")
        if self.index is None or len(self.documents) == 0:
            logger.warning("⚠️ Vector store is empty")
            return []

        # Create query embedding
        logger.info("(a) Query → Embedding")

        query_embedding = self._create_embeddings([query])

        logger.info("-----------------------------------Q U E S T I O N - E M B E D D I N G S---------------------------------------------")
        logger.info(f"🔍Query Embeddings: {query_embedding}")
        logger.info("-----------------------------------Q U E S T I O N - E M B E D D I N G S---------------------------------------------")


        # Search in FAISS
        logger.info("(b) FAISS similarity search")
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            min(top_k, len(self.documents))
        )
        logger.info("query embedding + FAISS index ==> nearest vectors")
        logger.info("-----------------------------------D I S T A N C E S    &   I N D I C E S---------------------------------------------")
        logger.info(f"Distances: {distances}")
        logger.info("--------------------------------------------------------------------------------")
        logger.info(f"Indices: {indices}")
        logger.info("-----------------------------------D I S T A N C E S    &   I N D I C E S---------------------------------------------")

        # Build results
        # Here the self.documents is       
        # self.docs_path = os.path.join(db_path, "documents.pkl")
        # -------- Save documents --------
        # with open(self.docs_path, 'wb') as f:
        #     pickle.dump(self.documents, f)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['score'] = float(distances[0][i])
                results.append(doc)

        logger.info("-----------------------------------R E S U L T---------------------------------------------")
        logger.info(f"🔍 RESULTS: {results}")
        logger.info("-----------------------------------R E S U L T---------------------------------------------")

        logger.info(f"🔍 Found {len(results)} relevant documents")
        return results

    def save(self):
        """Save index and documents to disk"""
        try:
            import faiss
        except ImportError:
            logger.error("FAISS not installed, cannot save")
            return

        if self.index is None:
            logger.warning("⚠️ No index to save")
            return

        # Save FAISS index
        faiss.write_index(self.index, self.index_path)

        # Save documents
        with open(self.docs_path, 'wb') as f:
            pickle.dump(self.documents, f)

        logger.info(f"💾 Saved vector store to {self.db_path}")

    def load(self) -> bool:
        """
        Load index and documents from disk
        
        Returns:
            True if successfully loaded, False otherwise
        """
        if not os.path.exists(self.index_path) or not os.path.exists(self.docs_path):
            logger.info("ℹ️ No existing vector store found")
            return False

        try:
            import faiss

            # Load embedding model first
            self._load_embedding_model()

            # Load FAISS index
            self.index = faiss.read_index(self.index_path)

            # Load documents
            with open(self.docs_path, 'rb') as f:
                self.documents = pickle.load(f)

            logger.info(f"✅ Loaded vector store with {len(self.documents)} documents")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {e}")
            return False

    def get_count(self) -> int:
        """Get number of documents in the store"""
        return len(self.documents)

    def clear(self):
        """Clear all documents and index"""
        self.index = None
        self.documents = []
        logger.info("🗑️ Cleared vector store")

    def delete_store(self):
        """Delete saved index and documents from disk"""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.docs_path):
            os.remove(self.docs_path)
        logger.info("🗑️ Deleted vector store from disk")