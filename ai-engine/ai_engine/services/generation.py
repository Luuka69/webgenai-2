import json
import html
import re
from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

from ai_engine.schemas.pydantic import AIResponse
from ai_engine.services.ai_client import call_ollama


PROMPT_TEMPLATE = (
    "You are a web UI generator AI.\n"
    "\n"
    "Given the user description, respond with EXACTLY ONE JSON object containing ONLY two keys: \"structure\" and \"code\".\n"
    "Return JSON only (no markdown, no explanations, no extra keys).\n"
    "\n"
    "HARD RULES:\n"
    "- The \"code\" value MUST be a SINGLE STRING that is a COMPLETE, valid HTML5 document starting with \"<!DOCTYPE html>\".\n"
    "- The HTML MUST include: <html>, <head>, <meta charset>, <meta name=\\\"viewport\\\">, <title>, ONE <style> block, and <body>.\n"
    "- Do NOT use ellipsis placeholders (three dots) anywhere in the output.\n"
    "- Do NOT write words like \"truncated\", \"for brevity\", or \"TODO\" anywhere.\n"
    "- Do NOT include HTML comments.\n"
    "- Use only valid CSS (no SCSS nesting).\n"
    "- No external assets, no external CSS/JS.\n"
    "- The HTML must render visible content: include an <h1> and the real UI elements described (inputs/buttons/table/etc.).\n"
    "- If it is a TABLE/LIST screen: include a real <table> with <thead> and at least ONE <tbody><tr> row (dummy values like \"—\" are OK).\n"
    "- If it is a FORM screen: include a real <form> with labels + inputs and at least one primary <button type=\\\"submit\\\">.\n"
    "\n"
    "Example:\n"
    "{\n"
    "  \"structure\": {\"title\":\"Login Page\",\"elements\":[\"form\",\"input\",\"button\"]},\n"
    "  \"code\": \"<!DOCTYPE html><html lang=\\\"en\\\"><head><meta charset=\\\"UTF-8\\\"><meta name=\\\"viewport\\\" content=\\\"width=device-width, initial-scale=1.0\\\"><title>Login Page</title><style>body{font-family:system-ui;margin:0;padding:24px;background:#f3f4f6}main{max-width:560px;margin:0 auto;background:#fff;padding:20px;border-radius:12px}label{display:block;margin:12px 0 6px}input{width:100%;padding:10px;border:1px solid #d1d5db;border-radius:10px}button{margin-top:14px;padding:10px 14px;border:0;border-radius:999px;background:#2563eb;color:#fff}</style></head><body><main><h1>Login</h1><form><label>Email</label><input type=\\\"email\\\" required><label>Password</label><input type=\\\"password\\\" required><button type=\\\"submit\\\">Sign in</button></form></main></body></html>\"\n"
    "}\n"
    "\n"
    "Description: \"{description}\"\n"
)





def build_prompt(description: str) -> str:
    # Avoid str.format collisions with the many braces in the template.
    return PROMPT_TEMPLATE.replace("{description}", description)


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r"^```[\w-]*\s*", '', stripped)
    if stripped.endswith('```'):
        stripped = re.sub(r"\s*```$", '', stripped)
    return stripped.strip()


def _extract_json_block(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None

    in_string = False
    escape = False
    depth = 0

    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    return None


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

    # Salvage path: the model sometimes outputs malformed JSON (e.g. unescaped newlines)
    # but still includes a complete HTML document we can extract for preview.
    lowered = cleaned.lower()
    start = lowered.find("<!doctype html")
    if start != -1:
        end = lowered.find("</html>", start)
        if end != -1:
            html = cleaned[start : end + len("</html>")]
            return None, html, cleaned

    return None, cleaned, cleaned


def _is_valid_html(candidate: str) -> bool:
    if not isinstance(candidate, str):
        return False
    text = candidate.strip()
    if not text:
        return False
    lowered = text.lower()

    # Must be an HTML document, not JSON that happens to contain HTML.
    if not re.match(r"(?is)^<!doctype\s+html\b", text):
        return False
    if "<html" not in lowered or "</html>" not in lowered:
        return False

    # Reject common placeholder patterns that break preview rendering.
    if "..." in text or "…" in text:
        return False
    if "truncated" in lowered or "for brevity" in lowered or "todo" in lowered:
        return False

    return True


def _build_fallback_html(title: str) -> str:
    safe_title = html.escape((title or "Generated Screen").strip()) or "Generated Screen"
    return (
        "<!DOCTYPE html>"
        "<html lang=\"en\">"
        "<head>"
        "<meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
        f"<title>{safe_title}</title>"
        "<style>"
        "body{font-family:system-ui;margin:0;padding:24px;background:#f3f4f6;color:#111827}"
        "main{max-width:760px;margin:0 auto;background:#fff;padding:20px;border-radius:12px;"
        "box-shadow:0 10px 30px rgba(15,23,42,.08)}"
        "h1{margin:0 0 8px;font-size:1.6rem}"
        "p{margin:0;line-height:1.5;color:#374151}"
        "</style>"
        "</head>"
        "<body>"
        "<main>"
        f"<h1>{safe_title}</h1>"
        "<p>Preview generated with a minimal template. Retry to regenerate a richer UI.</p>"
        "</main>"
        "</body>"
        "</html>"
    )


def generate_screen(description: str) -> Dict[str, Any]:
    prompt = build_prompt(description)
    raw_text = ""
    structure = None
    code = ""

    # Best-effort retry: models sometimes return placeholders or malformed output.
    for attempt in range(2):
        try:
            ai_payload = call_ollama(prompt)
        except Exception as exc:  # pragma: no cover - external failure path
            return {'error': f'Ollama request failed: {exc}'}

        generated = ai_payload.get('generated', '')
        structure, code, raw_text = _parse_generated_payload(generated)

        if _is_valid_html(code):
            break

        # Strengthen the instruction on retry.
        prompt = (
            build_prompt(description)
            + "\n\nYour previous output was invalid. Regenerate and strictly follow the rules."
        )

    preview_fallback = False
    if not _is_valid_html(code):
        preview_fallback = True
        code = _build_fallback_html("Generated Screen")
        if structure is None:
            structure = {"title": "Generated Screen", "elements": []}

    try:
        ai_response = AIResponse(
            structure=structure,
            code=code or '',
            raw_response=raw_text,
            preview_fallback=preview_fallback,
        )
    except ValidationError as exc:
        return {
            'error': 'Invalid AI response schema.',
            'details': exc.errors(),
            'raw_response': raw_text,
        }

    return ai_response.dict()
