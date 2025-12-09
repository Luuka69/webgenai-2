from flask import Blueprint, jsonify, request

from ai_engine.services.schema_generator import extract_schema

schema_bp = Blueprint("schema", __name__)

@schema_bp.route("/ai/extract-schema", methods=["POST"])
def extract_schema_route():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    screen_schema = data.get("screen_schema")
    if not prompt or not isinstance(screen_schema, dict):
        return jsonify({"error": "prompt and screen_schema are required"}), 400
    result = extract_schema(prompt, screen_schema)
    return jsonify(result)
