"""
Raw LLM metadata -> Oracle-shaped metadata transformation.

This module is intentionally pure (no I/O, no DB calls). It defines Pydantic
models for the *raw* (LLM-friendly) schema and provides a hydrator that
converts it into the Oracle-shaped rows we store in:

- TAB_IHM_WF
- ELEMENT_IHM_WF
- TAB_DETAIL_IHM_WF

Usage:

    raw = RawWorkflowScreenPayload.parse_obj(llm_json)
    hydrated = hydrate_oracle_metadata(
        raw,
        id_client=1,
        id_wf="WF_ACHAT",
        id_tache="FACTURE_FOURNISSEUR",
        id_ihm="INV_FORM",
    )
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


def _normalize_identifier(value: str) -> str:
    """
    Normalize an identifier to UPPER_SNAKE_CASE.

    Examples:
      - "N° BC" -> "N_BC" (we avoid locale-specific transliteration here)
      - "invoice-number" -> "INVOICE_NUMBER"
      - " supplier name " -> "SUPPLIER_NAME"
    """
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", (value or "").strip().upper())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "ID"


def _varchar2_length(oracle_type: Optional[str]) -> Optional[str]:
    """
    Extract VARCHAR2 length hint from an Oracle type string.
    Returns the numeric length as a string (e.g. "255") or None.
    """
    if not oracle_type:
        return None
    match = re.search(r"VARCHAR2\s*\(\s*(\d+)\s*\)", oracle_type.upper())
    return match.group(1) if match else None


def _normalize_type_element(value: Optional[str]) -> Optional[str]:
    """
    Normalize TYPE_ELEMENT to a consistent lowercase form.
    We keep "input_text", "input_number", etc as-is; "SEARCH" -> "search".
    """
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned.lower() if cleaned else None


class Column(BaseModel):
    """Raw column description produced by the LLM."""

    name: str
    type: str
    required: bool = False

    class Config:
        extra = "allow"


class LoadTab(BaseModel):
    """Raw LOAD_TAB produced by the LLM."""

    columns: List[Column] = Field(default_factory=list)
    primary_key: List[str] = Field(default_factory=list, alias="primaryKey")
    default_where_tab: Optional[Any] = Field(None, alias="default_where_tab")

    class Config:
        extra = "allow"
        allow_population_by_field_name = True


class RawTabIhm(BaseModel):
    """Raw table description produced by the LLM."""

    id_tab: Optional[str] = None
    name: Optional[str] = None
    type_tab: str = "M"  # "M" master, "D" detail
    load_tab: LoadTab
    default_where_tab: Optional[Any] = None

    class Config:
        extra = "allow"


class RawElementIhm(BaseModel):
    """Raw element description produced by the LLM."""

    id_tab: Optional[str] = None
    id_element: str
    type_element: str

    # Optional richer fields if the LLM provides them
    longueur_element: Optional[str] = None
    sql_lov_element: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    transit: Optional[str] = None
    hint_element: Optional[str] = None
    control_element: Optional[Any] = None
    validateur_element: Optional[Any] = None
    default_value_element: Optional[Any] = None
    active: Optional[str] = None
    codition_active: Optional[Any] = None

    class Config:
        extra = "allow"

    @validator("enum_values", pre=True)
    def _coerce_enum_values(cls, value: Any) -> Optional[List[str]]:
        """
        Coerce enum_values into a simple list[str].

        The LLM sometimes returns:
          - ["MALE", "FEMALE"]
          - [{"value":"MALE"}, {"value":"FEMALE"}]
        """
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return [str(value)]
        if isinstance(value, dict):
            extracted = value.get("value") or value.get("label") or value.get("name")
            return [str(extracted)] if extracted is not None else None
        if isinstance(value, list):
            out: List[str] = []
            for item in value:
                if item is None:
                    continue
                if isinstance(item, str):
                    out.append(item)
                    continue
                if isinstance(item, dict):
                    extracted = item.get("value") or item.get("label") or item.get("name")
                    if extracted is not None:
                        out.append(str(extracted))
                    continue
                out.append(str(item))
            return out or None
        return [str(value)]


class RawWorkflowScreenPayload(BaseModel):
    """
    Raw LLM output for one screen.
    This is intentionally *not* Oracle-shaped; it is easier for the LLM to produce.
    """

    tab_ihm_wf: List[RawTabIhm] = Field(default_factory=list)
    element_ihm_wf: List[RawElementIhm] = Field(default_factory=list)
    tab_detail_ihm_wf: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        extra = "allow"


def hydrate_oracle_metadata(
    raw: RawWorkflowScreenPayload,
    id_client: Optional[int],
    id_wf: Optional[str],
    id_tache: Optional[str],
    id_ihm: Optional[str],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert raw LLM metadata into Oracle-shaped metadata rows.

    - IDs are filled from function args.
    - Master/detail relations are applied to TAB_IHM_WF rows:
      all detail tables (TYPE_TAB="D") get ID_TAB_MAITRE = master table ID_TAB.
    - ELEMENT_IHM_WF rows:
      elements with no id_tab are attached to the master table.
      POSITION_Y is assigned sequentially (1..N) in the order elements appear.
      VALIDATEUR_ELEMENT.required is inferred from the matching column.required when possible.
    """

    # Resolve and normalize tab IDs (ID_TAB)
    resolved_tabs: List[tuple[RawTabIhm, str]] = []
    tab_id_by_key: Dict[str, str] = {}
    required_by_tab: Dict[str, Dict[str, bool]] = {}
    type_by_tab: Dict[str, Dict[str, str]] = {}

    master_tab_id: Optional[str] = None

    for tab in raw.tab_ihm_wf:
        resolved_id = _normalize_identifier(tab.id_tab or tab.name or id_ihm or "MAIN")
        resolved_tabs.append((tab, resolved_id))

        # Detect master table (first TYPE_TAB="M")
        if master_tab_id is None and (tab.type_tab or "").upper() == "M":
            master_tab_id = resolved_id

        # Map both "name" and "id_tab" for lookup from elements
        if tab.name:
            tab_id_by_key[_normalize_identifier(tab.name)] = resolved_id
        if tab.id_tab:
            tab_id_by_key[_normalize_identifier(tab.id_tab)] = resolved_id

        # Build column metadata maps for this table
        col_required: Dict[str, bool] = {}
        col_types: Dict[str, str] = {}
        for col in tab.load_tab.columns:
            col_name = _normalize_identifier(col.name)
            col_required[col_name] = bool(col.required)
            col_types[col_name] = col.type
        required_by_tab[resolved_id] = col_required
        type_by_tab[resolved_id] = col_types

    if master_tab_id is None:
        master_tab_id = (
            resolved_tabs[0][1] if resolved_tabs else _normalize_identifier(id_ihm or "MAIN")
        )

    # Build Oracle-shaped TAB_IHM_WF rows
    tab_rows: List[Dict[str, Any]] = []
    for tab, resolved_id in resolved_tabs:
        type_tab = (tab.type_tab or "M").upper()
        id_tab_maitre = master_tab_id if type_tab == "D" else None

        # Normalize columns + primary key to UPPER_SNAKE_CASE.
        load_tab = {
            "columns": [
                {
                    "name": _normalize_identifier(col.name),
                    "type": col.type,
                    "required": bool(col.required),
                }
                for col in tab.load_tab.columns
            ],
            "primaryKey": [_normalize_identifier(pk) for pk in (tab.load_tab.primary_key or [])],
        }

        tab_rows.append(
            {
                "ID_CLIENT": id_client,
                "ID_WF": id_wf,
                "ID_TACHE": id_tache,
                "ID_IHM": id_ihm,
                "ID_TAB": resolved_id,
                "TYPE_TAB": type_tab,
                "ID_TAB_MAITRE": id_tab_maitre,
                "LOAD_TAB": load_tab,
                "DEFAULT_WHERE_TAB": tab.default_where_tab
                if tab.default_where_tab is not None
                else tab.load_tab.default_where_tab,
                "CREATED_AT": None,
                "UPDATED_AT": None,
            }
        )

    # Build Oracle-shaped ELEMENT_IHM_WF rows
    element_rows: List[Dict[str, Any]] = []
    for idx, el in enumerate(raw.element_ihm_wf, start=1):
        raw_tab_key = _normalize_identifier(el.id_tab) if el.id_tab else None
        target_tab_id = (
            tab_id_by_key.get(raw_tab_key) if raw_tab_key else master_tab_id
        ) or master_tab_id

        element_id = _normalize_identifier(el.id_element)
        required = bool(required_by_tab.get(target_tab_id, {}).get(element_id, False))
        col_type = type_by_tab.get(target_tab_id, {}).get(element_id)

        # If the raw element already has a validator dict, keep it and ensure "required" exists.
        if isinstance(el.validateur_element, dict):
            validator = dict(el.validateur_element)
            validator.setdefault("required", required)
        else:
            validator = {"required": required}

        element_rows.append(
            {
                "ID_CLIENT": id_client,
                "ID_WF": id_wf,
                "ID_TACHE": id_tache,
                "ID_IHM": id_ihm,
                "ID_TAB": target_tab_id,
                "ID_ELEMENT": element_id,
                "TYPE_ELEMENT": _normalize_type_element(el.type_element),
                # Prefer explicit longueur_element; otherwise infer from VARCHAR2(N)
                "LONGEUR_ELEMENT": el.longueur_element or _varchar2_length(col_type),
                "SQL_LOV_ELEMENT": el.sql_lov_element,
                "ENUM_VALUES": el.enum_values,
                "TRANSIT": (el.transit or "N").upper(),
                "POSITION_X": 1,
                "POSITION_Y": idx,
                "HINT_ELEMENT": el.hint_element,
                "CONTROL_ELEMENT": el.control_element,
                "VALIDATEUR_ELEMENT": validator,
                "DEFAULT_VALUE_ELEMENT": el.default_value_element,
                "ACTIVE": (el.active or "O").upper(),
                "CODITION_ACTIVE": el.codition_active,
                "CREATED_AT": None,
                "UPDATED_AT": None,
            }
        )

    # TAB_DETAIL_IHM_WF is forwarded as-is (caller can normalize/fill IDs later if desired).
    tab_detail_rows: List[Dict[str, Any]] = [dict(r) for r in (raw.tab_detail_ihm_wf or [])]

    return {
        "tab_ihm_wf": tab_rows,
        "element_ihm_wf": element_rows,
        "tab_detail_ihm_wf": tab_detail_rows,
    }
