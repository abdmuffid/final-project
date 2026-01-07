import time
import sys
import os
import random
import json
from datetime import datetime
from core.rag_engine import RAGEngine
from core.llm_evaluator import LLMEvaluator

def get_time_greeting():
    """Menentukan salam berdasarkan jam"""
    hour = datetime.now().hour
    if 4 <= hour < 11:
        return "Selamat Pagi"
    elif 11 <= hour < 15:
        return "Selamat Siang"
    elif 15 <= hour < 18:
        return "Selamat Sore"
    else:
        return "Selamat Malam"

def print_hr(text, typing_speed=0.01):
    """Efek mengetik untuk HRD (Tanpa Warna)"""
    print(f"\n🤖 HRD: ", end="")
    clean_text = text.replace('"', '').strip()
    for char in clean_text:
        print(char, end='', flush=True)
        time.sleep(typing_speed)
    print()

def print_system(text):
    """Pesan Sistem (Tanpa Warna)"""
    print(f"\n⚙️  SISTEM: {text}")

def print_progress(current, total, current_topic=""):
    """Progress bar sederhana"""
    percent = int((current / total) * 100)
    bar_length = 20
    filled_length = int(bar_length * current // total)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    
    print(f"\n⏳ Progress: |{bar}| {percent}% Selesai")
    if current_topic:
        print(f"📌 Topik Saat Ini: {current_topic}")

def print_stage_transition(stage_name, description=""):
    """Transisi Tahapan Interview"""
    print(f"\n{'='*60}")
    print(f"🎯 MEMASUKI TAHAP: {stage_name.upper()}")
    if description:
        print(f"   {description}")
    print(f"{'='*60}\n")
    time.sleep(1)

def print_real_time_feedback(quality_score):
    """Indikator Feedback Real-time Sederhana"""
    msg = ""
    if quality_score >= 8:
        msg = "🌟 Jawaban Excellent!"
    elif quality_score >= 6:
        msg = "👍 Jawaban Bagus."
    else:
        msg = "💭 Jawaban Perlu Lebih Detail."
    
    print(f"   -> Feedback AI: {msg} (Score Estimasi: {quality_score}/10)")

def main():
    # =========================================================================
    # PHASE 1: INITIALIZATION & SETUP
    # =========================================================================
    
    rag = RAGEngine()
    llm = LLMEvaluator() 
    
    # Bersihkan layar
    os.system('cls' if os.name == 'nt' else 'clear') 
    
    print("="*70)
    print("      AI INTERVIEW SIMULATOR - ULTIMATE EDITION (LOGIC ONLY)")
    print("      Fitur: Adaptive Difficulty, STAR Method, Red Flag, Stress Test")
    print("="*70)
    
    # =========================================================================
    # PHASE 2: USER INPUT & ROLE SELECTION
    # =========================================================================
    
    print("\n📝 SETUP KANDIDAT")
    user_name = input("👤 Nama Lengkap: ")
    
    print("\n💼 PILIH POSISI YANG DILAMAR:")
    roles = [
        "Data Analyst / Scientist",
        "Software Engineer (Backend/Frontend)",
        "UI/UX Designer",
        "Digital Marketing / Social Media",
        "Product Manager",
        "Business Analyst",
        "DevOps Engineer"
    ]
    
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")
    print(f"  {len(roles)+1}. Lainnya (Ketik Manual)")
    
    role_choice = input("\n👉 Pilih Nomor: ")
    job_role = "Kandidat Umum"
    
    try:
        idx = int(role_choice) - 1
        if 0 <= idx < len(roles):
            job_role = roles[idx]
        else:
            job_role = input("👉 Tulis posisi spesifik: ")
    except:
        job_role = input("👉 Tulis posisi spesifik: ")
    
    print(f"\n✅ Mode Interview: {job_role}")
    
    print("\n📄 Job Description (Paste di sini, tekan Enter 2x untuk selesai):")
    print("-" * 50)
    
    job_desc_lines = []
    while True:
        line = input()
        if line == "" and len(job_desc_lines) > 0:
            break
        job_desc_lines.append(line)
    
    job_desc = "\n".join(job_desc_lines)
    
    print_system("Sedang menganalisis Job Description...")
    print_system("Merancang alur interview yang personalized...")
    time.sleep(1)
    
    # =========================================================================
    # PHASE 3: INTERVIEW SEQUENCE PLANNING
    # =========================================================================
    
    full_transcript = f"=== INTERVIEW TRANSCRIPT ===\nNama: {user_name}\nPosisi: {job_role}\n\nJob Description:\n{job_desc}\n\n=== PERCAKAPAN ===\n\n"
    history_q = []
    interview_sequence = []
    last_topic = ""
    
    # A. Opening & Ice Breaker
    interview_sequence.append({
        "stage": "Introductions", "sub_cat": "Greeting", "type": "Opening", "description": "Pembukaan"
    })
    interview_sequence.append({
        "stage": "Introductions", "sub_cat": "IceBreaker", "type": "WarmUp", "description": "Ice Breaker"
    })
    
    # B. Broad / General Questions (3 questions)
    broad_pool = [
        {"topic": "Motivational", "desc": "Motivasi"},
        {"topic": "Company Knowledge", "desc": "Riset Perusahaan"},
        {"topic": "Career Plan", "desc": "Rencana Karir"},
        {"topic": "Self Awareness", "desc": "Refleksi Diri"},
        {"topic": "Work Style", "desc": "Gaya Kerja"},
    ]
    for item in random.sample(broad_pool, 3):
        interview_sequence.append({
            "stage": "Broad", "sub_cat": item["topic"], "type": "General", "description": item["desc"]
        })
    
    # C. Core Position-Related (Alternating Technical & Behavioral)
    # Pattern: T-B-T-B-T-B
    core_questions = [
        {"type": "Technical-STAR", "desc": "Pengalaman Teknis (STAR)"},
        {"type": "Behavioral", "sub": "Teamwork", "desc": "Kerjasama Tim"},
        {"type": "Technical-Concept", "desc": "Pemahaman Konsep (Deep Dive)"},
        {"type": "Behavioral", "sub": "Adaptability", "desc": "Adaptabilitas"},
        {"type": "Technical-Case", "desc": "Troubleshooting / Studi Kasus"},
        {"type": "Behavioral", "sub": "Pressure", "desc": "Menangani Tekanan"},
    ]
    
    for item in core_questions:
        if item["type"].startswith("Technical"):
            interview_sequence.append({
                "stage": "Position-Related", "sub_cat": item["type"], "type": "Hard Skill", "description": item["desc"]
            })
        else:
            interview_sequence.append({
                "stage": "Position-Related", "sub_cat": "Behavioral", "behavioral_focus": item["sub"], "type": "Soft Skill", "description": item["desc"]
            })
    
    # D. Stress Test (Conditional)
    interview_sequence.append({
        "stage": "Advanced", "sub_cat": "StressTest", "type": "Challenge", "description": "Stress Test Scenario", "conditional": True
    })
    
    # E. Closing
    interview_sequence.append({
        "stage": "Conclusion", "sub_cat": "SmartClosing", "type": "Closing", "description": "Penutup"
    })
    interview_sequence.append({
        "stage": "Conclusion", "sub_cat": "CandidateQuestions", "type": "Q&A", "description": "Tanya Jawab Kandidat"
    })
    
    total_q = len(interview_sequence)
    last_participant_response = None
    
    # =========================================================================
    # PHASE 4: EXECUTE INTERVIEW (MAIN LOOP)
    # =========================================================================
    
    question_count = 0
    stage_tracker = None
    
    for idx, q_item in enumerate(interview_sequence, 1):
        
        # Cek Kondisional (Stress Test hanya jika nilai bagus)
        if q_item.get("conditional", False):
            # Hitung rata-rata skor saat ini
            current_avg = sum(llm.quality_scores) / len(llm.quality_scores) if llm.quality_scores else 0
            if current_avg < 7:
                # Skip jika performa kurang
                continue
        
        question_count += 1
        
        # Transisi Stage
        current_stage = q_item["stage"]
        if stage_tracker != current_stage:
            print_stage_transition(current_stage)
            stage_tracker = current_stage
        
        # Tampilkan Progress
        print_progress(question_count, total_q, q_item.get("description", ""))
        
        # Determine Difficulty dynamically
        curr_difficulty = llm.get_adaptive_difficulty()
        
        # --- HANDLERS PERTANYAAN ---
        
        # 1. GREETING
        if q_item["sub_cat"] == "Greeting":
            time_greeting = get_time_greeting()
            opening = llm.generate_opening_ultimate(user_name, job_role, time_greeting)
            print_hr(opening)
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"[OPENING]\nHR: {opening}\nKandidat: {ans}\n\n"
            last_participant_response = ans
            continue
            
        # 2. ICE BREAKER
        if q_item["sub_cat"] == "IceBreaker":
            icebreaker = llm.generate_icebreaker(user_name, job_role)
            print_hr(icebreaker)
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"[ICE BREAKER]\nHR: {icebreaker}\nKandidat: {ans}\n\n"
            last_participant_response = ans
            continue
            
        # 3. SMART CLOSING (Tanpa input, cuma statement HR)
        if q_item["sub_cat"] == "SmartClosing":
            closing = llm.generate_smart_closing(job_role)
            print_hr(closing)
            full_transcript += f"HR Closing: {closing}\n"
            continue
            
        # 4. CANDIDATE QUESTIONS
        if q_item["sub_cat"] == "CandidateQuestions":
            print("(Silakan ajukan pertanyaan Anda...)")
            user_q = input(f"🗣️  {user_name}: ")
            full_transcript += f"[CANDIDATE QUESTION]\n{user_name}: {user_q}\n"
            
            # Analisis Intensi (Ask vs No)
            intent = llm.analyze_closing_intent(user_q)
            
            if "ASK" in intent:
                print_system("HR merumuskan jawaban jujur & kontekstual...")
                hr_ans = llm.answer_user_question_contextual(user_q, job_role)
                print_hr(hr_ans)
                full_transcript += f"HR: {hr_ans}\n\n"
            else:
                print_hr("Baik, terima kasih sudah meluangkan waktu hari ini!")
            continue
            
        # --- GENERATOR LOGIC ---
        
        question_data = None
        final_q = ""
        
        # A. Stress Test
        if q_item["sub_cat"] == "StressTest":
            print_system("🔥 Performa Tinggi Terdeteksi. Mengaktifkan STRESS TEST MODE!")
            time.sleep(1)
            final_q = llm.generate_stress_test_question(job_role, job_desc, last_participant_response)
            question_data = {"question": final_q, "answer_key": "Handling Pressure", "type": "StressTest"}
            
        # B. Technical STAR (Combo)
        elif q_item["sub_cat"] == "Technical-STAR" or q_item["sub_cat"] == "Technical-Combo":
            print_system(f"Difficulty Level: {curr_difficulty.upper()}")
            final_q = llm.generate_technical_question_starmethod(
                job_desc, str(history_q), job_role, last_participant_response, curr_difficulty
            )
            question_data = {"question": final_q, "answer_key": "STAR Method", "type": "Technical"}
            
        # C. Technical Concept
        elif q_item["sub_cat"] == "Technical-Concept":
            # Menggunakan paraphrase contextual untuk variasi konsep
            gen = llm.paraphrase_question_contextual(f"Tanyakan konsep mendalam/teori tentang skill di JD", job_role, last_participant_response)
            question_data = {"question": gen, "answer_key": "Deep Concept", "type": "Technical"}
            final_q = gen

        # D. Technical Case
        elif q_item["sub_cat"] == "Technical-Case":
            # Case study biasanya level Hard
            gen = llm.generate_technical_question_starmethod(job_desc, str(history_q), job_role, last_participant_response, "hard")
            question_data = {"question": gen, "answer_key": "Troubleshooting", "type": "Technical"}
            final_q = gen
            
        # E. Behavioral
        elif q_item["sub_cat"] == "Behavioral":
            behavioral_focus = q_item.get("behavioral_focus", "Teamwork")
            final_q = llm.generate_behavioral_question_situational(
                behavioral_focus, job_role, str(history_q), last_participant_response
            )
            question_data = {"question": final_q, "answer_key": "Behavioral STAR", "type": "Behavioral"}
            
        # F. General / RAG
        else:
            # Coba ambil dari database RAG
            q_rag_data = rag.get_question(q_item["stage"], sub_category=q_item["sub_cat"])
            
            if q_rag_data:
                # Paraphrase hasil RAG biar ada bridging
                q_text = q_rag_data['question']
                final_q = llm.paraphrase_question_contextual(q_text, job_role, last_participant_response)
                question_data = {"question": final_q, "answer_key": q_rag_data.get('answer_key', 'General'), "type": "RAG"}
            else:
                # Generate manual
                final_q = llm.paraphrase_question_contextual(
                    f"Tanyakan tentang {q_item['sub_cat']}", job_role, last_participant_response
                )
                question_data = {"question": final_q, "answer_key": "General", "type": "Generated"}
        
        # Simpan Pertanyaan ke History
        if not final_q: final_q = question_data["question"]
        history_q.append(final_q)
        last_topic = q_item.get("description", q_item["sub_cat"])
        
        # Tampilkan Pertanyaan
        print_hr(final_q)
        full_transcript += f"[{q_item['description'].upper()}]\nHR: {final_q}\n"
        
        # =====================================================================
        # FOLLOW-UP LOOP (THE BRAIN)
        # =====================================================================
        
        follow_up_round = 0
        max_follow_ups = 2 if q_item.get("type") in ["Hard Skill", "Soft Skill"] else 1
        skip_followup_topics = ["Availability", "Source", "Compensation"]
        
        last_answer_in_loop = ""
        
        while True:
            ans = input(f"🗣️  {user_name}: ")
            full_transcript += f"Kandidat: {ans}\n"
            last_answer_in_loop = ans
            
            # Cek apakah perlu follow-up
            if q_item["sub_cat"] in skip_followup_topics or follow_up_round >= max_follow_ups:
                break
            
            print_system("Analisis AI: Scoring & Red Flags Check...")
            
            # Panggil Analyzer (JSON)
            analysis = llm.analyze_answer_quality(
                final_q, ans, question_data.get("answer_key", ""), job_role
            )
            
            # Real-time Feedback (Visual)
            quality_score = analysis.get("quality_score", 5)
            print_real_time_feedback(quality_score)
            
            # Fitur Hint (Coaching)
            if quality_score < 4:
                hint = llm.generate_subtle_hint(final_q, ans)
                print(f"   💡 HINT: {hint}")
            
            # Cek Logic Follow-up
            if not analysis.get("needs_followup", False):
                break # Jawaban sudah bagus
            
            # Generate Adaptive Follow-up
            missing = analysis.get("missing_elements", [])
            
            if analysis.get("followup_question"):
                fup_q = analysis["followup_question"]
            else:
                fup_q = llm.generate_adaptive_followup(final_q, ans, missing, follow_up_round + 1)
            
            print_hr(fup_q)
            full_transcript += f"HR Follow-up: {fup_q}\n"
            
            final_q = fup_q # Update konteks
            follow_up_round += 1
            
        # Update jawaban terakhir untuk bridging ronde berikutnya
        if last_answer_in_loop:
            last_participant_response = last_answer_in_loop
            
        # Cek Break
        needs_break, break_msg = llm.detect_need_for_break(len(full_transcript), "stable")
        if needs_break:
            print_hr(break_msg)
            time.sleep(2)
            
        print() # Spacer

    # =========================================================================
    # PHASE 5: GENERATE ULTIMATE REPORT
    # =========================================================================
    
    print_stage_transition("GENERATING COMPREHENSIVE REPORT", "Menganalisis seluruh transkrip...")
    print_system("⏳ Proses analisis mendalam (10-15 detik)...")
    
    report = llm.generate_final_report_ultimate(
        user_name,
        job_role,
        job_desc,
        full_transcript
        # Note: quality_scores & red_flags sudah tersimpan di dalam instance 'llm'
    )
    
    # Tampilkan Report
    os.system('cls' if os.name == 'nt' else 'clear') 
    
    print("="*70)
    print("                 📊 EVALUATION REPORT")
    print("="*70)
    
    print(report)
    
    # =========================================================================
    # PHASE 6: POST-INTERVIEW
    # =========================================================================
    
    print(f"\n{'='*70}")
    print("✅ SIMULASI INTERVIEW SELESAI!")
    print(f"{'='*70}\n")
    
    print("📈 STATISTIK PERFORMA:")
    if llm.quality_scores:
        avg_quality = sum(llm.quality_scores) / len(llm.quality_scores)
        print(f"   • Rata-rata Skor Kualitas: {avg_quality:.1f}/10")
        print(f"   • Total Red Flags: {len(llm.red_flags)}")
    
    # Save Report
    save_opt = input("\n💾 Simpan report ke file? (y/n): ")
    if save_opt.lower() == 'y':
        filename = f"report_{user_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report disimpan ke: {filename}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interview dibatalkan oleh user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")