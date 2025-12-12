import time
import sys
import os

# Import Modul
from core.rag_engine import RAGEngine
from core.llm_evaluator import LLMEvaluator

def print_hr(text):
    print("\n🤖 HRD: ", end="")
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.01)
    print()

def main():
    rag = RAGEngine()
    llm = LLMEvaluator()
    
    print("\n" + "="*70)
    print("      SIMULASI INTERVIEW KERJA (ROLE-CENTRIC MODE)")
    print("="*70)

    # --- 1. INPUT DATA & ROLE SELECTION ---
    user_name = input("👤 Nama Lengkap: ")
    
    print("\n💼 PILIH POSISI YANG DILAMAR:")
    roles = [
        "Data Analyst / Scientist",
        "Software Engineer (Backend/Frontend)",
        "UI/UX Designer",
        "Digital Marketing / Social Media",
        "Administrative / HR",
        "Product Manager",
        "Other (Ketik Sendiri)"
    ]
    
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")
        
    choice = input("\n👉 Pilih Nomor (1-7): ")
    job_role = "General Applicant" # Default
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(roles) - 1:
            job_role = roles[idx]
        else:
            job_role = input("👉 Tulis nama posisi spesifik: ")
    except:
        job_role = input("👉 Tulis nama posisi spesifik: ")

    print(f"\n✅ Mode diaktifkan: {job_role}")
    job_desc = input("📄 Copy-Paste Job Desc (Wajib): ")
    
    print("\n(System: Menganalisis Job Desc & Role...)\n")
    
    # Variabel Transkrip
    full_transcript = f"Nama: {user_name}\nPosisi: {job_role}\nJob Desc: {job_desc}\n\n"
    history_q = []

    # --- 2. ALUR INTERVIEW (Sequence) ---
    interview_sequence = [
        # Intro
        ("Introductions", "Greeting"),
        
        # Broad (Penggalian Profil)
        ("Broad", "Motivational"),
        ("Broad", "Source"),
        ("Broad", "Company Knowledge"),
        ("Broad", "Strengths/Weaknesses"),
        ("Broad", "Work Style"),
        ("Broad", "Career Plan"),
        ("Broad", "Unique Value"), # Why Hire You
        
        # Position (Inti - Hybrid)
        ("Position-Related", "Technical-GenAI"),
        ("Position-Related", "Behavioral"),
        ("Position-Related", "Technical-GenAI"), # Teknis lagi biar mantap
        
        # Closing
        ("Conclusion", "Availability"),
        ("Conclusion", "Compensation"),
        ("Conclusion", "Candidate Questions")
    ]

    # === 3. MULAI LOOP INTERVIEW ===
    for stage, sub_cat in interview_sequence:
        
        # A. HANDLER GREETING (Pake Job Role)
        if sub_cat == "Greeting":
            opening = llm.generate_opening(user_name, job_role)
            print_hr(opening)
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"HR: {opening}\nKandidat: {ans}\n\n"
            continue

        # B. HANDLER REVERSE QnA
        if sub_cat == "Candidate Questions":
            print("\n" + "-"*50)
            print_hr("Sesi tanya jawab selesai. Ada yang ingin ditanyakan?")
            user_q = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat Bertanya: {user_q}\n"
            if user_q.lower() not in ["tidak", "cukup", "no"]:
                hr_ans = llm.answer_user_question(user_q)
                print_hr(hr_ans)
                full_transcript += f"HR Menjawab: {hr_ans}\n"
            continue

        # C. LOGIC PENGAMBILAN PERTANYAAN
        question_data = None
        
        if sub_cat == "Technical-GenAI":
            # Generate Teknis berdasarkan Job Role & Job Desc
            raw_q = llm.generate_technical_question(job_desc, str(history_q), job_role)
            question_data = {"question": raw_q, "answer_key": "Sesuai Job Desc", "type": "Technical"}
        else:
            # Ambil dari RAG (Sudah FIX Fetching-nya)
            question_data = rag.get_question(stage, sub_category=sub_cat)
            
            # Fallback
            if not question_data:
                question_data = rag.get_question(stage) # Random di stage
                if not question_data:
                    gen_q = llm.paraphrase_question(f"Tanyakan tentang {sub_cat}", job_role)
                    question_data = {"question": gen_q, "answer_key": "General", "type": "Generated"}

        # D. PARAPHRASE (Inject Context Role)
        final_q = question_data['question']
        if question_data.get("type") != "Technical":
            final_q = llm.paraphrase_question(final_q, job_role)
        
        history_q.append(final_q)
        
        print("\n" + "-"*50)
        print(f"📌 Topik: {sub_cat}")
        print_hr(final_q)
        full_transcript += f"HR ({sub_cat}): {final_q}\n"
        
        # E. INTERACTIVE FOLLOW-UP LOOP
        current_round = 0
        max_round = 1 if sub_cat not in ["Technical-GenAI", "Behavioral"] else 2 # Teknis/Behavioral gali lebih dalam
        no_followup = ["Compensation", "Availability", "Source"]
        
        while True:
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat: {ans}\n"
            
            if sub_cat not in no_followup and current_round < max_round:
                print("\n(System: HR menganalisis jawaban...)")
                check = llm.check_response_and_followup(final_q, ans, question_data.get('answer_key',''))
                
                if "[NEXT]" in check or "NEXT" in check:
                    break
                else:
                    print_hr(check)
                    full_transcript += f"HR Follow-up: {check}\n"
                    current_round += 1
            else:
                break

    # === FINAL REPORT ===
    print("\n\n" + "="*70)
    print(f"📊 MENYUSUN LAPORAN EVALUASI: {job_role.upper()}...")
    print("="*70)
    
    # Generate Report dengan Job Role
    report = llm.generate_final_report(user_name, job_role, job_desc, full_transcript)
    print("\n" + report)
    print("\n✅ Simulasi Selesai.")

if __name__ == "__main__":
    main()