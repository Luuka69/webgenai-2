from __future__ import annotations

import re
from typing import Any, Dict, Optional

from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload

_FLAG_VALUES = {"O", "N"}
_TYPE_TAB_VALUES = {"M", "D"}
_NULLISH = {"", "null", "none", "undefined"}


def _normalize_identifier(value: Optional[str]) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", (value or "").strip().upper())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "ID"


def _coerce_flag(value: Optional[str], default: str) -> str:
    if value is None:
        return default
    candidate = str(value).strip().upper()
    return candidate if candidate in _FLAG_VALUES else default


def _coerce_type_tab(value: Optional[str]) -> str:
    candidate = str(value).strip().upper() if value else "M"
    return candidate if candidate in _TYPE_TAB_VALUES else "M"


def _normalize_type_element(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    candidate = str(value).strip()
    if candidate.lower() in _NULLISH:
        return None
    return candidate.lower()


def _infer_length_from_load_tab(load_tab: Any, column_name: str) -> Optional[str]:
    if not isinstance(load_tab, dict):
        return None
    columns = load_tab.get("columns")
    if not isinstance(columns, list):
        return None
    for col in columns:
        if not isinstance(col, dict):
            continue
        name = _normalize_identifier(col.get("name"))
        if name != column_name:
            continue
        oracle_type = col.get("type")
        if not isinstance(oracle_type, str):
            return None
        match = re.search(r"VARCHAR2\s*\(\s*(\d+)\s*\)", oracle_type.upper())
        return match.group(1) if match else None
    return None


def _default_type_element_for_id(id_element: str) -> str:
    key = _normalize_identifier(id_element)
    if key in {"PAGINATION"}:
        return "pagination"
    if key in {"DATA_TABLE", "TABLE", "GRID"} or key.endswith("_TABLE") or key.endswith("_GRID"):
        return "table"
    if key.endswith("_BUTTON") or "BUTTON" in key:
        return "button"
    if "BADGE" in key or "CHIP" in key:
        return "label"
    if key == "SEARCH":
        return "input_text"
    return "label"


def _align_element_with_columns(
    columns_by_tab: Dict[str, Dict[str, Dict[str, Any]]],
    tab_id: str,
    element_id: str,
) -> str:
    """
    Align an element identifier with a persisted column name when possible.

    - Exact match: keep it.
    - Suffix match: strip prefix (SUPPLIER_EMAIL -> EMAIL) if EMAIL is a column.
    """
    columns = columns_by_tab.get(tab_id)
    if not columns:
        return element_id

    if element_id in columns:
        return element_id

    for col_name in sorted(columns.keys(), key=len, reverse=True):
        if element_id.endswith("_" + col_name):
            return col_name

    return element_id


def hydrate_oracle_metadata(
    payload: WorkflowScreenPayload,
    id_client: int,
    id_wf: str,
    id_tache: str,
    id_ihm: str,
) -> WorkflowScreenPayload:
    """
    Fill missing IDs and defaults in Oracle metadata after the LLM.
    """
    default_tab_id: Optional[str] = None
    columns_by_tab: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # Tables: set IDs, defaults, and ensure an ID_TAB
    if payload.tab_ihm_wf:
        normalized_tab_ids = []
        master_tab_id: Optional[str] = None

        for t in payload.tab_ihm_wf:
            t.id_client = id_client
            t.id_wf = id_wf
            t.id_tache = id_tache
            t.id_ihm = id_ihm
            t.type_tab = _coerce_type_tab(getattr(t, "type_tab", None))
            t.id_tab = _normalize_identifier(getattr(t, "id_tab", None)) or f"{id_ihm}_MAIN".upper()

            if master_tab_id is None and t.type_tab == "M":
                master_tab_id = t.id_tab
            normalized_tab_ids.append(t.id_tab)

            if isinstance(t.load_tab, dict):
                columns = t.load_tab.get("columns")
                if isinstance(columns, list):
                    for col in columns:
                        if isinstance(col, dict) and "name" in col:
                            col["name"] = _normalize_identifier(col.get("name"))
                primary_key = t.load_tab.get("primaryKey")
                if isinstance(primary_key, list):
                    t.load_tab["primaryKey"] = [_normalize_identifier(pk) for pk in primary_key]

                # Build column lookup for element alignment/inference.
                col_map: Dict[str, Dict[str, Any]] = {}
                for col in t.load_tab.get("columns") or []:
                    if not isinstance(col, dict):
                        continue
                    col_name = _normalize_identifier(col.get("name"))
                    col["name"] = col_name
                    col_map[col_name] = col
                columns_by_tab[t.id_tab] = col_map

        master_tab_id = master_tab_id or normalized_tab_ids[0]
        for t in payload.tab_ihm_wf:
            if t.type_tab == "D":
                t.id_tab_maitre = _normalize_identifier(getattr(t, "id_tab_maitre", None)) or master_tab_id
            else:
                t.id_tab_maitre = None

        default_tab_id = master_tab_id
    else:
        default_tab_id = f"{id_ihm}_MAIN".upper()

    # Elements: set IDs, defaults, and attach to a table
    position_y = 0
    for el in payload.element_ihm_wf:
        el.id_client = id_client
        el.id_wf = id_wf
        el.id_tache = id_tache
        el.id_ihm = id_ihm
        el.id_tab = _normalize_identifier(getattr(el, "id_tab", None)) or default_tab_id
        original_element_id = _normalize_identifier(getattr(el, "id_element", None))
        el.id_element = _align_element_with_columns(columns_by_tab, el.id_tab, original_element_id)

        el.type_element = _normalize_type_element(getattr(el, "type_element", None)) or _default_type_element_for_id(
            el.id_element
        )

        # Type normalizations for consistency with the future renderer.
        if el.type_element == "tel":
            el.type_element = "input_tel"
        if el.id_element in {"ACTIONS", "ACTION_BUTTONS"} and el.type_element == "pagination":
            el.type_element = "actions"

        el.active = _coerce_flag(getattr(el, "active", None), "O")
        el.transit = _coerce_flag(getattr(el, "transit", None), "N")

        if getattr(el, "hint_element", None) in (None, "", original_element_id):
            el.hint_element = el.id_element

        if getattr(el, "position_x", None) is None:
            el.position_x = 1
        if getattr(el, "position_y", None) is None:
            position_y += 1
            el.position_y = position_y

        # If the element maps to a persisted column, derive required + length from LOAD_TAB.
        col = columns_by_tab.get(el.id_tab, {}).get(el.id_element)
        if col:
            required = bool(col.get("required"))
            validator = getattr(el, "validateur_element", None)
            if not isinstance(validator, dict):
                validator = {}
            validator["required"] = required
            el.validateur_element = validator

            if getattr(el, "longueur_element", None) in (None, ""):
                oracle_type = col.get("type")
                if isinstance(oracle_type, str):
                    match = re.search(r"VARCHAR2\\s*\\(\\s*(\\d+)\\s*\\)", oracle_type.upper())
                    if match:
                        el.longueur_element = match.group(1)

        # Last-resort VARCHAR2 length inference.
        if getattr(el, "longueur_element", None) in (None, ""):
            for t in payload.tab_ihm_wf:
                if t.id_tab == el.id_tab:
                    inferred = _infer_length_from_load_tab(t.load_tab, el.id_element)
                    if inferred:
                        el.longueur_element = inferred
                    break

    # Relations: set IDs
    for rel in payload.tab_detail_ihm_wf:
        rel.id_client = id_client
        rel.id_wf = id_wf
        rel.id_tache = id_tache
        rel.id_ihm = id_ihm
        rel.id_tab = _normalize_identifier(getattr(rel, "id_tab", None))
        rel.id_tab_maitre = _normalize_identifier(getattr(rel, "id_tab_maitre", None))
        if getattr(rel, "id_elem_tab", None):
            rel.id_elem_tab = _normalize_identifier(getattr(rel, "id_elem_tab", None))
        if getattr(rel, "id_elem_tab_maitre", None):
            rel.id_elem_tab_maitre = _normalize_identifier(getattr(rel, "id_elem_tab_maitre", None))

    return payload
