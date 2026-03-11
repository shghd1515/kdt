# KDT Voice Translation 프로젝트

음성 입력(STT)과 번역 기능을 실험하고, FastAPI 기반 번역 API를 제공하는 프로젝트입니다.

## 프로젝트 목적

- 한국어 음성을 인식해 텍스트로 변환(STT)
- 한국어 텍스트를 외국어(일본어/영어/프랑스어/중국어 간체)로 번역
- 추후 스마트 스피커 형태로 확장 가능한 구조 준비

## 작업 파일 요약

### `app.py` (메인 API 서버)

FastAPI 서버를 실행하고 Google GenAI(Gemini)를 사용해 번역 API를 제공합니다.

주요 기능:
- `.env`에서 환경변수 로드 (`GEMINI_API_KEY`, `HOST`, `PORT`, `GEMINI_MODEL`)
- `GET /api/health`: 서버 상태 확인
- `GET /api/models`: 사용 가능한 모델 목록 조회
- `POST /api/translate`: 번역 수행
	- 입력: 원문 텍스트 + 타겟 언어
	- 출력: 사용 모델명 + 번역 결과
- 모델 호출 실패 시 fallback 모델 목록을 순차 시도

핵심 포인트:
- `GEMINI_API_KEY`가 없으면 실행 시 에러 발생
- `static/index.html` 파일이 있어야 루트(`/`) 접근 가능

---

### `stt.py` (로컬 음성 인식 실험 스크립트)

마이크 입력을 받아 VAD(Voice Activity Detection)로 발화 구간만 저장한 뒤,
Google STT로 한국어를 인식하고 일본어로 번역까지 수행합니다.

처리 흐름:
1. Silero VAD 모델 로드
2. 마이크 스트림 입력 수집
3. 발화 구간만 버퍼에 저장
4. `vad_recorded.wav` 저장
5. Google STT (`ko-KR`)로 텍스트 변환
6. `deep_translator`로 일본어 번역

주의사항:
- 마이크 장치가 정상 인식되어야 함
- VAD/STT 관련 라이브러리 추가 설치가 필요할 수 있음

---

### `tts.py`

현재는 FastAPI/환경설정 관련 import가 작성된 초기 상태입니다.

현재 상태:
- TTS 엔드포인트/로직은 아직 구현 전
- 추후 텍스트를 음성으로 변환하는 기능을 추가할 예정

---

### `smart_speaker.py`

현재는 `smart_speaker` 문자열만 있는 placeholder 파일입니다.

권장 확장 방향:
- STT → 번역 → TTS 파이프라인을 하나로 연결
- 실시간 명령 처리 루프 구성
- wake-word(호출어) 감지 기능 추가

## 실행 전 준비

### 1) 의존성 설치

현재 `requirements.txt` 기준:
- `fastapi==0.115.0`
- `uvicorn[standard]==0.30.6`
- `python-dotenv==1.0.1`
- `google-genai==1.0.0`

> 참고: 기존 `requirement.txt`도 동일 내용으로 유지되어 있습니다.

추가로 `stt.py` 실행 시에는 아래 패키지가 더 필요할 수 있습니다.
- `torch`, `sounddevice`, `numpy`, `soundfile`, `SpeechRecognition`, `deep-translator`

### 2) 환경변수 설정 (`.env`)

프로젝트 루트의 `.env` 예시:

- `GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE`
- `HOST=127.0.0.1`
- `PORT=5177`
- `GEMINI_MODEL=models/gemini-2.5-flash`

## 실행 예시

- API 서버: `app.py` 실행
- 음성 인식 실험: `stt.py` 실행

## 현재 진행 상태 한눈에 보기

- [x] FastAPI 번역 API 기본 구현 (`app.py`)
- [x] STT + 일본어 번역 실험 스크립트 (`stt.py`)
- [ ] TTS 기능 구현 (`tts.py`)
- [ ] 스마트 스피커 통합 흐름 구현 (`smart_speaker.py`)