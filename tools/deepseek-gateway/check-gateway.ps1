# 게이트웨이가 제대로 떴는지 확인합니다.
# 앱 설정을 건드리기 전에 이 스크립트가 통과하는지 먼저 보세요.

$key = if ($env:LITELLM_MASTER_KEY) { $env:LITELLM_MASTER_KEY } else { "sk-local-deepseek-gateway" }
$headers = @{ "Authorization" = "Bearer $key" }

Write-Host "[1/2] 모델 목록 조회 (앱 연결 테스트가 쓰는 엔드포인트)" -ForegroundColor Cyan
try {
    $models = Invoke-RestMethod -Uri "http://localhost:4000/v1/models" -Headers $headers
    $models.data | ForEach-Object { Write-Host "  - $($_.id)" }
} catch {
    Write-Host "  실패: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/2] 실제 추론 요청 (Anthropic 형식)" -ForegroundColor Cyan
$body = @{
    model      = "claude-opus-4-1"
    max_tokens = 64
    messages   = @(@{ role = "user"; content = "ping 이라고만 답해줘" })
} | ConvertTo-Json -Depth 5

try {
    $res = Invoke-RestMethod -Uri "http://localhost:4000/v1/messages" -Method Post `
        -Headers ($headers + @{ "content-type" = "application/json" }) -Body $body
    Write-Host "  응답: $($res.content[0].text)" -ForegroundColor Green
    Write-Host ""
    Write-Host "정상입니다. 이제 앱 설정을 바꾸세요." -ForegroundColor Green
} catch {
    Write-Host "  실패: $_" -ForegroundColor Red
    Write-Host "  config.yaml 의 deepseek/ 뒤 모델 ID 가 실제로 존재하는지 확인하세요." -ForegroundColor Yellow
    exit 1
}
