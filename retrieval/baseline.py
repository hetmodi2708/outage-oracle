from ingest.index import EmbeddingManager, VectorStore
from typing import List, Dict, Any

class RAGretriever:
    """Baseline retriever: embed the query, search the symptom embeddings"""

    def __init__(self, vector_store:VectorStore, embedding_manager: EmbeddingManager):
        """ Initialize the retriever
        
        Args:
            vector_store: Vector store containing incident symptom embeddings
            embedding_manager: Manager for generating query embeddings
        """

        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.0, verbose: bool = False) -> List[Dict[str, Any]]:
        """Retrieve top_k most similar incidents for a given query

        Returns:
            List of dictionaries with id, similarity_score, metadata, content (symptoms), rank
        """

        #Generate embedding for the query
        query_embedding = self.embedding_manager.generate_embeddings([query])[0]

        try:
            results = self.vector_store.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
            )

            retrieved_docs = []

            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                ids = results['ids'][0]

                for i, (doc_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                    #Convert distance to similarity score (assuming distance is cosine distance)
                    similarity = 1 - (distance)
                    if similarity >= score_threshold:
                        doc_info = {
                            "similarity_score": float(similarity),
                            "metadata": metadata,
                            "content": document,
                            "id": doc_id,
                            "distance": float(distance),
                            "rank": i + 1

                        }
                        retrieved_docs.append(doc_info)
                if verbose:
                    print(f"Retrieved {len(retrieved_docs)} incidents for query: '{query}'")
                
            else:
                print(f"No documents found for query: '{query}'")
        except Exception as e:
            print(f"Error occurred while querying the vector store: {e}")
            return []

        return retrieved_docs

embedding_manager = EmbeddingManager()
vector_store = VectorStore()
retriever = RAGretriever(vector_store, embedding_manager)

def query_retrieve(query: str, k: int = 5) -> List[str]:
    """Simple helper for evals: return just the top-k incident ids"""
    return [doc["id"] for doc in retriever.retrieve(query, top_k=k)] 