from flask import Blueprint, jsonify, request

from ai_engine.services.generation import generate_screen


generation_bp = Blueprint('generation', __name__)


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

    return jsonify(result)
