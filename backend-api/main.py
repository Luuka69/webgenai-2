import os
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# ✅ Correct internal Docker hostname for AI engine
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://webgen-ai-ai-engine:5005")

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

app = FastAPI(title="WebGen AI Backend")

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----
@app.post("/api/generate")
async def generate(request: Request):
    data = await request.json()
    description = data.get("description", "")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AI_ENGINE_URL}/process", json={"description": description})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Backend could not reach AI Engine: {str(e)}"}

@app.get("/")
def root():
    return {"message": "WebGen AI Backend running", "ai_engine_url": AI_ENGINE_URL}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
