# 🧠 WebGen AI

**WebGen AI** is a full‑stack platform that generates **complete HTML/CSS screens** from a natural language description.
It uses an **Ollama-hosted LLM** (Mistral by default) and provides a **live preview** UI.

It also supports **workflow screens**: when workflow identifiers are provided (`id_client`, `id_wf`, `id_tache`, `id_ihm`),
the AI engine enriches the result with **Oracle-friendly metadata payloads**
(`tab_ihm_wf`, `element_ihm_wf`, `tab_detail_ihm_wf`) and persists generations in `ai-engine/.data/`.

---

## 🧩 What’s Inside (Components)

- **`frontend/`**: React UI (prompt input + iframe preview) and a browser for cached screens & workflows.
- **`backend-api/`**: FastAPI gateway used by the frontend; proxies requests to the AI engine and exposes a stable REST API.
- **`ai-engine/`**: Flask AI engine; calls Ollama to generate HTML, extracts screen/schema data, hydrates Oracle metadata, and stores artifacts.
- **`ollama`** (service): model runtime exposing `:11434` (pulled model is persisted in a Docker volume).

---

## 🧠 Data & Storage (`ai-engine/.data/`)

- **`ai-engine/.data/workflows.json`**: input catalog of workflows/tasks/screens shown in the UI “Workflows” tab.
- **`ai-engine/.data/generations.jsonl`**: append-only JSONL file containing generated screens (HTML + metadata).
- **`ai-engine/.data/index.json`**: offsets index used for quick lookups in the JSONL file.

---

## 🚀 Launch (Docker Compose)

### 1) (Recommended) Configure the frontend API base (build-time)

The frontend can call the backend through the Nginx reverse-proxy (`/api/*`). To enable that, create `frontend/.env`:

```env
VITE_API_URL=.
```

### 2) Start the stack

```bash
docker compose up -d --build
docker compose ps
```

### 3) Pull the model (first run only)

```bash
docker exec -it webgen-ai-ollama ollama pull mistral
```

### 4) Open the UI

- Frontend: `http://localhost:8090`

---

## ⚙️ Ports (Docker Compose)

Ports are defined in `docker-compose.yml` (edit that file if you need different host ports).

| Service | Host Port | Container Port | What it is |
|---|---:|---:|---|
| Frontend | **8090** | 80 | React UI (served by Nginx) |
| Backend API | **8100** | 8000 | FastAPI REST API (Swagger: `/docs`) |
| AI Engine | **8505** | 5005 | Flask AI service |
| Ollama | **11434** | 11434 | Model endpoint |

Quick checks:

```bash
curl http://localhost:8100/
curl http://localhost:8505/
curl http://localhost:11434/api/tags
```

---

## 🔌 API Endpoints (Backend)

The frontend talks to the **Backend API** (FastAPI):

- `POST /api/generate` — generate a screen from a description (optionally with workflow IDs)
- `GET /api/screens` — list cached generations
- `GET /api/screens/{screen_id}` — fetch a saved generation (supports `?wf_id=...` for workflow screens)
- `GET /api/workflows` — list workflows from `ai-engine/.data/workflows.json`
- `GET /api/workflows/{wf_id}/screens` — list screens for a workflow

Example:

```bash
curl -X POST http://localhost:8100/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"description":"A login page with email/password inputs and a primary blue button (#2563eb)."}'
```

---

## 🧑‍💻 Local Development (No Docker)

Prereqs: **Python 3.11+**, **Node 22+**, and **Ollama** running locally.

### 1) Ollama

```bash
ollama serve
ollama pull mistral
```

### 2) AI Engine (Flask, default `:5005`)

```bash
cd ai-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OLLAMA_URL=http://127.0.0.1:11434
export AI_ENGINE_STORAGE_DIR="$(pwd)/.data"
python main.py
```

### 3) Backend API (FastAPI, default `:8011`)

```bash
cd backend-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AI_ENGINE_URL=http://127.0.0.1:5005
python main.py
```

### 4) Frontend (Vite dev server, default `:5173`)

```bash
cd frontend
npm install
npm run dev
```

---

## 💬 Credits

Developed by **Melek**  
Powered by **Ollama + Mistral + FastAPI + Flask + React**
