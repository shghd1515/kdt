import os
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from google import genai

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

# app.py와 같은 폴더의 .env를 명시적으로 로드 (경로 꼬임 방지)
load_ok = load_dotenv(dotenv_path=DOTENV_PATH, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5177"))
PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

print("RUNNING APP.PY FROM:", BASE_DIR)
print("CWD:", Path.cwd())
print("DOTENV PATH:", DOTENV_PATH, "loaded=", load_ok)
print("PREFERRED_MODEL (final):", PREFERRED_MODEL)

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 없습니다. .env 파일에 Google AI Studio 키를 설정하세요.")

STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Voice Translation Suite (Python + google.genai)")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class TranslateRequest(BaseModel):
    source: Optional[str] = Field(default="ko")
    target: Literal["ja", "en", "fr", "zh-CN"]
    text: str


class TranslateResponse(BaseModel):
    model: str
    translatedText: str


def _list_models() -> List[Dict[str, Any]]:
    models = []
    for m in client.models.list():
        name = getattr(m, "name", None) or (m.get("name") if isinstance(m, dict) else None)
        supported = getattr(m, "supported_actions", None) or (m.get("supported_actions") if isinstance(m, dict) else None)
        models.append({"name": name, "supported_actions": supported, "raw": m})
    return models


@app.get("/")
def root():
    if not INDEX_HTML.exists():
        raise HTTPException(
            status_code=500,
            detail=f"static/index.html 파일이 없습니다. 다음 위치에 index.html을 넣어주세요: {INDEX_HTML}",
        )
    return FileResponse(str(INDEX_HTML))


@app.get("/api/health")
def health():
    return {"ok": True, "preferred_model": PREFERRED_MODEL}


@app.get("/api/models")
def models():
    try:
        return {"models": _list_models()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"list_models_failed: {e}")


@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    labels = {"ja": "일본어", "en": "영어", "fr": "프랑스어", "zh-CN": "중국어(간체)"}

    prompt = f"""너는 번역기다.
아래 한국어를 {labels[req.target]}로만 번역해라.
번역 결과 '텍스트만' 출력해라. (설명/머리말/따옴표/마크다운 금지)

한국어:
{text}
"""

    # preferred 모델 먼저
    model_to_use = PREFERRED_MODEL

    try:
        resp = client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config={"temperature": 0.2, "max_output_tokens": 512},
        )
        out = (getattr(resp, "text", None) or "").strip()
        if not out:
            raise HTTPException(status_code=502, detail="empty translation response")
        return TranslateResponse(model=model_to_use, translatedText=out)

    except Exception as e1:
        # 당신 /api/models에 실제로 존재하는 모델들로만 fallback
        fallback_candidates = [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001",
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.0-flash-lite-001",
        ]

        last_err = e1
        for cand in fallback_candidates:
            if cand == model_to_use:
                continue
            try:
                resp = client.models.generate_content(
                    model=cand,
                    contents=prompt,
                    config={"temperature": 0.2, "max_output_tokens": 512},
                )
                out = (getattr(resp, "text", None) or "").strip()
                if out:
                    return TranslateResponse(model=cand, translatedText=out)
                last_err = RuntimeError("empty translation response")
            except Exception as e2:
                last_err = e2

        raise HTTPException(
            status_code=500,
            detail=(
                f"translate_failed: {last_err}. "
                "현재 키에서 가능한 모델명은 /api/models를 확인하고 "
                ".env의 GEMINI_MODEL에 models/... 형태로 그대로 넣어주세요."
            ),
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)