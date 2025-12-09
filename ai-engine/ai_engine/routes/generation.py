from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService
from ai_engine.services.schema_generator import extract_schema


generation_bp = Blueprint('generation', __name__)
storage = StorageService()


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

    # Determine storage kind/logical_key
    if id_client and id_wf and id_tache and id_ihm:
        kind = "workflow_screen"
        logical_key = f"{id_client}:{id_wf}:{id_tache}:{id_ihm}"
    else:
        kind = "cached"
        logical_key = None

    stored = storage.store_generation({
        'kind': kind,
        'logical_key': logical_key,
        'prompt': description,
        'structure': screen_schema,
        'code': ui_result.get('code') or ui_result.get('html'),
        'raw_response': ui_result.get('raw_response'),
        'load_ihm': schema_result.get('ihm'),
        'tab_ihm_wf': schema_result.get('tab_ihm_wf'),
        'element_ihm_wf': schema_result.get('element_ihm_wf'),
        'tab_detail_ihm_wf': schema_result.get('tab_detail_ihm_wf'),
        'id_client': id_client,
        'id_wf': id_wf,
        'id_tache': id_tache,
        'id_ihm': id_ihm,
    })

    return jsonify({
        'id': stored['id'],
        'kind': stored.get('kind'),
        'logical_key': stored.get('logical_key'),
        'screen_schema': screen_schema,
        'code': ui_result.get('code') or ui_result.get('html'),
        'load_ihm': schema_result.get('ihm'),
        'tab_ihm_wf': schema_result.get('tab_ihm_wf'),
        'element_ihm_wf': schema_result.get('element_ihm_wf'),
        'tab_detail_ihm_wf': schema_result.get('tab_detail_ihm_wf'),
    })
