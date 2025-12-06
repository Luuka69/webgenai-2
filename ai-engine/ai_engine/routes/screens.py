from flask import Blueprint, jsonify, request

from ai_engine.services.storage import StorageService

screens_bp = Blueprint('screens', __name__)

storage = StorageService()


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
    records = storage.list_generations()
    return jsonify(records)


@screens_bp.route('/screens/<screen_id>', methods=['GET'])
def get_screen_record(screen_id: str):
    record = storage.get_generation(screen_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)
