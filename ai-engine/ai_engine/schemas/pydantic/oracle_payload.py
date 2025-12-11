from typing import List
from pydantic import BaseModel
from ai_engine.schemas.pydantic.oracle_metadata import (
    IhmWf,
    TabIhmWf,
    TabDetailIhmWf,
    ElementIhmWf,
)

class WorkflowScreenPayload(BaseModel):
    ihm: IhmWf
    tab_ihm_wf: List[TabIhmWf] = []
    element_ihm_wf: List[ElementIhmWf] = []
    tab_detail_ihm_wf: List[TabDetailIhmWf] = []

    class Config:
        extra = "allow"
