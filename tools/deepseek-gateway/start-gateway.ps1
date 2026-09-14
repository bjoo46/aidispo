# DeepSeek 게이트웨이 기동 스크립트 (Windows / PowerShell)
#
#   1) DeepSeek API 키를 환경변수로 설정한 뒤
#   2) 이 스크립트를 실행하면 http://localhost:4000 에 프록시가 뜹니다.
#
#   $env:DEEPSEEK_API_KEY = "sk-..."
#   .\start-gateway.ps1
#
# 키를 매번 넣기 싫으면 사용자 환경변수로 영구 등록:
#   [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-...", "User")

$ErrorActionPreference = "Stop"
$configPath = Join-Path $PSScriptRoot "config.yaml"

if (-not $env:DEEPSEEK_API_KEY) {
    Write-Error "DEEPSEEK_API_KEY 환경변수가 없습니다. `$env:DEEPSEEK_API_KEY = 'sk-...' 로 설정하세요."
}

# 앱에서 Gateway API key 로 넣을 값. 로컬 전용이라 고정값이어도 무방합니다.
if (-not $env:LITELLM_MASTER_KEY) {
    $env:LITELLM_MASTER_KEY = "sk-local-deepseek-gateway"
}

if (-not (Get-Command litellm -ErrorAction SilentlyContinue)) {
    Write-Host "litellm 이 없어 설치합니다..." -ForegroundColor Yellow
    python -m pip install --upgrade "litellm[proxy]"
}

Write-Host ""
Write-Host "게이트웨이 주소 : http://localhost:4000" -ForegroundColor Green
Write-Host "Gateway API key : $env:LITELLM_MASTER_KEY" -ForegroundColor Green
Write-Host "중지하려면 Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

litellm --config $configPath --port 4000
