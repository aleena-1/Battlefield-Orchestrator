from pydantic import BaseModel
from typing import Dict, List, Optional

class NodeState(BaseModel):
    node_id: str
    node_type: str
    battery: float
    is_connected: bool
    workload_share: float
    lat: float
    lon: float
    security_status: str            # CLEAN | SUSPICIOUS | QUARANTINED | ENCRYPTED
    kill_chain_phase: int           # 0–7
    ttf_minutes: float
    latency_ms: int
    os_patched: bool
    smb_port_open: bool
    is_compromised: bool

class IOCHit(BaseModel):
    type: str
    value: str
    phase: int
    confidence: int
    description: str

class KillChainStage(BaseModel):
    phase: int
    stage: str
    technique_id: str
    color: str
    active: bool

class MissionStatus(BaseModel):
    accuracy: float
    threat_level: str               # CLEAR | LOW | MEDIUM | HIGH | CRITICAL
    kill_chain_phase: int
    total_kill_chain_phases: int
    ransomware_active: bool
    encrypted_nodes: List[str]
    ioc_count: int
    recent_iocs: List[dict]
    soc_alerts: List[dict]
    kill_chain_stages: List[KillChainStage]
    nodes: Dict[str, NodeState]

class SOCActionRequest(BaseModel):
    action: str                     # isolate | patch | scan | restore | block_ioc
    target_node: Optional[str] = None