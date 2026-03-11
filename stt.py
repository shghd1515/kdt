import torch
import sounddevice as sd
import numpy as np
import soundfile as sf
import speech_recognition as sr
import time
from deep_translator import GoogleTranslator

# ── 1. Silero VAD 모델 로드 ──────────────────────────────
model, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad'
)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

vad_iterator = VADIterator(model)

# ── 2. 설정 ─────────────────────────────────────────────
SAMPLE_RATE    = 16000
BLOCK_SIZE     = 512
RECORD_SECONDS = 10

speech_buffer = []
is_speaking   = False

# ── 3. 마이크 입력 & VAD ─────────────────────────────────
print("🎙️  녹음 시작 (한국어로 말씀해주세요)")
start_time = time.time()

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BLOCK_SIZE,
    dtype='float32'
) as stream:

    while True:
        audio_chunk, _ = stream.read(BLOCK_SIZE)
        audio_chunk = audio_chunk.flatten()

        audio_tensor = torch.from_numpy(audio_chunk)
        speech_dict  = vad_iterator(audio_tensor)

        if speech_dict:
            if "start" in speech_dict:
                is_speaking = True
                print("🔊 발화 감지됨")
            if "end" in speech_dict:
                is_speaking = False
                print("🔇 발화 종료")

        if is_speaking:
            speech_buffer.extend(audio_chunk)

        if time.time() - start_time > RECORD_SECONDS:
            break

print("✅ 녹음 종료")

# ── 4. 음성 버퍼 확인 ────────────────────────────────────
if not speech_buffer:
    print("⚠️  감지된 음성이 없습니다. 다시 시도해주세요.")
    exit()

# ── 5. WAV 저장 ──────────────────────────────────────────
speech_audio = np.array(speech_buffer)
wav_path = "vad_recorded.wav"
sf.write(wav_path, speech_audio, SAMPLE_RATE)
print(f"💾 음성 저장 완료: {wav_path}")

# ── 6. Google STT: 한국어 인식 ───────────────────────────
recognizer = sr.Recognizer()

with sr.AudioFile(wav_path) as source:
    print("🔄 음성 인식 중...")
    audio_data = recognizer.record(source)

try:
    # 한국어로 인식
    korean_text = recognizer.recognize_google(audio_data, language='ko-KR')
    print(f"\n🇰🇷 한국어 원문: {korean_text}")

    # ── 7. 일본어 번역 ─────────────────────────────────────
    japanese_text = GoogleTranslator(source='ko', target='ja').translate(korean_text)
    print(f"🇯🇵 일본어 번역: {japanese_text}")

except sr.UnknownValueError:
    print("⚠️  음성을 인식하지 못했습니다.")
except sr.RequestError as e:
    print(f"⚠️  STT 서비스 오류: {e}")