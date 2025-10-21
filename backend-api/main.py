from fastapi import FastAPI, Request
import os, requests

app = FastAPI()
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8500")

@app.get("/")
def root():
    return {"status": "Backend API running"}

@app.post("/generate")
def generate(request: Request):
    data = request.json()
    description = data.get("description", "")
    response = requests.post(f"{AI_ENGINE_URL}/generate", json={"description": description})
    return response.json()
