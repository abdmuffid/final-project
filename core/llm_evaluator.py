import os
from dotenv import load_dotenv
from groq import Groq

# Load API Key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class LLMEvaluator:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def _chat(self, prompt, system_role="Kamu adalah HRD Interviewer Profesional & Analis Ahli."):
        """Fungsi helper untuk mengirim request ke Groq"""
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=3000 
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error LLM: {e}"

    # =========================================================================
    # 1. FASE GENERATOR PERTANYAAN (MULUT HRD)
    # =========================================================================

    def generate_opening(self, user_name, job_role, time_context="Selamat Pagi"):
        """
        Membuat pembukaan interview yang sadar waktu.
        """
        prompt = f"""
        Nama Kandidat: {user_name}
        Posisi Dilamar: {job_role}
        Waktu Saat Ini: {time_context}
        
        Tugas: Buatlah kalimat pembuka interview yang profesional namun ramah.
        Instruksi Wajib: 
        1. Mulailah kalimat persis dengan ucapan salam waktu: "{time_context}".
        2. Sambut kandidat dan sebutkan secara spesifik posisi ({job_role}) yang dilamar.
        3. Bahasa: Bahasa Indonesia yang natural.
        
        Output: HANYA kalimat ucapannya saja.
        """
        return self._chat(prompt)

    def paraphrase_question(self, question, job_role="Kandidat"):
        """
        Mengubah pertanyaan kaku menjadi natural.
        Aturan: Maksimal 30 kata.
        """
        prompt = f"""
        Konteks Peran: {job_role}
        Pertanyaan Asli: "{question}"
        
        Tugas: Ubah pertanyaan di atas menjadi gaya bahasa lisan interview yang natural.
        Panduan:
        - Pertahankan nada profesional namun tidak kaku.
        - Gunakan pertanyaan terbuka (open-ended).
        - WAJIB: Pertanyaan harus DI BAWAH 30 KATA.
        - Bahasa: Bahasa Indonesia.
        
        Output: HANYA kalimat tanyanya saja.
        """
        return self._chat(prompt)

    def generate_technical_question_combo(self, job_desc, history_q, job_role):
        """
        Membangkitkan pertanyaan teknis (Kombo).
        Fokus: Pengalaman Proyek Nyata (Hands-on).
        """
        prompt = f"""
        Kamu adalah Interviewer Teknis yang spesialis untuk posisi {job_role}.
        
        Konteks:
        - Deskripsi Pekerjaan (JD): "{job_desc[:1500]}"
        - Pertanyaan Sebelumnya: {history_q}

        Tugas: Buat SATU "Pertanyaan Teknis Kombo".
        
        Ikuti panduan detail ini:
        1. Pindai JD untuk menemukan skill teknis utama (misal: SQL + Python + Tableau).
        2. Buat satu "Studi Kasus/Skenario" spesifik yang memaksa kandidat menjelaskan bagaimana mereka menggunakan skill-skill tersebut secara bersamaan.
        3. FOKUS: Galilah pengalaman proyek nyata (Hands-on), bukan sekadar definisi teori.
        4. WAJIB: Pertanyaan harus DI BAWAH 40 KATA. Langsung pada inti masalah.
        5. Bahasa: Bahasa Indonesia.

        Output: HANYA kalimat pertanyaannya saja.
        """
        return self._chat(prompt)

    # =========================================================================
    # 2. FASE FOLLOW-UP (TELINGA HRD)
    # =========================================================================

    def check_response_and_followup(self, question, user_answer, ideal_answer):
        """
        Mengecek jawaban user.
        Persona: Ahli penggali insight mendalam.
        """
        prompt = f"""
        Kamu adalah ahli dalam membuat pertanyaan tindak lanjut (follow-up) untuk menggali wawasan lebih dalam.
        
        Pertanyaan Awal: "{question}"
        Jawaban Kandidat: "{user_answer}"
        Kunci Jawaban/Konteks Ideal: "{ideal_answer}"
        
        Tugas Analisis:
        1. Apakah jawaban tersebut menunjukkan "Pengalaman Nyata/Praktek" atau hanya sekadar teori/hafalan?
        2. Apakah jawabannya terlalu singkat atau tidak jelas?
        
        Logika Keputusan:
        - JIKA jawaban sudah cukup/bagus/ada bukti pengalaman -> Output persis: "[NEXT]"
        - JIKA jawaban tidak jelas/hanya teori/kurang detail -> Buat 1 pertanyaan follow-up singkat untuk meminta CONTOH SPESIFIK atau BUKTI NYATA.
        
        Bahasa Follow-up: Bahasa Indonesia.
        """
        return self._chat(prompt)

    def answer_user_question(self, user_question):
        return self._chat(f"Jawab pertanyaan kandidat ini secara singkat, positif, dan profesional (Bahasa Indonesia): '{user_question}'")

    # =========================================================================
    # 3. FASE FINAL REPORT (RAPOR AKHIR)
    # =========================================================================

    def generate_final_report(self, user_name, job_role, job_desc, full_transcript):
        """
        FUSION TOTAL PROMPT (VERSI BAHASA INDONESIA).
        Menggabungkan: 12 Faktor Analisis, Skor Komunikasi, Kutipan Bukti, & Insight Eksekutif.
        """
        
        # 1. Definisi Rubrik Komunikasi (Diterjemahkan)
        rubric = """
        SISTEM PENILAIAN KOMUNIKASI (Skala 0-10):
        - 10: Penguasaan penuh, penggunaan bahasa sangat tepat, akurat, lancar, menunjukkan pemahaman total.
        - 09: Penguasaan penuh dengan sedikit ketidaktepatan sesekali. Menangani argumen kompleks dengan baik.
        - 08: Penguasaan operasional dengan sedikit kesalahan. Bisa menangani bahasa/topik kompleks.
        - 07: Penguasaan efektif meski ada ketidaktepatan. Memahami bahasa yang cukup kompleks.
        - 06: Penguasaan parsial/sebagian, mengerti makna umum, tapi sering ada kesalahan.
        - 05: Kompetensi dasar terbatas pada situasi yang familiar saja.
        - 04: Hanya mengerti makna umum di situasi yang sangat familiar.
        - 03: Sangat kesulitan memahami percakapan.
        - 02: Tidak ada kemampuan komunikasi kecuali beberapa kata terpisah.
        - 01: Tidak menjawab.
        """

        # 2. Definisi 12 Faktor Analisis (Diterjemahkan)
        factors = """
        FAKTOR ANALISIS YANG HARUS DINILAI:
        1. Skill Komunikasi (Tata bahasa, kosa kata, kejelasan)
        2. Waktu Menjawab (Sigap vs bertele-tele)
        3. Kepercayaan Diri (Tegas vs ragu-ragu)
        4. Kejelasan (Struktur jawaban)
        5. Sikap/Attitude (Positif, hormat, antusias)
        6. Relevansi (Apakah jawaban nyambung dengan pertanyaan?)
        7. Kedalaman Pengetahuan (Detail vs dangkal)
        8. Kemampuan Pemecahan Masalah (Logika berpikir analitis)
        9. Contoh dan Bukti (Apakah memberikan contoh nyata?)
        10. Kemampuan Mendengar (Merespons follow-up dengan tepat)
        11. Konsistensi (Apakah jawaban bertentangan?)
        12. Adaptabilitas (Menangani pertanyaan sulit)
        """

        # 3. Prompt Utama
        prompt = f"""
        Kamu adalah Evaluator Interview & Analis Ahli.
        
        KANDIDAT: {user_name}
        POSISI DILAMAR: {job_role}
        
        TRANSKRIP WAWANCARA:
        {full_transcript}
        
        DESKRIPSI PEKERJAAN (JD):
        {job_desc[:1500]}

        {rubric}
        {factors}

        ---------------------------------------------------------
        TUGAS:
        Berdasarkan transkrip dan faktor-faktor di atas, buatlah laporan evaluasi yang sangat mendetail.
        Output hasilnya dalam format MARKDOWN terstruktur (Bahasa Indonesia).

        STRUKTUR LAPORAN:

        # 📑 LAPORAN HASIL EVALUASI: {job_role.upper()}

        ## 1. 💡 EXECUTIVE INSIGHTS (Wawasan Utama)
        *Berikan 3 wawasan/insight kunci tentang kandidat ini. Maksimal 25 kata per poin.*
        * 🔹 (Insight 1)
        * 🔹 (Insight 2)
        * 🔹 (Insight 3)

        ## 2. 📊 ANALISIS KOMUNIKASI
        **Skor Komunikasi:** [0-10] / 10
        **Status:** [Sangat Baik / Baik / Cukup / Kurang]
        **Feedback:** (Tulis rangkuman 60 kata tentang skill komunikasi mereka berdasarkan rubrik).

        ## 3. 📈 SCORECARD 12 FAKTOR
        *Evaluasi kandidat berdasarkan faktor kunci (Confidence, Knowledge, dll).*
        
        | Faktor Utama | Kualitas (Tinggi/Sedang/Rendah) | Catatan Analis |
        | :--- | :--- | :--- |
        | **Kepercayaan Diri & Sikap** | ... | ... |
        | **Kedalaman Pengetahuan** | ... | ... |
        | **Pemecahan Masalah (Logika)** | ... | ... |
        | **Bukti & Contoh Nyata** | ... | (Apakah kandidat memberikan contoh real?) |

        **Soft Skill Summary (15 kata):** ...

        ## 4. 💬 ANALISIS BERBASIS BUKTI (QUOTES)
        *Identifikasi kutipan spesifik dari transkrip yang mendukung analisismu.*

        **✅ KEKUATAN (STRENGTHS)**
        > "Kutip kalimat persis dari kandidat di sini..."
        * **Analisis:** (Jelaskan kenapa kutipan ini menunjukkan kekuatan).

        **⚠️ AREA PENGEMBANGAN (IMPROVEMENTS)**
        > "Kutip kalimat persis dari kandidat di sini..."
        * **Analisis:** (Jelaskan kenapa kutipan ini menunjukkan kekurangan/keraguan).

        ## 5. ✅ CHECKLIST TEKNIS (VALIDASI JD)
        *Cek apakah hard skill yang diminta di JD muncul dalam jawaban kandidat.*
        * [ ] (Skill 1) - (Muncul/Tidak Muncul)
        * [ ] (Skill 2) - (Muncul/Tidak Muncul)

        ## 6. ⚖️ KESIMPULAN AKHIR (VERDICT)
        **Skor Keseluruhan:** [0-100]
        **Rekomendasi:** [SIAP LANJUT / DIPERTIMBANGKAN / BELUM SESUAI]
        **Saran Penutup:** (Saran pengembangan karir singkat).
        """
        
        return self._chat(prompt, system_role="Kamu adalah Analis Evaluasi yang ketat dan objektif. Berikan feedback berbasis bukti.")