# Onyx — чат и RAG поверх вашей модели

[Onyx](https://github.com/onyx-dot-app/onyx) — это отдельный стек (PostgreSQL, OpenSearch, nginx, backend и др.). Его **нельзя** безопасно «впаять» одной строкой в compose лабы: официальный `docker-compose.yml` тянет десятки сервисов и рассчитан на запуск из каталога `deployment/docker_compose` внутри клона репозитория.

## Быстрый старт

1. Поднимите **Ollama** из лабы (профиль `inference`):

   ```bash
   cd gpu
   docker compose --env-file ../.env --profile inference up -d ollama
   ```

   Или CPU-режим:

   ```bash
   cd cpu
   docker compose --env-file ../.env --profile inference up -d ollama
   ```

2. Склонируйте Onyx один раз:

   **Windows (PowerShell):**

   ```powershell
   cd onyx
   .\bootstrap.ps1
   ```

   **Linux / macOS:**

   ```bash
   chmod +x onyx/bootstrap.sh
   ./onyx/bootstrap.sh
   ```

3. Запустите официальный compose:

   ```bash
   cd onyx/upstream/deployment/docker_compose
   cp env.template .env
   docker compose up -d
   ```

4. Откройте **http://localhost:3000** и пройдите первичную настройку.

5. В админке: **Configuration → Language Models** — добавьте провайдер **Ollama**.  
   Базовый URL для контейнеров Onyx на той же машине, что и Docker Desktop:

   - Windows / macOS: `http://host.docker.internal:11434`
   - Linux: `http://172.17.0.1:11434` или IP вашего хоста в bridge-сети (см. `ip addr` / `docker network inspect bridge`).

   Порт `11434` можно изменить в корневом `.env` лабы (`OLLAMA_PORT`).

## Порты и конфликты

- Onyx по умолчанию слушает **3000** (через nginx в официальном compose).
- Лаба **не** поднимает свой UI на 3000 — конфликта с Open WebUI больше нет.

## Общая Docker-сеть (опционально)

Если нужен доступ к Ollama по имени `ollama`, подключите сервис `api_server` или nginx Onyx к внешней сети `ailab` / `ailab-cpu`. Это ручная правка официального compose у вас в `upstream/` — обновления `git pull` её перезапишут.

## Каталог `upstream/`

После `bootstrap` здесь появится полный clone Onyx. Каталог **`onyx/upstream/`** добавлен в `.gitignore`.
