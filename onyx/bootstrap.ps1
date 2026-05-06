$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Upstream = Join-Path $PSScriptRoot "upstream"

if (Test-Path (Join-Path $Upstream ".git")) {
    Write-Host "Он уже клонирован: $Upstream"
    Write-Host "Обновление: git -C $Upstream pull"
    git -C $Upstream pull
} else {
    if (Test-Path $Upstream) { Remove-Item -Recurse -Force $Upstream }
    Write-Host "Клонирование Onyx в $Upstream ..."
    git clone --depth 1 https://github.com/onyx-dot-app/onyx.git $Upstream
}

Write-Host ""
Write-Host "Дальше (из корня репозитория Onyx):"
Write-Host "  cd `"$Upstream\deployment\docker_compose`""
Write-Host "  copy env.template .env   # при необходимости"
Write-Host "  docker compose up -d"
Write-Host ""
Write-Host "Чат-интерфейс Onyx: http://localhost:3000"
Write-Host "Ollama из AI Lab (Docker Desktop): в админке Onyx укажите провайдер Ollama:"
Write-Host "  http://host.docker.internal:${env:OLLAMA_PORT:-11434}"
