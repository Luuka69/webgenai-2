import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_ENGINE_HOST = os.getenv("AI_ENGINE_HOST", "0.0.0.0")
AI_ENGINE_PORT = int(os.getenv("AI_ENGINE_PORT", "5005"))

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "AI Engine running", "ollama_url": OLLAMA_URL})

@app.route("/process", methods=["POST"])
def process():
    """
    Receives a description from the backend, sends it to Ollama,
    and returns generated HTML/CSS or structured JSON.
    """
    data = request.get_json()
    description = data.get("description", "")

    prompt = f"""
    You are a web interface generator AI.
    Given this description: "{description}",
    output a JSON object with two keys:
    1. "structure": structured component description
    2. "code": full HTML+CSS for the page
    """

    payload = {"model": "mistral", "prompt": prompt}

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=600)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"AI Engine running on {AI_ENGINE_HOST}:{AI_ENGINE_PORT}")
    app.run(host=AI_ENGINE_HOST, port=AI_ENGINE_PORT)
