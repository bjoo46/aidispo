# DeepSeek 게이트웨이 (Claude 데스크톱 서드파티 모드용)

Claude 데스크톱 앱을 DeepSeek에 붙이려 할 때 막히는 두 지점을 우회하기 위한 로컬 프록시입니다.

- 앱은 모델 ID가 `claude-*` 형식이 아니면 설정 저장을 막습니다.
- 앱의 연결 테스트는 `GET {base}/v1/models` 를 호출하는데,
  `https://api.deepseek.com/anthropic/v1/models` 는 404 를 반환합니다.

LiteLLM 을 중간에 두면 모델 목록을 제공하면서 이름만 `claude-*` 로 바꿔주고,
실제 호출은 DeepSeek 로 보냅니다.

```
Claude 데스크톱 ──► localhost:4000 (LiteLLM) ──► api.deepseek.com
      claude-opus-4-1              deepseek-v4-pro
```

## 1. 게이트웨이 실행

PowerShell 에서:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."      # DeepSeek 콘솔에서 발급한 키
.\start-gateway.ps1
```

처음 실행하면 `litellm` 을 자동 설치합니다 (Python 3.10+ 필요).
창은 켜둔 채로 두세요. 이 창이 게이트웨이입니다.

## 2. 동작 확인

**다른** PowerShell 창에서:

```powershell
.\check-gateway.ps1
```

두 단계가 모두 통과해야 앱 설정으로 넘어갑니다.
2단계에서 실패하면 `config.yaml` 의 `deepseek/` 뒤 모델 ID 가 실제 DeepSeek 모델 이름과
다른 것이므로, platform.deepseek.com 의 모델 목록을 보고 고치세요.

## 3. 앱 설정

로그인 화면 → ☰ → Developer → Configure Third-Party Inference

| 항목 | 값 |
|---|---|
| Inference provider | Gateway |
| Gateway base URL | `http://localhost:4000` |
| Credential kind | Static API key |
| Gateway API key | `sk-local-deepseek-gateway` |
| Gateway auth scheme | Bearer |

모델 목록은 **비워 두세요.** LiteLLM 이 `/v1/models` 로 알려주므로 자동 검색됩니다.
직접 넣고 싶다면 `config.yaml` 의 `model_name` 값들을 그대로 쓰고, 티어 별칭은
`claude-opus-4-1` → opus, `claude-sonnet-4-5` → sonnet, `claude-haiku-4-5` → haiku
로 맞추고 각각 티어 기본값을 켜면 됩니다.

Apply Changes → Save & Restart → 재시작된 로그인 화면에서 서드파티 모드로 시작.

## 알아둘 것

- 게이트웨이 창을 닫으면 앱에서 요청이 실패합니다. 쓰는 동안은 켜두세요.
- API 키는 이 폴더 어디에도 저장되지 않습니다. 환경변수로만 전달됩니다.
- 세 라우트 중 opus/sonnet 은 같은 DeepSeek 모델을 가리킵니다.
  나누고 싶으면 `config.yaml` 에서 각각 다른 모델로 지정하세요.
- 서드파티 모드는 로컬 세션 전용입니다. SSH·클라우드·원격 제어는 쓸 수 없습니다.

## 문제 해결

| 증상 | 원인 |
|---|---|
| `Gateway was unreachable` | 게이트웨이 창이 꺼져 있음 |
| 연결 테스트 404 | base URL 이 아직 DeepSeek 주소로 남아 있음 |
| 401 | Gateway API key 가 `LITELLM_MASTER_KEY` 와 불일치 |
| 402 | DeepSeek 잔액 부족 |
| `Model Not Exist` | `config.yaml` 의 DeepSeek 모델 ID 오류 |
