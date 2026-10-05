# 동영상 대사 → 한국어 번역기

동영상을 브라우저에 드래그하면:

1. **ffmpeg**로 영상에서 오디오만 추출 (16kHz 모노)
2. **faster-whisper**(로컬)로 음성 인식, 타임스탬프 포함
3. **Claude**로 대사만 골라 한국어로 번역 (음악, 효과음 태그, 인식 오류는 제외)

결과는 영상 위에 한국어 자막으로 표시되고, 줄을 클릭하면 해당 위치로 이동합니다. SRT 파일로 내려받거나 텍스트로 복사할 수 있습니다.

## 바탕화면 바로가기 (Windows)

1. [Python](https://www.python.org/downloads/)과 ffmpeg(`winget install Gyan.FFmpeg`)를 설치합니다.
2. 이 폴더의 `create_shortcut.bat`을 더블클릭하면 바탕화면에 아이콘이 붙은 **대사 번역기** 바로가기가 생깁니다.
3. 바로가기를 더블클릭하면 서버가 켜지고 브라우저가 열립니다. 처음 한 번만 API 키를 물어보고 저장합니다. 필요한 패키지도 처음에 자동으로 설치합니다.
4. 끄려면 검은 서버 창을 닫습니다.

## 직접 실행

```bash
# ffmpeg 필요 (macOS: brew install ffmpeg / Ubuntu: apt install ffmpeg)
cd video_translator
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn app:app --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 을 엽니다.

## 설정 (환경변수)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `ANTHROPIC_API_KEY` | (필수) | Claude API 키 |
| `CLAUDE_MODEL` | `claude-haiku-4-5` | 번역에 쓸 모델. 가장 저렴한 모델이 기본값이고, 번역 품질을 높이려면 `claude-sonnet-5-5`로 바꾸세요 |
| `WHISPER_MODEL` | `small` | `tiny`/`base`/`small`/`medium`/`large-v3`. 클수록 정확하지만 느림 |

Whisper 모델은 처음 실행할 때 Hugging Face에서 자동으로 내려받습니다. GPU가 있으면 자동으로 사용합니다.
