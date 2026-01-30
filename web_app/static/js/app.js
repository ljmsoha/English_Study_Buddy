// 전역 변수
let sessionId = '';
let currentIndex = 0;
let currentSet = [];
let currentMode = 'Words';
let allWords = [];

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    document.getElementById('answerInput').focus();
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            e.preventDefault();
            playAudio();
        }
    });
});

async function initApp() {
    try {
        const response = await fetch('/api/init');
        const data = await response.json();
        
        sessionId = data.session_id;
        currentSet = data.current_set;
        allWords = data.categories;
        
        // 카테고리 채우기
        const categorySelect = document.getElementById('categorySelect');
        data.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            categorySelect.appendChild(option);
        });
        
        displayWord();
        updateStats();
    } catch (error) {
        console.error('초기화 실패:', error);
        alert('앱 초기화에 실패했습니다.');
    }
}

function displayWord() {
    if (!currentSet || currentSet.length === 0) return;
    
    const word = currentSet[currentIndex];
    const meaningDisplay = document.getElementById('meaningDisplay');
    
    if (currentMode === 'Words') {
        meaningDisplay.textContent = word.meaning;
    } else if (currentMode === 'ed') {
        meaningDisplay.textContent = word.meaning;
    }
    
    document.getElementById('answerInput').value = '';
    document.getElementById('answerInput').focus();
    document.getElementById('resultMessage').textContent = '';
    document.getElementById('resultMessage').className = 'result-message';
    
    updateStats();
}

function updateStats() {
    document.getElementById('wordStats').textContent = `단어: ${currentIndex + 1}/3`;
    document.getElementById('setStats').textContent = `세트: ${Math.floor(currentIndex / 3) + 1}/3`;
}

async function checkAnswer() {
    const input = document.getElementById('answerInput').value.trim();
    if (!input) return;
    
    const word = currentSet[currentIndex];
    
    try {
        const response = await fetch('/api/check-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                user_input: input,
                word_data: word,
                mode: currentMode
            })
        });
        
        const data = await response.json();
        const resultDiv = document.getElementById('resultMessage');
        
        if (data.is_correct) {
            resultDiv.textContent = currentMode === 'Words' 
                ? `✅ 정답: ${word.word}` 
                : `✅ 정답: ${word.word} → ${word.past_tense}`;
            resultDiv.className = 'result-message correct';
            playAudio();
            
            setTimeout(() => {
                nextWord();
            }, 1000);
        } else {
            resultDiv.textContent = currentMode === 'Words'
                ? `❌ 오답! 정답: ${word.word}`
                : `❌ 오답! 정답: ${word.word} → ${word.past_tense}`;
            resultDiv.className = 'result-message incorrect';
            playAudio();
        }
        
        updateStats();
    } catch (error) {
        console.error('답 확인 실패:', error);
    }
}

async function nextWord() {
    try {
        const response = await fetch('/api/next-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                current_index: currentIndex
            })
        });
        
        const data = await response.json();
        
        if (data.action === 'next_word') {
            currentIndex = data.index;
            displayWord();
        } else if (data.action === 'next_set') {
            currentSet = data.current_set;
            currentIndex = 0;
            displayWord();
        } else if (data.action === 'set_complete') {
            showSetCompleteDialog();
        }
    } catch (error) {
        console.error('다음 단어 실패:', error);
    }
}

function prevWord() {
    if (currentIndex > 0) {
        currentIndex--;
        displayWord();
    }
}

async function playAudio() {
    const word = currentSet[currentIndex];
    try {
        const audio = new Audio(`/api/play-audio?word=${encodeURIComponent(word.word)}`);
        audio.play();
    } catch (error) {
        console.error('음성 재생 실패:', error);
        alert(`발음: ${word.word}`);
    }
}

function showHint() {
    const word = currentSet[currentIndex];
    const hintText = `[예문]\n${word.example || '없음'}\n\n[첫 글자]\n${word.word[0]}...`;
    document.getElementById('hintText').textContent = hintText;
    document.getElementById('hintModal').style.display = 'block';
}

function closeHintModal() {
    document.getElementById('hintModal').style.display = 'none';
}

function showSetCompleteDialog() {
    const result = confirm(
        '총 9개 단어를 완료했습니다.\n\n' +
        '확인: 같은 9개 단어를 다시 반복\n' +
        '취소: 새로운 9개 단어로 이동'
    );
    
    if (result) {
        repeatNineWords();
    } else {
        nextNineWords();
    }
}

async function loadWordsSheet() {
    try {
        const response = await fetch('/api/load-words-sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        currentSet = data.current_set;
        currentIndex = 0;
        currentMode = 'Words';
        displayWord();
        alert('📘 Words 탭을 로드했습니다.\n원형을 입력해주세요.');
    } catch (error) {
        console.error('Words 탭 로드 실패:', error);
    }
}

async function loadEdSheet() {
    try {
        const response = await fetch('/api/load-ed-sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        currentSet = data.current_set;
        currentIndex = 0;
        currentMode = 'ed';
        displayWord();
        alert('⏰ Past Tense 탭을 로드했습니다.\n원형과 과거형을 space로 구분해서 입력해주세요.\n예: arrive arrived');
    } catch (error) {
        console.error('ed 탭 로드 실패:', error);
    }
}

async function nextNineWords() {
    try {
        const category = document.getElementById('categorySelect').value;
        const response = await fetch('/api/next-nine-words', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                category: category
            })
        });
        
        const data = await response.json();
        currentSet = data.current_set;
        currentIndex = 0;
        displayWord();
    } catch (error) {
        console.error('새로운 9개 단어 로드 실패:', error);
    }
}

async function repeatNineWords() {
    try {
        const response = await fetch('/api/repeat-nine-words', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        currentSet = data.current_set;
        currentIndex = 0;
        displayWord();
    } catch (error) {
        console.error('9개 단어 반복 실패:', error);
    }
}

function addWordDialog() {
    const word = prompt('영어 단어를 입력하세요:');
    if (!word) return;
    
    const meaning = prompt('뜻을 입력하세요:');
    if (!meaning) return;
    
    addWord(word, meaning);
}

async function addWord(word, meaning) {
    try {
        const response = await fetch('/api/add-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                word: word,
                meaning: meaning
            })
        });
        
        const data = await response.json();
        alert(data.message || '단어가 추가되었습니다.');
    } catch (error) {
        console.error('단어 추가 실패:', error);
        alert('단어 추가에 실패했습니다.');
    }
}

function deleteWordDialog() {
    const word = currentSet[currentIndex];
    const confirmed = confirm(`'${word.word}'를 삭제할까요?`);
    
    if (confirmed) {
        deleteWord(word.word);
    }
}

async function deleteWord(word) {
    try {
        const response = await fetch('/api/delete-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: word })
        });
        
        const data = await response.json();
        alert(data.message || '단어가 삭제되었습니다.');
        nextWord();
    } catch (error) {
        console.error('단어 삭제 실패:', error);
        alert('단어 삭제에 실패했습니다.');
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        checkAnswer();
    }
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('hintModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}
