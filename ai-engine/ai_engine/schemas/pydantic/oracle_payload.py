from typing import List
from pydantic import BaseModel
from ai_engine.schemas.pydantic.oracle_metadata import (
    TabIhmWf,
    ElementIhmWf,
    TabDetailIhmWf,
)

class WorkflowScreenPayload(BaseModel):
    """
    Result of the second LLM: Oracle metadata for one screen.
    NOTE: Do not include IHM/LOAD_IHM here; that comes from another system.
    """
    tab_ihm_wf: List[TabIhmWf] = []
    element_ihm_wf: List[ElementIhmWf] = []
    tab_detail_ihm_wf: List[TabDetailIhmWf] = []

    class Config:
        extra = "allow"
