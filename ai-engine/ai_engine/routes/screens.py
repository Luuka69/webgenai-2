from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService
from ai_engine.services.workflow_index import WorkflowIndex
from ai_engine.services.metadata_normalizer import hydrate_oracle_metadata
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

    tab_ihm_wf = []
    element_ihm_wf = []
    tab_detail_ihm_wf = []
    nom_ihm = screen_meta.get("name")
    html_from_schema = None

    if schema_result:
        schema_result = hydrate_oracle_metadata(
            schema_result, id_client, id_wf_val, id_tache, id_ihm
        )

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
