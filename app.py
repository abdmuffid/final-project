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
    session['job_description'] = data.get('jd')

    hour = datetime.now().hour
    if 5 <= hour < 11: time_context = "Selamat pagi"
    elif 11 <= hour < 15: time_context = "Selamat siang"
    elif 15 <= hour < 18: time_context = "Selamat sore"
    else: time_context = "Selamat malam"
    session['time_context'] = time_context
    
    # === MENYUSUN SKENARIO ===
    sequence = []
    
    # A. Opening 
    sequence.append({"stage": "Introductions", "sub_category": "Greeting", "source": "llm"})
    sequence.append({"stage": "Introductions", "sub_category": "General", "source": "rag"}) 
    
    # B. Broad - WAJIB
    broad_wajib = [
        {"sub_category": "Motivational"},
        {"sub_category": "Strengths/Weaknesses"},
        {"sub_category": "Company Knowledge"},
        {"sub_category": "Past Experience"},
        {"sub_category": "Career Plan"},
        {"sub_category": "Why Hire You"}
    ]
    for item in broad_wajib:
        sequence.append({"stage": "Broad", "sub_category": item["sub_category"], "source": "rag"})
    
    # B. Broad - OPSIONAL
    broad_opsional_pool = [
        "Career Change", "Leadership Style", "Self-Awareness",
        "Self-Development", "Onboarding Plan", "Unique Value",
        "Work Environment", "Work Style"
    ]
    num_opsional = random.randint(1, 3)
    selected_opsional = random.sample(broad_opsional_pool, k=min(num_opsional, len(broad_opsional_pool)))
    for sub_category in selected_opsional:
        sequence.append({"stage": "Broad", "sub_category": sub_category, "source": "rag"})
    
    # C. Position-Related
    position_related_pool = ["Behavioral", "Technical"]
    num_position = random.randint(1, 2)  
    selected_position = random.sample(position_related_pool, k=num_position)
    
    for topic in selected_position:
        if topic == "Behavioral":
            sequence.append({"stage": "Position-Related", "sub_category": "Behavioral", "source": "rag"})
        elif topic == "Technical":
            pass 
    
    # D. Technical Questions (LLM - Hard Skill)
    technical_types = ["Technical-STAR", "Technical-Concept", "Technical-Case"]
    for tech_type in technical_types:
        sequence.append({
            "stage": "Position-Related",
            "sub_category": tech_type,
            "source": "llm",
            "type": "Hard Skill"
        })
    
    # E. Stress Test (Conditional)
    sequence.append({"stage": "Position-Related", "sub_category": "StressTest", "source": "llm", "conditional": True})
    
    # F. Conclusion
    conclusion_items = [
        {"sub_category": "Availability", "source": "rag"},
        {"sub_category": "Compensation", "source": "rag"},
        {"sub_category": "SmartClosing", "source": "llm"},
        {"sub_category": "CandidateQuestions", "source": "llm"}
    ]
    for item in conclusion_items:
        sequence.append({"stage": "Conclusion", "sub_category": item["sub_category"], "source": item["source"]})
    
    # Simpan State Awal
    session['sequence'] = sequence
    session['sequence_index'] = -1
    session['history_questions'] = []
    session['used_rag_ids'] = [] 
    session['full_transcript'] = ""
    session['followup_count'] = 0
    session['quality_scores'] = []
    session['red_flags'] = []
    session['last_user_response'] = None
    session['current_question_context'] = None
    
    return jsonify({"status": "ready"})

@app.route('/chat')
def chat_page():
    return render_template('chat.html', name=session.get('user_name'), role=session.get('job_role'))

@app.route('/api/next_step', methods=['POST'])
def next_step():
    user_message = request.json.get('message')
    feedback_data = None
    
    # =========================================================================
    # STEP 1: PROSES JAWABAN USER (SCORING & LOGGING REASONING)
    # =========================================================================
    if user_message:
        session['full_transcript'] += f"Kandidat: {user_message}\n"
        session['last_user_response'] = user_message
        
        current_context = session.get('current_question_context')
        
        # Cek Intent di Closing
        if current_context and current_context.get('sub_category') == "CandidateQuestions":
            intent = llm.analyze_closing_intent(user_message)
            if "ASK" in intent:
                hr_response = llm.answer_user_question_contextual(user_message, session['job_role'])
                session['full_transcript'] += f"HR Jawab: {hr_response}\n"
                return jsonify({"type": "answer", "message": hr_response, "feedback": None})
            else:
                return jsonify({"type": "finish"})

        # Analisis Jawaban (Skip Greeting)
        if current_context and current_context.get('sub_category') != "Greeting":
            # Panggil fungsi analyzer
            analysis = llm.analyze_answer_quality(
                current_context['question'], user_message, current_context.get('key', ''), session['job_role'],
                q_category=current_context.get('sub_category', 'General')
            )
            
            # --- [LOG DATA SKRIPSI - HASIL PENILAIAN] ---
            print(f"\n{'='*20} 📝 HASIL PENILAIAN 📝 {'='*20}")
            print(f"📌 Pertanyaan     : {current_context['question']}")
            print(f"🔑 Kunci/Kriteria : {current_context.get('key', 'General')}")
            print(f"🗣️  Jawaban User   : {user_message}")
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
                hint = llm.generate_subtle_hint(current_context['question'], user_message)

            feedback_data = {"score": analysis.get('quality_score', 5), "hint": hint}

            # Follow Up Logic
            maximum_followup = 2 if current_context.get('type') in ["Hard Skill", "StressTest"] else 1
            followup_count = session.get('followup_count', 0)
            blacklist_fup = ['Greeting', 'General', 'SmartClosing', 'CandidateQuestions']
            
            if (analysis.get('needs_followup') and followup_count < maximum_followup and current_context.get('sub_category') not in blacklist_fup):
                followup_question = analysis.get('followup_question')
                if not followup_question:
                    missing = analysis.get('missing_elements', [])
                    followup_question = llm.generate_adaptive_followup(current_context['question'], user_message, missing, followup_count+1)
                
                session['followup_count'] = followup_count + 1
                session['full_transcript'] += f"HR Followup: {followup_question}\n"
                
                current_context['question'] = followup_question
                session['current_question_context'] = current_context
                
                return jsonify({"type": "question", "message": followup_question, "feedback": feedback_data})

    # =========================================================================
    # STEP 2: GENERATE PERTANYAAN BARU
    # =========================================================================
    seq_index = session.get('sequence_index', -1) + 1
    sequence = session.get('sequence')
    
    if seq_index >= len(sequence): return jsonify({"type": "finish"})
    
    # Logic Conditional (Stress Test)
    while seq_index < len(sequence):
        stage_config = sequence[seq_index]
        scores = session.get('quality_scores', [])
        average_quality_score = sum(scores)/len(scores) if scores else 7.0
        if stage_config.get('conditional') and average_quality_score < 7:
            seq_index += 1; continue
        break
    
    if seq_index >= len(sequence): return jsonify({"type": "finish"})
    
    session['sequence_index'] = seq_index
    session['followup_count'] = 0 
    stage_config = sequence[seq_index]
    
    # Context
    job_role = session['job_role']
    job_description = session['job_description']
    history = session['history_questions']
    last_user_response = session.get('last_user_response')
    
    scores = session.get('quality_scores', [])
    average_quality_score = sum(scores)/len(scores) if scores else 0
    difficulty = "medium"
    if average_quality_score >= 8: difficulty = "hard"
    elif average_quality_score >= 6: difficulty = "medium"
    else: difficulty = "easy"

    final_question_prompt = ""
    expected_answer_criteria = "General Logic" # Default key
    extracted_skills = []    # Khusus Technical
    source = stage_config.get("source", "rag")
 
    try:
        # A. LOGIC: PURE LLM
        if source == "llm":
            if stage_config['sub_category'] == "Greeting":
                final_question_prompt = llm.generate_opening(session['user_name'], job_role, session.get('time_context', 'Selamat Pagi'))
                expected_answer_criteria = "Sapaan Ramah" # Placeholder biar ga error log

            elif stage_config['sub_category'] == "SmartClosing":
                final_question_prompt = llm.generate_closing(job_role, session['user_name'], scores)
                expected_answer_criteria = "Penutup Profesional"

            elif stage_config['sub_category'] == "CandidateQuestions":
                final_question_prompt = "Sekarang giliran Anda. Ada yang ingin ditanyakan tentang posisi ini atau perusahaan?"
                expected_answer_criteria = "Memberi kesempatan bertanya"

            elif stage_config['sub_category'] == "Technical-STAR":
                # [MODIFIKASI PENTING]: Handle JSON Return
                technical_question_data = llm.generate_technical_question_starmethod(job_description, str(history), job_role, last_user_response, difficulty)
                final_question_prompt = technical_question_data['question_text']
                expected_answer_criteria = technical_question_data.get('expected_criteria', 'STAR Criteria') # Key Dinamis dari LLM
                extracted_skills = technical_question_data.get('extracted_skills', [])      # Skill yang dideteksi

            elif stage_config['sub_category'] == "Technical-Concept":
                raw = f"Tanyakan konsep mendalam skill JD. Level: {difficulty}"
                final_question_prompt = llm.paraphrase_question_contextual(raw, job_role, last_user_response)
                expected_answer_criteria = "Pemahaman Konsep Teoritis"

            elif stage_config['sub_category'] == "Technical-Case":
                # [MODIFIKASI PENTING]: Handle JSON Return (Hard)
                technical_question_data = llm.generate_technical_question_starmethod(job_description, str(history), job_role, last_user_response, "hard")
                final_question_prompt = technical_question_data['question_text']
                expected_answer_criteria = technical_question_data.get('expected_criteria', 'Troubleshooting Logic')
                extracted_skills = technical_question_data.get('extracted_skills', [])

            elif stage_config['sub_category'] == "StressTest":
                final_question_prompt = llm.generate_stress_test_question(job_role, job_description, last_user_response)
                expected_answer_criteria = "Ketenangan & Problem Solving under Pressure"

        # B. LOGIC: RAG (DATASET)
        else:
            excluded_ids = session.get('used_rag_ids', [])
            rag_result = rag.get_question(stage_config['stage'], stage_config['sub_category'], excluded_ids=excluded_ids)
            
            if rag_result:
                original_rag_question = rag_result['question']
                # Paraphrase
                final_question_prompt = llm.paraphrase_question_contextual(original_rag_question, job_role, last_user_response)
                
                expected_answer_criteria = rag_result.get('answer_key', 'General')
                stage_config['original_q'] = original_rag_question # Simpan Base Q untuk Log Terminal
                
                excluded_ids.append(rag_result['id'])
                session['used_rag_ids'] = excluded_ids
            else:
                fallback_prompt = f"Tanyakan tentang {stage_config['sub_category']} untuk posisi {job_role}"
                final_question_prompt = llm.paraphrase_question_contextual(fallback_prompt, job_role, last_user_response)

    except Exception as e:
        print(f"Error Gen: {e}")
        final_question_prompt = "Bisa ceritakan lebih lanjut pengalaman Anda di bidang ini?"

    history.append(final_question_prompt)
    session['history_questions'] = history
    session['full_transcript'] += f"HR: {final_question_prompt}\n"
    
    # Simpan Context Pertanyaan Aktif (PENTING untuk Penilaian step berikutnya)
    q_data = {
        "question": final_question_prompt,
        "key": expected_answer_criteria, # Kunci jawaban (Generated Criteria / DB Key)
        "sub_category": stage_config['sub_category'],
        "type": stage_config.get('type', 'General')
    }
    session['current_question_context'] = q_data
    
    # --- [LOG DATA SKRIPSI - GENERASI PERTANYAAN] ---
    print(f"\n{'='*65}")
    print(f"🚀 GENERASI PERTANYAAN BARU ({stage_config.get('sub_category')})")
    
    if source == "llm" and "Technical" in stage_config['sub_category']:
        print(f"🤖 MODE         : Pure LLM Generation (Technical)")
        print(f"🛠️  SKILL READ   : {extracted_skills}")  # <--- DATA SKILL
        print(f"🎯 KRITERIA IDL : {expected_answer_criteria}")            # <--- DATA KUNCI JAWABAN DINAMIS
    elif source == "rag":
        print(f"📚 MODE         : RAG (Dataset)")
        print(f"📄 BASE Q (DB)  : {stage_config.get('original_q', 'N/A')}") # <--- PERTANYAAN ASLI DB
        print(f"🔑 ANSWER KEY   : {expected_answer_criteria}")            # <--- KUNCI JAWABAN DB
    else:
        print(f"🗣️  MODE         : Conversational (Greeting/Closing)")
    
    print(f"📝 FINAL PROMPT : {final_question_prompt}")
    print(f"{'='*65}\n")
    # ------------------------------------------------
    
    return jsonify({
        "type": "question",
        "message": final_question_prompt,
        "difficulty": difficulty.upper() if stage_config.get('type') == 'Hard Skill' else None,
        "is_info": (stage_config['sub_category'] == "SmartClosing"),
        "feedback": feedback_data
    })

@app.route('/report')
def report_page():
    scores = session.get('quality_scores', [])
    flags = session.get('red_flags', [])
    transcript = session.get('full_transcript', "")
    
    if not transcript: transcript = "(User batal.)"

    raw_report = llm.generate_final_report(
        session['user_name'], session['job_role'], session['job_description'], transcript, scores, flags
    )
    
    html_report = markdown.markdown(raw_report, extensions=['extra', 'nl2br'])
    return render_template('report.html', report_content=html_report)

if __name__ == '__main__':
    if not os.path.exists("flask_session"):
        os.makedirs("flask_session")
    app.run(debug=True, port=5000)