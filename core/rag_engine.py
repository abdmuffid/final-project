import os
import chromadb
from chromadb.utils import embedding_functions
import random

# --- CONFIG PATH ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR)) 
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "chroma_db")

COLLECTION_NAME = "interview_simulation"

class RAGEngine:
    def __init__(self):
        self.collection = None
        
        if not os.path.exists(DB_PATH):
            print(f"⚠️ Warning: Database tidak ditemukan di {DB_PATH}")
            return

        try:
            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME, 
                embedding_function=self.ef
            )
        except Exception as e:
            print(f"❌ Error Init RAG: {e}")
            self.collection = None

    def _fetch_candidates(self, where_filter, limit=50):
        try:
            results = self.collection.get(
                where=where_filter,
                limit=limit,
                include=['metadatas', 'documents']
            )
            return results
        except Exception:
            return None

    def get_question(self, stage, sub_category=None, excluded_ids=None):
        """
        Stateless: Menerima 'excluded_ids' (daftar ID yang sudah ditanyakan ke user ini) dari luar.
        """
        if not self.collection: return None
        if excluded_ids is None: excluded_ids = []

        candidates = []
        
        # --- LOGIC FILTER STRICT ($and) ---
        where_filter = {}
        if not sub_category or sub_category in ["General", "Random"]:
            where_filter = {"stage": stage}
        else:
            where_filter = {
                "$and": [
                    {"stage": {"$eq": stage}},
                    {"sub_category": {"$eq": sub_category}}
                ]
            }

        # 1. FETCH UTAMA
        raw_data = self._fetch_candidates(where_filter)
        
        if raw_data and raw_data['ids']:
            for i, doc_id in enumerate(raw_data['ids']):
                if doc_id in excluded_ids: continue # Skip kalau sudah ditanya
                
                meta = raw_data['metadatas'][i]
                q_text = meta.get('original_q') or meta.get('question') or raw_data['documents'][i]
                ans_text = meta.get('answer') or meta.get('ideal_answer') or "General Logic"
                
                candidates.append({
                    "id": doc_id,
                    "question": q_text,
                    "answer_key": ans_text,
                    "sub_category": meta.get('sub_category', 'General'),
                    "source": "RAG Strict"
                })

        # 2. FALLBACK (Jika Stok Habis, cari random di stage yang sama)
        if not candidates and sub_category != "General":
            fallback_filter = {"stage": stage}
            raw_fallback = self._fetch_candidates(fallback_filter, limit=50)
            
            if raw_fallback and raw_fallback['ids']:
                for i, doc_id in enumerate(raw_fallback['ids']):
                    if doc_id in excluded_ids: continue
                    meta = raw_fallback['metadatas'][i]
                    q_text = meta.get('original_q') or raw_fallback['documents'][i]
                    candidates.append({
                        "id": doc_id,
                        "question": q_text,
                        "answer_key": meta.get('answer', 'General'),
                        "sub_category": meta.get('sub_category', 'Fallback'),
                        "source": "RAG Fallback"
                    })

        # 3. SELECT RANDOM
        if candidates:
            return random.choice(candidates)
        else:
            return None