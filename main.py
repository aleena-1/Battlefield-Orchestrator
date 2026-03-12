from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from engine import Orchestrator, WANNACRY_IOCS, MITRE_MATRIX, WANNACRY_ACTIVE_TTPS
import uvicorn, asyncio, json
from datetime import datetime

app = FastAPI(title="BridgeIT CTI Orchestrator v2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orchestrator = Orchestrator()

# ── WebSocket manager ─────────────────────────────────────────────────────────
class WSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)

ws_manager = WSManager()

class SOCActionRequest(BaseModel):
    action: str
    target_node: Optional[str] = None

# ── Static & index ────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index(): return FileResponse("static/index.html")

# ── REST status ───────────────────────────────────────────────────────────────
@app.get("/status")
async def status(): return orchestrator.get_full_status()

# ── WebSocket live feed ───────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send full state immediately on connect
        await ws.send_json({"type":"state","data":orchestrator.get_full_status()})
        while True:
            # Every 2s push a lightweight tick update
            await asyncio.sleep(2)
            orchestrator.calculate_metrics()
            await ws.send_json({"type":"tick","data":orchestrator.get_full_status()})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        try: ws_manager.disconnect(ws)
        except: pass

async def _broadcast_state(extra: dict = None):
    data = orchestrator.get_full_status()
    if extra: data.update(extra)
    await ws_manager.broadcast({"type":"state","data":data})

# ── Kill chain ────────────────────────────────────────────────────────────────
@app.post("/kill-chain/advance")
async def advance():
    result = orchestrator.advance_kill_chain()
    await _broadcast_state()
    return result

@app.post("/kill-chain/reset")
async def reset():
    global orchestrator
    orchestrator = Orchestrator()
    await _broadcast_state()
    return {"message":"Simulation reset. All nodes restored to CLEAN."}

# ── DDIL ──────────────────────────────────────────────────────────────────────
@app.post("/simulate-failure")
async def ddil():
    msg = orchestrator.simulate_failure()
    await _broadcast_state()
    return {"message": msg}

# ── SOC actions ───────────────────────────────────────────────────────────────
@app.post("/soc/action")
async def soc(req: SOCActionRequest):
    result = orchestrator.soc_response(req.action, req.target_node)
    await _broadcast_state()
    return result

# Legacy
@app.post("/cyber-scan")
async def cyber_scan(): return await advance()

# ── IOC feed ─────────────────────────────────────────────────────────────────
@app.get("/ioc-feed")
async def ioc_feed():
    return {"iocs":WANNACRY_IOCS,"detected":orchestrator.ioc_hits,
            "total":sum(len(v) for v in WANNACRY_IOCS.values())}

# ── MITRE matrix ──────────────────────────────────────────────────────────────
@app.get("/mitre-matrix")
async def mitre():
    return {"matrix":MITRE_MATRIX,"active_ttps":list(WANNACRY_ACTIVE_TTPS),
            "actor":"WannaCry (Lazarus Group / APT38)"}

# ── Defender score ────────────────────────────────────────────────────────────
@app.get("/defender-score")
async def def_score(): return orchestrator.defender_score()

# ── Timeline ──────────────────────────────────────────────────────────────────
@app.get("/timeline")
async def timeline(): return {"events":orchestrator.timeline}

# ── STIX 2.1 export ───────────────────────────────────────────────────────────
@app.get("/export-stix")
async def stix():
    bundle = orchestrator.export_stix()
    return Response(content=bundle, media_type="application/json",
                    headers={"Content-Disposition":"attachment; filename=wannacry_bridgeit.stix2.json"})

# ── Mission text report ───────────────────────────────────────────────────────
@app.get("/export-mission")
async def mission():
    s = orchestrator.get_full_status()
    d = s["defender"]
    r = f"""
══════════════════════════════════════════════════════
  BRIDGEIT CTI TACTICAL MISSION REPORT
  {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
══════════════════════════════════════════════════════
THREAT ACTOR  : WannaCry Ransomware (Lazarus Group / APT38)
THREAT LEVEL  : {s['threat_level']}
KILL CHAIN    : Phase {s['kill_chain_phase']}/7
IOCs DETECTED : {s['ioc_count']}
ENCRYPTED     : {len(s['encrypted_nodes'])} nodes

DEFENDER SCORE: {d['total_score']}/100  GRADE: {d['grade']}
  Survival:     {d['survival_score']}/40
  Patch:        {d['patch_score']}/25
  Actions:      {d['action_score']}/20
  IOC Blocks:   {d['ioc_block_score']}/15
  Avg CVSS:     {d['avg_cvss']}
  Elapsed:      {d['elapsed_seconds']}s

NODE STATUS
{'─'*55}
"""
    for nid,n in s["nodes"].items():
        r += f"  {nid:<20} | {n['node_type']:<14} | {n['security_status']:<12} | BATT:{n['battery']:.1f}% | {'PATCHED' if n['os_patched'] else 'VULN'} | CVSS:{n['cvss_score']}\n"
    r += f"\nDETECTED IOCs\n{'─'*55}\n"
    for ioc in orchestrator.ioc_hits:
        r += f"  [{ioc['type']}] {ioc['value']}  Conf:{ioc['confidence']}%  CVSS:{ioc.get('cvss',0)}\n"
    r += f"\n{'═'*54}\n"
    return PlainTextResponse(r)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)