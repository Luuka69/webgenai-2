import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default to repo-level .data/workflows.json (ai-engine/.data/workflows.json)
WORKFLOWS_PATH = (
    Path(__file__).resolve().parent.parent.parent / ".data" / "workflows.json"
)

class WorkflowIndex:
    def __init__(self, path: Path = WORKFLOWS_PATH) -> None:
        self.path = path

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"workflows": []}

    def list_workflows(self) -> List[Dict[str, Any]]:
        return self._load().get("workflows", [])

    def find_workflow(self, wf_id: str) -> Optional[Dict[str, Any]]:
        return next((w for w in self.list_workflows() if w.get("id_wf") == wf_id), None)

    def find_screen(self, wf_id: str, screen_id: str) -> Optional[Dict[str, Any]]:
        wf = self.find_workflow(wf_id)
        if not wf:
            return None
        for task in wf.get("tasks", []):
            for scr in task.get("screens", []):
                if scr.get("id_ihm") == screen_id:
                    return {
                        **scr,
                        "id_client": wf.get("id_client"),
                        "id_wf": wf_id,
                        "id_tache": task.get("id_tache"),
                        "task_name": task.get("name"),
                    }
        return None
