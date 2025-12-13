import time
import sys
import os
import random
from datetime import datetime # <--- Import Modul Waktu

# Import Modul Core
# Pastikan file core/rag_engine.py dan core/llm_evaluator.py sudah diupdate ke versi terbaru
from core.rag_engine import RAGEngine
from core.llm_evaluator import LLMEvaluator

def get_time_greeting():
    """
    Menentukan salam (Pagi/Siang/Sore/Malam) berdasarkan jam komputer user.
    """
    hour = datetime.now().hour
    
    if 4 <= hour < 11:
        return "Selamat Pagi"
    elif 11 <= hour < 15:
        return "Selamat Siang"
    elif 15 <= hour < 18:
        return "Selamat Sore"
    else:
        return "Selamat Malam"

def print_hr(text):
    """Efek mengetik untuk HRD"""
    print("\n🤖 HRD: ", end="")
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.01) # Kecepatan ketik (bisa diatur)
    print()

def print_progress(current, total):
    """Visualisasi Progress Bar"""
    percent = int((current / total) * 100)
    bar_length = 25
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\n⏳ Status: |{bar}| {percent}% Selesai")

def main():
    # 1. INISIALISASI SISTEM
    rag = RAGEngine()
    llm = LLMEvaluator()
    
    # Bersihkan layar terminal (Windows/Mac/Linux compatible)
    os.system('cls' if os.name == 'nt' else 'clear') 
    
    print("\n" + "="*70)
    print("      SIMULASI WAWANCARA KERJA BERBASIS AI (VERSI INDONESIA)")
    print("      Fitur: Role-Centric, Smart Pooling, Analisis Proyek & Real-time Clock")
    print("="*70)

    # 2. INPUT DATA PENGGUNA & POSISI
    user_name = input("👤 Nama Lengkap Anda: ")
    
    print("\n💼 PILIH POSISI YANG DILAMAR:")
    roles = [
        "Data Analyst / Scientist",
        "Software Engineer (Backend/Frontend)",
        "UI/UX Designer",
        "Digital Marketing / Social Media",
        "Administrative / HR",
        "Product Manager",
        "Business Development / Sales"
    ]
    
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")
    print(f"  {len(roles)+1}. Lainnya (Ketik Sendiri)")
    
    role_choice = input("\n👉 Pilih Nomor Posisi (1-8): ")
    job_role = "Kandidat Umum" # Default
    
    try:
        idx = int(role_choice) - 1
        if 0 <= idx < len(roles):
            job_role = roles[idx]
        else:
            job_role = input("👉 Tulis nama posisi spesifik: ")
    except:
        job_role = input("👉 Tulis nama posisi spesifik: ")

    print(f"\n✅ Mode Wawancara Diaktifkan: {job_role}")
    job_desc = input("📄 Silakan Copy-Paste Job Description (Wajib): ")
    
    print("\n(Sistem: Sedang merancang alur pertanyaan spesifik untuk Anda...)\n")
    
    # 3. MENYUSUN SKENARIO (THE POOL SYSTEM)
    full_transcript = f"Nama: {user_name}\nPosisi: {job_role}\nJob Desc: {job_desc}\n\n"
    history_q = []
    interview_sequence = []

    # A. Tahap Pembukaan (1 Pertanyaan)
    interview_sequence.append(("Introductions", "Greeting", "Opening"))

    # B. Tahap Umum / Broad (Ambil 3 Topik Acak dari Database)
    # CATATAN: Kunci string harus tetap Inggris agar cocok dengan Database RAG
    broad_pool = [
        "Motivational", 
        "Source", 
        "Company Knowledge", 
        "Strengths/Weaknesses", 
        "Work Style", 
        "Career Plan", 
        "Self Awareness",
        "Unique Value"
    ]
    # Mengambil 3 topik secara acak
    selected_broad = random.sample(broad_pool, 3)
    for topic in selected_broad:
        interview_sequence.append(("Broad", topic, "General"))

    # C. Tahap Inti Posisi (5 Pertanyaan: Campuran Teknis & Behavioral)
    # Pola: Teknis -> Behavioral -> Teknis -> Behavioral -> Teknis
    for i in range(5):
        if i % 2 == 0:
            interview_sequence.append(("Position-Related", "Technical-Combo", "Hard Skill"))
        else:
            interview_sequence.append(("Position-Related", "Behavioral", "Soft Skill"))

    # D. Tahap Penutup (2 Pertanyaan)
    interview_sequence.append(("Conclusion", "Availability", "Closing"))
    interview_sequence.append(("Conclusion", "Candidate Questions", "Closing"))

    total_q = len(interview_sequence)

    # === 4. EKSEKUSI WAWANCARA ===
    for idx, (stage, sub_cat, q_type) in enumerate(interview_sequence, 1):
        
        # Tampilkan Bar Progress
        print_progress(idx, total_q)
        
        # EFEK CHEERLEADER (Penyemangat di tengah jalan)
        if idx == 6:
            print("\n🌟 SISTEM: Tarik napas sejenak... Anda sudah menyelesaikan separuh sesi!")
            print(f"🌟 SISTEM: Sekarang kita akan masuk ke pendalaman teknis untuk posisi {job_role}.")
            time.sleep(2)

        # A. HANDLER SAPAAN (Opening) - UPDATE FITUR WAKTU
        if sub_cat == "Greeting":
            # Hitung waktu (Pagi/Siang/Malam)
            salam_waktu = get_time_greeting()
            
            # Kirim konteks waktu ke AI
            opening = llm.generate_opening(user_name, job_role, salam_waktu)
            
            print_hr(opening)
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"HR: {opening}\nKandidat: {ans}\n\n"
            continue

        # B. HANDLER TANYA JAWAB TERBALIK (Closing)
        if sub_cat == "Candidate Questions":
            print("\n" + "-"*50)
            print_hr("Sesi wawancara inti sudah selesai. Apakah ada yang ingin Anda tanyakan tentang posisi atau perusahaan ini?")
            user_q = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat Bertanya: {user_q}\n"
            
            # Cek apakah user bilang "tidak ada"
            check_negatives = ["tidak", "cukup", "no", "nggak", "ga", "sudah jelas"]
            if not any(word in user_q.lower() for word in check_negatives):
                hr_ans = llm.answer_user_question(user_q)
                print_hr(hr_ans)
                full_transcript += f"HR Menjawab: {hr_ans}\n"
            else:
                print_hr("Baik, terima kasih.")
            continue

        # C. LOGIKA PENGAMBILAN PERTANYAAN
        question_data = None
        
        if sub_cat == "Technical-Combo":
            # Generate Pertanyaan Kombo (Technical + Job Desc)
            # Memanggil fungsi prompt "Kombo" yang baru
            raw_q = llm.generate_technical_question_combo(job_desc, str(history_q), job_role)
            question_data = {"question": raw_q, "answer_key": "Sesuai Job Desc/Proyek Nyata", "type": "Technical"}
            
        else:
            # Ambil dari Database RAG
            question_data = rag.get_question(stage, sub_category=sub_cat)
            
            # Fallback (Cadangan jika database kosong/error)
            if not question_data:
                question_data = rag.get_question(stage) # Ambil random di stage yg sama
                if not question_data:
                    # Terpaksa generate pakai AI
                    gen_q = llm.paraphrase_question(f"Tanyakan satu pertanyaan tentang {sub_cat}", job_role)
                    question_data = {"question": gen_q, "answer_key": "General Logic", "type": "Generated"}

        # D. FINALISASI PERTANYAAN (Paraphrase ke Bahasa Indonesia)
        final_q = question_data['question']
        
        # Kalau bukan pertanyaan teknis (yg sudah digenerate langsung), kita paraphrase dulu biar natural
        if question_data.get("type") != "Technical":
            final_q = llm.paraphrase_question(final_q, job_role)
        
        history_q.append(final_q)
        
        print("\n" + "-"*50)
        # Menampilkan topik (opsional)
        print(f"📌 Topik Fokus: {sub_cat.replace('-', ' ')}") 
        print_hr(final_q)
        full_transcript += f"HR ({sub_cat}): {final_q}\n"
        
        # E. LOOP FOLLOW-UP (Pendalaman Jawaban)
        current_round = 0
        max_round = 1 
        if sub_cat in ["Technical-Combo", "Behavioral"]:
            max_round = 2 # Lebih dalam untuk pertanyaan inti
        
        no_followup_topics = ["Compensation", "Availability", "Source"]
        
        while True:
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat: {ans}\n"
            
            if sub_cat not in no_followup_topics and current_round < max_round:
                print("\n(Sistem: HR sedang menganalisis kualitas jawaban...)")
                
                # Cek jawaban pake "Expert Insight" (Prompt Baru)
                check = llm.check_response_and_followup(final_q, ans, question_data.get('answer_key',''))
                
                if "[NEXT]" in check or "NEXT" in check:
                    break
                else:
                    # Jika AI merasa jawaban kurang bukti, dia akan nanya lagi
                    print_hr(check)
                    full_transcript += f"HR Follow-up: {check}\n"
                    final_q = check # Update konteks
                    current_round += 1
            else:
                break

    # === 5. LAPORAN AKHIR (THE MONSTER REPORT) ===
    print("\n\n" + "="*70)
    print(f"📊 MENYUSUN LAPORAN EVALUASI DETAIL: {job_role.upper()}...")
    print("(Sistem: Menganalisis Transkrip, Mencari Bukti Kutipan, Menghitung Skor...)")
    print("="*70)
    
    # Generate Report Full Bahasa Indonesia
    report = llm.generate_final_report(user_name, job_role, job_desc, full_transcript)
    
    print("\n" + report)
    print("\n✅ Simulasi Selesai. Semangat untuk interview aslinya!")

if __name__ == "__main__":
    main()