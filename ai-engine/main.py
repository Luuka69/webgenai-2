import html
import json
import os
import re
from collections.abc import Iterable
from typing import Any, Dict, Optional, Tuple, Union

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


def _camel_to_kebab(value: str) -> str:
    """Convert camelCase style keys into kebab-case for CSS."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", value).lower()


def _styles_to_inline(styles: Dict[str, Any]) -> str:
    """Transform a style dict into an inline CSS string."""
    if not styles:
        return ""
    parts = []
    for key, val in styles.items():
        if val is None:
            continue
        parts.append(f"{_camel_to_kebab(str(key))}: {val}")
    return "; ".join(parts)


def _normalize_attributes(props: Dict[str, Any]) -> Dict[str, str]:
    """Flatten prop dictionaries to HTML attributes."""
    attrs: Dict[str, str] = {}
    for key, value in props.items():
        if value is None:
            continue
        attr_name = "class" if key == "className" else key
        if isinstance(value, bool):
            if value:
                attrs[attr_name] = attr_name
            continue
        attrs[attr_name] = str(value)
    return attrs


def _collect_attributes(node: Dict[str, Any]) -> Dict[str, str]:
    """Gather attributes from props and top-level keys."""
    attrs: Dict[str, str] = {}
    if "id" in node and node["id"]:
        attrs["id"] = str(node["id"])

    props = node.get("props")
    if isinstance(props, dict):
        attrs.update(_normalize_attributes(props))

    for key, value in node.items():
        if key in {"type", "children", "styles", "text", "props", "id"}:
            continue
        if value is None:
            continue
        attrs.setdefault(key, str(value))

    styles = node.get("styles")
    style_str = _styles_to_inline(styles) if isinstance(styles, dict) else ""
    if style_str:
        attrs["style"] = style_str

    return attrs


def _attrs_to_string(attrs: Dict[str, str]) -> str:
    if not attrs:
        return ""
    parts = []
    for key, value in attrs.items():
        escaped = html.escape(value, quote=True)
        parts.append(f'{key}="{escaped}"')
    return " " + " ".join(parts)


SELF_CLOSING_TAGS = {"img", "input", "hr", "br", "meta", "link"}


def _render_node(node: Dict[str, Any]) -> str:
    """Recursively render a JSON node into HTML."""
    if not isinstance(node, dict):
        return ""

    tag = (node.get("type") or "div").lower()
    attrs = _attrs_to_string(_collect_attributes(node))
    text = html.escape(str(node.get("text", "") or ""))

    children_html = ""
    children = node.get("children")
    if isinstance(children, Iterable) and not isinstance(children, (str, bytes, dict)):
        children_html = "".join(
            _render_node(child) for child in children if isinstance(child, dict)
        )
    elif isinstance(children, dict):
        children_html = _render_node(children)

    if tag in SELF_CLOSING_TAGS and not children_html:
        return f"<{tag}{attrs} />"

    return f"<{tag}{attrs}>{text}{children_html}</{tag}>"


BASE_CSS = """
body {
  margin: 0;
  font-family: 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f7fb;
  color: #1f2933;
}
* {
  box-sizing: border-box;
}
a {
  color: #2563eb;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  text-align: left;
}
button {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
}
"""


def _render_structure_html(structure: Union[Dict[str, Any], Iterable[Any]]) -> str:
    """Render the provided structure into a full HTML document."""
    nodes: Iterable[Dict[str, Any]]
    if isinstance(structure, dict):
        if "layout" in structure and isinstance(structure["layout"], Iterable):
            nodes = [
                child for child in structure["layout"] if isinstance(child, dict)
            ]
        else:
            nodes = [structure]
    elif isinstance(structure, Iterable):
        nodes = [node for node in structure if isinstance(node, dict)]
    else:
        return ""

    body_html = "".join(_render_node(node) for node in nodes)
    return (
        "<!DOCTYPE html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='UTF-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0' />"
        "<title>Generated Interface</title>"
        f"<style>{BASE_CSS}</style>"
        "</head>"
        f"<body>{body_html}</body>"
        "</html>"
    )


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

    if structure is not None and (not code or not code.strip()):
        try:
            rendered = _render_structure_html(structure)
        except Exception:
            rendered = ""
        if rendered:
            code = rendered

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
