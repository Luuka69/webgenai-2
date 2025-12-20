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
            data = json.loads(INDEX_FILE.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            data = {}
        for entry in data.values():
            entry.setdefault("kind", "cached")
            entry.setdefault("logical_key", None)
        return data


    def _write_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        INDEX_FILE.write_text(json.dumps(index), encoding="utf-8")

    def store_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")

        gen_id = payload.get("id") or str(uuid.uuid4())
        id_client = payload.get("id_client")
        id_wf = payload.get("id_wf")
        id_tache = payload.get("id_tache")
        id_ihm = payload.get("id_ihm")

        kind = payload.get("kind")
        logical_key = payload.get("logical_key")
        if not kind and id_client and id_wf and id_tache and id_ihm:
            kind = "workflow_screen"
            logical_key = f"{id_client}:{id_wf}:{id_tache}:{id_ihm}"
        if not kind:
            kind = "cached"

        record = {
            "id": gen_id,
            "kind": kind,
            "logical_key": logical_key,
            "prompt": payload.get("prompt") or payload.get("description"),
            "code": payload.get("code"),
            "load_ihm": payload.get("load_ihm"),
            "tab_ihm_wf": payload.get("tab_ihm_wf"),
            "element_ihm_wf": payload.get("element_ihm_wf"),
            "tab_detail_ihm_wf": payload.get("tab_detail_ihm_wf"),
            "id_client": id_client,
            "id_wf": id_wf,
            "id_tache": id_tache,
            "id_ihm": id_ihm,
            "nom_ihm": payload.get("nom_ihm"),
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
        index[record["id"]] = {
            "offset": offset,
            "length": length,
            "kind": kind,
            "logical_key": logical_key,
        }
        self._write_index(index)
        return record

    def _read_at(self, offset: int, length: int) -> Optional[Dict[str, Any]]:
        with GEN_FILE.open("r", encoding="utf-8") as f:
            f.seek(offset)
            chunk = f.read(length)
            try:
                rec = json.loads(chunk.strip())
                rec.setdefault("kind", "cached")
                rec.setdefault("logical_key", None)
                return rec
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
                    # backfill defaults for old records
                    rec.setdefault("kind", "cached")
                    rec.setdefault("logical_key", None)
                    results.append(rec)
                except json.JSONDecodeError:
                    continue
        return results

    def list_generations_by_kind(self, kind: str) -> List[Dict[str, Any]]:
        kind = kind or "cached"
        return [rec for rec in self.list_generations() if rec.get("kind", "cached") == kind]

    def update_generation(self, gen_id: str, updater_fn) -> Optional[Dict[str, Any]]:
        """
        Update an existing generation in-place by rewriting the jsonl file.
        updater_fn takes the record and mutates it.
        """
        records = self.list_generations()
        updated_record = None

        for rec in records:
            if rec.get("id") == gen_id:
                updater_fn(rec)
                rec["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                updated_record = rec
                break

        if not updated_record:
            return None

        # Rewrite FULL file (safe & simple)
        with GEN_FILE.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        # Rebuild index (VERY IMPORTANT)
        index = {}
        offset = 0
        for rec in records:
            line = json.dumps(rec) + "\n"
            index[rec["id"]] = {
                "offset": offset,
                "length": len(line),
                "kind": rec.get("kind", "cached"),
                "logical_key": rec.get("logical_key"),
            }
            offset += len(line)

        self._write_index(index)

        return updated_record
