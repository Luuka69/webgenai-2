from typing import Any, Dict, Optional
import json
import logging
from ai_engine.services.ai_client import call_ollama
from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
from ai_engine.services.raw_metadata_hydrator import (
    RawWorkflowScreenPayload,
    hydrate_oracle_metadata as hydrate_raw_oracle_metadata,
)


SCHEMA_PROMPT = """You are an assistant that generates Oracle metadata for workflow-driven screens.

Context:
- A first LLM generated a high-level screen schema and HTML (preview only).
- Your job (second step) is ONLY to generate Oracle metadata (no HTML).
- The backend will fill the workflow IDs itself and then persist into Oracle tables:
  - TAB_IHM_WF
  - ELEMENT_IHM_WF
  - TAB_DETAIL_IHM_WF

Inputs:
- description (natural language): "{prompt}"
- workflow context (for understanding only): {context}
- optional screen schema + html: {screen_schema}

VERY IMPORTANT RULES
1) Never invent workflow IDs:
   - NEVER invent or derive ID_CLIENT / ID_WF / ID_TACHE / ID_IHM.
   - ALWAYS set those keys to null in your JSON output.
2) Output MUST be valid JSON only:
   - Top-level object must be exactly:
     { "tab_ihm_wf": [...], "element_ihm_wf": [...], "tab_detail_ihm_wf": [...] }
   - No prose, no markdown, no comments, no trailing commas, no extra top-level keys.
3) Naming conventions:
   - ID_TAB and column names and ID_ELEMENT must be UPPER_SNAKE_CASE (ASCII), e.g. SUPPLIER_MASTER, SUPPLIER_ID, SUPPLIER_NAME.
4) ENUM_VALUES format:
   - ENUM_VALUES must be a JSON array of strings, e.g. ["MALE","FEMALE"] (never objects like {"value":"MALE"}).

TAB_IHM_WF rules:
- Create at least 1 master table (TYPE_TAB=\"M\") for the main entity (supplier, purchase order, invoice, reception, etc.).
- Use TYPE_TAB=\"D\" for detail/line tables if needed.
- ID_TAB must be present and not null.
- LOAD_TAB is optional. The backend derives LOAD_TAB.columns and sql_ddl from ELEMENT_IHM_WF (elements define schema).
- You MAY set LOAD_TAB.primaryKey: list of column names that MUST match ID_ELEMENT of data fields (e.g. [\"SUPPLIER_ID\"]).
- If you include LOAD_TAB.columns, set it to [] (do not invent columns here).
- DEFAULT_WHERE_TAB: null unless you infer a safe default filter.

ELEMENT_IHM_WF rules:
- One row per UI element/field.
- ID_TAB must reference a table from tab_ihm_wf.
- ID_ELEMENT:
  - Prefer a column name for persisted fields (e.g. SUPPLIER_NAME).
  - Use logical names for non-persisted controls (SEARCH, PAGINATION, ADD_BUTTON).
- TYPE_ELEMENT must reflect semantics:
  - text -> input_text
  - email -> input_email
  - phone -> tel or input_tel
  - number/money -> input_number
  - date -> input_date
  - select/dropdown -> select
  - textarea/notes -> textarea
  - action button -> button
  - pagination control -> pagination
- LONGEUR_ELEMENT: string length hint (\"50\", \"255\", \"4000\") or null.
- SQL_LOV_ELEMENT: null or SQL/JSON for list-of-values.
- ENUM_VALUES: null or list of values (for select/radio).
- VALIDATEUR_ELEMENT: JSON object (at least {\"required\": true/false}); do NOT output null.
- ACTIVE: \"O\" for visible; TRANSIT: \"N\" by default.
- POSITION_X / POSITION_Y: simple integer positions (1,2,3,...).

TAB_DETAIL_IHM_WF:
- Return [] if no master/detail relationship.

Return ONLY valid JSON."""





def build_schema_prompt(prompt: str, screen_schema: Dict[str, Any], context: Dict[str, Any]) -> str:
    # Avoid str.format collisions with braces in the prompt template.
    return (
        SCHEMA_PROMPT
        .replace("{prompt}", prompt)
        .replace("{screen_schema}", json.dumps(screen_schema))
        .replace("{context}", json.dumps(context))
    )

def extract_schema(prompt: str, screen_schema: Dict[str, Any], context: Dict[str, Any]) -> WorkflowScreenPayload:
    p = build_schema_prompt(prompt, screen_schema, context)
    resp = call_ollama(p)
    raw = resp.get("generated") or resp.get("response") or ""
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(data, dict) and "ihm" in data:
            data.pop("ihm")

        # Preferred: Oracle-shaped payload (TAB_IHM_WF / ELEMENT_IHM_WF keys).
        try:
            return WorkflowScreenPayload.parse_obj(data)
        except Exception as oracle_exc:
            # Fallback: raw (LLM-friendly) payload with keys like id_tab/name/type_tab/load_tab.
            try:
                raw_payload = RawWorkflowScreenPayload.parse_obj(data)
                id_client = context.get("id_client")
                id_wf = context.get("id_wf")
                id_tache = context.get("id_tache")
                id_ihm = context.get("id_ihm")

                hydrated_dict = hydrate_raw_oracle_metadata(
                    raw_payload,
                    id_client=int(id_client) if id_client is not None else None,
                    id_wf=str(id_wf) if id_wf is not None else None,
                    id_tache=str(id_tache) if id_tache is not None else None,
                    id_ihm=str(id_ihm) if id_ihm is not None else None,
                )
                return WorkflowScreenPayload.parse_obj(hydrated_dict)
            except Exception as raw_exc:
                logger.warning(
                    "Failed to parse schema output; oracle_err=%s raw_err=%s raw=%s",
                    oracle_exc,
                    raw_exc,
                    raw,
                )
                return WorkflowScreenPayload(
                    tab_ihm_wf=[],
                    element_ihm_wf=[],
                    tab_detail_ihm_wf=[],
                )
    except Exception as exc:
        logger.warning("Failed to parse schema JSON; err=%s raw=%s", exc, raw)
        return WorkflowScreenPayload(tab_ihm_wf=[], element_ihm_wf=[], tab_detail_ihm_wf=[])
