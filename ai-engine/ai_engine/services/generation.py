import json
import re
from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

from ai_engine.schemas.pydantic import AIResponse
from ai_engine.services.ai_client import call_ollama


PROMPT_TEMPLATE = (
    "You are WebGen UI, a deterministic UI generator.\n"
    "\n"
    "TASK\n"
    "- Given a natural language description, you must output EXACTLY ONE JSON object\n"
    "  with ONLY two keys: \"structure\" and \"code\".\n"
    "- \"code\" MUST be based on one of the two templates below (FORM or TABLE).\n"
    "- You are NOT allowed to invent a different layout structure.\n"
    "\n"
    "JSON SHAPE (MANDATORY)\n"
    "{\n"
    "  \"structure\": { \"title\": \"...\", \"elements\": [ ... ] },\n"
    "  \"code\": \"<!DOCTYPE html>...\"\n"
    "}\n"
    "\n"
    "TEMPLATE A – FORM PAGE (use when the description is mainly about a form)\n"
    "You MUST keep the overall structure and classes and only customize:\n"
    "- The <title> text\n"
    "- The <h1> main title\n"
    "- Optional subtitle text\n"
    "- The inner fields inside <!-- FORM_FIELDS -->\n"
    "- Button labels in <!-- ACTION_BUTTONS -->\n"
    "\n"
    "<!DOCTYPE html><html lang=\"en\">\n"
    "<head>\n"
    "  <meta charset=\"UTF-8\">\n"
    "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    "  <title>__PAGE_TITLE__</title>\n"
    "  <style>\n"
    "    :root { --primary: #2563eb; }\n"
    "    * { box-sizing: border-box; }\n"
    "    body {\n"
    "      margin: 0;\n"
    "      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n"
    "      background-color: #f3f4f6;\n"
    "      color: #111827;\n"
    "    }\n"
    "    .page {\n"
    "      min-height: 100vh;\n"
    "      display: flex;\n"
    "      justify-content: center;\n"
    "      align-items: flex-start;\n"
    "      padding: 32px 16px;\n"
    "    }\n"
    "    .card {\n"
    "      width: 100%;\n"
    "      max-width: 960px;\n"
    "      background-color: #ffffff;\n"
    "      border-radius: 16px;\n"
    "      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.15);\n"
    "      padding: 24px 28px;\n"
    "    }\n"
    "    .card-header { margin-bottom: 24px; }\n"
    "    .card-title {\n"
    "      margin: 0 0 8px;\n"
    "      font-size: 1.9rem;\n"
    "      font-weight: 600;\n"
    "    }\n"
    "    .card-subtitle {\n"
    "      margin: 0;\n"
    "      font-size: 0.95rem;\n"
    "      color: #6b7280;\n"
    "    }\n"
    "    form {\n"
    "      display: flex;\n"
    "      flex-direction: column;\n"
    "      gap: 20px;\n"
    "    }\n"
    "    .form-grid {\n"
    "      display: grid;\n"
    "      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));\n"
    "      gap: 16px 24px;\n"
    "    }\n"
    "    .field {\n"
    "      display: flex;\n"
    "      flex-direction: column;\n"
    "      gap: 4px;\n"
    "    }\n"
    "    label {\n"
    "      font-size: 0.9rem;\n"
    "      color: #374151;\n"
    "    }\n"
    "    input, select, textarea {\n"
    "      width: 100%;\n"
    "      padding: 9px 11px;\n"
    "      border-radius: 10px;\n"
    "      border: 1px solid #d1d5db;\n"
    "      font-size: 0.95rem;\n"
    "      outline: none;\n"
    "    }\n"
    "    input:focus, select:focus, textarea:focus {\n"
    "      border-color: var(--primary);\n"
    "      box-shadow: 0 0 0 1px var(--primary);\n"
    "    }\n"
    "    textarea { min-height: 120px; resize: vertical; }\n"
    "    .actions {\n"
    "      margin-top: 8px;\n"
    "      display: flex;\n"
    "      justify-content: flex-end;\n"
    "      gap: 12px;\n"
    "    }\n"
    "    .btn-primary,\n"
    "    .btn-secondary {\n"
    "      border-radius: 999px;\n"
    "      border: none;\n"
    "      padding: 9px 20px;\n"
    "      font-size: 0.95rem;\n"
    "      cursor: pointer;\n"
    "      transition: background-color 0.18s ease, color 0.18s ease, transform 0.12s ease;\n"
    "    }\n"
    "    .btn-primary {\n"
    "      background-color: var(--primary);\n"
    "      color: #ffffff;\n"
    "    }\n"
    "    .btn-secondary {\n"
    "      background-color: #ffffff;\n"
    "      color: #374151;\n"
    "      border: 1px solid #d1d5db;\n"
    "    }\n"
    "    .btn-primary:hover { background-color: #1d4ed8; transform: translateY(-1px); }\n"
    "    .btn-secondary:hover { background-color: #f9fafb; transform: translateY(-1px); }\n"
    "    @media (max-width: 640px) {\n"
    "      .card { padding: 20px 16px; }\n"
    "    }\n"
    "  </style>\n"
    "</head>\n"
    "<body>\n"
    "  <div class=\"page\">\n"
    "    <div class=\"card\">\n"
    "      <header class=\"card-header\">\n"
    "        <h1 class=\"card-title\">__MAIN_TITLE__</h1>\n"
    "        <p class=\"card-subtitle\">__SUBTITLE__</p>\n"
    "      </header>\n"
    "      <main>\n"
    "        <form aria-label=\"__MAIN_TITLE__\">\n"
    "          <div class=\"form-grid\">\n"
    "            <!-- FORM_FIELDS -->\n"
    "          </div>\n"
    "          <div class=\"actions\">\n"
    "            <!-- ACTION_BUTTONS -->\n"
    "          </div>\n"
    "        </form>\n"
    "      </main>\n"
    "    </div>\n"
    "  </div>\n"
    "</body>\n"
    "</html>\n"
    "\n"
    "TEMPLATE B – TABLE / LIST PAGE (use when the description clearly talks about a table or list of items)\n"
    "- Keep page/card styles identical, but the main content is a table and toolbar.\n"
    "\n"
    "<!DOCTYPE html><html lang=\"en\">\n"
    "<head>\n"
    "  <meta charset=\"UTF-8\">\n"
    "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    "  <title>__PAGE_TITLE__</title>\n"
    "  <style>\n"
    "    :root { --primary: #2563eb; }\n"
    "    * { box-sizing: border-box; }\n"
    "    body {\n"
    "      margin: 0;\n"
    "      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n"
    "      background-color: #f3f4f6;\n"
    "      color: #111827;\n"
    "    }\n"
    "    .page { min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 32px 16px; }\n"
    "    .card { width: 100%; max-width: 1200px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.15); padding: 24px 28px; }\n"
    "    .card-header { margin-bottom: 16px; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }\n"
    "    .card-title { margin: 0; font-size: 1.9rem; font-weight: 600; }\n"
    "    .card-subtitle { margin: 0; font-size: 0.95rem; color: #6b7280; }\n"
    "    .toolbar { margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; }\n"
    "    .toolbar-left, .toolbar-right { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }\n"
    "    .toolbar input[type=\"search\"], .toolbar select { padding: 7px 10px; border-radius: 999px; border: 1px solid #d1d5db; font-size: 0.9rem; }\n"
    "    .btn-primary { background-color: var(--primary); color: #ffffff; border-radius: 999px; border: none; padding: 7px 16px; font-size: 0.9rem; cursor: pointer; }\n"
    "    .btn-primary:hover { background-color: #1d4ed8; }\n"
    "    table { width: 100%; border-collapse: collapse; border-radius: 12px; overflow: hidden; margin-top: 4px; }\n"
    "    thead { background-color: #f9fafb; }\n"
    "    th, td { padding: 10px 12px; text-align: left; font-size: 0.9rem; border-bottom: 1px solid #e5e7eb; }\n"
    "    tbody tr:hover { background-color: #f3f4ff; }\n"
    "    .status-chip { display: inline-flex; align-items: center; justify-content: center; padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 500; background-color: #e5edff; color: #1d4ed8; }\n"
    "    .pagination { margin-top: 12px; display: flex; justify-content: flex-end; gap: 4px; font-size: 0.85rem; }\n"
    "    .page-link { padding: 4px 8px; border-radius: 999px; border: 1px solid transparent; cursor: pointer; }\n"
    "    .page-link.active { background-color: var(--primary); color: #ffffff; }\n"
    "    @media (max-width: 640px) { .card { padding: 20px 12px; } table { font-size: 0.8rem; } th, td { padding: 8px 8px; } }\n"
    "  </style>\n"
    "</head>\n"
    "<body>\n"
    "  <div class=\"page\">\n"
    "    <div class=\"card\">\n"
    "      <header class=\"card-header\">\n"
    "        <div>\n"
    "          <h1 class=\"card-title\">__MAIN_TITLE__</h1>\n"
    "          <p class=\"card-subtitle\">__SUBTITLE__</p>\n"
    "        </div>\n"
    "        <!-- OPTIONAL_HEADER_ACTIONS -->\n"
    "      </header>\n"
    "      <div class=\"toolbar\">\n"
    "        <div class=\"toolbar-left\">\n"
    "          <!-- SEARCH_FILTERS -->\n"
    "        </div>\n"
    "        <div class=\"toolbar-right\">\n"
    "          <!-- TOOLBAR_ACTIONS -->\n"
    "        </div>\n"
    "      </div>\n"
    "      <main>\n"
    "        <!-- DATA_TABLE -->\n"
    "        <div class=\"pagination\">\n"
    "          <!-- PAGINATION -->\n"
    "        </div>\n"
    "      </main>\n"
    "    </div>\n"
    "  </div>\n"
    "</body>\n"
    "</html>\n"
    "\n"
    "STRICT CSS RULES\n"
    "- CSS MUST be valid standard CSS.\n"
    "- DO NOT use SCSS/Sass features (no '&:hover', no nested '@media').\n"
    "- All '@media' rules must be at top level inside <style>, not nested in selectors.\n"
    "- Do NOT use <table> for positioning forms; only for real tabular data.\n"
    "\n"
    "HOW TO CHOOSE THE TEMPLATE\n"
    "- If the description talks about a form, creation, edition, details with inputs → use TEMPLATE A.\n"
    "- If the description talks about a table, list, grid of rows, filters, pagination → use TEMPLATE B.\n"
    "\n"
    "STRUCTURE FIELD\n"
    "- \"structure.title\" = human-readable screen title.\n"
    "- \"structure.elements\" = list of high-level elements you used (e.g. [\"form\", \"input\", \"textarea\", \"table\"…]).\n"
    "\n"
    "Output ONLY the JSON object, no markdown, no extra text.\n"
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

    if not _is_valid_html(code):
        return {
            'error': 'Model failed to produce valid HTML.',
            'raw_response': raw_text,
        }

    try:
        ai_response = AIResponse(
            structure=structure,
            code=code or '',
            raw_response=raw_text,
        )
    except ValidationError as exc:
        return {
            'error': 'Invalid AI response schema.',
            'details': exc.errors(),
            'raw_response': raw_text,
        }

    return ai_response.dict()
