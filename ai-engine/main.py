import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ✅ Ollama inside same host (localhost on the server)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_ENGINE_HOST = os.getenv("AI_ENGINE_HOST", "0.0.0.0")
AI_ENGINE_PORT = int(os.getenv("AI_ENGINE_PORT", "5005"))

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "AI Engine running", "ollama_url": OLLAMA_URL})

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    description = data.get("description", "")

    prompt = f"""
    You are a web interface generator AI.
    Given this description: "{description}",
    return a JSON object with two keys:
    - "structure": summary of the page layout
    - "html": full HTML+CSS code of the page
    """

    payload = {"model": "mistral", "prompt": prompt}

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=600)
        response.raise_for_status()
        ollama_result = response.json()

        # Extract the text part safely
        generated_text = ollama_result.get("response", "")
        return jsonify({
            "structure": "auto-generated",
            "html": generated_text or "<p>No content generated.</p>"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to reach Ollama: {str(e)}"}), 500


if __name__ == "__main__":
    print(f"✅ AI Engine running on {AI_ENGINE_HOST}:{AI_ENGINE_PORT}")
    app.run(host=AI_ENGINE_HOST, port=AI_ENGINE_PORT)
