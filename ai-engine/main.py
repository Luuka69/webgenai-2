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
        "You are a web UI generator AI.\n"
        "Given the user description, respond with exactly ONE JSON object containing only two keys: \"structure\" and \"code\".\n"
        "Example (follow the schema and quoting exactly):\n"
        "{\n"
        "  \"structure\": {\n"
        "    \"title\": \"Login Page\",\n"
        "    \"elements\": [\"form\", \"input\", \"button\"]\n"
        "  },\n"
        "  \"code\": \"<!DOCTYPE html><html lang=\\\"en\\\"><head><meta charset=\\\"UTF-8\\\"><meta name=\\\"viewport\\\" content=\\\"width=device-width, initial-scale=1.0\\\"><title>Login Page</title><style>/* CSS here */</style></head><body><h1>Login</h1></body></html>\"\n"
        "}\n"
        "Rules:\n"
        "- \"code\" MUST be a single string containing a complete, valid HTML5 document beginning with <!DOCTYPE html>.\n"
        "- Include <head> with meta tags, title, and one <style> block containing all CSS (no external assets).\n"
        "- Use accessible, semantic markup (header, main, nav, footer, labels, alt text, aria-* etc.).\n"
        "- Keep styling modern and responsive (flexbox/grid) with a professional tone.\n"
        "- Do not return arrays, markdown fences, explanations, or additional keys.\n"
        "- If you fail to satisfy any rule, regenerate internally before responding.\n"
        f'Description: \"{description}\"'
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


def _is_valid_html(candidate: str) -> bool:
    """Check if the given string looks like valid HTML output."""
    if not isinstance(candidate, str):
        return False
    lowered = candidate.strip().lower()
    return bool(lowered) and ("<!doctype" in lowered or "<html" in lowered)


def _generate_with_retry(description: str, retries: int = 1) -> Dict[str, Any]:
    """
    Call Ollama to generate the page, validating output.
    Retry up to `retries` times if HTML is missing or malformed.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_prompt(description),
        "stream": False,
        "format": "json",
    }

    for attempt in range(retries + 1):
        try:
            ollama_payload = _call_ollama(payload)
        except requests.RequestException as exc:
            return {"error": f"Ollama request failed: {exc}"}
        except ValueError:
            return {"error": "Ollama returned invalid JSON"}

        generated = ollama_payload.get("response", "")
        if isinstance(generated, str):
            generated = generated.strip()

        structure, code, raw_text = _parse_generated_payload(generated)

        if _is_valid_html(code):
            return {
                "structure": structure,
                "code": code or "",
                "raw_response": raw_text,
            }

        if attempt < retries:
            print("⚠️ Model failed to produce HTML — retrying...")
            payload["prompt"] = _build_prompt(description)
            payload["prompt"] += (
                "\n\nYour last answer omitted the HTML document. "
                "Return the same JSON schema with a 'code' field containing a valid HTML5 document."
            )
        else:
            return {
                "error": "Model failed to produce valid HTML after retry.",
                "raw_response": raw_text,
            }

    return {"error": "Unknown generation failure."}


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

    result = _generate_with_retry(description, retries=1)

    if "error" in result:
        status = 502 if "raw_response" in result else 502
        return jsonify(result), status

    return jsonify(result)


if __name__ == "__main__":
    print(f"AI Engine running on {AI_ENGINE_HOST}:{AI_ENGINE_PORT}")
    app.run(host=AI_ENGINE_HOST, port=AI_ENGINE_PORT)
