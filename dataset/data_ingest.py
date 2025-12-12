import os
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import logging

# ==============================
# CONFIG PATH
# ==============================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(CURRENT_DIR, "Pertanyaan Interview Indonesia.xlsx")
DB_PATH = os.path.join(CURRENT_DIR, "chroma_db")
COLLECTION_NAME = "interview_simulation"

# ==============================
# LOGGING SETUP
# ==============================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# ==============================
# 1. LOAD DATASET
# ==============================
def load_data():
    if not os.path.exists(EXCEL_FILE):
        csv_file = EXCEL_FILE.replace(".xlsx", ".csv")
        if os.path.exists(csv_file):
            logging.info(f"File Excel tidak ditemukan, menggunakan CSV: {csv_file}")
            return pd.read_csv(csv_file)
        else:
            logging.error(f"File dataset tidak ditemukan di: {EXCEL_FILE}")
            exit(1)
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        # Isi data kosong dengan "General" biar aman
        df = df.fillna("General")
        logging.info(f"Dataset dimuat → {df.shape[0]} pertanyaan")
        return df
    except Exception as e:
        logging.error(f"Gagal membaca file: {e}")
        exit(1)

# ==============================
# 2. SETUP CHROMA + EMBEDDING
# ==============================
def setup_chroma():
    logging.info("Menyiapkan model embedding (MiniLM)...")
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # Bikin folder DB kalau belum ada
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)

    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Hapus DB lama biar fresh (Re-ingest)
    try:
        client.delete_collection(COLLECTION_NAME)
        logging.info("Database lama dihapus (Fresh Ingest).")
    except Exception: 
        logging.info("Database baru, membuat collection pertama kali...")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    return collection

# ==============================
# 3. INGEST DATA
# ==============================
def ingest_all(df, collection):
    logging.info("Mulai proses ingest data...")
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        q = str(row.get("Question", "")).strip()
        a = str(row.get("Answer", "")).strip()
        
        # Skip kalau pertanyaan kosong
        if not q: continue 

        stage = str(row.get("Stage", "General"))
        sub_cat = str(row.get("Sub_Category", "General"))
        
        # Format teks embedding
        text_content = f"[{stage} - {sub_cat}] {q}"
        
        meta = {
            "stage":        stage,
            "sub_category": sub_cat,
            "intent":       str(row.get("Intent", "General")),
            "source":       str(row.get("Source", "Manual")),
            "answer":       a[:2000],
            "original_q":   q
        }
        
        documents.append(text_content)
        metadatas.append(meta)
        ids.append(f"q_{idx}") 
    
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logging.info(f"SELESAI! Berhasil menyimpan {len(ids)} data ke ChromaDB.")
    else:
        logging.warning("Tidak ada data yang valid untuk disimpan.")

# ==============================
# MAIN EXECUTION
# ==============================
if __name__ == "__main__":
    df_data = load_data()
    chroma_collection = setup_chroma()
    ingest_all(df_data, chroma_collection)
    
    print(f"   Database tersimpan di: {DB_PATH}")