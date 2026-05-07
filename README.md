# AI Lab — Docker-стек для дообучения LLM

Полноценная лаборатория для дообучения больших языковых моделей.
Стек разделён на **GPU** и **CPU** (два отдельных `docker-compose.yml`).

**Пошаговая инструкция по работе:** [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md).

## Два режима

| Каталог | Назначение |
|---------|------------|
| **`gpu/`** | NVIDIA GPU: LLaMA-Factory, Jupyter CUDA, Ollama на GPU |
| **`cpu/`** | Только CPU/RAM: те же сервисы без запроса GPU (медленное дообучение) |

Из корня репозитория можно запускать **GPU**-вариант так же, как раньше:

```bash
docker compose --env-file .env up -d
```

(корневой [`docker-compose.yml`](docker-compose.yml) подключает [`gpu/docker-compose.yml`](gpu/docker-compose.yml)).

Для **CPU**:

```bash
docker compose -f cpu/docker-compose.yml --env-file .env up -d
```

При запуске из подкаталога указывайте env-файл явно:

```bash
cd gpu
docker compose --env-file ../.env up -d
```

## Компоненты лабы

| Сервис | Порт | Назначение |
|--------|------|------------|
| **LLaMA-Factory** | `:7860` | Веб-интерфейс для дообучения (100+ моделей, LoRA/QLoRA/Full/DPO) |
| **TensorBoard** | `:6006` | Визуализация loss, lr, гистограмм весов и градиентов |
| **Aim** | `:43800` | Трекер экспериментов, сравнение запусков |
| **JupyterLab** | `:8888` | Кастомные скрипты и отладка |
| **Ollama** | `:11434` | Инференс (профиль `inference`); в CPU-режиме работает на CPU |

## Onyx (чат и RAG)

Вместо Open WebUI используется **[Onyx](https://github.com/onyx-dot-app/onyx)** — отдельный официальный compose (свой PostgreSQL, OpenSearch и т.д.). Его поднимают один раз скриптом из каталога [`onyx/`](onyx/README.md): `bootstrap.ps1` / `bootstrap.sh`, затем `docker compose` в клоне репозитория. В админке Onyx укажите Ollama: `http://host.docker.internal:11434` (Docker Desktop Win/Mac) или IP хоста на Linux.

## Структура проекта

```
AIlab/
├── docker-compose.yml          # по умолчанию → gpu/docker-compose.yml
├── gpu/
│   └── docker-compose.yml      # стек с NVIDIA GPU
├── cpu/
│   └── docker-compose.yml      # стек без GPU (сеть ailab-cpu)
├── onyx/
│   ├── README.md               # как поставить Onyx и связать с Ollama
│   ├── bootstrap.ps1
│   └── bootstrap.sh
├── docker/
│   └── tensorboard/
│       └── Dockerfile
├── scripts/
│   ├── layer_histograms.py
│   └── aim_logger.py
├── data/
│   ├── models/
│   ├── datasets/
│   ├── output/
│   ├── logs/tb/, logs/aim/
│   ├── hf_cache/
│   ├── notebooks/
│   └── ollama/
├── .env
├── .env.example
└── .gitignore
```

## Требования

### GPU-стек

- **Docker** 24.0+ с **Docker Compose** v2
- **NVIDIA GPU**, драйвер 525+
- [**NVIDIA Container Toolkit**](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- **VRAM**: ориентир 16+ ГБ для 7B (QLoRA)

### CPU-стек

- Достаточно Docker; GPU не нужен. Дообучение больших LLM на CPU обычно непрактично; Ollama и небольшие эксперименты — возможны.

## Быстрый старт

### 1. Окружение

```bash
cd AIlab
cp .env.example .env
```

Укажите `HF_TOKEN` для gated-моделей.

### 2. Запуск обучения (GPU)

```bash
docker compose --env-file .env up -d
```

### 3. URL

| Сервис | URL |
|--------|-----|
| LLaMA-Factory | http://localhost:7860 |
| TensorBoard | http://localhost:6006 |
| Aim | http://localhost:43800 |
| JupyterLab | http://localhost:8888 |

### 4. Остановка

```bash
docker compose --profile inference down
docker compose down
```

(Для CPU замените команду на `-f cpu/docker-compose.yml`.)

## Воркфлоу дообучения

### Вариант A: LLaMA-Factory WebUI

1. http://localhost:7860 — базовая модель, датасет в `./data/datasets/`
2. Fine-tune → QLoRA; `report_to: tensorboard`, `output_dir: /app/output`
3. Мониторинг: http://localhost:6006 и встроенный LlamaBoard

### Вариант B: Jupyter

1. http://localhost:8888 — ноутбук `work/01_custom_training.ipynb`
2. Гистограммы слоёв → TensorBoard; при необходимости Aim через колбэк или `tb_to_aim`

### TB → Aim

```python
from aim_logger import tb_to_aim
tb_to_aim("/home/jovyan/logs/tb", repo="/home/jovyan/logs/aim")
```

## Инференс и Onyx

### Ollama (профиль inference)

**GPU:**

```bash
cd gpu
docker compose --env-file ../.env --profile inference up -d ollama
```

**CPU:**

```bash
cd cpu
docker compose --env-file ../.env --profile inference up -d ollama
```

Имена контейнеров: `ailab-ollama` (GPU) и `ailab-ollama-cpu` (CPU).

### Загрузка GGUF в Ollama

```bash
docker exec -i ailab-ollama ollama create my-model -f - <<EOF
FROM /models/my-model.gguf
EOF
```

(На CPU замените имя контейнера на `ailab-ollama-cpu`.)

### Onyx

См. [onyx/README.md](onyx/README.md). UI Onyx после установки: **http://localhost:3000**.

## Визуализация

- **TensorBoard** — Scalars / Histograms / Graphs
- **Aim** — метрики, сравнение runs, параметры

## Нюансы

- **VRAM**: реже логировать гистограммы (`log_every_n_steps`), `gradient_checkpointing`, фильтр `filter_patterns=["lora"]`.
- **ipc: host** в GPU compose нужен в первую очередь для Linux; на Docker Desktop может вести себя иначе.
- **Не открывайте** порты в интернет без защиты.
- **Одновременно** не поднимайте `gpu` и `cpu` compose на одних портах — будет конфликт.
- **Onyx + Ollama**: при типичной установке Onyx обращается к Ollama по URL хоста (`host.docker.internal:11434`), а не по Docker-имени `ollama`.
- **LLaMA-Factory / :7860**: образ по умолчанию поднимал только `bash`, без WebUI — в compose задано `command: llamafactory-cli webui`. Если страница «не отправила данных», пересоздайте сервис: `docker compose ... up -d --force-recreate llama-factory`.

## Управление

```bash
docker compose ps
docker compose -f gpu/docker-compose.yml logs -f llama-factory
docker compose down
```
