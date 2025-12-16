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
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7, # Sedikit kreatif untuk bridging natural
                max_tokens=3000 
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error LLM: {e}"

    # =========================================================================
    # 1. GENERATOR PERTANYAAN
    # =========================================================================

    def generate_opening(self, user_name, job_role, time_context="Selamat Pagi"):
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

    def paraphrase_question(self, question, job_role="Kandidat", prev_answer=None):
        # Logika Bridging: Respons dulu jawaban sebelumnya
        bridge_instruction = ""
        if prev_answer:
            bridge_instruction = f"""
            Konteks Jawaban Terakhir Kandidat: "{prev_answer}"
            Instruksi Tambahan: Mulailah dengan 1 kalimat pendek yang merespons/mengapresiasi jawaban terakhir kandidat secara natural (misal: "Menarik sekali.", "Poin yang bagus.", "Saya mengerti pendekatannya."), BARU kemudian ajukan pertanyaan target.
            """
        
        prompt = f"""
        Konteks Peran: {job_role}
        Pertanyaan Baru Target: "{question}"
        {bridge_instruction}
        
        Tugas: Sampaikan pertanyaan target dengan gaya lisan natural Indonesia.
        Panduan:
        - Pertahankan nada profesional namun tidak kaku.
        - Gunakan pertanyaan terbuka (open-ended).
        - WAJIB: Pertanyaan harus DI BAWAH 45 KATA (Termasuk respons awal jika ada).
        - Bahasa: Bahasa Indonesia.
        
        Output: HANYA kalimat HRD yang akan diucapkan.
        """
        return self._chat(prompt)

    # --- VARIASI 1: COMBO (PROYEK GABUNGAN) ---
    def generate_technical_question_combo(self, job_desc, history_q, job_role, prev_answer=None):
        bridge_instruction = f'User baru saja menjawab: "{prev_answer}". Berikan respons singkat yang nyambung (apresiasi/validasi) SEBELUM bertanya.' if prev_answer else ""

        prompt = f"""
        Kamu adalah Interviewer Teknis yang spesialis untuk posisi {job_role}.
        Konteks JD: "{job_desc[:1500]}"
        History Pertanyaan: {history_q}
        {bridge_instruction}

        Tugas: Buat SATU "Pertanyaan Teknis Kombo".
        
        Panduan Detail:
        1. Pindai JD untuk menemukan 2-3 skill teknis utama.
        2. Buat satu "Studi Kasus/Skenario" spesifik yang memaksa kandidat menjelaskan bagaimana mereka menggunakan skill-skill tersebut secara bersamaan dalam PROYEK NYATA.
        3. FOKUS: Galilah pengalaman Hands-on, bukan sekadar definisi teori.
        4. Cek History: JANGAN tanyakan skill yang sudah pernah ditanyakan sebelumnya.
        5. WAJIB: Pertanyaan harus DI BAWAH 50 KATA (Termasuk respons awal).
        6. Bahasa: Bahasa Indonesia.

        Output: HANYA kalimat pertanyaannya saja (Respons + Pertanyaan).
        """
        return self._chat(prompt)

    # --- VARIASI 2: CONCEPT (TEORI MENDALAM) ---
    def generate_technical_concept(self, job_desc, history_q, job_role, prev_answer=None):
        bridge_instruction = f'User baru saja menjawab: "{prev_answer}". Berikan respons singkat yang nyambung (apresiasi/validasi) SEBELUM bertanya.' if prev_answer else ""

        prompt = f"""
        Kamu adalah Interviewer Teknis.
        Konteks JD: "{job_desc[:1500]}"
        History Pertanyaan: {history_q}
        {bridge_instruction}

        Tugas: Buat SATU "Pertanyaan Konseptual/Deep Dive".
        
        Panduan Detail:
        1. Cari skill di JD yang BELUM sering dibahas di History Pertanyaan.
        2. Minta kandidat menjelaskan 'Cara Kerja', 'Best Practice', atau 'Perbedaan' dari teknologi tersebut.
        3. Tujuannya menguji pemahaman teoritis yang mendalam.
        4. WAJIB: Pertanyaan harus DI BAWAH 40 KATA (Termasuk respons awal).
        5. Bahasa: Bahasa Indonesia.

        Output: HANYA kalimat pertanyaannya saja (Respons + Pertanyaan).
        """
        return self._chat(prompt)

    # --- VARIASI 3: CASE (STUDI KASUS ERROR) ---
    def generate_technical_case(self, job_desc, history_q, job_role, prev_answer=None):
        bridge_instruction = f'User baru saja menjawab: "{prev_answer}". Berikan respons singkat yang nyambung (apresiasi/validasi) SEBELUM bertanya.' if prev_answer else ""

        prompt = f"""
        Kamu adalah User/Lead Teknis.
        Konteks JD: "{job_desc[:1500]}"
        History Pertanyaan: {history_q}
        {bridge_instruction}

        Tugas: Buat SATU "Studi Kasus Masalah (Troubleshooting)".
        
        Panduan Detail:
        1. Berikan situasi singkat tentang masalah teknis/error/bug yang relevan dengan JD.
        2. Tanyakan langkah solutif apa yang akan diambil kandidat.
        3. Contoh: "Jika query SQL lambat saat data membesar, apa langkah optimasi Anda?"
        4. WAJIB: Pertanyaan harus DI BAWAH 50 KATA (Termasuk respons awal).
        5. Bahasa: Bahasa Indonesia.

        Output: HANYA kalimat pertanyaannya saja (Respons + Pertanyaan).
        """
        return self._chat(prompt)

    # =========================================================================
    # 2. FASE FOLLOW-UP
    # =========================================================================

    def check_response_and_followup(self, question, user_answer, ideal_answer):
        prompt = f"""
        Kamu adalah ahli dalam membuat pertanyaan tindak lanjut (follow-up) untuk menggali wawasan lebih dalam.
        
        Pertanyaan Awal: "{question}"
        Jawaban Kandidat: "{user_answer}"
        Kunci Jawaban/Konteks Ideal: "{ideal_answer}"
        
        Tugas Analisis:
        1. Apakah jawaban tersebut menunjukkan "Pengalaman Nyata/Praktek" atau hanya sekadar teori/hafalan?
        2. Apakah jawabannya terlalu singkat atau tidak jelas?
        
        CONSTRAINT KERAS (JANGAN DILANGGAR):
        - JANGAN PERNAH menyertakan teks analisis atau intro seperti "Berdasarkan jawaban kandidat...".
        - JANGAN ada "internal monologue".
        - Output HANYA SATU hal:
            a) Teks "[NEXT]" jika jawaban sudah bagus.
            b) Kalimat pertanyaan follow-up (Bahasa Indonesia) jika jawaban kurang.
        """
        return self._chat(prompt)

    # =========================================================================
    # 3. CLOSING INTENT
    # =========================================================================

    def analyze_closing_intent(self, user_input):
        prompt = f"""
        Tugas: Analisis kalimat kandidat di sesi akhir interview.
        Kalimat Kandidat: "{user_input}"
        
        Tentukan INTENSI kandidat:
        1. Jika kandidat mengajukan pertanyaan atau minta penjelasan -> Output: "ASK"
        2. Jika kandidat bilang cukup, tidak ada, sudah jelas, atau terima kasih saja -> Output: "NO"
        
        Contoh:
        - "Apa ada lembur?" -> ASK
        - "Tidak ada pertanyaan." -> NO
        - "Cukup jelas bu." -> NO
        - "Sebenarnya saya ingin tahu soal gaji." -> ASK
        - "Apakah tidak ada WFH?" -> ASK (Walau ada kata 'tidak', ini pertanyaan)
        
        Output HANYA satu kata: ASK atau NO.
        """
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model, temperature=0.1, max_tokens=5 
            )
            return completion.choices[0].message.content.strip().upper()
        except:
            return "NO"

    def answer_user_question(self, user_question):
        return self._chat(f"Jawab pertanyaan kandidat ini secara singkat, positif, dan profesional (Bahasa Indonesia): '{user_question}'")

    # =========================================================================
    # 4. FINAL REPORT
    # =========================================================================

    def generate_final_report(self, user_name, job_role, job_desc, full_transcript):
        # RUBRIK LENGKAP DARI STANDAR IELTS
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

        # 12 FAKTOR ANALISIS
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
        *Cari skill HARD SKILL di JD, cek apakah muncul di jawaban.*
        * [ ] (Skill 1) - (Muncul/Tidak Muncul)
        * [ ] (Skill 2) - (Muncul/Tidak Muncul)

        ## 6. ⚖️ KESIMPULAN AKHIR (VERDICT)
        **Skor Keseluruhan:** [0-100]
        **Rekomendasi:** [SIAP LANJUT / DIPERTIMBANGKAN / BELUM SESUAI]
        **Saran Penutup:** (Saran pengembangan karir singkat).
        """
        
        return self._chat(prompt, system_role="Kamu adalah Analis Evaluasi yang ketat dan objektif. Berikan feedback berbasis bukti.")