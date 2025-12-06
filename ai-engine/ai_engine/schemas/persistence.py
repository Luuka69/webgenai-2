from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PromptLog:
    id: str
    workflow_id: Optional[str]
    screen_id: Optional[str]
    prompt_text: str
    ai_model: Optional[str]
    ai_response_raw: Any
    created_at: Optional[str] = None


@dataclass
class StoredScreen:
    id: str
    prompt: Optional[str]
    screen_schema: Dict[str, Any]
    data_schema: Optional[Dict[str, Any]]
    bindings: Optional[Any]
    relations: Optional[Any]
    raw_response: Optional[Any]
    version: int = 1
    status: str = 'draft'
