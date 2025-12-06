import json
import re
from typing import Any, Dict, Optional, Tuple

from ai_engine.services.ai_client import call_ollama


PROMPT_TEMPLATE = (
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
    "Description: \"{description}\""
)


def build_prompt(description: str) -> str:
    return PROMPT_TEMPLATE.format(description=description)


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r"^```[\w-]*\s*", '', stripped)
    if stripped.endswith('```'):
        stripped = re.sub(r"\s*```$", '', stripped)
    return stripped.strip()


def _extract_json_block(text: str) -> Optional[str]:
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def _parse_generated_payload(generated: Any) -> Tuple[Optional[Any], str, str]:
    if isinstance(generated, dict):
        structure = generated.get('structure')
        code = generated.get('code', '') or ''
        raw_text = json.dumps(generated)
        return structure, code, raw_text

    if not isinstance(generated, str):
        return None, '', ''

    raw_text = generated.strip()
    cleaned = _strip_code_fences(raw_text)

    json_block = _extract_json_block(cleaned)
    if json_block:
        try:
            parsed = json.loads(json_block)
            if isinstance(parsed, dict):
                return (
                    parsed.get('structure'),
                    parsed.get('code', '') or '',
                    cleaned,
                )
        except json.JSONDecodeError:
            pass

    return None, cleaned, cleaned


def _is_valid_html(candidate: str) -> bool:
    if not isinstance(candidate, str):
        return False
    lowered = candidate.strip().lower()
    return bool(lowered) and ('<!doctype' in lowered or '<html' in lowered)


def generate_screen(description: str) -> Dict[str, Any]:
    prompt = build_prompt(description)
    try:
        ai_payload = call_ollama(prompt)
    except Exception as exc:  # pragma: no cover - external failure path
        return {'error': f'Ollama request failed: {exc}'}

    generated = ai_payload.get('generated', '')
    structure, code, raw_text = _parse_generated_payload(generated)

    if _is_valid_html(code):
        return {
            'structure': structure,
            'code': code or '',
            'raw_response': raw_text,
        }

    return {
        'error': 'Model failed to produce valid HTML.',
        'raw_response': raw_text,
    }
