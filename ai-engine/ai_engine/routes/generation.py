from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen
from ai_engine.services.storage import StorageService


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

    result = generate_screen(description)

    if 'error' in result:
        status = 502 if 'raw_response' in result else 502
        return jsonify(result), status

    stored = storage.store_generation({
        'prompt': description,
        **result,
    })
    return jsonify({
        'screenId': stored['id'],
        **result,
    })
