import os
import time
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import json # Import json for robust parsing

class MemoryManager:
    def __init__(self, qdrant_host="localhost", qdrant_port=6333, collection_name="voice_notes_collection"):
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.model = SentenceTransformer('all-MiniLM-L6-v2') 
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.model.get_sentence_embedding_dimension(), distance=models.Distance.COSINE),
            )
            print(f"Collection '{self.collection_name}' created or recreated.")
        except Exception as e:
            if "already exists" in str(e): 
                print(f"Collection '{self.collection_name}' already exists.")
            else:
                print(f"Error ensuring collection exists: {e}")
                try:
                    self.qdrant_client.get_collection(collection_name=self.collection_name)
                    print(f"Collection '{self.collection_name}' confirmed to exist despite earlier error.")
                except Exception as inner_e:
                    print(f"Failed to get collection info after initial error: {inner_e}")
                    raise

    def embed_text(self, text):
        return self.model.encode(text).tolist()

    def store_voice_note(self, text, tags=None, action_items=None, sentiment="neutral"):
        if tags is None:
            tags = []
        if action_items is None:
            action_items = []

        if isinstance(action_items, str):
            try:
                action_items = json.loads(action_items)
                if not isinstance(action_items, list):
                    action_items = []
            except json.JSONDecodeError:
                action_items = []

        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
                if not isinstance(tags, list):
                    tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            except json.JSONDecodeError:
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif not isinstance(tags, list):
            tags = [] 

        embedding_text = f"Summary: {text}. Tags: {', '.join(tags)}. Action Items: {', '.join([item.get('item', '') for item in action_items])}. Sentiment: {sentiment}."
        vector = self.embed_text(embedding_text)

        payload = {
            "text": text,
            "tags": tags,
            "timestamp": time.time(),
            "source": "voice_note",
            "action_items": action_items,
            "sentiment": sentiment
        }

        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        vector=vector,
                        payload=payload
                    )
                ]
            ).wait()
            print(f"Successfully stored voice note with text: {text[:50]}...")
            return True, "Voice note stored successfully."
        except Exception as e:
            print(f"Failed to store voice note: {e}")
            return False, f"Failed to store voice note: {e}"

    def search_voice_notes(self, query_text, limit=5):
        query_vector = self.embed_text(query_text)
        try:
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                append_payload=True
            )
            formatted_results = []
            for hit in search_result:
                formatted_results.append({
                    "score": hit.score,
                    "text": hit.payload.get('text', 'N/A'),
                    "tags": hit.payload.get('tags', []),
                    "id": hit.id,
                    "timestamp": hit.payload.get('timestamp', 'N/A'),
                    "action_items": hit.payload.get('action_items', []),
                    "sentiment": hit.payload.get('sentiment', 'N/A')
                })
            return formatted_results
        except Exception as e:
            print(f"Failed to search voice notes: {e}")
            return []

if __name__ == '__main__':
    manager = MemoryManager()