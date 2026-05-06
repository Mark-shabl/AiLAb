#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/upstream"

if [[ -d "$UPSTREAM/.git" ]]; then
  echo "Onyx уже клонирован: $UPSTREAM"
  git -C "$UPSTREAM" pull
else
  rm -rf "$UPSTREAM"
  echo "Клонирование Onyx в $UPSTREAM ..."
  git clone --depth 1 https://github.com/onyx-dot-app/onyx.git "$UPSTREAM"
fi

echo ""
echo "Дальше:"
echo "  cd \"$UPSTREAM/deployment/docker_compose\""
echo "  cp env.template .env   # при необходимости"
echo "  docker compose up -d"
echo ""
echo "Onyx UI: http://localhost:3000"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
echo "Ollama из AI Lab: в админке Onyx задайте Ollama URL, например"
echo "  http://host.docker.internal:${OLLAMA_PORT}   (Docker Desktop Win/Mac)"
echo "  или http://<IP_хоста>:${OLLAMA_PORT}   (Linux)"
