import os
import json
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Tuple

STRUCTURED_DIR = "data/structured"
CHROMA_DIR = "chroma"

### Step 1: Load the structured incidents

def load_incidents():
    """Load every structured postmortem, skipping pages that weren't real postmortems"""
    incidents = []
    for file in sorted(os.listdir(STRUCTURED_DIR)):
        with open(os.path.join(STRUCTURED_DIR, file), "r", encoding="utf-8") as f:
            record = json.load(f)

        if not record.get("symptoms") or not record.get("root_cause"):
            print(f"Skipping {file}: not a postmortem")
            continue

        record["id"] = file.replace(".json", "")
        incidents.append(record)

    print(f"Loaded {len(incidents)} incidents")
    return incidents

### Step 2: Chunking

def split_incidents(incidents, chunk_size = 800, chunk_overlap = 150):
    """Split incidents into smaller chunks for better RAG performance"""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""] 
    )

    chunks = []

    for inc in incidents:
        text = inc["text"][:30000]
        pieces = text_splitter.split_text(text)

        for i, piece in enumerate(pieces):
            chunks.append({
                "id": f"{inc['id']}__{i}",
                "text": piece,
                "metadata": {"incident_id": inc["id"], "chunk_index": i, "company": inc["company"], "url": inc["url"], "category": inc["category"]}
            })
        
    print(f"Split {len(incidents)} documents into {len(chunks)} chunks")

    return chunks

### Step 2: EmbeddingManager 
class EmbeddingManager:
    """Handle embedding generation and storage using SentenceTransformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding manager
        
        Args: 
            model_name: HuggingFace model name for sentence embeddings
        
        """

        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the SentenceTransformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}. Embedding dimension: {self.model.get_embedding_dimension()} ")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            raise e
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts
        
        Args:
            texts: List of strings to embed
        
        Returns:
            np.ndarray: Array of embeddings with shape (len(texts), embedding_dimension)
        """
        if not self.model:
            raise ValueError("Model not loaded. Call _load_model() first.")

        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        print(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings


### Step 3: VectorStore  

class VectorStore:
    """Manages document embeddings in a ChromaDB vector store"""

    def __init__(self, collection_name: str = "incidents", persist_directory: str = CHROMA_DIR):
        """Initialize the vector store
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_store()

    def _initialize_store(self):
        """Initialize the ChromaDB client and collection"""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            self.collection = self.client.get_or_create_collection(
                name = self.collection_name,
                metadata = {"description": "Collection of incident reports"},
                configuration={"hnsw": {"space": "cosine"}},
                )
            print(f"Initialized ChromaDB collection: {self.collection_name} at {self.persist_directory}")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise e

    def add_incidents(self, incidents: List[Dict[str, Any]], embeddings: np.ndarray):
        """Upsert incidents and their symptom embeddings into the vector store

        Args:
            incidents: List of structured incident dicts (from load_incidents)
            embeddings: Embeddings of each incident's symptoms, same order
        """
        if len(incidents) != len(embeddings):
            raise ValueError("Number of incidents must match number of embeddings")

        ids = []
        metadatas = []
        documents_texts = []
        embeddings_list = []

        for inc, emb in zip(incidents, embeddings):
            ids.append(inc["id"])
            documents_texts.append(inc["symptoms"])
            embeddings_list.append(emb.tolist())

            metadata = {
                "company": inc["company"],
                "url": inc["url"],
                "category": inc["category"],
                "trigger": inc["trigger"],
                "severity": inc["severity"],
            }
            #Chroma rejects None values, so only add duration when it exists
            if inc.get("duration_minutes") is not None:
                metadata["duration_minutes"] = int(inc["duration_minutes"])
            metadatas.append(metadata)

        try:
            #upsert = insert new ids, overwrite existing ones -> safe to re-run
            self.collection.upsert(
                ids=ids,
                metadatas=metadatas,
                embeddings=embeddings_list,
                documents=documents_texts,
            )
            print(f"Upserted {len(ids)} incidents")
            print(f"Total incidents in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Error adding incidents to vector store: {e}")
            raise e

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        """Upsert full-text chunks; each one remembers its parent incident in metadata"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        try:
            self.collection.upsert(
                ids=[c["id"] for c in chunks],
                documents=[c["text"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
                embeddings=[emb.tolist() for emb in embeddings],
            )
            print(f"Upserted {len(chunks)} chunks")
            print(f"Total chunks in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Error adding chunks to vector store: {e}")
            raise e


if __name__ == "__main__":
    incidents = load_incidents()

    embedding_manager = EmbeddingManager()
    vector_store = VectorStore()

    symptoms = [inc["symptoms"] for inc in incidents]
    embeddings = embedding_manager.generate_embeddings(symptoms)
    vector_store.add_incidents(incidents, embeddings)
    chunks = split_incidents(incidents)
    chunk_store = VectorStore(collection_name="incident_chunks")
    chunk_embeddings = embedding_manager.generate_embeddings([c["text"] for c in chunks])
    chunk_store.add_chunks(chunks, chunk_embeddings)

    ### Quick sanity check
    query = "database connections maxed out after a deploy"
    query_emb = embedding_manager.generate_embeddings([query])[0]
    results = vector_store.collection.query(query_embeddings=[query_emb.tolist()], n_results=5)

    print(f"\nTop 5 for: '{query}'")
    for id_, meta, dist in zip(results["ids"][0], results["metadatas"][0], results["distances"][0]):
        print(f"  {1 - dist:.3f}  {id_}  ({meta['category']}, {meta['trigger']})")