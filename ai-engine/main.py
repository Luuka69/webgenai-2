import json
import os
from typing import Any, Dict

import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Load environment variables once on startup
load_dotenv()


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
AI_ENGINE_HOST = os.getenv("AI_ENGINE_HOST", "0.0.0.0")
AI_ENGINE_PORT = int(os.getenv("AI_ENGINE_PORT", "5005"))

app = Flask(__name__)


def _build_prompt(description: str) -> str:
    """Create the instruction sent to the LLM."""
    return (
        "You are a web interface generator AI.\n"
        f'Given this description: "{description}",\n'
        "output a JSON object with two keys:\n"
        '1. \"structure\": structured component description\n'
        '2. \"code\": full HTML+CSS for the page'
    )


def _call_ollama(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send the request to Ollama and return its JSON payload."""
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    return response.json()


@app.route("/")
def home():
    return jsonify({"message": "AI Engine running", "ollama_url": OLLAMA_URL})


@app.route("/process", methods=["POST"])
def process():
    """
    Receives a description from the backend, sends it to Ollama,
    parses the LLM output, and returns structured data + HTML.
    """
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()

    if not description:
        return jsonify({"error": "Description is required"}), 400

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_prompt(description),
        "stream": False,
        "format": "json",
    }

    try:
        ollama_payload = _call_ollama(payload)
    except requests.RequestException as exc:
        return jsonify({"error": f"Ollama request failed: {exc}"}), 502
    except ValueError:
        return jsonify({"error": "Ollama returned invalid JSON"}), 502

    generated = ollama_payload.get("response", "")
    if isinstance(generated, str):
        generated = generated.strip()

    structure = None
    code = ""

    if generated:
        try:
            parsed = json.loads(generated)
            if isinstance(parsed, dict):
                structure = parsed.get("structure")
                code = parsed.get("code", "") or ""
            else:
                code = generated
        except json.JSONDecodeError:
            code = generated

    return jsonify(
        {
            "structure": structure,
            "code": code or "",
            "raw_response": generated,
        }
    )


if __name__ == "__main__":
    print(f"AI Engine running on {AI_ENGINE_HOST}:{AI_ENGINE_PORT}")
    app.run(host=AI_ENGINE_HOST, port=AI_ENGINE_PORT)
