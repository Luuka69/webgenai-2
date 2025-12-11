# 🧠 WebGen AI

**WebGen AI** is a full-stack, containerized AI platform that generates **complete web pages** from plain text descriptions using **Ollama + Mistral**.

Simply describe a web interface (e.g. *“A login page with username and password fields, and a login button”*), and the system generates a complete responsive HTML/CSS page with a live preview.

---

## 🚀 Features

✅ Generate HTML/CSS layouts from plain text  
✅ Interactive React-based frontend with live iframe preview  
✅ FastAPI backend to route AI requests  
✅ Flask-based AI Engine for AI processing  
✅ Mistral model via Ollama for smart web generation  
✅ Fully containerized architecture (Docker + Compose)  
✅ Easily deployable on any Linux or cloud server  

---

## 🧩 Architecture

```
Frontend (React + Nginx, port 8090)
   │
   ▼
Backend API (FastAPI, port 8010)
   │
   ▼
AI Engine (Flask, port 5005)
   │
   ▼
Ollama (Mistral model, host port 11434)
```

---

## ⚙️ Ports Configuration

| Service | Host Port | Container Port | Description |
|----------|------------|----------------|-------------|
| Frontend | **8090** | 80 | React UI served by Nginx |
| Backend API | **8010** | 8000 | FastAPI REST service |
| AI Engine | **5005** | 5005 | Flask service linked to Ollama |
| Ollama | **11434** | 11434 | Model endpoint |

---

## 📁 Project Structure

```
webgen-ai/
├── backend-api/
│   ├── main.py
│   └── requirements.txt
├── ai-engine/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx
│   ├── src/App.css
│   └── nginx.conf
├── docker-compose.yml
├── .env
└── README.md
```

---

## 🧾 Environment Configuration (`.env`)

```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8010
AI_ENGINE_URL=http://webgen-ai-ai-engine:5005

# AI Engine
AI_ENGINE_HOST=0.0.0.0
AI_ENGINE_PORT=5005
OLLAMA_URL=http://host.docker.internal:11434

# Frontend
FRONTEND_PORT=8090
VITE_API_URL=http://51.75.240.22:8010
```

---

## 🐳 Docker Setup (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend-api:
    build: ./backend-api
    container_name: webgen-ai-backend-api
    ports:
      - "8010:8000"
    environment:
      - AI_ENGINE_URL=http://webgen-ai-ai-engine:5005
    depends_on:
      - ai-engine
    networks:
      - webnet

  ai-engine:
    build: ./ai-engine
    container_name: webgen-ai-ai-engine
    ports:
      - "5005:5005"
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - webnet

  frontend:
    build: ./frontend
    container_name: webgen-ai-frontend
    ports:
      - "8090:80"
    depends_on:
      - backend-api
    networks:
      - webnet

networks:
  webnet:
    driver: bridge
```

---

## 🧪 Testing Commands

### Ollama Test
```bash
curl http://127.0.0.1:11434/api/tags
```

### Docker Lifecycle
```bash
docker compose build --no-cache
docker compose up -d
docker compose down -v
docker compose logs -f
docker ps --format "table {{.Names}}	{{.Ports}}	{{.Status}}"
```

### Server SSH Access
```bash
ssh melek@51.75.240.22
cd /opt/webgenai/webgen-ai
source .venv/bin/activate
```

### Backend Check
```bash
curl http://51.75.240.22:8010
```

### Frontend Access
Open [http://51.75.240.22:8090](http://51.75.240.22:8090)

---

## ✅ Current Status

| Component | Status | Port |
|------------|----------|------|
| Frontend | 🟢 Running | 8090 |
| Backend API | 🟢 Running | 8010 |
| AI Engine | 🟢 Running | 5005 |
| Ollama | 🟢 Active | 11434 |

---

## 💬 Credits

Developed by **Melek & Team**  
Powered by **Ollama + Mistral + FastAPI + Flask + React**
