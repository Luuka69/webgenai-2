from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService
from ai_engine.services.workflow_index import WorkflowIndex
from ai_engine.services.schema_generator import extract_schema


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
    namespaced_id = f"{wf_id}:{screen_id}" if wf_id else screen_id

    # Try cache first
    cached = storage.get_generation(namespaced_id)
    if cached:
        return jsonify(cached)

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
        return jsonify(gen_result), 502

    screen_schema = gen_result.get("screen_schema") or gen_result.get("structure") or {}
    context_ids = {
        "ID_CLIENT": screen_meta.get("id_client"),
        "ID_WF": screen_meta.get("id_wf") or wf_id,
        "ID_TACHE": screen_meta.get("id_tache"),
        "ID_IHM": screen_id,
    }
    schema_result = extract_schema(screen_meta.get("description", ""), screen_schema, context_ids)

    record = storage.store_generation({
        "id": namespaced_id,
        "prompt": screen_meta.get("description"),
        "structure": screen_schema,
        "code": gen_result.get("code") or gen_result.get("html"),
        "raw_response": gen_result.get("raw_response"),
        "status": "draft",
        "version": 1,
        "id_client": screen_meta.get("id_client"),
        "id_wf": screen_meta.get("id_wf") or wf_id,
        "id_tache": screen_meta.get("id_tache"),
        "id_ihm": screen_id,
        "nom_ihm": screen_meta.get("name"),
        "load_ihm": schema_result.get("ihm"),
        "tab_ihm_wf": schema_result.get("tab_ihm_wf"),
        "element_ihm_wf": schema_result.get("element_ihm_wf"),
        "tab_detail_ihm_wf": schema_result.get("tab_detail_ihm_wf"),
    })
    return jsonify(record)

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
