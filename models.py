from pydantic import BaseModel
from typing import Dict

class NodeState(BaseModel):
    node_id: str
    node_type: str
    battery: int
    is_connected: bool
    workload_share: float
    lat: float
    lon: float

class MissionUpdate(BaseModel):
    status: str
    accuracy: float
    nodes: Dict[str, NodeState]