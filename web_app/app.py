from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import random
from pathlib import Path
from gtts import gTTS
import io

app = Flask(__name__)

# 데이터 파일 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), 'static', 'data')
WORDS_FILE = os.path.join(DATA_DIR, 'english_words.json')

# 세션 데이터 저장소 (실제로는 데이터베이스 사용 권장)
sessions = {}

def load_words():
    """JSON에서 단어 로드"""
    if os.path.exists(WORDS_FILE):
        try:
            with open(WORDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [{"word": "Apple", "meaning": "사과", "example": "I ate an apple.", "category": "기초"}]

def save_words(words):
    """단어 JSON에 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['GET'])
def api_init():
    """초기화 및 9개 단어 세트 생성"""
    words = load_words()
    categories = sorted(list(set(w.get('category', '기타') for w in words)))
    
    # 세션 ID 생성
    session_id = request.args.get('session_id', str(random.randint(100000, 999999)))
    
    # 전체 단어로 9개 세트 생성
    all_nine_words = []
    for _ in range(3):
        if words:
            all_nine_words.extend(random.sample(words, min(3, len(words))))
    
    sessions[session_id] = {
        'all_nine_words': all_nine_words,
        'repeat_count': 0,
        'correct_count': 0,
        'total_attempts': 0,
        'current_mode': 'Words'
    }
    
    current_set = all_nine_words[0:3]
    
    return jsonify({
        'session_id': session_id,
        'categories': categories,
        'current_set': current_set,
        'repeat_count': 0,
        'max_repeats': 3
    })

@app.route('/api/load-words-sheet', methods=['POST'])
def load_words_sheet():
    """Words 탭 로드"""
    session_id = request.json.get('session_id')
    words = load_words()
    
    all_nine_words = []
    for _ in range(3):
        if words:
            all_nine_words.extend(random.sample(words, min(3, len(words))))
    
    if session_id in sessions:
        sessions[session_id]['all_nine_words'] = all_nine_words
        sessions[session_id]['repeat_count'] = 0
        sessions[session_id]['current_mode'] = 'Words'
        sessions[session_id]['correct_count'] = 0
        sessions[session_id]['total_attempts'] = 0
    
    current_set = all_nine_words[0:3]
    
    return jsonify({
        'current_set': current_set,
        'repeat_count': 0,
        'correct_count': 0,
        'total_attempts': 0
    })

@app.route('/api/load-ed-sheet', methods=['POST'])
def load_ed_sheet():
    """ed (Past Tense) 탭 로드"""
    session_id = request.json.get('session_id')
    words = load_words()
    
    # ed 시트에서 과거형 데이터 있는 것만 필터링
    ed_words = [w for w in words if 'past_tense' in w]
    
    all_nine_words = []
    for _ in range(3):
        if ed_words:
            all_nine_words.extend(random.sample(ed_words, min(3, len(ed_words))))
    
    if session_id in sessions:
        sessions[session_id]['all_nine_words'] = all_nine_words
        sessions[session_id]['repeat_count'] = 0
        sessions[session_id]['current_mode'] = 'ed'
        sessions[session_id]['correct_count'] = 0
        sessions[session_id]['total_attempts'] = 0
    
    current_set = all_nine_words[0:3]
    
    return jsonify({
        'current_set': current_set,
        'repeat_count': 0,
        'correct_count': 0,
        'total_attempts': 0
    })

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """답 확인"""
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('user_input', '').lower().strip()
    word_data = data.get('word_data')
    mode = data.get('mode', 'Words')
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    is_correct = False
    
    if mode == 'Words':
        is_correct = user_input == word_data['word'].lower()
    elif mode == 'ed':
        parts = user_input.split()
        if len(parts) == 2:
            is_correct = (parts[0] == word_data.get('word', '').lower() and 
                         parts[1] == word_data.get('past_tense', '').lower())
    
    if is_correct:
        session['correct_count'] += 1
    session['total_attempts'] += 1
    
    accuracy = (session['correct_count'] / session['total_attempts'] * 100) if session['total_attempts'] > 0 else 0
    
    return jsonify({
        'is_correct': is_correct,
        'correct_count': session['correct_count'],
        'total_attempts': session['total_attempts'],
        'accuracy': round(accuracy, 1)
    })

@app.route('/api/next-word', methods=['POST'])
def next_word():
    """다음 단어 또는 세트로 이동"""
    data = request.json
    session_id = data.get('session_id')
    current_index = data.get('current_index', 0)
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    if current_index < 2:
        # 현재 세트 내 다음 단어
        return jsonify({'action': 'next_word', 'index': current_index + 1})
    else:
        # 세트 완료 - 다음 세트로 이동할지 확인
        session['repeat_count'] += 1
        
        if session['repeat_count'] >= 3:
            # 9개 단어 완료
            return jsonify({'action': 'set_complete', 'repeat_count': session['repeat_count']})
        else:
            # 다음 세트로 자동 이동
            set_index = session['repeat_count']
            start_idx = set_index * 3
            current_set = session['all_nine_words'][start_idx:start_idx + 3]
            return jsonify({
                'action': 'next_set',
                'current_set': current_set,
                'repeat_count': session['repeat_count']
            })

@app.route('/api/next-nine-words', methods=['POST'])
def next_nine_words():
    """새로운 9개 단어로 이동"""
    data = request.json
    session_id = data.get('session_id')
    category = data.get('category', '전체')
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    words = load_words()
    if category != '전체':
        words = [w for w in words if w.get('category') == category]
    
    # 새로운 9개 단어 생성
    all_nine_words = []
    for _ in range(3):
        if words:
            all_nine_words.extend(random.sample(words, min(3, len(words))))
    
    session['all_nine_words'] = all_nine_words
    session['repeat_count'] = 0
    session['correct_count'] = 0
    session['total_attempts'] = 0
    
    current_set = all_nine_words[0:3]
    
    return jsonify({
        'current_set': current_set,
        'repeat_count': 0,
        'correct_count': 0,
        'total_attempts': 0
    })

@app.route('/api/repeat-nine-words', methods=['POST'])
def repeat_nine_words():
    """같은 9개 단어 반복"""
    data = request.json
    session_id = data.get('session_id')
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    session['repeat_count'] = 0
    session['correct_count'] = 0
    session['total_attempts'] = 0
    
    current_set = session['all_nine_words'][0:3]
    
    return jsonify({
        'current_set': current_set,
        'repeat_count': 0,
        'correct_count': 0,
        'total_attempts': 0
    })

@app.route('/api/play-audio', methods=['GET'])
def play_audio():
    """단어 발음 생성"""
    word = request.args.get('word', '')
    
    try:
        tts = gTTS(text=word, lang='en')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        return send_file(
            audio_fp,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f'{word}.mp3'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-word', methods=['POST'])
def add_word():
    """단어 추가"""
    data = request.json
    word = data.get('word', '').strip()
    meaning = data.get('meaning', '').strip()
    
    if not word or not meaning:
        return jsonify({'error': 'Word and meaning are required'}), 400
    
    words = load_words()
    words.append({
        'word': word,
        'meaning': meaning,
        'example': '',
        'category': '기타'
    })
    save_words(words)
    
    return jsonify({'success': True, 'message': '단어가 추가되었습니다.'})

@app.route('/api/delete-word', methods=['POST'])
def delete_word():
    """단어 삭제"""
    data = request.json
    word = data.get('word', '').strip()
    
    words = load_words()
    words = [w for w in words if w['word'].lower() != word.lower()]
    save_words(words)
    
    return jsonify({'success': True, 'message': '단어가 삭제되었습니다.'})

@app.route('/api/get-words', methods=['GET'])
def get_words():
    """모든 단어 조회"""
    words = load_words()
    return jsonify(words)

@app.route('/api/get-categories', methods=['GET'])
def get_categories():
    """카테고리 조회"""
    words = load_words()
    categories = sorted(list(set(w.get('category', '기타') for w in words)))
    return jsonify(categories)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
