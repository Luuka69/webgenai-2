from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ai_engine.schemas.pydantic.screen import ScreenSchema


class BindingSuggestion(BaseModel):
    field_id: Optional[str] = None
    column_id: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    accepted: bool = False

    class Config:
        extra = "allow"


class AIResponse(BaseModel):
    structure: Optional[ScreenSchema] = None
    code: str = ""
    raw_response: Optional[str] = None
    
    class Config:
        extra = "allow"



class StoredGeneration(BaseModel):
    id: str
    kind: str = "cached"  # or "workflow_screen"
    logical_key: Optional[str] = None  # "ID_CLIENT:ID_WF:ID_TACHE:ID_IHM"

    prompt: Optional[str] = None
    title: Optional[str] = None

    # Oracle metadata
    load_ihm: Optional[Any] = None
    tab_ihm_wf: Optional[List[Any]] = None
    element_ihm_wf: Optional[List[Any]] = None
    tab_detail_ihm_wf: Optional[List[Any]] = None

    id_client: Optional[int] = None
    id_wf: Optional[str] = None
    id_tache: Optional[str] = None
    id_ihm: Optional[str] = None
    nom_ihm: Optional[str] = None

    # keep code for preview during transition (optional)
    code: str = ""

    status: str = "draft"
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"
