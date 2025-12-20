from flask import Blueprint, jsonify, request

import logging
from ai_engine.services.generation import generate_screen
from ai_engine.services.schema_generator import extract_schema
from ai_engine.services.storage import StorageService
from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
from ai_engine.services.metadata_normalizer import hydrate_oracle_metadata


generation_bp = Blueprint('generation', __name__)
storage = StorageService()
logger = logging.getLogger(__name__)

@generation_bp.route('/', methods=['GET'])
def health():
    return jsonify({'message': 'AI Engine running'})


@generation_bp.route('/process', methods=['POST'])
def process():
    data = request.get_json(silent=True) or {}
    description = data.get('description', '').strip()
    if not description:
        return jsonify({'error': 'Description is required'}), 400

    # Optional workflow context
    id_client = data.get('id_client')
    id_wf = data.get('id_wf')
    id_tache = data.get('id_tache')
    id_ihm = data.get('id_ihm')

    is_workflow = bool(id_client and id_wf and id_tache and id_ihm)

    ui_result = generate_screen(description)
    if 'error' in ui_result:
        logger.warning(
            "generate_screen failed in /process: error=%s raw=%s",
            ui_result.get("error"),
            (ui_result.get("raw_response") or "")[:2000],
        )
        return jsonify(ui_result), 502

    # Simple schema from first LLM (HTML generator)
    screen_schema = ui_result.get('structure') or ui_result.get('screen_schema') or {}
    tab_ihm_wf = []
    element_ihm_wf = []
    tab_detail_ihm_wf = []
    nom_ihm = data.get("nom_ihm") or (screen_schema.get("title") if isinstance(screen_schema, dict) else None)
    html_from_schema = None  # second LLM no longer returns HTML

    # Second step: extract Oracle-friendly metadata for both cached and workflow screens.
    # For cached generations, workflow IDs stay null; for workflow generations, we hydrate IDs.
    context_ids = {
        "id_client": id_client,
        "id_wf": id_wf,
        "id_tache": id_tache,
        "id_ihm": id_ihm,
    }
    schema_input = {
        "screen_schema": screen_schema,
        "html": ui_result.get("code") or ui_result.get("html") or "",
    }
    schema_result = extract_schema(description, schema_input, context_ids)

    if is_workflow:
        schema_result = hydrate_oracle_metadata(
            schema_result, id_client, id_wf, id_tache, id_ihm
        )

    if isinstance(schema_result, WorkflowScreenPayload):
        tab_ihm_wf = [t.dict(by_alias=True) for t in (schema_result.tab_ihm_wf or [])]
        element_ihm_wf = [e.dict(by_alias=True) for e in (schema_result.element_ihm_wf or [])]
        tab_detail_ihm_wf = [d.dict(by_alias=True) for d in (schema_result.tab_detail_ihm_wf or [])]

    # Determine storage kind/logical_key
    if is_workflow:
        kind = "workflow_screen"
        logical_key = f"{id_client}:{id_wf}:{id_tache}:{id_ihm}"
        gen_id = f"{id_wf}:{id_ihm}"
    else:
        kind = "cached"
        logical_key = None
        gen_id = None

    if kind == "workflow_screen":
        logger.info(f"Saving workflow_screen: logical_key={logical_key}, id_wf={id_wf}, id_ihm={id_ihm}")


    stored = storage.store_generation({
        'id': gen_id,
        'kind': kind,
        'logical_key': logical_key,
        'prompt': description,
        'structure': screen_schema,  # kept for backward compatibility
        'code': html_from_schema or ui_result.get('code') or ui_result.get('html'),
        'raw_response': ui_result.get('raw_response'),
        'tab_ihm_wf': tab_ihm_wf,
        'element_ihm_wf': element_ihm_wf,
        'tab_detail_ihm_wf': tab_detail_ihm_wf,
        'id_client': id_client,
        'id_wf': id_wf,
        'id_tache': id_tache,
        'id_ihm': id_ihm,
        'nom_ihm': nom_ihm,
    })

    return jsonify({
        'id': stored['id'],
        'kind': stored.get('kind'),
        'logical_key': stored.get('logical_key'),
        'id_client': stored.get('id_client'),
        'id_wf': stored.get('id_wf'),
        'id_tache': stored.get('id_tache'),
        'id_ihm': stored.get('id_ihm'),
        'nom_ihm': stored.get('nom_ihm'),
        'screen_schema': screen_schema,
        'code': stored.get('code'),
        'tab_ihm_wf': stored.get('tab_ihm_wf'),
        'element_ihm_wf': stored.get('element_ihm_wf'),
        'tab_detail_ihm_wf': stored.get('tab_detail_ihm_wf'),
    })
