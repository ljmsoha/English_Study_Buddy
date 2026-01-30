# 웹 앱 실행 가이드

## 설치 및 실행

### 1단계: 필요한 라이브러리 설치
```bash
cd web_app
pip install -r requirements.txt
```

### 2단계: 웹 앱 실행
```bash
python app.py
```

### 3단계: 브라우저에서 접속
```
http://localhost:5000
```

## 기능

✅ **3개 단어 × 3세트 = 9개 단어 학습**
- 같은 9개 단어를 3번 반복 또는 새로운 9개로 전환

✅ **음성 재생**
- Google Text-to-Speech(gTTS) 사용

✅ **카테고리별 학습**
- 원하는 카테고리만 선택해서 학습

✅ **단어 추가/삭제**
- 새로운 단어 추가 가능
- 학습 중인 단어 삭제 가능

✅ **모바일 지원**
- 반응형 디자인으로 스마트폰에서도 사용 가능

✅ **두 가지 학습 모드**
- **Words 탭**: 의미를 보고 영어 단어 입력
- **Past Tense 탭**: 의미를 보고 원형과 과거형 입력 (space로 구분)

## 팁

- **Space**: 발음 재생
- **Enter**: 답 확인
- **💡 버튼**: 예문과 첫 글자 힌트 보기

## 안드로이드에서 사용하기

로컬 네트워크에서 사용:
1. Windows IP 주소 확인: `ipconfig` 명령어 실행
2. 안드로이드 기기에서 브라우저로 접속: `http://[Windows IP]:5000`

예: `http://192.168.1.100:5000`

## 클라우드 배포

배포 서비스 (Heroku, PythonAnywhere, Replit 등)를 이용하면 언제 어디서나 접속 가능합니다.

---

**개발 환경**: Flask + HTML/CSS/JavaScript  
**데이터**: JSON 형식  
**음성**: Google Text-to-Speech (gTTS)
