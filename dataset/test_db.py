import os
import chromadb
from chromadb.utils import embedding_functions

# ==============================
# CONFIG PATH (Harus sama dengan ingest)
# ==============================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "chroma_db")
COLLECTION_NAME = "interview_simulation"

def main():
    print(f"\n🚀 MEMULAI TEST QUERY DATABASE")
    print(f"📂 Lokasi DB: {DB_PATH}")

    # 1. Cek Apakah Database Ada
    if not os.path.exists(DB_PATH):
        print("❌ Error: Database tidak ditemukan!")
        print("   Jalankan 'python dataset/data_ingest.py' dulu.")
        return

    # 2. Koneksi ke Database (Mode Baca)
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # Setup Model Embedding (Wajib SAMA PERSIS dengan Ingest)
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Ambil Koleksi (Pakai get_collection, bukan get_or_create)
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn
        )
        
        total_data = collection.count()
        print(f"✅ Terhubung! Total Data: {total_data} pertanyaan.")
        print("-" * 60)

    except Exception as e:
        print(f"❌ Gagal koneksi: {e}")
        return

    # 3. Loop Interaktif (Tanya Jawab)
    print("💡 Ketik pertanyaan topik interview (atau 'exit' untuk keluar)")
    
    while True:
        print("\n" + "="*60)
        query = input("🔍 Masukkan Topik/Keyword: ").strip()
        
        if query.lower() in ['exit', 'keluar', 'quit']:
            break
        
        if not query: continue

        # Cari di Database (Ambil 3 teratas)
        print("   ⏳ Sedang mencari...")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        # Tampilkan Hasil
        if results['documents'] and results['documents'][0]:
            print(f"   ✅ Ditemukan {len(results['documents'][0])} hasil relevan:\n")
            
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i]
                
                # Format Output Rapi
                print(f"   [{i+1}] Score Kemiripan: {dist:.4f} (Makin kecil makin mirip)")
                print(f"       📂 Stage     : {meta.get('stage', '-')}")
                print(f"       🏷️  Sub-Cat   : {meta.get('sub_category', '-')}")
                print(f"       ❓ Pertanyaan: {meta.get('original_q', '-')}")
                print(f"       💡 Jawaban   : {meta.get('answer', '')[:100]}...") # Potong jawaban
                print("       " + "-"*40)
        else:
            print("   ❌ Tidak ada data yang cocok.")

    print("\n👋 Bye!")

if __name__ == "__main__":
    main()