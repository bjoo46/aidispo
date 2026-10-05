"""동영상 → 음성 추출 → 대사 인식 → 한국어 번역 웹 앱.

실행: uvicorn app:app --host 0.0.0.0 --port 8000
"""
import json
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import anthropic
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
BATCH_SIZE = 80  # 한 번의 LLM 호출로 번역할 세그먼트 수

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Video Dialogue Translator")
client = anthropic.Anthropic()

TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "is_dialogue": {"type": "boolean"},
                    "ko": {"type": "string"},
                },
                "required": ["id", "is_dialogue", "ko"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You translate speech-recognition transcripts of videos into natural Korean subtitles.

You receive a JSON list of segments (id, start/end seconds, text). For every segment return:
- id: the same id
- is_dialogue: true if the segment is spoken dialogue or narration. false if it is song lyrics, \
background music, sound-effect tags like [Music] or (applause), or an obvious recognition artifact \
(e.g. a lone "Thanks for watching!" over silence).
- ko: a natural, concise Korean subtitle translation of the dialogue (keep speaker tone and \
politeness level consistent across segments; keep proper nouns sensible). Use "" when is_dialogue is false. \
If the text is already Korean, clean it up lightly.

Use neighbouring segments as context: sentences are often split across segments, so translate each \
segment so that the subtitles read naturally in order. Return every id exactly once."""


@lru_cache(maxsize=1)
def get_whisper():
    from faster_whisper import WhisperModel

    return WhisperModel(WHISPER_MODEL, device="auto", compute_type="int8")


def extract_audio(video_path: str, audio_path: str) -> None:
    """ffmpeg로 영상에서 16kHz 모노 오디오만 추출한다."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", audio_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = result.stderr.strip().splitlines()[-3:]
        raise RuntimeError("오디오 추출 실패: " + " / ".join(tail))


def transcribe(audio_path: str):
    segments, info = get_whisper().transcribe(audio_path, vad_filter=True)
    items = [
        {"id": i, "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for i, s in enumerate(segments)
        if s.text.strip()
    ]
    return items, info.language


def translate_batch(batch, source_lang: str) -> dict:
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        output_config={"format": {"type": "json_schema", "schema": TRANSLATION_SCHEMA}},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Detected source language: {source_lang}\n\nSegments:\n"
            + json.dumps(batch, ensure_ascii=False),
        }],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("번역 요청이 거부되었습니다.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("번역 응답이 너무 길어 잘렸습니다. BATCH_SIZE를 줄여 주세요.")
    text = next(b.text for b in response.content if b.type == "text")
    return {item["id"]: item for item in json.loads(text)["items"]}


def event(**kwargs) -> bytes:
    return (json.dumps(kwargs, ensure_ascii=False) + "\n").encode()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/translate")
def translate(file: UploadFile = File(...)):
    workdir = tempfile.mkdtemp(prefix="vt_")
    video_path = os.path.join(workdir, "input" + Path(file.filename or "video").suffix)
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    def run():
        try:
            yield event(type="progress", step="audio", message="동영상에서 오디오 추출 중…")
            audio_path = os.path.join(workdir, "audio.wav")
            extract_audio(video_path, audio_path)

            yield event(type="progress", step="transcribe", message="음성 인식 중… (영상 길이에 따라 시간이 걸립니다)")
            segments, lang = transcribe(audio_path)
            if not segments:
                yield event(type="result", language=lang, segments=[])
                return

            total = len(segments)
            for start in range(0, total, BATCH_SIZE):
                batch = segments[start:start + BATCH_SIZE]
                yield event(
                    type="progress", step="translate",
                    message=f"한국어로 번역 중… ({start}/{total})",
                    done=start, total=total,
                )
                translated = translate_batch(batch, lang)
                for seg in batch:
                    t = translated.get(seg["id"], {})
                    seg["ko"] = t.get("ko", "")
                    seg["is_dialogue"] = t.get("is_dialogue", True)

            yield event(type="result", language=lang, segments=segments)
        except anthropic.AuthenticationError:
            yield event(type="error", message="Anthropic API 키가 올바르지 않습니다 (ANTHROPIC_API_KEY 확인).")
        except anthropic.APIConnectionError:
            yield event(type="error", message="Claude API에 연결하지 못했습니다.")
        except anthropic.APIStatusError as e:
            yield event(type="error", message=f"Claude API 오류 ({e.status_code}): {e.message}")
        except Exception as e:  # noqa: BLE001 - 사용자에게 오류를 그대로 보여준다
            yield event(type="error", message=str(e))
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    return StreamingResponse(run(), media_type="application/x-ndjson")
