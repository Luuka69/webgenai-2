from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ai_engine.schemas.pydantic.data import DataSchema
from ai_engine.schemas.pydantic.relations import ScreenRelation
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
    data_schema: Optional[DataSchema] = None
    bindings: List[BindingSuggestion] = Field(default_factory=list)
    relations: List[ScreenRelation] = Field(default_factory=list)
    raw_response: Optional[str] = None

    class Config:
        extra = "allow"
class StoredGeneration(BaseModel):
    id: str
    kind: str = "cached"  # "cached" or "workflow_screen"
    logical_key: Optional[str] = None  # e.g. "1:WF_CONTACTS:CREATE_CONTACT:CONTACT_FORM"

    prompt: Optional[str] = None
    structure: Optional[Any] = None
    code: str = ""
    data_schema: Optional[DataSchema] = None
    bindings: List[Any] = Field(default_factory=list)
    relations: List[Any] = Field(default_factory=list)
    load_ihm: Optional[Any] = None
    tab_ihm_wf: Optional[List[Any]] = None
    element_ihm_wf: Optional[List[Any]] = None
    tab_detail_ihm_wf: Optional[List[Any]] = None

    id_client: Optional[Any] = None
    id_wf: Optional[Any] = None
    id_tache: Optional[Any] = None
    id_ihm: Optional[Any] = None
    nom_ihm: Optional[Any] = None

    raw_response: Optional[str] = None
    status: str = "draft"
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"
