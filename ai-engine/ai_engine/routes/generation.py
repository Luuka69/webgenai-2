from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService
from ai_engine.services.schema_generator import extract_schema
from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
import logging


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

    ui_result = generate_screen(description)
    if 'error' in ui_result:
        return jsonify(ui_result), 502

    screen_schema = ui_result.get('screen_schema') or ui_result.get('structure') or {}
    context_ids = {
        "id_client": id_client,
        "id_wf": id_wf,
        "id_tache": id_tache,
        "id_ihm": id_ihm,
    }
    schema_result = extract_schema(description, screen_schema, context_ids)
    load_ihm = None
    tab_ihm_wf = []
    element_ihm_wf = []
    tab_detail_ihm_wf = []
    nom_ihm = data.get("nom_ihm")
    html_from_schema = None

    if isinstance(schema_result, WorkflowScreenPayload):
        load_ihm = schema_result.ihm.load_ihm if getattr(schema_result, "ihm", None) else None
        tab_ihm_wf = schema_result.tab_ihm_wf or []
        element_ihm_wf = schema_result.element_ihm_wf or []
        tab_detail_ihm_wf = schema_result.tab_detail_ihm_wf or []
        if getattr(schema_result, "ihm", None) and getattr(schema_result.ihm, "nom_ihm", None):
            nom_ihm = schema_result.ihm.nom_ihm
        if load_ihm and isinstance(load_ihm, dict):
            li = load_ihm.get("LOAD_IHM") or {}
            if not li.get("html"):
                li["html"] = ui_result.get("code") or ui_result.get("html")
            load_ihm["LOAD_IHM"] = li
            html_from_schema = li.get("html")


    # Determine storage kind/logical_key
    if id_client and id_wf and id_tache and id_ihm:
        kind = "workflow_screen"
        logical_key = f"{id_client}:{id_wf}:{id_tache}:{id_ihm}"
    else:
        kind = "cached"
        logical_key = None

    if kind == "workflow_screen":
        logger.info(f"Saving workflow_screen: logical_key={logical_key}, id_wf={id_wf}, id_ihm={id_ihm}")


    stored = storage.store_generation({
        'kind': kind,
        'logical_key': logical_key,
        'prompt': description,
        'structure': screen_schema,
        'code': html_from_schema or ui_result.get('code') or ui_result.get('html'),
        'raw_response': ui_result.get('raw_response'),
        'load_ihm': load_ihm,
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
        'screen_schema': screen_schema,
        'code': stored.get('code'),
        'load_ihm': stored.get('load_ihm'),
        'tab_ihm_wf': stored.get('tab_ihm_wf'),
        'element_ihm_wf': stored.get('element_ihm_wf'),
        'tab_detail_ihm_wf': stored.get('tab_detail_ihm_wf'),
    })

