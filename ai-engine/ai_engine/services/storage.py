import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Simple JSONL-based storage for now; swap with DB later
STORAGE_DIR = Path(os.getenv("AI_ENGINE_STORAGE_DIR", "/opt/webgenai/webgen-ai/ai-engine/.data"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
GEN_FILE = STORAGE_DIR / "generations.jsonl"
INDEX_FILE = STORAGE_DIR / "index.json"


class StorageService:
    def __init__(self) -> None:
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not GEN_FILE.exists():
            GEN_FILE.touch()
        if not INDEX_FILE.exists():
            INDEX_FILE.write_text("{}", encoding="utf-8")

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _write_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        INDEX_FILE.write_text(json.dumps(index), encoding="utf-8")

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
            "status": payload.get("status", "draft"),
            "version": payload.get("version", 1),
            "created_at": payload.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": payload.get("updated_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        line = json.dumps(record) + "\n"
        with GEN_FILE.open("a", encoding="utf-8") as f:
            offset = f.tell()
            f.write(line)
            length = len(line)

        index = self._load_index()
        index[record["id"]] = {"offset": offset, "length": length}
        self._write_index(index)
        return record

    def _read_at(self, offset: int, length: int) -> Optional[Dict[str, Any]]:
        with GEN_FILE.open("r", encoding="utf-8") as f:
            f.seek(offset)
            chunk = f.read(length)
            try:
                return json.loads(chunk.strip())
            except json.JSONDecodeError:
                return None

    def get_generation(self, gen_id: str) -> Optional[Dict[str, Any]]:
        index = self._load_index()
        entry = index.get(gen_id)
        if not entry:
            return None
        return self._read_at(entry["offset"], entry["length"])

    def list_generations(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        with GEN_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                    results.append(rec)
                except json.JSONDecodeError:
                    continue
        return results
