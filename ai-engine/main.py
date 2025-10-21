from fastapi import FastAPI, Request
import requests, json, os

app = FastAPI()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

@app.get("/")
def root():
    return {"status": "AI Engine running"}

@app.post("/generate")
def generate(request: Request):
    data = request.json()
    description = data.get("description", "")
    prompt = f"""
You are an assistant that generates HTML+CSS web screens.
Description: "{description}"
Output HTML (include inline CSS).
    """
    r = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )
    result = r.json()
    html_output = result.get("response", "<p>Error generating</p>")
    return {"html": html_output}
