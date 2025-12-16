import time
import sys
import os
import random
from datetime import datetime
from core.rag_engine import RAGEngine
from core.llm_evaluator import LLMEvaluator

def get_time_greeting():
    """Menentukan salam berdasarkan jam saat ini"""
    hour = datetime.now().hour
    if 4 <= hour < 11: return "Selamat Pagi"
    elif 11 <= hour < 15: return "Selamat Siang"
    elif 15 <= hour < 18: return "Selamat Sore"
    else: return "Selamat Malam"

def print_hr(text):
    """Efek mengetik untuk HRD"""
    print("\n🤖 HRD: ", end="")
    # Bersihkan jika masih ada sisa tanda kutip tak sengaja dari output LLM
    clean_text = text.replace('"', '').strip()
    for char in clean_text:
        print(char, end='', flush=True)
        time.sleep(0.01)
    print()

def print_progress(current, total):
    """Visualisasi Progress Bar"""
    percent = int((current / total) * 100)
    bar_length = 25
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\n⏳ Status: |{bar}| {percent}% Selesai")

def main():
    rag = RAGEngine()
    llm = LLMEvaluator()
    os.system('cls' if os.name == 'nt' else 'clear') 

    print("\n" + "="*70)
    print("      SIMULASI WAWANCARA KERJA BERBASIS AI (ULTIMATE VERSION)")
    print("      Fitur: Conversational Bridging, Variasi Teknis, Smart Closing")
    print("="*70)

    # 1. INPUT DATA
    user_name = input("👤 Nama Lengkap Anda: ")
    print("\n💼 PILIH POSISI YANG DILAMAR:")
    roles = ["Data Analyst / Scientist", "Software Engineer (Backend/Frontend)", "UI/UX Designer", "Digital Marketing", "Administrative / HR", "Product Manager"]
    for i, role in enumerate(roles, 1): print(f"  {i}. {role}")
    
    try:
        choice = int(input("👉 Pilih Nomor (Angka): ")) - 1
        job_role = roles[choice] if 0 <= choice < len(roles) else input("👉 Tulis posisi spesifik: ")
    except: job_role = input("👉 Tulis posisi spesifik: ")

    print(f"\n✅ Mode Wawancara: {job_role}")
    job_desc = input("📄 Copy-Paste Job Desc Lengkap (Wajib): ")
    print("\n(Sistem: Merancang strategi pertanyaan...)\n")

    # 2. SUSUN SKENARIO
    full_transcript = f"Nama: {user_name}\nPosisi: {job_role}\nJD: {job_desc}\n\n"
    history_q = []
    interview_sequence = []

    # A. Opening
    interview_sequence.append(("Introductions", "Greeting", "Opening"))

    # B. Broad (3 Acak)
    broad_pool = ["Motivational", "Source", "Company Knowledge", "Strengths/Weaknesses", "Work Style", "Career Plan"]
    for topic in random.sample(broad_pool, 3): interview_sequence.append(("Broad", topic, "General"))

    # C. Core (VARIASI TEKNIS - SELANG SELING)
    # Urutan: Combo -> Behavioral -> Concept -> Behavioral -> Case
    interview_sequence.append(("Position-Related", "Technical-Combo", "Hard Skill"))
    interview_sequence.append(("Position-Related", "Behavioral", "Soft Skill"))
    interview_sequence.append(("Position-Related", "Technical-Concept", "Hard Skill"))
    interview_sequence.append(("Position-Related", "Behavioral", "Soft Skill"))
    interview_sequence.append(("Position-Related", "Technical-Case", "Hard Skill"))

    # D. Closing
    interview_sequence.append(("Conclusion", "Availability", "Closing"))
    interview_sequence.append(("Conclusion", "Candidate Questions", "Closing"))

    # VARIABEL PENYIMPAN JAWABAN TERAKHIR (UNTUK FITUR BRIDGING)
    last_participant_response = None

    # 3. EKSEKUSI LOOP INTERVIEW
    total_q = len(interview_sequence)
    for idx, (stage, sub_cat, q_type) in enumerate(interview_sequence, 1):
        print_progress(idx, total_q)
        
        if idx == 6: 
            print("\n🌟 SISTEM: Tarik napas sejenak... Masuk ke sesi pendalaman teknis!")
            time.sleep(1)

        # HANDLER OPENING
        if sub_cat == "Greeting":
            opening = llm.generate_opening(user_name, job_role, get_time_greeting())
            print_hr(opening)
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"HR: {opening}\nKandidat: {ans}\n\n"
            last_participant_response = ans # Simpan untuk bridging
            continue

        # HANDLER CLOSING (SMART AI)
        if sub_cat == "Candidate Questions":
            print_hr("Sesi inti sudah selesai. Ada yang ingin Anda tanyakan tentang posisi atau perusahaan ini?")
            user_q = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat Bertanya: {user_q}\n"
            
            # Deteksi Niat User pake AI
            intent = llm.analyze_closing_intent(user_q)
            
            if "ASK" in intent:
                print("(Sistem: HR sedang memikirkan jawaban...)")
                ans = llm.answer_user_question(user_q)
                print_hr(ans)
                full_transcript += f"HR Jawab: {ans}\n"
            else:
                print_hr("Baik, terima kasih. Kami akan segera memberi kabar.")
            continue

        # GENERATOR PERTANYAAN (DENGAN CONTEXT BRIDGING)
        question_data = None
        
        # Kirim 'last_participant_response' ke fungsi generator agar AI merespons jawaban sebelumnya
        if sub_cat == "Technical-Combo":
            raw = llm.generate_technical_question_combo(job_desc, str(history_q), job_role, last_participant_response)
            question_data = {"q": raw, "key": "Proyek", "type": "Tech"}
        elif sub_cat == "Technical-Concept":
            raw = llm.generate_technical_concept(job_desc, str(history_q), job_role, last_participant_response)
            question_data = {"q": raw, "key": "Konsep", "type": "Tech"}
        elif sub_cat == "Technical-Case":
            raw = llm.generate_technical_case(job_desc, str(history_q), job_role, last_participant_response)
            question_data = {"q": raw, "key": "Solusi", "type": "Tech"}
        else:
            # Ambil RAG / General
            question_data = rag.get_question(stage, sub_cat)
            if not question_data:
                # Generate manual + Bridge
                gen = llm.paraphrase_question(f"Tanyakan tentang {sub_cat}", job_role, last_participant_response)
                question_data = {"question": gen, "answer_key": "General", "type": "Gen"}
            else:
                # Jika dapat dari Database, Tetap Paraphrase agar dapat Bridging-nya
                q_rag = question_data['question']
                q_bridged = llm.paraphrase_question(q_rag, job_role, last_participant_response)
                question_data['question'] = q_bridged

            # Normalisasi key
            if 'question' in question_data: question_data['q'] = question_data['question']

        # FINALISASI
        final_q = question_data['q']
        
        history_q.append(final_q)
        print(f"\n📌 Topik: {sub_cat}")
        print_hr(final_q)
        full_transcript += f"HR: {final_q}\n"

        # FOLLOW-UP LOOP
        curr, limit = 0, 1
        if sub_cat in ["Technical-Combo", "Technical-Case", "Behavioral"]: limit = 2
        no_fup = ["Compensation", "Availability"]
        
        last_answer_in_loop = "" # Variable lokal untuk menyimpan jawaban terakhir sesi ini

        while True:
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat: {ans}\n"
            last_answer_in_loop = ans # Update jawaban
            
            if sub_cat not in no_fup and curr < limit:
                print("(Analisis jawaban...)")
                check = llm.check_response_and_followup(final_q, ans, question_data.get('answer_key',''))
                
                if "NEXT" in check or "[NEXT]" in check: break
                
                print_hr(check)
                full_transcript += f"HR Follow-up: {check}\n"
                final_q = check
                curr += 1
            else: break
        
        # UPDATE VARIABEL GLOBAL UNTUK BRIDGING PERTANYAAN BERIKUTNYA
        if last_answer_in_loop:
            last_participant_response = last_answer_in_loop

    # 4. REPORT
    print("\n" + "="*70 + "\n📊 MENYUSUN LAPORAN AKHIR...\n" + "="*70)
    rep = llm.generate_final_report(user_name, job_role, job_desc, full_transcript)
    print("\n" + rep + "\n✅ Simulasi Selesai.")

if __name__ == "__main__": main()