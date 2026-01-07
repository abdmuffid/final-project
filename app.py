import os
import random
import markdown
import json  
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session  
from core.llm_evaluator import LLMEvaluator
from core.rag_engine import RAGEngine

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY") 

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.getcwd(), "flask_session")
app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_USE_SIGNER"] = True 
Session(app)

# Init Engine
llm = LLMEvaluator()
rag = RAGEngine()

# ==============================================================================
# ROUTES
# ==============================================================================

@app.route('/')
def index():
    session.clear() 
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_interview():
    """Setup Data & Sequence Interview"""
    data = request.json
    session['user_name'] = data.get('name')
    session['job_role'] = data.get('role')
    session['job_desc'] = data.get('jd')

    hour = datetime.now().hour
    if 5 <= hour < 11: time_context = "Selamat pagi"
    elif 11 <= hour < 15: time_context = "Selamat siang"
    elif 15 <= hour < 18: time_context = "Selamat sore"
    else: time_context = "Selamat malam"
    session['time_context'] = time_context
    
    # === MENYUSUN SKENARIO ===
    sequence = []
    
    # A. Opening 
    sequence.append({"stage": "Introductions", "sub": "Greeting", "source": "llm"})
    sequence.append({"stage": "Introductions", "sub": "General", "source": "rag"}) 
    
    # B. Broad - WAJIB
    broad_wajib = [
        {"sub": "Motivational"},
        {"sub": "Strengths/Weaknesses"},
        {"sub": "Company Knowledge"},
        {"sub": "Past Experience"},
        {"sub": "Career Plan"},
        {"sub": "Why Hire You"}
    ]
    for item in broad_wajib:
        sequence.append({"stage": "Broad", "sub": item["sub"], "source": "rag"})
    
    # B. Broad - OPSIONAL
    broad_opsional_pool = [
        "Career Change", "Leadership Style", "Self-Awareness",
        "Self-Development", "Onboarding Plan", "Unique Value",
        "Work Environment", "Work Style"
    ]
    num_opsional = random.randint(1, 3)
    selected_opsional = random.sample(broad_opsional_pool, k=min(num_opsional, len(broad_opsional_pool)))
    for sub in selected_opsional:
        sequence.append({"stage": "Broad", "sub": sub, "source": "rag"})
    
    # C. Position-Related
    position_related_pool = ["Behavioral", "Technical"]
    num_position = random.randint(1, 2)  
    selected_position = random.sample(position_related_pool, k=num_position)
    
    for topic in selected_position:
        if topic == "Behavioral":
            sequence.append({"stage": "Position-Related", "sub": "Behavioral", "source": "rag"})
        elif topic == "Technical":
            pass # Technical dihandle di section D (Hard Skill)
    
    # D. Technical Questions (LLM - Hard Skill)
    technical_types = ["Technical-STAR", "Technical-Concept", "Technical-Case"]
    for tech_type in technical_types:
        sequence.append({
            "stage": "Position-Related",
            "sub": tech_type,
            "source": "llm",
            "type": "Hard Skill"
        })
    
    # E. Stress Test (Conditional)
    sequence.append({"stage": "Position-Related", "sub": "StressTest", "source": "llm", "conditional": True})
    
    # F. Conclusion
    conclusion_items = [
        {"sub": "Availability", "source": "rag"},
        {"sub": "Compensation", "source": "rag"},
        {"sub": "SmartClosing", "source": "llm"},
        {"sub": "CandidateQuestions", "source": "llm"}
    ]
    for item in conclusion_items:
        sequence.append({"stage": "Conclusion", "sub": item["sub"], "source": item["source"]})
    
    # Simpan State Awal
    session['sequence'] = sequence
    session['current_idx'] = -1
    session['history_q'] = []
    session['history_ids'] = [] 
    session['full_transcript'] = ""
    session['followup_count'] = 0
    session['quality_scores'] = []
    session['red_flags'] = []
    session['last_resp'] = None
    session['current_q_data'] = None
    
    return jsonify({"status": "ready"})

@app.route('/chat')
def chat_page():
    return render_template('chat.html', name=session.get('user_name'), role=session.get('job_role'))

@app.route('/api/next_step', methods=['POST'])
def next_step():
    user_input = request.json.get('message')
    feedback_data = None
    
    # =========================================================================
    # STEP 1: PROSES JAWABAN USER (SCORING & LOGGING REASONING)
    # =========================================================================
    if user_input:
        session['full_transcript'] += f"Kandidat: {user_input}\n"
        session['last_resp'] = user_input
        
        curr_q = session.get('current_q_data')
        
        # Cek Intent di Closing
        if curr_q and curr_q.get('sub') == "CandidateQuestions":
            intent = llm.analyze_closing_intent(user_input)
            if "ASK" in intent:
                ans = llm.answer_user_question_contextual(user_input, session['job_role'])
                session['full_transcript'] += f"HR Jawab: {ans}\n"
                return jsonify({"type": "answer", "message": ans, "feedback": None})
            else:
                return jsonify({"type": "finish"})

        # Analisis Jawaban (Skip Greeting)
        if curr_q and curr_q.get('sub') != "Greeting":
            # Panggil fungsi analyzer
            analysis = llm.analyze_answer_quality(
                curr_q['question'], user_input, curr_q.get('key', ''), session['job_role'],
                q_category=curr_q.get('sub', 'General')
            )
            
            # --- [LOG DATA SKRIPSI - HASIL PENILAIAN] ---
            print(f"\n{'='*20} 📝 HASIL PENILAIAN 📝 {'='*20}")
            print(f"📌 Pertanyaan     : {curr_q['question']}")
            print(f"🔑 Kunci/Kriteria : {curr_q.get('key', 'General')}")
            print(f"🗣️  Jawaban User   : {user_input}")
            print(f"⭐ Skor Diberikan  : {analysis.get('quality_score')}/10")
            print(f"💡 Alasan (Reason) : {analysis.get('reasoning')}") # <--- INI YG KAMU CARI
            print(f"{'='*60}\n")
            # ---------------------------------------------
            
            scores = session.get('quality_scores', [])
            scores.append(analysis.get('quality_score', 5))
            session['quality_scores'] = scores
            
            if analysis.get('has_red_flags'):
                flags = session.get('red_flags', [])
                flags.extend(analysis.get('red_flag_types', []))
                session['red_flags'] = flags
            
            hint = None
            if analysis.get('quality_score', 5) < 5:
                hint = llm.generate_subtle_hint(curr_q['question'], user_input)

            feedback_data = {"score": analysis.get('quality_score', 5), "hint": hint}

            # Follow Up Logic
            max_fup = 2 if curr_q.get('type') in ["Hard Skill", "StressTest"] else 1
            fup_count = session.get('followup_count', 0)
            blacklist_fup = ['Greeting', 'General', 'SmartClosing', 'CandidateQuestions']
            
            if (analysis.get('needs_followup') and fup_count < max_fup and curr_q.get('sub') not in blacklist_fup):
                fup_q = analysis.get('followup_question')
                if not fup_q:
                    missing = analysis.get('missing_elements', [])
                    fup_q = llm.generate_adaptive_followup(curr_q['question'], user_input, missing, fup_count+1)
                
                session['followup_count'] = fup_count + 1
                session['full_transcript'] += f"HR Followup: {fup_q}\n"
                
                curr_q['question'] = fup_q
                session['current_q_data'] = curr_q
                
                return jsonify({"type": "question", "message": fup_q, "feedback": feedback_data})

    # =========================================================================
    # STEP 2: GENERATE PERTANYAAN BARU
    # =========================================================================
    idx = session.get('current_idx', -1) + 1
    sequence = session.get('sequence')
    
    if idx >= len(sequence): return jsonify({"type": "finish"})
    
    # Logic Conditional (Stress Test)
    while idx < len(sequence):
        q_item = sequence[idx]
        scores = session.get('quality_scores', [])
        avg_score = sum(scores)/len(scores) if scores else 7.0
        if q_item.get('conditional') and avg_score < 7:
            idx += 1; continue
        break
    
    if idx >= len(sequence): return jsonify({"type": "finish"})
    
    session['current_idx'] = idx
    session['followup_count'] = 0 
    q_item = sequence[idx]
    
    # Context
    job_role = session['job_role']
    job_desc = session['job_desc']
    history = session['history_q']
    last_resp = session.get('last_resp')
    
    scores = session.get('quality_scores', [])
    avg_score = sum(scores)/len(scores) if scores else 0
    difficulty = "medium"
    if avg_score >= 8: difficulty = "hard"
    elif avg_score >= 6: difficulty = "medium"
    else: difficulty = "easy"

    final_q = ""
    q_key = "General Logic" # Default key
    detected_skills = []    # Khusus Technical
    source = q_item.get("source", "rag")
 
    try:
        # A. LOGIC: PURE LLM
        if source == "llm":
            if q_item['sub'] == "Greeting":
                final_q = llm.generate_opening(session['user_name'], job_role, session.get('time_context', 'Selamat Pagi'))
                q_key = "Sapaan Ramah" # Placeholder biar ga error log

            elif q_item['sub'] == "SmartClosing":
                final_q = llm.generate_closing(job_role, session['user_name'], scores)
                q_key = "Penutup Profesional"

            elif q_item['sub'] == "CandidateQuestions":
                final_q = "Sekarang giliran Anda. Ada yang ingin ditanyakan tentang posisi ini atau perusahaan?"
                q_key = "Memberi kesempatan bertanya"

            elif q_item['sub'] == "Technical-STAR":
                # [MODIFIKASI PENTING]: Handle JSON Return
                tech_data = llm.generate_technical_question_starmethod(job_desc, str(history), job_role, last_resp, difficulty)
                final_q = tech_data['question_text']
                q_key = tech_data.get('expected_criteria', 'STAR Criteria') # Key Dinamis dari LLM
                detected_skills = tech_data.get('detected_skills', [])      # Skill yang dideteksi

            elif q_item['sub'] == "Technical-Concept":
                raw = f"Tanyakan konsep mendalam skill JD. Level: {difficulty}"
                final_q = llm.paraphrase_question_contextual(raw, job_role, last_resp)
                q_key = "Pemahaman Konsep Teoritis"

            elif q_item['sub'] == "Technical-Case":
                # [MODIFIKASI PENTING]: Handle JSON Return (Hard)
                tech_data = llm.generate_technical_question_starmethod(job_desc, str(history), job_role, last_resp, "hard")
                final_q = tech_data['question_text']
                q_key = tech_data.get('expected_criteria', 'Troubleshooting Logic')
                detected_skills = tech_data.get('detected_skills', [])

            elif q_item['sub'] == "StressTest":
                final_q = llm.generate_stress_test_question(job_role, job_desc, last_resp)
                q_key = "Ketenangan & Problem Solving under Pressure"

        # B. LOGIC: RAG (DATASET)
        else:
            excluded_ids = session.get('history_ids', [])
            rag_result = rag.get_question(q_item['stage'], q_item['sub'], excluded_ids=excluded_ids)
            
            if rag_result:
                base_q = rag_result['question']
                # Paraphrase
                final_q = llm.paraphrase_question_contextual(base_q, job_role, last_resp)
                
                q_key = rag_result.get('answer_key', 'General')
                q_item['original_q'] = base_q # Simpan Base Q untuk Log Terminal
                
                excluded_ids.append(rag_result['id'])
                session['history_ids'] = excluded_ids
            else:
                fallback_prompt = f"Tanyakan tentang {q_item['sub']} untuk posisi {job_role}"
                final_q = llm.paraphrase_question_contextual(fallback_prompt, job_role, last_resp)

    except Exception as e:
        print(f"Error Gen: {e}")
        final_q = "Bisa ceritakan lebih lanjut pengalaman Anda di bidang ini?"

    history.append(final_q)
    session['history_q'] = history
    session['full_transcript'] += f"HR: {final_q}\n"
    
    # Simpan Context Pertanyaan Aktif (PENTING untuk Penilaian step berikutnya)
    q_data = {
        "question": final_q,
        "key": q_key, # Kunci jawaban (Generated Criteria / DB Key)
        "sub": q_item['sub'],
        "type": q_item.get('type', 'General')
    }
    session['current_q_data'] = q_data
    
    # --- [LOG DATA SKRIPSI - GENERASI PERTANYAAN] ---
    print(f"\n{'='*65}")
    print(f"🚀 GENERASI PERTANYAAN BARU ({q_item.get('sub')})")
    
    if source == "llm" and "Technical" in q_item['sub']:
        print(f"🤖 MODE         : Pure LLM Generation (Technical)")
        print(f"🛠️  SKILL READ   : {detected_skills}")  # <--- DATA SKILL
        print(f"🎯 KRITERIA IDL : {q_key}")            # <--- DATA KUNCI JAWABAN DINAMIS
    elif source == "rag":
        print(f"📚 MODE         : RAG (Dataset)")
        print(f"📄 BASE Q (DB)  : {q_item.get('original_q', 'N/A')}") # <--- PERTANYAAN ASLI DB
        print(f"🔑 ANSWER KEY   : {q_key}")            # <--- KUNCI JAWABAN DB
    else:
        print(f"🗣️  MODE         : Conversational (Greeting/Closing)")
    
    print(f"📝 FINAL PROMPT : {final_q}")
    print(f"{'='*65}\n")
    # ------------------------------------------------
    
    return jsonify({
        "type": "question",
        "message": final_q,
        "difficulty": difficulty.upper() if q_item.get('type') == 'Hard Skill' else None,
        "is_info": (q_item['sub'] == "SmartClosing"),
        "feedback": feedback_data
    })

@app.route('/report')
def report_page():
    scores = session.get('quality_scores', [])
    flags = session.get('red_flags', [])
    transcript = session.get('full_transcript', "")
    
    if not transcript: transcript = "(User batal.)"

    raw_report = llm.generate_final_report(
        session['user_name'], session['job_role'], session['job_desc'], transcript, scores, flags
    )
    
    html_report = markdown.markdown(raw_report, extensions=['extra', 'nl2br'])
    return render_template('report.html', report_content=html_report)

if __name__ == '__main__':
    if not os.path.exists("flask_session"):
        os.makedirs("flask_session")
    app.run(debug=True, port=5000)