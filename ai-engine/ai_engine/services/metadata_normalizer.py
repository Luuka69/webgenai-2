from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, List
from collections import Counter, defaultdict
from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
from ai_engine.schemas.pydantic.oracle_metadata import ElementIhmWf, TabIhmWf, TabDetailIhmWf

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
    lowered = candidate.lower()
    if lowered == "text":
        return "input_text"
    if lowered in {"tel", "phone"}:
        return "input_tel"
    if lowered == "email":
        return "input_email"
    if lowered in {"number", "money"}:
        return "input_number"
    if lowered == "date":
        return "input_date"
    if lowered in {"select", "dropdown"}:
        return "select"
    if lowered in {"textarea", "notes"}:    
        return "textarea"
    return lowered


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

_NON_DATA_TYPES = {
    "button",
    "pagination",
    "label",
    "table",
    "actions",
    "input_hidden",
}
_NON_DATA_IDS = {"SEARCH", "PAGINATION", "ACTIONS", "ACTION_BUTTONS"}

_TYPE_TO_DB = {
    "input_text": "VARCHAR2(255)",
    "input_email": "VARCHAR2(255)",
    "input_password": "VARCHAR2(255)",
    "input_number": "NUMBER",
    "input_date": "DATE",
    "input_tel": "VARCHAR2(30)",
    "textarea": "CLOB",
    "select": "VARCHAR2(255)",
    "input_checkbox": "CHAR(1)",
    "input_boolean": "CHAR(1)",
}


def _parse_positive_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        n = int(str(value).strip())
    except Exception:
        return None
    return n if n > 0 else None


def _is_column_element(el: Any) -> bool:
    element_id = _normalize_identifier(getattr(el, "id_element", None))
    if element_id in _NON_DATA_IDS:
        return False
    if element_id.startswith("FILTER_") or element_id.endswith("_FILTER"):
        return False
    type_element = (getattr(el, "type_element", None) or "").strip().lower()
    return type_element not in _NON_DATA_TYPES


def _db_type_for_element(el: Any) -> str:
    type_element = (getattr(el, "type_element", None) or "").strip().lower()
    base = _TYPE_TO_DB.get(type_element, "VARCHAR2(255)")

    length = _parse_positive_int(getattr(el, "longueur_element", None))
    if length and base.upper().startswith("VARCHAR2("):
        return f"VARCHAR2({length})"

    return base


def _build_columns_from_elements(elements: list[Any]) -> list[dict[str, Any]]:
    ordered = sorted(
        elements,
        key=lambda e: (
            getattr(e, "position_y", 0) or 0,
            getattr(e, "position_x", 0) or 0,
        ),
    )

    cols: list[dict[str, Any]] = []
    seen: set[str] = set()

    for el in ordered:
        if not _is_column_element(el):
            continue

        name = _normalize_identifier(getattr(el, "id_element", None))
        if name in seen:
            continue
        seen.add(name)

        validator = getattr(el, "validateur_element", None)
        required = bool(validator.get("required")) if isinstance(validator, dict) else False

        cols.append(
            {
                "name": name,
                "type": _db_type_for_element(el),
                "required": required,
            }
        )

    return cols


def _guess_primary_key(columns: list[dict[str, Any]], existing_pk: Any) -> list[str]:
    col_names = [_normalize_identifier(c.get("name")) for c in columns]
    col_set = set(col_names)

    if isinstance(existing_pk, list):
        keep = [_normalize_identifier(x) for x in existing_pk]
        keep = [x for x in keep if x in col_set]
        if keep:
            return keep

    for name in col_names:
        if name == "ID" or name.endswith("_ID"):
            return [name]

    return [col_names[0]] if col_names else []


def _build_create_table_sql(
    table_name: str,
    columns: list[dict[str, Any]],
    primary_key: list[str],
) -> str:
    if not columns:
        return ""

    pk_set = set(primary_key or [])
    lines: list[str] = []

    for col in columns:
        name = _normalize_identifier(col.get("name"))
        col_type = col.get("type") if isinstance(col.get("type"), str) else "VARCHAR2(255)"
        required = bool(col.get("required")) or name in pk_set

        line = f"{name} {col_type}"
        if required:
            line += " NOT NULL"
        lines.append(line)

    cols_sql = ",\n    ".join(lines)
    pk_clause = ""
    if primary_key:
        pk_cols = ", ".join(primary_key)
        pk_clause = f",\n    CONSTRAINT PK_{table_name} PRIMARY KEY ({pk_cols})"

    return f"CREATE TABLE {table_name} (\n    {cols_sql}{pk_clause}\n);"


def _derive_load_tab_for_tab(table_name: str, elements: list[Any], existing_load_tab: Any) -> Dict[str, Any]:
    load_tab = dict(existing_load_tab) if isinstance(existing_load_tab, dict) else {}

    columns = _build_columns_from_elements(elements)
    load_tab["columns"] = columns

    pk = _guess_primary_key(columns, load_tab.get("primaryKey"))
    load_tab["primaryKey"] = pk

    ddl = _build_create_table_sql(table_name, columns, pk)
    if ddl:
        load_tab["sql_ddl"] = ddl

    return load_tab


def _ensure_primary_key_elements(payload: WorkflowScreenPayload) -> None:
    if not payload.tab_ihm_wf:
        return

    elements_by_tab: Dict[str, set[str]] = {}
    for el in payload.element_ihm_wf or []:
        tab_id = _normalize_identifier(getattr(el, "id_tab", None))
        element_id = _normalize_identifier(getattr(el, "id_element", None))
        elements_by_tab.setdefault(tab_id, set()).add(element_id)

    for t in payload.tab_ihm_wf:
        tab_id = _normalize_identifier(getattr(t, "id_tab", None))
        load_tab = getattr(t, "load_tab", None)
        if not isinstance(load_tab, dict):
            continue
        primary_key = load_tab.get("primaryKey")
        if not isinstance(primary_key, list):
            continue

        for pk in primary_key:
            pk_id = _normalize_identifier(pk)
            if pk_id in elements_by_tab.get(tab_id, set()):
                continue

            ids = {
                "ID_CLIENT": getattr(t, "id_client", None),
                "ID_WF": getattr(t, "id_wf", None),
                "ID_TACHE": getattr(t, "id_tache", None),
                "ID_IHM": getattr(t, "id_ihm", None),
            }
            type_element = "input_number" if pk_id == "ID" or pk_id.endswith("_ID") else "input_text"
            payload.element_ihm_wf.append(
                ElementIhmWf.parse_obj(
                    {
                        **ids,
                        "ID_TAB": tab_id,
                        "ID_ELEMENT": pk_id,
                        "TYPE_ELEMENT": type_element,
                        "LONGEUR_ELEMENT": None,
                        "SQL_LOV_ELEMENT": None,
                        "ENUM_VALUES": None,
                        "TRANSIT": "N",
                        "POSITION_X": None,
                        "POSITION_Y": None,
                        "HINT_ELEMENT": pk_id,
                        "CONTROL_ELEMENT": {"generated": "primaryKey"},
                        "VALIDATEUR_ELEMENT": {"required": True},
                        "DEFAULT_VALUE_ELEMENT": None,
                        "ACTIVE": "N",
                        "CODITION_ACTIVE": None,
                        "CREATED_AT": None,
                        "UPDATED_AT": None,
                    }
                )
            )
            elements_by_tab.setdefault(tab_id, set()).add(pk_id)


def derive_load_tab_from_elements(payload: WorkflowScreenPayload) -> WorkflowScreenPayload:
    """
    Derive TAB_IHM_WF.LOAD_TAB from ELEMENT_IHM_WF.

    This mutates the payload in-place and returns it for convenience.
    """
    if not payload.tab_ihm_wf:
        return payload

    _ensure_primary_key_elements(payload)
    


    elements_by_tab: Dict[str, list[Any]] = {}
    for el in payload.element_ihm_wf or []:
        tab_id = _normalize_identifier(getattr(el, "id_tab", None))
        elements_by_tab.setdefault(tab_id, []).append(el)

    for t in payload.tab_ihm_wf:
        tab_id = _normalize_identifier(getattr(t, "id_tab", None))
        t.id_tab = tab_id
        t.load_tab = _derive_load_tab_for_tab(tab_id, elements_by_tab.get(tab_id, []), getattr(t, "load_tab", None))

    return payload

def _extract_balanced_segment(
    text: str,
    start_index: int,
    open_char: str,
    close_char: str,
) -> Optional[str]:
    if start_index < 0 or start_index >= len(text):
        return None
    if text[start_index] != open_char:
        return None

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start_index, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start_index : idx + 1]

    return None


def _parse_inline_json_value(text: str, key: str) -> Optional[Any]:
    match = re.search(rf"{re.escape(key)}\s*[:=]\s*", text, flags=re.IGNORECASE)
    if not match:
        return None

    start = match.end()
    while start < len(text) and text[start].isspace():
        start += 1

    if start >= len(text):
        return None

    open_char = text[start]
    if open_char == "{":
        segment = _extract_balanced_segment(text, start, "{", "}")
    elif open_char == "[":
        segment = _extract_balanced_segment(text, start, "[", "]")
    else:
        return None

    if not segment:
        return None

    try:
        return json.loads(segment)
    except Exception:
        return None


def _parse_prompt_tab_specs(prompt: str) -> list[dict[str, Any]]:
    # Only match the explicit tab definitions that include ID_TAB, TYPE_TAB and ID_TAB_MAITRE.
    pattern = re.compile(
        r"ID_TAB\s*[:=]\s*\"?(?P<id>[A-Za-z0-9_]+)\"?"
        r"[\s\S]{0,400}?"
        r"TYPE_TAB\s*[:=]\s*\"?(?P<type>[MD])\"?"
        r"[\s\S]{0,400}?"
        r"ID_TAB_MAITRE\s*[:=]\s*(?P<maitre>null|\"?[A-Za-z0-9_]+\"?)",
        flags=re.IGNORECASE,
    )

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for m in pattern.finditer(prompt or ""):
        id_tab = _normalize_identifier(m.group("id"))
        if id_tab in seen:
            continue
        seen.add(id_tab)

        type_tab = _coerce_type_tab(m.group("type"))
        raw_maitre = (m.group("maitre") or "").strip().strip('"')
        id_tab_maitre = None if raw_maitre.lower() in _NULLISH else _normalize_identifier(raw_maitre)
        if type_tab == "M":
            id_tab_maitre = None

        out.append(
            {
                "id_tab": id_tab,
                "type_tab": type_tab,
                "id_tab_maitre": id_tab_maitre,
            }
        )

    return out


def _parse_prompt_elements(
    prompt: str,
    known_tab_ids: set[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    elements_by_tab: dict[str, list[dict[str, Any]]] = defaultdict(list)
    table_specs: dict[str, dict[str, Any]] = {}

    current_tab_id: Optional[str] = None
    pending_table_validator_for_tab: Optional[str] = None

    cursor = 0
    for raw_line in (prompt or "").splitlines(True):
        line = raw_line.strip()
        lowered = line.lower()

        tab_match = re.search(r"\bID_TAB\b\s*[:=]\s*\"?([A-Za-z0-9_]+)\"?", line, flags=re.IGNORECASE)
        if tab_match:
            candidate = _normalize_identifier(tab_match.group(1))
            if candidate in known_tab_ids:
                current_tab_id = candidate
                pending_table_validator_for_tab = None

        if not current_tab_id:
            cursor += len(raw_line)
            continue

        table_id_match = re.search(r"\bID_ELEMENT\b\s*[:=]\s*\"?([A-Za-z0-9_]+)\"?", line, flags=re.IGNORECASE)
        if table_id_match:
            table_specs.setdefault(current_tab_id, {})["id_element"] = _normalize_identifier(table_id_match.group(1))
            pending_table_validator_for_tab = current_tab_id
            cursor += len(raw_line)
            continue

        if pending_table_validator_for_tab and "validateur_element" in lowered:
            parsed = _parse_inline_json_value(line, "VALIDATEUR_ELEMENT")
            if isinstance(parsed, dict):
                table_specs.setdefault(pending_table_validator_for_tab, {})["validateur_element"] = parsed
            pending_table_validator_for_tab = None
            cursor += len(raw_line)
            continue

        if "default_value_element" in lowered:
            key_pos = lowered.find("default_value_element")
            search_from = cursor + (key_pos if key_pos >= 0 else 0)
            array_start = (prompt or "").find("[", search_from)
            if array_start != -1:
                segment = _extract_balanced_segment(prompt, array_start, "[", "]")
                if segment:
                    try:
                        parsed = json.loads(segment)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, list) and parsed:
                        table_specs.setdefault(current_tab_id, {})["default_value_element"] = parsed
            cursor += len(raw_line)
            continue

        # Element definitions: "- ID_ELEMENT : type, ACTIVE=\"N\", ..."
        el_match = re.match(r"^[\-\*\s]*([A-Z0-9_]{2,})\s*:\s*([A-Za-z0-9_]+)(.*)$", line)
        if not el_match:
            cursor += len(raw_line)
            continue

        id_element = _normalize_identifier(el_match.group(1))
        type_element = _normalize_type_element(el_match.group(2))
        rest = el_match.group(3) or ""

        active_default = "O"
        active_match = re.search(r"\bACTIVE\b\s*[:=]\s*\"?([ON])\"?", rest, flags=re.IGNORECASE)
        if active_match:
            active = _coerce_flag(active_match.group(1), active_default)
        else:
            active = active_default

        validator = _parse_inline_json_value(rest, "VALIDATEUR_ELEMENT")
        control = _parse_inline_json_value(rest, "CONTROL_ELEMENT")
        enum_values = _parse_inline_json_value(rest, "ENUM_VALUES")

        if isinstance(enum_values, list):
            enum_values = [str(v) for v in enum_values]
        else:
            enum_values = None

        if "readonly" in rest.lower():
            if isinstance(control, dict):
                control = {**control, "readonly": True}
            elif control is None:
                control = {"readonly": True}

        elements_by_tab[current_tab_id].append(
            {
                "id_element": id_element,
                "type_element": type_element,
                "active": active,
                "validateur_element": validator if isinstance(validator, dict) else None,
                "control_element": control if isinstance(control, dict) else control,
                "enum_values": enum_values,
            }
        )

        cursor += len(raw_line)

    return dict(elements_by_tab), table_specs


def _apply_prompt_contract(
    payload: WorkflowScreenPayload,
    prompt: str,
) -> Optional[WorkflowScreenPayload]:
    tabs = _parse_prompt_tab_specs(prompt)
    if not tabs:
        return None

    masters = [t for t in tabs if t.get("type_tab") == "M"]
    details = [t for t in tabs if t.get("type_tab") == "D"]
    if len(masters) != 1 or len(details) < 1:
        return None

    master_id = masters[0]["id_tab"]
    for t in details:
        if not t.get("id_tab_maitre"):
            t["id_tab_maitre"] = master_id

    known_tab_ids = {t["id_tab"] for t in tabs}
    elements_by_tab, table_specs = _parse_prompt_elements(prompt, known_tab_ids)

    if not any(elements_by_tab.values()) and not table_specs:
        return None

    # Rebuild tabs exactly as requested.
    payload.tab_ihm_wf = [
        TabIhmWf(
            id_tab=t["id_tab"],
            type_tab=t["type_tab"],
            id_tab_maitre=t.get("id_tab_maitre"),
        )
        for t in tabs
    ]

    # Rebuild master/detail relations
    payload.tab_detail_ihm_wf = [
        TabDetailIhmWf(
            id_tab=t["id_tab"],
            id_tab_maitre=t.get("id_tab_maitre") or master_id,
        )
        for t in tabs
        if t.get("type_tab") == "D"
    ]

    # Build elements (master fields visible; detail fields hidden, with a visible table).
    elements: list[ElementIhmWf] = []

    # Master positions: 2 columns, increasing rows.
    master_row = 1
    master_col = 1

    for spec in elements_by_tab.get(master_id, []):
        active = _coerce_flag(spec.get("active"), "O")
        pos_x = None
        pos_y = None
        if active != "N":
            pos_x = master_col
            pos_y = master_row
            master_col = 2 if master_col == 1 else 1
            if master_col == 1:
                master_row += 1

        elements.append(
            ElementIhmWf(
                ID_TAB=master_id,
                ID_ELEMENT=spec["id_element"],
                TYPE_ELEMENT=spec.get("type_element"),
                ACTIVE=active,
                POSITION_X=pos_x,
                POSITION_Y=pos_y,
                ENUM_VALUES=spec.get("enum_values"),
                CONTROL_ELEMENT=spec.get("control_element"),
                VALIDATEUR_ELEMENT=spec.get("validateur_element"),
            )
        )

    for t in details:
        tab_id = t["id_tab"]
        tab_elements = elements_by_tab.get(tab_id, [])

        # Add column elements as hidden metadata, even if the prompt forgets ACTIVE="N".
        column_ids: list[str] = []
        for spec in tab_elements:
            if (spec.get("type_element") or "").lower() == "table":
                continue
            active = "N"
            column_ids.append(spec["id_element"])
            elements.append(
                ElementIhmWf(
                    ID_TAB=tab_id,
                    ID_ELEMENT=spec["id_element"],
                    TYPE_ELEMENT=spec.get("type_element"),
                    ACTIVE=active,
                    ENUM_VALUES=spec.get("enum_values"),
                    CONTROL_ELEMENT=spec.get("control_element"),
                    VALIDATEUR_ELEMENT=spec.get("validateur_element"),
                )
            )

        # Ensure a visible table element with deterministic columns.
        spec_table_id = table_specs.get(tab_id, {}).get("id_element")
        if not spec_table_id:
            # fallback to first parsed table element id, or a stable default
            parsed_table_ids = [
                e.get("id_element")
                for e in tab_elements
                if (e.get("type_element") or "").lower() == "table"
            ]
            spec_table_id = parsed_table_ids[0] if parsed_table_ids else f"TABLE_{tab_id}"

        default_rows = table_specs.get(tab_id, {}).get("default_value_element")
        if isinstance(default_rows, list) and default_rows and isinstance(default_rows[0], dict):
            row = default_rows[0]
        else:
            row = {col: "" for col in column_ids} if column_ids else {}
        if not row:
            # Avoid an empty table; render at least two placeholder columns.
            row = {"COL1": "", "COL2": ""}

        normalized_row: dict[str, Any] = {
            _normalize_identifier(k): v for k, v in row.items()
        }
        row = normalized_row

        # If the prompt provided DEFAULT_VALUE_ELEMENT columns but not explicit column elements,
        # create hidden column metadata from the row keys so Oracle LOAD_TAB isn't empty.
        missing_columns = [c for c in row.keys() if c not in column_ids]
        for col in missing_columns:
            column_ids.append(col)
            elements.append(
                ElementIhmWf(
                    ID_TAB=tab_id,
                    ID_ELEMENT=col,
                    TYPE_ELEMENT="input_text",
                    ACTIVE="N",
                    VALIDATEUR_ELEMENT={"required": False},
                )
            )

        table_validator = table_specs.get(tab_id, {}).get("validateur_element")
        if not isinstance(table_validator, dict):
            table_validator = {"required": False}

        elements.append(
            ElementIhmWf(
                ID_TAB=tab_id,
                ID_ELEMENT=spec_table_id,
                TYPE_ELEMENT="table",
                ACTIVE="O",
                POSITION_X=1,
                POSITION_Y=1,
                DEFAULT_VALUE_ELEMENT=[row],
                VALIDATEUR_ELEMENT=table_validator,
            )
        )

    payload.element_ihm_wf = elements
    return payload


def enforce_minimum_metadata(
    payload: WorkflowScreenPayload,
    html: str = "",
    prompt: str = "",
) -> WorkflowScreenPayload:
    """
    Guarantees:
    - tabs exist if elements exist
    - master/detail tab structure
    - detail tabs always have a table
    - elements are normalized and safe to render
    """

    # If the prompt explicitly specifies IDs (tabs/elements), enforce them even if the LLM deviates.
    if prompt:
        enforced = _apply_prompt_contract(payload, prompt)
        if enforced is not None:
            payload = enforced

    # -----------------------------
    # 1) Ensure tabs exist
    # -----------------------------
    if not payload.tab_ihm_wf and payload.element_ihm_wf:
        tab_counts = Counter(e.id_tab for e in payload.element_ihm_wf if e.id_tab)
        if tab_counts:
            master_tab = tab_counts.most_common(1)[0][0]

            payload.tab_ihm_wf = []
            for tab_id in tab_counts.keys():
                if tab_id == master_tab:
                    payload.tab_ihm_wf.append(
                        TabIhmWf(
                            ID_TAB=tab_id,
                            TYPE_TAB="M",
                            id_tab_maitre=None
                        )
                    )
                else:
                    payload.tab_ihm_wf.append(
                        TabIhmWf(
                            ID_TAB=tab_id,
                            TYPE_TAB="D",
                            id_tab_maitre=master_tab
                        )
                    )
        else:
            return payload

    # Identify master tab
    master_tabs = [t for t in payload.tab_ihm_wf if t.type_tab == "M"]
    master_tab_id = master_tabs[0].id_tab if master_tabs else None

    # -----------------------------
    # 2) Ensure tab_detail_ihm_wf
    # -----------------------------
    if payload.tab_detail_ihm_wf is None:
        payload.tab_detail_ihm_wf = []

    existing_pairs = {
        (d.id_tab, d.id_tab_maitre) for d in payload.tab_detail_ihm_wf
    }

    for tab in payload.tab_ihm_wf:
        if tab.type_tab == "D":
            key = (tab.id_tab, tab.id_tab_maitre)
            if key not in existing_pairs:
                payload.tab_detail_ihm_wf.append(
                    TabDetailIhmWf(
                        ID_TAB=tab.id_tab,
                        id_tab_maitre=tab.id_tab_maitre
                    )
                )

    # -----------------------------
    # 3) Normalize elements
    # -----------------------------
    for e in payload.element_ihm_wf:
        e.type_element = _normalize_type_element(e.type_element)

        if not isinstance(e.validateur_element, dict):
            e.validateur_element = {}

        e.validateur_element.setdefault("required", False)

    # Group elements by tab
    elements_by_tab: Dict[str, List] = defaultdict(list)
    for e in payload.element_ihm_wf:
        if e.id_tab:
            elements_by_tab[e.id_tab].append(e)

    # -----------------------------
    # 4) Ensure one table per detail tab
    # -----------------------------
    for tab in payload.tab_ihm_wf:
        if tab.type_tab != "D":
            continue

        tab_elements = elements_by_tab.get(tab.id_tab, [])
        has_table = any(e.type_element == "table" for e in tab_elements)

        if has_table:
            continue

        # ---- build columns from data elements
        column_elements = [
            e for e in tab_elements
            if e.type_element not in {"button", "pagination", "table"}
        ]

        if not column_elements:
            continue

        columns = {}
        for e in column_elements:
            columns[e.id_element] = ""

        # deactivate individual fields
        for e in column_elements:
            e.active = "N"

        # ---- try extracting table id from HTML
        table_id = None
        if html:
            match = re.search(
                rf'<fieldset[^>]*id=["\']{re.escape(tab.id_tab)}["\'][\s\S]*?<table[^>]*id=["\']([^"\']+)["\']',
                html,
                flags=re.IGNORECASE,
            )

            if match:
                table_id = match.group(1)

        if not table_id:
            table_id = f"TABLE_{tab.id_tab}"

        payload.element_ihm_wf.append(
            ElementIhmWf(
                ID_TAB=tab.id_tab,
                ID_ELEMENT=table_id,
                TYPE_ELEMENT="table",
                DEFAULT_VALUE_ELEMENT=[columns],
                ACTIVE="O",
                VALIDATEUR_ELEMENT={"required": False}
            )
        )

    return payload


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
                raw_master = getattr(t, "id_tab_maitre", None)
                t.id_tab_maitre = _normalize_identifier(raw_master) if raw_master else master_tab_id

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
