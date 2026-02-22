from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from engine import Orchestrator
from fastapi.staticfiles import StaticFiles
import uvicorn
import random

app = FastAPI(title="BridgeIT Battlefield Orchestrator")
orchestrator = Orchestrator()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index(): return FileResponse("static/index.html")

@app.get("/status")
async def get_status():
    orchestrator.calculate_metrics()
    total_workload = sum(n.workload_share for n in orchestrator.nodes.values())
    
    # Logic: Accuracy is affected by network Latency
    avg_lat = sum(n.latency_ms for n in orchestrator.nodes.values() if n.is_connected) / 8
    accuracy = 92.4 if total_workload >= 90 else (total_workload * 0.9)
    final_acc = accuracy - (avg_lat / 40) # Higher latency = lower accuracy
    
    return {
        "accuracy": round(final_acc, 1),
        "nodes": {nid: vars(node) for nid, node in orchestrator.nodes.items()}
    }

@app.post("/simulate-failure")
async def trigger_failure():
    return {"message": orchestrator.simulate_failure()}

@app.post("/cyber-scan")
async def cyber_scan():
    # This now uses the phased Kill-Chain logic
    return {"message": orchestrator.trigger_kill_chain()}

@app.get("/export-mission")
async def export_mission():
    """FEATURE: Black Box Mission Report Generator."""
    report = "--- BRIDGEIT TACTICAL MISSION REPORT ---\n"
    for nid, n in orchestrator.nodes.items():
        report += f"NODE: {nid} | TYPE: {n.node_type} | BATT: {n.battery}% | SEC: {n.security_status}\n"
    return PlainTextResponse(report)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
