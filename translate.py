from google import genai

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

# app.py와 같은 폴더의 .env를 명시적으로 로드 (경로 꼬임 방지)
load_ok = load_dotenv(dotenv_path=DOTENV_PATH, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5177"))
PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")