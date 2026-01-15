from flask import Blueprint, jsonify, request

from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService
from ai_engine.services.workflow_index import WorkflowIndex
from ai_engine.services.metadata_normalizer import (
    derive_load_tab_from_elements,
    hydrate_oracle_metadata,
    enforce_minimum_metadata,
)

from ai_engine.services.schema_generator import extract_schema
import logging

logger = logging.getLogger(__name__)
screens_bp = Blueprint('screens', __name__)
storage = StorageService()
workflow_index = WorkflowIndex()


@screens_bp.route('/screens', methods=['POST'])
def create_screen_record():
    payload = request.get_json(silent=True) or {}
    try:
        record = storage.store_generation(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify(record), 201


@screens_bp.route('/screens', methods=['GET'])
def list_screens():
    kind_filter = request.args.get("kind")
    if kind_filter:
        records = storage.list_generations_by_kind(kind_filter)
    else:
        records = storage.list_generations()
    # Summaries with key fields
    summaries = []
    for rec in records:
        summaries.append({
            "id": rec.get("id"),
            "kind": rec.get("kind", "cached"),
            "logical_key": rec.get("logical_key"),
            "id_client": rec.get("id_client"),
            "id_wf": rec.get("id_wf"),
            "id_tache": rec.get("id_tache"),
            "id_ihm": rec.get("id_ihm"),
            "prompt": rec.get("prompt"),
            "title": (rec.get("structure") or {}).get("title") if isinstance(rec.get("structure"), dict) else None,
        })
    return jsonify(summaries)


@screens_bp.route('/screens/<screen_id>', methods=['GET'])
def get_screen_record(screen_id: str):
    wf_id = request.args.get("wf_id")  # required to disambiguate when duplicate ids exist
    # Allow callers to pass namespaced ids directly as /screens/WF_XYZ:SCREEN_ID
    if not wf_id and ":" in screen_id:
        wf_id, screen_id = screen_id.split(":", 1)
    namespaced_id = f"{wf_id}:{screen_id}" if wf_id else screen_id

    # Try cache first
    cached = storage.get_generation(namespaced_id)
    if cached:
        if cached.get("kind") != "workflow_screen":
            # Cached screens may predate the Oracle-metadata step or may have failed metadata parsing.
            # Best-effort: backfill metadata from stored prompt + HTML on first access.
            has_any_metadata = any(
                bool(cached.get(k))
                for k in ("tab_ihm_wf", "element_ihm_wf", "tab_detail_ihm_wf")
            )

            if not has_any_metadata:
                try:
                    description = (cached.get("prompt") or "").strip()
                    if description:
                        schema_input = {
                            "screen_schema": cached.get("structure") or {},
                            "html": cached.get("code") or "",
                        }
                        context_ids = {
                            "id_client": None,
                            "id_wf": None,
                            "id_tache": None,
                            "id_ihm": None,
                        }
                        schema_result = extract_schema(description, schema_input, context_ids)
                        if isinstance(schema_result, WorkflowScreenPayload):
                            schema_result = enforce_minimum_metadata(
                                schema_result,
                                schema_input.get("html") or "",
                                description,
                            )

                        if isinstance(schema_result, WorkflowScreenPayload):
                            derive_load_tab_from_elements(schema_result)
                            tab_ihm_wf = [
                                t.dict(by_alias=True) for t in (schema_result.tab_ihm_wf or [])
                            ]
                            element_ihm_wf = [
                                e.dict(by_alias=True)
                                for e in (schema_result.element_ihm_wf or [])
                            ]
                            tab_detail_ihm_wf = [
                                d.dict(by_alias=True)
                                for d in (schema_result.tab_detail_ihm_wf or [])
                            ]

                            def updater(record):
                                record["tab_ihm_wf"] = tab_ihm_wf
                                record["element_ihm_wf"] = element_ihm_wf
                                record["tab_detail_ihm_wf"] = tab_detail_ihm_wf

                            updated = storage.update_generation(namespaced_id, updater)
                            if updated:
                                cached = updated
                except Exception as exc:
                    logger.warning(
                        "Failed to backfill metadata for cached screen: id=%s err=%s",
                        namespaced_id,
                        exc,
                    )
            else:
                # Metadata exists, but may be incomplete/wrong (e.g. missing tables or wrong IDs).
                # Normalize without calling the LLM again.
                try:
                    description = (cached.get("prompt") or "").strip()
                    screen_payload = WorkflowScreenPayload.parse_obj(
                        {
                            "tab_ihm_wf": cached.get("tab_ihm_wf") or [],
                            "element_ihm_wf": cached.get("element_ihm_wf") or [],
                            "tab_detail_ihm_wf": cached.get("tab_detail_ihm_wf") or [],
                        }
                    )
                    screen_payload = enforce_minimum_metadata(
                        screen_payload,
                        cached.get("code") or "",
                        description,
                    )
                    derive_load_tab_from_elements(screen_payload)

                    tab_ihm_wf = [t.dict(by_alias=True) for t in (screen_payload.tab_ihm_wf or [])]
                    element_ihm_wf = [
                        e.dict(by_alias=True) for e in (screen_payload.element_ihm_wf or [])
                    ]
                    tab_detail_ihm_wf = [
                        d.dict(by_alias=True) for d in (screen_payload.tab_detail_ihm_wf or [])
                    ]

                    def updater(record):
                        record["tab_ihm_wf"] = tab_ihm_wf
                        record["element_ihm_wf"] = element_ihm_wf
                        record["tab_detail_ihm_wf"] = tab_detail_ihm_wf

                    updated = storage.update_generation(namespaced_id, updater)
                    if updated:
                        cached = updated
                except Exception as exc:
                    logger.warning(
                        "Failed to normalize cached metadata: id=%s err=%s",
                        namespaced_id,
                        exc,
                    )
            return jsonify(cached)

        code = cached.get("code")
        if isinstance(code, str):
            stripped = code.lstrip()
            lowered = stripped.lower()
            is_html = lowered.startswith("<!doctype html")
            looks_placeholder = (
                "..." in stripped
                or "…" in stripped
                or "truncated" in lowered
                or "for brevity" in lowered
            )
            if is_html and not looks_placeholder:
                return jsonify(cached)
        logger.info("Ignoring cached screen due to invalid preview HTML: id=%s", namespaced_id)

    # Lookup screen in workflow index
    screen_meta = None
    if wf_id:
        screen_meta = workflow_index.find_screen(wf_id, screen_id)
    else:
        # fallback: search all workflows
        for wf in workflow_index.list_workflows():
            screen_meta = workflow_index.find_screen(wf.get("id_wf"), screen_id)
            if screen_meta:
                wf_id = wf.get("id_wf")
                namespaced_id = f"{wf_id}:{screen_id}"
                break

    if not screen_meta:
        return jsonify({'error': 'Not found'}), 404

    # Generate on first access
    gen_result = generate_screen(screen_meta.get("description", ""))
    if 'error' in gen_result:
        logger.warning(
            "generate_screen failed: id=%s error=%s raw=%s",
            namespaced_id,
            gen_result.get("error"),
            (gen_result.get("raw_response") or "")[:2000],
        )
        return jsonify(gen_result), 502

    screen_schema = gen_result.get("screen_schema") or gen_result.get("structure") or {}
    # Context IDs (lowercase for prompt) and explicit variables for hydration
    id_client = screen_meta.get("id_client")
    id_wf_val = screen_meta.get("id_wf") or wf_id
    id_tache = screen_meta.get("id_tache")
    id_ihm = screen_id
    context_ids = {
        "id_client": id_client,
        "id_wf": id_wf_val,
        "id_tache": id_tache,
        "id_ihm": id_ihm,
    }
    schema_input = {
        "screen_schema": screen_schema,
        "html": gen_result.get("code") or gen_result.get("html") or "",
    }
    schema_result = extract_schema(screen_meta.get("description", ""), schema_input, context_ids)

    if isinstance(schema_result, WorkflowScreenPayload):
        schema_result = enforce_minimum_metadata(
            schema_result,
            schema_input.get("html") or "",
            screen_meta.get("description", ""),
        )


    tab_ihm_wf = []
    element_ihm_wf = []
    tab_detail_ihm_wf = []
    nom_ihm = screen_meta.get("name")
    html_from_schema = None

    if schema_result:
        schema_result = hydrate_oracle_metadata(
            schema_result, id_client, id_wf_val, id_tache, id_ihm
        )
        derive_load_tab_from_elements(schema_result)

    if schema_result:
        tab_ihm_wf = [t.dict(by_alias=True) for t in (schema_result.tab_ihm_wf or [])]
        element_ihm_wf = [e.dict(by_alias=True) for e in (schema_result.element_ihm_wf or [])]
        tab_detail_ihm_wf = [d.dict(by_alias=True) for d in (schema_result.tab_detail_ihm_wf or [])]

    if id_client and id_wf_val and id_tache and screen_id:
        kind = "workflow_screen"
        logical_key = f"{id_client}:{id_wf_val}:{id_tache}:{screen_id}"
    else:
        kind = "cached"
        logical_key = None

    if kind == "workflow_screen":
        logger.info(
            f"Lazy save workflow_screen: logical_key={logical_key}, "
            f"id_wf={screen_meta.get('id_wf') or wf_id}, id_ihm={screen_id}"
        )

    record = storage.store_generation({
        "id": namespaced_id,
        "kind": kind,
        "logical_key": logical_key,
        "prompt": screen_meta.get("description"),
        "structure": screen_schema,
        # prefer HTML from Oracle payload; fallback to first LLM code
        "code": html_from_schema or gen_result.get("code") or gen_result.get("html"),
        "raw_response": gen_result.get("raw_response"),
        "status": "draft",
        "version": 1,
        "id_client": screen_meta.get("id_client"),
        "id_wf": screen_meta.get("id_wf") or wf_id,
        "id_tache": screen_meta.get("id_tache"),
        "id_ihm": screen_id,
        "nom_ihm": nom_ihm,
        "tab_ihm_wf": tab_ihm_wf,
        "element_ihm_wf": element_ihm_wf,
        "tab_detail_ihm_wf": tab_detail_ihm_wf,
    })

    return jsonify(record)


@screens_bp.route("/screens/<screen_id>/elements", methods=["POST"])
def add_screen_element(screen_id: str):
    payload = request.get_json(silent=True) or {}

    id_tab = payload.get("ID_TAB")
    id_element = payload.get("ID_ELEMENT")
    type_element = payload.get("TYPE_ELEMENT")

    if not id_tab or not id_element or not type_element:
        return jsonify({"error": "ID_TAB, ID_ELEMENT, TYPE_ELEMENT are required"}), 400

    def updater(record):
        elements = record.get("element_ihm_wf") or []

        if any(e.get("ID_ELEMENT") == id_element for e in elements):
            raise ValueError("Element already exists")

        # default position: append at bottom of the tab
        max_y = max(
            (e.get("POSITION_Y") or 0) for e in elements if e.get("ID_TAB") == id_tab
        ) if elements else 0

        new_el = {
            "ID_TAB": id_tab,
            "ID_ELEMENT": id_element,
            "TYPE_ELEMENT": type_element,
            "ACTIVE": payload.get("ACTIVE", "O"),
            "POSITION_X": payload.get("POSITION_X", 1),
            "POSITION_Y": payload.get("POSITION_Y", max_y + 1),
            "ENUM_VALUES": payload.get("ENUM_VALUES"),
            "VALIDATEUR_ELEMENT": payload.get("VALIDATEUR_ELEMENT"),
            "CONTROL_ELEMENT": payload.get("CONTROL_ELEMENT"),
            "DEFAULT_VALUE_ELEMENT": payload.get("DEFAULT_VALUE_ELEMENT"),
            "LONGEUR_ELEMENT": payload.get("LONGEUR_ELEMENT"),
            "SQL_LOV_ELEMENT": payload.get("SQL_LOV_ELEMENT"),
            "TRANSIT": payload.get("TRANSIT", "N"),
            "HINT_ELEMENT": payload.get("HINT_ELEMENT"),
        }
        # keep json clean
        elements.append({k: v for k, v in new_el.items() if v is not None})
        record["element_ihm_wf"] = elements

        # normalize + recompute LOAD_TAB (don’t enforce prompt contract here)
        screen_payload = WorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": record.get("tab_ihm_wf") or [],
                "element_ihm_wf": record.get("element_ihm_wf") or [],
                "tab_detail_ihm_wf": record.get("tab_detail_ihm_wf") or [],
            }
        )
        screen_payload = enforce_minimum_metadata(screen_payload, record.get("code") or "", "")
        derive_load_tab_from_elements(screen_payload)

        record["tab_ihm_wf"] = [t.dict(by_alias=True) for t in (screen_payload.tab_ihm_wf or [])]
        record["element_ihm_wf"] = [e.dict(by_alias=True) for e in (screen_payload.element_ihm_wf or [])]
        record["tab_detail_ihm_wf"] = [d.dict(by_alias=True) for d in (screen_payload.tab_detail_ihm_wf or [])]

    try:
        updated = storage.update_generation(screen_id, updater)
    except ValueError as exc:
        msg = str(exc)
        if "already exists" in msg:
            return jsonify({"error": msg}), 409
        return jsonify({"error": msg}), 400

    if not updated:
        return jsonify({"error": "Screen not found"}), 404

    return jsonify({"status": "ok", "id_element": id_element}), 201


@screens_bp.route('/screens/<screen_id>/elements/<id_element>', methods=['PUT'])
def update_screen_element(screen_id: str, id_element: str):
    payload = request.get_json(silent=True) or {}

    def updater(record):
        elements = record.get("element_ihm_wf", [])
        for idx, el in enumerate(elements):
            if el.get("ID_ELEMENT") == id_element:
                elements[idx] = {
                    **el,
                    **payload,
                    "ID_ELEMENT": id_element,
                }
                try:
                    screen_payload = WorkflowScreenPayload.parse_obj(
                        {
                            "tab_ihm_wf": record.get("tab_ihm_wf") or [],
                            "element_ihm_wf": elements,
                            "tab_detail_ihm_wf": record.get("tab_detail_ihm_wf") or [],
                        }
                    )
                    derive_load_tab_from_elements(screen_payload)
                    record["tab_ihm_wf"] = [
                        t.dict(by_alias=True) for t in (screen_payload.tab_ihm_wf or [])
                    ]
                except Exception as exc:
                    logger.warning(
                        "Failed to derive LOAD_TAB after element update: id=%s err=%s",
                        record.get("id"),
                        exc,
                    )
                return
        raise ValueError("Element not found")

    try:
        updated = storage.update_generation(screen_id, updater)
    except ValueError:
        return jsonify({"error": "Element not found"}), 404

    if not updated:
        return jsonify({"error": "Screen not found"}), 404

    return jsonify({"status": "ok"})


@screens_bp.route('/workflows', methods=['GET'])
def list_workflows():
    return jsonify(workflow_index.list_workflows())

@screens_bp.route('/workflows/<wf_id>/screens', methods=['GET'])
def list_workflow_screens(wf_id: str):
    wf = workflow_index.find_workflow(wf_id)
    if not wf:
        return jsonify({'error': 'Not found'}), 404
    screens = []
    for task in wf.get("tasks", []):
        for scr in task.get("screens", []):
            screens.append({
                **scr,
                "id_client": wf.get("id_client"),
                "id_wf": wf_id,
                "id_tache": task.get("id_tache"),
                "task_name": task.get("name"),
            })
    return jsonify(screens)
