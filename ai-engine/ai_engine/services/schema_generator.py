from typing import Any, Dict, Optional
import json
import logging
from ai_engine.services.ai_client import call_ollama
from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload


SCHEMA_PROMPT = """You are WebGen AI. Given a natural language screen prompt, screen_schema, and context IDs, output JSON matching Oracle metadata tables.
Inputs:
- prompt: "{prompt}"
- context: {context}
- screen_schema: {screen_schema}
Output EXACT JSON with four top-level keys:
{{
  "ihm": {{
    "LOAD_IHM": {{
      "screenSchema": {{ ... }},   // any schema you infer
      "html": "<!DOCTYPE html> ...", // full HTML for the screen
      "version": 1
    }}
  }},
  "tab_ihm_wf": [
    {{
      "ID_CLIENT": <int>,
      "ID_WF": "<wf id>",
      "ID_TACHE": "<task id>",
      "ID_IHM": "<screen id>",
      "ID_TAB": "<UPPERCASE_TABLE_ID>",
      "TYPE_TAB": "M" or "D",
      "ID_TAB_MAITRE": null or "<master table id>",
      "LOAD_TAB": {{ "columns": [ {{ "name": "...", "type": "VARCHAR2(255)", "required": bool }} ], "primaryKey": [...]? }},
      "DEFAULT_WHERE_TAB": null,
      "CREATED_AT": null,
      "UPDATED_AT": null
    }}
  ],
  "element_ihm_wf": [
    {{
      "ID_CLIENT": <int>,
      "ID_WF": "<wf id>",
      "ID_TACHE": "<task id>",
      "ID_IHM": "<screen id>",
      "ID_TAB": "<table id>",
      "ID_ELEMENT": "<UPPERCASE_ELEMENT_ID>",
      "TYPE_ELEMENT": "input_text|input_email|textarea|select|date|grid|number|tel|checkbox|radio",
      "LONGEUR_ELEMENT": "255" ?,
      "SQL_LOV_ELEMENT": null or string,
      "TRANSIT": "N",
      "POSITION_X": <int>,
      "POSITION_Y": <int>,
      "HINT_ELEMENT": "<label/placeholder>",
      "CONTROL_ELEMENT": null,
      "VALIDATEUR_ELEMENT": {{ "required": bool }}?,
      "DEFAULT_VALUE_ELEMENT": null,
      "ACTIVE": "O",
      "CODITION_ACTIVE": null,
      "CREATED_AT": null,
      "UPDATED_AT": null
    }}
  ],
  "tab_detail_ihm_wf": [
    {{
      "ID_CLIENT": <int>,
      "ID_WF": "<wf id>",
      "ID_TACHE": "<task id>",
      "ID_IHM": "<screen id>",
      "ID_TAB": "<detail table id>",
      "ID_TAB_MAITRE": "<master table id>",
      "ID_ELEM_TAB": "<fk column>",
      "ID_ELEM_TAB_MAITRE": "<pk column>",
      "CREATED_AT": null,
      "UPDATED_AT": null
    }}
  ]
}}
Rules:
- Include ID_CLIENT, ID_WF, ID_TACHE, ID_IHM on every row.
- Use TYPE_TAB M for master, D for detail; set ID_TAB_MAITRE on details.
- Use Oracle-like types: text/email/tel/string→VARCHAR2(255); number→NUMBER; date/datetime→DATE; textarea→CLOB; select/radio→VARCHAR2(255) with CHECK in LOAD_TAB if enumValues known.
- Positions: simple grid numbers (POSITION_X for column, POSITION_Y for row) are fine.
- If no master-detail, return an empty array for tab_detail_ihm_wf.
- Return STRICT JSON only; no prose."""


def build_schema_prompt(prompt: str, screen_schema: Dict[str, Any], context: Dict[str, Any]) -> str:
    # Avoid str.format collisions with braces in the prompt template.
    return (
        SCHEMA_PROMPT
        .replace("{prompt}", prompt)
        .replace("{screen_schema}", json.dumps(screen_schema))
        .replace("{context}", json.dumps(context))
    )

def extract_schema(prompt: str, screen_schema: Dict[str, Any], context: Dict[str, Any]) -> Optional[WorkflowScreenPayload]:
    p = build_schema_prompt(prompt, screen_schema, context)
    resp = call_ollama(p)  # adjust for your model
    raw = resp.get("generated") or resp.get("response") or ""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        ihm = data.get("ihm", {})
        if isinstance(ihm, dict):
            ihm.setdefault("ID_CLIENT", context.get("id_client"))
            ihm.setdefault("ID_WF", context.get("id_wf"))
            ihm.setdefault("ID_TACHE", context.get("id_tache"))
            ihm.setdefault("ID_IHM", context.get("id_ihm"))
            data["ihm"] = ihm
        return WorkflowScreenPayload(**data)
    except Exception:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to parse WorkflowScreenPayload; raw={raw}")
        return None

