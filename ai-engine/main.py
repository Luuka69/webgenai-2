import json
import os
import re
from typing import Any, Dict, Optional, Tuple

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


# ...existing code...
def _build_prompt(description: str) -> str:
    """Create the instruction sent to the LLM."""
    return (
        "You are a professional front-end engineer AI that outputs a single JSON object only.\n"
        "Output requirements (must follow exactly):\n"
        "- Return EXACTLY one JSON object with only these two keys: \"structure\" and \"code\".\n"
        "- Do NOT include markdown fences, explanations, extra keys, or surrounding text.\n"
        "- \"code\" must be a single string containing a complete, standalone HTML document beginning with \"<!DOCTYPE html>\".\n"
        "- The HTML must include: <meta name=\"viewport\">, semantic elements (header, main, nav, footer, etc.), accessible attributes (aria-*, alt, labels), and a single <style> block in <head> containing all CSS.\n"
        "- Use mobile-first responsive CSS (flexbox and/or grid), avoid external resources (no external fonts, CDNs, or scripts). Images may be referenced by URL only if explicitly allowed—prefer placeholders.\n"
        "- Use plain, modern CSS (no frameworks). Keep class/id names semantic and unique. Prefer classes for styling and minimal inline styles.\n"
        "- Ensure CSS is valid, avoids duplicate rules, and includes sensible defaults for typography and spacing. Include comments inside the HTML/CSS only if necessary (these must remain inside the \"code\" string).\n"
        "- \"structure\" must be a JSON object describing the page layout in a machine-readable way. Provide a top-level \"layout\" array of components; each component is an object with keys: type, id, text (or content), props (dictionary of attributes), styles (CSS properties dictionary), and children (array).\n"
        "Example response (follow this structure exactly):\n"
        "{\n"
        "  \"structure\": {\n"
        "    \"layout\": [\n"
        "      {\"type\": \"header\", \"id\": \"site-header\", \"text\": \"Site Title\", \"props\": {\"role\": \"banner\"}, \"styles\": {\"display\": \"flex\"}, \"children\": []}\n"
        "    ]\n"
        "  },\n"
        "  \"code\": \"<!DOCTYPE html>...\"\n"
        "}\n"
        f'Description: \"{description}\"\n'
    )
# ...existing code...


def _call_ollama(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send the request to Ollama and return its JSON payload."""
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    return response.json()


def _strip_code_fences(text: str) -> str:
    """Remove surrounding Markdown code fences that break iframe rendering."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[\w-]*\s*", "", stripped)
    if stripped.endswith("```"):
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_json_block(text: str) -> Optional[str]:
    """Find the first JSON object in the text."""
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def _parse_generated_payload(generated: Any) -> Tuple[Optional[Any], str, str]:
    """
    Normalize Ollama's response into (structure, code, raw_text).
    Returns the raw normalized text so the UI can surface it for debugging.
    """
    if isinstance(generated, dict):
        structure = generated.get("structure")
        code = generated.get("code", "") or ""
        raw_text = json.dumps(generated)
        return structure, code, raw_text

    if not isinstance(generated, str):
        return None, "", ""

    raw_text = generated.strip()
    cleaned = _strip_code_fences(raw_text)

    json_block = _extract_json_block(cleaned)
    if json_block:
        try:
            parsed = json.loads(json_block)
            if isinstance(parsed, dict):
                return (
                    parsed.get("structure"),
                    parsed.get("code", "") or "",
                    cleaned,
                )
        except json.JSONDecodeError:
            pass

    return None, cleaned, cleaned


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

    structure, code, raw_text = _parse_generated_payload(generated)

    return jsonify(
        {
            "structure": structure,
            "code": code or "",
            "raw_response": raw_text,
        }
    )


if __name__ == "__main__":
    print(f"AI Engine running on {AI_ENGINE_HOST}:{AI_ENGINE_PORT}")
    app.run(host=AI_ENGINE_HOST, port=AI_ENGINE_PORT)
