import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Simple JSONL-based storage for now; swap with DB later
STORAGE_DIR = Path(os.getenv("AI_ENGINE_STORAGE_DIR", "/opt/webgenai/webgen-ai/ai-engine/.data"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
GEN_FILE = STORAGE_DIR / "generations.jsonl"


class StorageService:
    def store_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")
        record = {
            "id": payload.get("id") or str(uuid.uuid4()),
            "prompt": payload.get("prompt") or payload.get("description"),
            "structure": payload.get("structure"),
            "code": payload.get("code"),
            "data_schema": payload.get("data_schema"),
            "bindings": payload.get("bindings"),
            "relations": payload.get("relations"),
            "raw_response": payload.get("raw_response"),
        }
        with GEN_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def get_generation(self, gen_id: str) -> Optional[Dict[str, Any]]:
        if not GEN_FILE.exists():
            return None
        with GEN_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if rec.get("id") == gen_id:
                    return rec
        return None
