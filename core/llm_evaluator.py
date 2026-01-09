import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

# Load API Key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class LLMEvaluator:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # --- 1. UNIFIED PERSONA DEFINITION ---
        # Ini adalah "jiwa" dari AI Anda. Satu prompt untuk semua fungsi.
        self.SYSTEM_PERSONA = """
        Anda adalah "Senior Talent Acquisition Specialist" & "Technical Recruiter" berpengalaman di perusahaan teknologi terkemuka.
        
        Karakteristik Anda:
        1. Profesional namun ramah (Human-Centric).
        2. Sangat tajam dalam menilai Hard Skill (Teknis) maupun Soft Skill (STAR Method).
        3. Objektif dalam memberikan penilaian skor (0-10).
        4. Gaya bicara: Formal, sopan, menggunakan Bahasa Indonesia yang baik dan mengalir (tidak kaku seperti robot).
        5. Tujuan: Menemukan kandidat terbaik dengan menggali potensi mereka secara mendalam namun nyaman.
        
        Jangan pernah keluar dari karakter ini. Anda adalah satu orang yang sama dari awal sapaan hingga laporan akhir.
        """

    def _chat(self, prompt, system_role=None, temperature=0.3, max_tokens=5000, response_format=None):
        """Enhanced chat dengan Unified Persona support"""
        
        # --- LOGIKA PERSONA ---
        # Jika tidak ada system_role khusus yg dikirim, pakai Persona Utama HRD
        if system_role is None:
            active_role = self.SYSTEM_PERSONA
        else:
            active_role = system_role

        try:
            params = {
                "messages": [
                    {"role": "system", "content": active_role}, 
                    {"role": "user", "content": prompt}
                ],
                "model": "moonshotai/kimi-k2-instruct", 
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format == "json_object":
                params["response_format"] = {"type": "json_object"}

            completion = self.client.chat.completions.create(**params)
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Error LLM: {e}")
            return ""

    # =========================================================================
    # SECTION 1: OPENING & WARMING UP
    # =========================================================================

    def generate_opening(self, user_name, job_role, time_context="Selamat Pagi"):
        """
        - Warm & Professional tone
        - Sets expectation
        - Builds rapport
        """
        prompt = f"""
        KONTEKS:
        - Kandidat: {user_name}
        - Posisi: {job_role}
        - Waktu: {time_context}
        
        TUGAS: Buat pembukaan interview yang:
        1. WAJIB mulai dengan "{time_context}"
        2. Sambut hangat dengan menyebut nama kandidat
        3. Sebutkan posisi yang dilamar
        4. Berikan konteks tentang flow interview (akan ada pertanyaan umum, teknis, dan behavioral)
        5. Buat kandidat merasa nyaman tapi tetap profesional
        
        CONTOH TONE YANG DIINGINKAN:
        "{time_context}, {user_name}! Terima kasih sudah meluangkan waktu untuk bergabung dengan kami hari ini. 
        Saya akan memandu Anda dalam sesi interview untuk posisi {job_role}. Nanti kita akan berbincang 
        tentang pengalaman Anda, keahlian teknis, dan bagaimana Anda menangani berbagai situasi kerja. 
        Santai saja, ini adalah diskusi dua arah. Siap untuk memulai?"
        
        PANJANG: Maksimal 60 kata.
        BAHASA: Bahasa Indonesia natural, bukan terjemahan kaku.
        
        Output: HANYA kalimat pembukaan.
        """
        return self._chat(prompt, temperature=0.5)

    # =========================================================================
    # SECTION 2: QUESTION GENERATOR (WITH BRIDGING INTEGRATION)
    # =========================================================================

    def paraphrase_question_contextual(self, question, job_role, last_user_response=None, conversation_context=""):
        """
        UPGRADED: Paraphrase dengan awareness terhadap konteks percakapan + SENTIMENT BRIDGING.
        """
        # --- LOGIKA SENTIMEN BRIDGING ---
        bridge_instruction = ""
        if last_user_response:
            bridge_instruction = f"""
            Konteks Jawaban Terakhir Kandidat: "{last_user_response}"
            INSTRUKSI BRIDGING TAMBAHAN:
            - Analisis sentimen jawaban (Positif/Negatif/Kasar/Singkat).
            - Jika Negatif/Kasar: JANGAN memuji. Gunakan nada netral.
            - Jika Bagus: Beri apresiasi singkat.
            - Gabungkan respons ini di awal pertanyaan secara natural.
            """
        # ---------------------------------------------------

        prompt = f"""
        KONTEKS PERCAKAPAN SEBELUMNYA:
        {conversation_context if conversation_context else "Baru memulai interview"}
        {bridge_instruction}
        
        PERTANYAAN ASLI: "{question}"
        POSISI: {job_role}
        
        TUGAS: Ubah pertanyaan menjadi natural dengan aturan:
        
        1. **BRIDGING** (Wajib jika ada konteks jawaban sebelumnya):
           - Buat transisi smooth sesuai instruksi sentimen di atas.
        
        2. **TONE**:
           - Conversational, bukan interogasi
           - Professional tapi approachable
           - Gunakan "Anda" bukan "kamu"
        
        3. **STRUCTURE**:
           - Open-ended question
           - Encourage storytelling
           - Maksimal 50 kata (termasuk bridging)
        
        4. **AVOID**:
           - Jangan pakai "Bisakah Anda jelaskan..." (terlalu kaku)
           - Lebih baik: "Bagaimana...", "Apa yang...", "Ceritakan tentang..."
        
        Output: HANYA kalimat pertanyaan yang sudah diubah.
        """
        return self._chat(prompt, temperature=0.3)

    def generate_technical_question_starmethod(self, job_description, history_questions, job_role, last_user_response=None, difficulty_level="medium"):
        """
        TECHNICAL QUESTION dengan STAR Method guidance.
        MODIFIED: Return Dictionary (JSON) untuk keperluan logging skripsi.
        """
        
        # --- LOGIKA SENTIMEN BRIDGING (TETAP ADA) ---
        bridge_instruction = ""
        if last_user_response:
            bridge_instruction = f'User menjawab: "{last_user_response}". Beri respons bridging (sesuai sentimen) SEBELUM tanya.'
        # --------------------------------

        difficulty_instructions = {
            "easy": "Fokus pada tools dan konsep dasar. Contoh: 'Jelaskan pengalaman Anda menggunakan SQL'",
            "medium": "Fokus pada proyek nyata dan problem-solving. Contoh: 'Ceritakan saat Anda harus mengoptimasi query yang lambat'",
            "hard": "Fokus pada skenario kompleks dan decision-making. Contoh: 'Bagaimana Anda mendesain data pipeline untuk handle 1M records/day?'"
        }
        
        prompt = f"""
        JOB DESCRIPTION (Key Skills):
        {job_description[:2500]}
        
        PERTANYAAN SEBELUMNYA:
        {history_questions[-3:] if len(history_questions) > 3 else history_questions}
        
        INSTRUKSI BRIDGING:
        {bridge_instruction}
        
        DIFFICULTY LEVEL: {difficulty_level.upper()}
        {difficulty_instructions.get(difficulty_level, "medium")}
        
        TUGAS UTAMA:
        Analisis JD, pilih skill, dan buat pertanyaan teknis. Output HARUS dalam format JSON.
        
        INSTRUKSI PEMBUATAN PERTANYAAN (Wajib diterapkan pada field 'question_text'):
        
        1. **STAR METHOD GUIDANCE**:
           Pertanyaan harus memandu kandidat untuk jawab dengan format:
           - Situation: Konteks proyek/masalah
           - Task: Tanggung jawab mereka
           - Action: Langkah konkret yang diambil
           - Result: Hasil yang terukur
        
        2. **TEKNOLOGI SPESIFIK**:
           - Pilih maksimal 10 skill dari JD yang BELUM ditanyakan di history
           - Gabungkan dalam satu skenario real-world
        
        3. **FORMAT KALIMAT**:
           - Dimulai dengan: "Ceritakan pengalaman Anda ketika..." atau "Bagaimana Anda menangani situasi..."
           - Maksimal 100 kata
           - BAHASA: Bahasa Indonesia formal dan natural.
           - Sertakan bridging sentiment di awal kalimat (jika ada instruksi bridging).
        
        FORMAT OUTPUT JSON (Wajib):
        {{
            "detected_skills": ["Sebutkan skill 1 dari JD", "Sebutkan skill 2"],
            "expected_criteria": "Jelaskan poin-poin kunci jawaban ideal yang diharapkan secara teknis (sebagai kunci jawaban)",
            "question_text": "Kalimat pertanyaan lengkap (termasuk bridging) sesuai instruksi di atas"
        }}
        """
        
        # Minta JSON Object ke LLM
        raw_response = self._chat(prompt, temperature=0.3, response_format="json_object")
        
        try:
            # Bersihkan potensi markdown formatting
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            
            # Parse ke Dictionary Python
            parsed_data = json.loads(clean_json)
            return parsed_data
            
        except json.JSONDecodeError:
            print("⚠️ Warning: Gagal parse JSON Teknikal, menggunakan fallback string.")
            return {
                "detected_skills": ["General Technical Skill"],
                "expected_criteria": "Kesesuaian dengan metode STAR, pemecahan masalah teknis, dan relevansi dengan JD.",
                "question_text": raw_response 
            }

    def generate_behavioral_question_situational(self, sub_category, job_role, history_questions, last_user_response=None):
        """
        BEHAVIORAL QUESTION dengan situational approach.
        """
        # --- LOGIKA SENTIMEN BRIDGING ---
        bridge_instruction = ""
        if last_user_response:
             bridge_instruction = f'User menjawab: "{last_user_response}". Beri respons bridging (sesuai sentimen) SEBELUM tanya.'
        # --------------------------------

        behavioral_frameworks = {
            "Leadership": "kepemimpinan: memimpin tim, mengambil inisiatif, atau mentoring junior",
            "Conflict": "konflik: perbedaan pendapat dengan rekan/atasan, menangani feedback negatif",
            "Pressure": "tekanan: deadline ketat, multiple priorities, atau situasi crisis",
            "Failure": "kegagalan: project yang tidak sesuai rencana, mistake yang dibuat, atau lesson learned",
            "Teamwork": "kolaborasi: bekerja dengan tim yang sulit, cross-functional collaboration",
            "Adaptability": "perubahan: situasi yang tidak terduga, perubahan requirement, atau pivot strategy"
        }
        
        framework = behavioral_frameworks.get(sub_category, "situasi kerja yang challenging")
        
        prompt = f"""
        FOKUS AREA: {sub_category}
        POSISI: {job_role}
        PERTANYAAN SEBELUMNYA: {history_questions[-2:] if len(history_questions) > 2 else "Belum ada"}
        {bridge_instruction}
        
        TUGAS: Buat SATU pertanyaan behavioral tentang {framework}.
        
        FRAMEWORK YANG HARUS DIIKUTI:
        1. **STRUKTUR PERTANYAAN**:
           - Mulai dengan: "Ceritakan tentang suatu waktu ketika..."
           - Atau: "Berikan contoh situasi di mana Anda..."
           - Spesifik pada situasi real, bukan hypothetical
        
        2. **PROBING UNTUK STAR**:
           - Pastikan pertanyaan mendorong kandidat cerita lengkap (S-T-A-R).
        
        3. **RELEVANSI DENGAN {job_role}**:
           - Connect behavioral aspect dengan job requirement
        
        PANJANG: Maksimal 100 kata (Termasuk Bridging).
        BAHASA: Bahasa Indonesia yang formal dan natural.
        Output: HANYA pertanyaannya.
        """
        return self._chat(prompt, temperature=0.3)

    # =========================================================================
    # SECTION 3: FOLLOW-UP SYSTEM (JSON & ADAPTIVE)
    # =========================================================================

    def analyze_answer_quality(self, question, user_answer, answer_key, job_role, q_category="General"):
        """
        ANSWER ANALYZER dengan JSON Output.
        Menggunakan logika STAR Method detection dari user.
        """

        # --- LOGIKA USER (TIDAK DIKURANGI) ---
        star_required_categories = ["Behavioral", "Technical-STAR", "Technical-Case", "StressTest"]
        is_star_needed = "true" if q_category in star_required_categories else "false"
        # -------------------------------------

        prompt = f"""
        KONTEKS:
        - Posisi: {job_role}
        - Pertanyaan: "{question}"
        - Jawaban Kandidat: "{user_answer}"
        - Jawaban Ideal: "{answer_key}"
        
        MASALAH:
        Kunci Jawaban Referensi mungkin berasal dari domain/posisi yang berbeda (misal: Marketing), 
        sedangkan Pelamar melamar sebagai {job_role}.
        
        TUGAS UTAMA:
        Nilai jawaban pelamar berdasarkan **STRUKTUR dan ESENSI** dari Jawaban Ideal, BUKAN kesamaan topik kata-per-kata. Buat dalam format JSON!
        
        INSTRUKSI PENILAIAN ADAPTIF (PENTING):
        1. **Ekstrak Pola Kunci**: Lihat Kunci Jawaban. Apa intinya? (Misal: Ada Masalah -> Aksi -> Hasil).
        2. **Abaikan Domain Kunci**: Jika Kunci bicara soal "Jualan", tapi User bicara soal "Coding" (sesuai role {job_role}), ITU BENAR. Jangan kurangi nilai karena beda topik.
        3. **Cek Relevansi Role**: Pastikan jawaban user relevan dengan role {job_role}.

        KRITERIA ANALISIS:
        1. **CEK METODE STAR** (Situation, Task, Action, Result):
            - Status Wajib STAR: {is_star_needed.upper()}
            - JIKA Kategori adalah 'Motivational', 'Intro', atau 'Concept': JANGAN cari STAR. Nilai berdasarkan kejelasan & relevansi saja.
            - JIKA Kategori adalah 'Behavioral' atau 'Technical Case': WAJIB ada STAR.
        
        2. **QUALITY SCORE (1-10)**:
            - 9-10: Excellent, STAR lengkap.
            - 7-8: Bagus, ada pengalaman nyata.
            - 5-6: Cukup, terlalu umum.
            - <5: Buruk, teori doang/tidak menjawab.
        
        3. **RED FLAG DETECTION**:
            - Deteksi: "Tidak tahu", "Asal daftar", "Ga mau lembur", "Kasar", "Bohong", (dan jawaban tidak profesional lainnya).
        
        4. **STAR COMPLETENESS**:
            - Situation, Task, Action, Result.
        
        5. **FOLLOW-UP DECISION**:
            - needs_followup: true JIKA Score < 7 ATAU STAR tidak lengkap ATAU Jawaban singkat.
            - JIKA Score >= 7: needs_followup HARUS false (Jangan tanya lagi detailnya).
        
        6. **FOLLOW-UP QUESTION**:
            - Buat pertanyaan follow-up (max 50 kata) KHUSUS menggali missing element.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "quality_score": 7,
            "has_red_flags": false,
            "red_flag_types": [],
            "needs_followup": true,
            "followup_question": "Pertanyaan follow-up...",
            "reasoning": "Alasan penilaian..." 
        }}
        """
        
        # Request ke LLM
        raw_result = self._chat(prompt, temperature=0.2, response_format="json_object")
        
        try:
            # Buang markdown dan spasi
            clean_result = raw_result.replace("```json", "").replace("```", "").strip()
            
            # Cari kurung kurawal terluar
            start_idx = clean_result.find('{')
            end_idx = clean_result.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                clean_result = clean_result[start_idx : end_idx + 1]
            
            parsed = json.loads(clean_result)
            
            # Update State Sukses
            self.quality_scores.append(parsed.get("quality_score", 5))
            if parsed.get("has_red_flags"): 
                self.red_flags.extend(parsed.get("red_flag_types", []))

            return parsed

        except Exception as e:
            # --- LAPISAN 2: REGEX RESCUE (Penyelamat Data) ---
            print(f"⚠️ JSON Gagal, mencoba Regex Rescue...")
            
            # Coba cari reasoning manual pakai pola Regex
            reason_match = re.search(r'"reasoning"\s*:\s*"(.*?)"', raw_result, re.DOTALL)
            fup_match = re.search(r'"followup_question"\s*:\s*"(.*?)"', raw_result, re.DOTALL)
            score_match = re.search(r'"quality_score"\s*:\s*(\d+)', raw_result)
            
            reasoning_text = reason_match.group(1) if reason_match else f"Analisis gagal diparsing. Raw: {raw_result[:50]}..."
            fup_text = fup_match.group(1) if fup_match else "Bisa ceritakan lebih detail bagian ini?"
            score_val = int(score_match.group(1)) if score_match else 5
            
            # Kembalikan data hasil rescue
            return {
                "quality_score": score_val, 
                "has_red_flags": False, 
                "red_flag_types": [],
                "needs_followup": True, 
                "followup_question": fup_text, 
                "missing_elements": [],
                "reasoning": f"[RESCUED] {reasoning_text}" 
            }


    def generate_adaptive_followup(self, original_question, user_answer, missing_elements, round_number=1):
        """
        Generate follow-up yang adaptive berdasarkan missing elements.
        """
        prompt = f"""
        KONTEKS:
        - Pertanyaan Awal: "{original_question}"
        - Jawaban Kandidat: "{user_answer}"
        - Element yang Hilang: {missing_elements}
        - Round: {round_number}
        
        TUGAS: Buat follow-up question yang:
        1. FOKUS PADA MISSING ELEMENTS (misal: "Apa hasilnya?", "Bagaimana caranya?").
        2. NATURAL TONE: Jangan interogasi. Gunakan "Menarik, bisa dijelaskan..."
        3. Max 60 kata.
        
        Output: HANYA pertanyaan follow-up.
        """
        return self._chat(prompt, temperature=0.3)

    # =========================================================================
    # SECTION 4: ADAPTIVE DIFFICULTY & STRESS TEST
    # =========================================================================

    def get_adaptive_difficulty(self, quality_scores):
        """Menentukan difficulty level berdasarkan performance kandidat (Stateless)."""
        if not quality_scores or len(quality_scores) < 3:
            return "medium"
        
        avg_score = sum(quality_scores[-5:]) / min(len(quality_scores), 5)
        
        if avg_score >= 8: return "hard"
        elif avg_score >= 6: return "medium"
        else: return "easy"

    def generate_stress_test_question(self, job_role, job_description, last_user_response=None):
        """
        Generate pertanyaan stress test untuk melihat kandidat under pressure.
        """
        # --- LOGIKA SENTIMEN BRIDGING ---
        bridge_instruction = ""
        if last_user_response:
             bridge_instruction = f'User menjawab: "{last_user_response}". Beri respons bridging SEBELUM tanya.'
        # --------------------------------

        prompt = f"""
        POSISI: {job_role}
        JOB DESC (Key Challenges): {job_description[:1000]}
        {bridge_instruction}
        
        TUGAS: Buat SATU pertanyaan "stress test" yang:
        1. SKENARIO REALISTIS TAPI CHALLENGING (Deadline ketat, Data berantakan, Stakeholder sulit).
        2. FRAMEWORK: "Bayangkan Anda dalam situasi X. Apa yang Anda lakukan?"
        3. TUJUAN: Test problem-solving under pressure.
        
        PANJANG: Maksimal 100 kata.
        Output: HANYA pertanyaan stress test.
        """
        return self._chat(prompt, temperature=0.3)

    # =========================================================================
    # SECTION 5: CLOSING, HINTS & USER QUESTIONS
    # =========================================================================

    # Menerima user_name & quality_scores
    def generate_closing(self, job_role, user_name="Kandidat", quality_scores=None):
        """Generate closing statement yang adaptive."""
        avg_score = 0
        if quality_scores:
            avg_score = sum(quality_scores)/len(quality_scores)
            
        quality = "excellent" if avg_score >= 8 else "good" if avg_score >= 6 else "fair"
        
        prompt = f"""
        TUGAS: Buat closing statement yang:
        1. Apresiasi waktu kandidat.
        2. Buka kesempatan bertanya (Q&A).
        3. Tone: {quality} (Positif/Netral/Respectful).
        4. Max 50 kata.
        Output: HANYA closing statement.
        """
        return self._chat(prompt, temperature=0.5)

    def analyze_closing_intent(self, user_message):
        """Intent Detection (ASK vs NO)"""
        prompt = f"""
        Kalimat: "{user_message}"
        Tentukan INTENSI: "ASK" (Nanya/Minta Info) atau "NO" (Nolak/Cukup/Makasih).
        Output HANYA satu kata: ASK atau NO.
        """
        return self._chat(prompt, temperature=0.1).upper()

    def answer_user_question_contextual(self, user_question, job_role):
        """Answer dengan context awareness."""
        prompt = f"""
        Simpan informasi berpa Pertanyaan Kandidat: "{user_question}". Posisi: {job_role}.
        
        TUGAS: Jawab pertanyaan kandidat secara diplomatis dan profesional.
        
        ATURAN JAWABAN:
        1. **JIKA Bertanya GAJI/BENEFIT/LEMBUR:**
           - Jawab DIPLOMATIS & NORMATIF.
           - "Kami menawarkan paket kompetitif sesuai pasar."
           - JANGAN sebut angka nominal (Anti-Halusinasi).
           
        2. **JIKA Bertanya BUDAYA KERJA / TIM:**
           - Jawab ANTUSIAS & POSITIF.
           - Gambarkan lingkungan yang kolaboratif, agile, dan suportif.
           - Tekankan kesempatan belajar (growth mindset).
           
        3. **JIKA Bertanya TANTANGAN / EKSPEKTASI:**
           - Jawab REALISTIS tapi OPTIMIS.
           - "Tantangannya dinamis, tapi kami fokus pada solusi dan dampak."
        
        Output: HANYA jawaban langsung ke kandidat.
        """
        return self._chat(prompt, temperature=0.5)

    def generate_subtle_hint(self, question, user_response):
        """Generate gentle hint untuk kandidat yang struggling."""
        prompt = f"""
        Q: "{question}". A: "{user_response}".
        TUGAS: Beri hint lembut (JANGAN SPOILER JAWABAN).
        Contoh: "Coba pikirkan dari sisi..."
        Max 30 kata.
        Output: HANYA hint.
        """
        return self._chat(prompt, temperature=0.5)

    def detect_need_for_break(self, transcript_length, quality_trend):
        """Detect apakah kandidat butuh break."""
        if transcript_length > 5000 and quality_trend == "declining":
            return True, "Baik, kita sudah banyak membahas topik. Mau istirahat sebentar? Ambil air dulu."
        return False, ""

    # =========================================================================
    # SECTION 6: FINAL REPORT (FIXED & FULL FEATURED)
    # =========================================================================

    # Menerima scores dan red_flags agar tidak error TypeError
    def generate_final_report(self, user_name, job_role, job_description, full_transcript, quality_scores, red_flags):
        """
        REPORT GENERATOR (EDISI COACH UNTUK JOBSEEKER).
        Fokus: Memberikan feedback konstruktif agar user bisa memperbaiki diri.
        """
        # Hitung rata-rata skor
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        if not quality_scores:
            readiness = "Belum Ada Data"
        elif avg_quality >= 8:
            readiness = "Sangat Siap (Ready to Apply)"
        elif avg_quality >= 6:
            readiness = "Cukup Siap (Perlu Sedikit Polesan)"
        else:
            readiness = "Butuh Latihan Intensif"

        prompt = f"""
        Tugasmu BUKAN merekrut, tapi MEMBANTU kandidat ({user_name}) agar sukses di interview asli nanti.

        Catatan Khusus:
        - Jika transkrip sangat pendek, artinya user mengakhiri sesi lebih awal.
        - Jangan menghakimi user, berikan saran bahwa "konsistensi menyelesaikan latihan adalah kunci keberhasilan".
        
        DATA SIMULASI:
        - Posisi Target: {job_role}
        - Skor Latihan: {avg_quality:.1f}/10
        - Status: {readiness}
        - Red Flags (Hal fatal): {red_flags}
        
        TRANSKRIP LATIHAN:
        {full_transcript[-6000:]}
        
        TUGAS: Buat Laporan Feedback (Markdown) yang edukatif.
        
        STRUKTUR LAPORAN:
        
        # 🎓 Raport Latihan Interview: {user_name}
        
        ## 📊 Ringkasan Performa
        (Berikan komentar mentor 1 paragraf tentang kesan umum performa user. Apakah percaya diri? Apakah jelas?)
        * **Skor Latihan:** {avg_quality:.1f} / 10
        * **Status Kesiapan:** {readiness}
        
        ## ✅ Apa yang Sudah Bagus (Pertahankan!)
        (Sebutkan poin-poin kekuatan user berdasarkan transkrip. Puji penggunaan STAR method jika ada).
        
        ## ⚠️ Apa yang Perlu Diperbaiki (Fokus Latihan)
        (Sebutkan kelemahan spesifik. Misal: "Jawaban terlalu singkat", "Kurang contoh nyata", "Terlalu bertele-tele").
        * **Perhatian Khusus:** Jika ada Red Flags ({red_flags}), jelaskan kenapa itu berbahaya di mata HRD.
        
        ## 💡 Tips Spesifik untuk Posisi {job_role}
        (Berikan saran teknis atau soft skill yang relevan dengan JD posisi ini).
        
        ## 📝 Rencana Latihan Selanjutnya
        (Berikan 3 langkah konkret/PR buat user).
        1. ...
        2. ...
        3. ...
        
        ## Kata Penutup Motivasi
        (Kalimat penyemangat singkat).
        
        Gunakan Bahasa Indonesia yang luwes, tidak kaku, tapi tetap profesional layaknya mentor.
        """
        return self._chat(prompt, temperature=0.5, max_tokens=4000)