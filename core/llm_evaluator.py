import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class LLMEvaluator:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def _chat(self, prompt, system_role="Kamu adalah HRD Interviewer Profesional."):
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error LLM: {e}"

    # --- FITUR PERCAKAPAN (ROLE AWARE) ---
    
    def generate_opening(self, user_name, job_role):
        """Sapaan dengan menyebutkan posisi yang dilamar."""
        prompt = f"""
        Nama kandidat: {user_name}.
        Posisi yang dilamar: {job_role}.
        
        Tugas: Berikan sapaan pembuka interview yang ramah namun profesional.
        Sebutkan spesifik bahwa interview ini untuk posisi {job_role}.
        Bahasa: Indonesia.
        """
        return self._chat(prompt)

    def paraphrase_question(self, question, job_role="Kandidat"):
        """Paraphrase dengan tone yang sesuai job role."""
        prompt = f"""
        Konteks Posisi: {job_role}.
        Pertanyaan Asli: "{question}"
        
        Tugas: Ubah pertanyaan ini menjadi gaya bahasa lisan natural HRD kepada pelamar {job_role}.
        Hubungkan pertanyaan dengan konteks pekerjaan jika memungkinkan.
        Output: HANYA kalimat tanya.
        """
        return self._chat(prompt)

    def generate_technical_question(self, job_desc, history, job_role):
        prompt = f"""
        Role: Technical Recruiter untuk posisi {job_role}.
        Job Desc: "{job_desc[:1000]}"
        History Pertanyaan: {history}
        
        Tugas: Buat 1 pertanyaan teknis spesifik (Hard Skill/Studi Kasus) yang sangat relevan untuk seorang {job_role} berdasarkan Job Desc.
        Output: HANYA kalimat pertanyaan.
        """
        return self._chat(prompt)

    def check_response_and_followup(self, question, user_answer, ideal_answer):
        prompt = f"""
        Pertanyaan: "{question}"
        Jawaban: "{user_answer}"
        Kunci: "{ideal_answer}"
        
        Analisis:
        - Jika jawaban terlalu singkat/tidak jelas -> Buat 1 pertanyaan follow-up pendek.
        - Jika jawaban cukup -> Tulis "[NEXT]".
        """
        return self._chat(prompt)

    def answer_user_question(self, user_question):
        return self._chat(f"Kamu HRD. Jawab pertanyaan kandidat dengan diplomatis & positif: '{user_question}'")

    # --- FINAL REPORT (ROLE SPECIFIC) ---
    
    def generate_final_report(self, user_name, job_role, job_desc, full_transcript):
        prompt = f"""
        Bertindaklah sebagai Hiring Manager. Buat Laporan Evaluasi Interview.
        Kandidat: {user_name}
        Posisi: {job_role}
        
        JOB DESC: "{job_desc[:1500]}"
        TRANSKRIP: {full_transcript}

        Tugas: Buat laporan kualitatif.
        
        FORMAT MARKDOWN:
        # 📑 LAPORAN EVALUASI: {job_role.upper()} - {user_name.upper()}

        ## 1. HARD SKILL CHECKLIST (Sesuai Job Desc {job_role})
        | Skill Wajib | Status (✅/⚠️/❌) | Bukti/Catatan |
        | :--- | :--- | :--- |
        | (Skill 1) | ... | ... |
        | (Skill 2) | ... | ... |

        ## 2. SOFT SKILL & BEHAVIOR
        * **Komunikasi:** ...
        * **Motivasi:** ...
        * **Culture Fit:** ...

        ## 3. KESIMPULAN (VERDICT)
        **STATUS:** [SIAP LANJUT / DIPERTIMBANGKAN / BELUM SESUAI]
        **Alasan:** ...
        **Saran Pengembangan:** ...
        """
        return self._chat(prompt)