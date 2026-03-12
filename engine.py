import random
import uuid
import json
from datetime import datetime, timezone

WANNACRY_KILL_CHAIN = [
    {"phase":1,"stage":"RECONNAISSANCE","technique_id":"T1595","technique":"Active Scanning",
     "description":"Scanning for SMBv1 (port 445) vulnerable hosts across subnet",
     "color":"#6366f1","cvss_base":4.0,"cvss_vector":"AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L"},
    {"phase":2,"stage":"WEAPONIZATION","technique_id":"T1587.001","technique":"Malware Development",
     "description":"EternalBlue exploit + DoublePulsar kernel backdoor assembly",
     "color":"#8b5cf6","cvss_base":6.5,"cvss_vector":"AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:L/A:N"},
    {"phase":3,"stage":"DELIVERY","technique_id":"T1210","technique":"Exploit Remote Services",
     "description":"SMBv1 RCE via MS17-010 targeting unpatched Windows systems",
     "color":"#f59e0b","cvss_base":8.1,"cvss_vector":"AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H"},
    {"phase":4,"stage":"EXPLOITATION","technique_id":"T1055","technique":"Process Injection",
     "description":"DoublePulsar kernel backdoor installed, WannaCry payload injected",
     "color":"#f97316","cvss_base":8.8,"cvss_vector":"AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"},
    {"phase":5,"stage":"LATERAL MOVE","technique_id":"T1021.002","technique":"SMB/Windows Admin Shares",
     "description":"Worm self-propagating across all reachable subnet nodes via SMB",
     "color":"#ef4444","cvss_base":9.0,"cvss_vector":"AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"},
    {"phase":6,"stage":"C2","technique_id":"T1071","technique":"Application Layer Protocol",
     "description":"Kill-switch domain lookup via Tor relay; C2 beacon established",
     "color":"#dc2626","cvss_base":7.5,"cvss_vector":"AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"},
    {"phase":7,"stage":"IMPACT","technique_id":"T1486","technique":"Data Encrypted for Impact",
     "description":"AES-128 file encryption, RSA-2048 key exchange, .WNCRY extension",
     "color":"#991b1b","cvss_base":10.0,"cvss_vector":"AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"},
]

WANNACRY_IOCS = {
    "hashes":[
        {"value":"84c82835a5d21bbcf75a61706d8ab549","type":"MD5","confidence":95,"description":"WannaCry primary dropper"},
        {"value":"db349b97c37d22f5ea1d1841e3c89eb4","type":"MD5","confidence":92,"description":"mssecsvc.exe worm service"},
        {"value":"ed01ebfbc9eb5bbea545af4d01bf5f10","type":"SHA256","confidence":98,"description":"taskche.exe encryptor"},
        {"value":"b9c5d4339809e0ad9a00d4d3dd26fdf4","type":"SHA256","confidence":89,"description":"WannaCry v2.0 variant"},
    ],
    "ips":[
        {"value":"197.231.221.221","port":445,"confidence":91,"description":"Known C2 infrastructure"},
        {"value":"128.31.0.39","port":9001,"confidence":85,"description":"Tor relay used for C2"},
        {"value":"79.172.193.32","port":445,"confidence":88,"description":"SMB scanning origin"},
        {"value":"89.45.235.21","port":443,"confidence":76,"description":"Secondary C2 relay"},
    ],
    "domains":[
        {"value":"iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea.com","type":"kill_switch","confidence":100,"description":"WannaCry kill-switch (MalwareTech)"},
        {"value":"ifferfsodp9ifjaposdfjhgosurijfaewrwergwea.com","type":"kill_switch","confidence":97,"description":"WannaCry v2 kill-switch"},
    ],
    "registry_keys":[
        {"value":"HKLM\\SOFTWARE\\WanaCrypt0r\\wd","confidence":94,"description":"WannaCry working directory"},
        {"value":"HKLM\\SYSTEM\\CurrentControlSet\\Services\\mssecsvc2.0","confidence":96,"description":"Malicious service"},
    ]
}

MITRE_MATRIX = {
    "Initial Access":   [("T1190","Exploit Public App"),("T1566","Phishing"),("T1133","External Remote Svc")],
    "Execution":        [("T1059","Cmd Interpreter"),("T1055","Process Injection"),("T1106","Native API")],
    "Persistence":      [("T1543","Create Sys Process"),("T1547","Boot Autostart"),("T1136","Create Account")],
    "Defense Evasion":  [("T1562","Impair Defenses"),("T1070","Indicator Removal"),("T1036","Masquerading")],
    "Lateral Movement": [("T1021","Remote Services"),("T1210","Exploit Remote Svc"),("T1021.002","SMB Shares")],
    "Collection":       [("T1005","Local Sys Data"),("T1039","Network Share"),("T1025","Removable Media")],
    "Impact":           [("T1486","Data Encrypted"),("T1498","Network DoS"),("T1529","System Shutdown")],
}
WANNACRY_ACTIVE_TTPS = {"T1190","T1055","T1543","T1562","T1021","T1210","T1486","T1595","T1587.001","T1071","T1021.002"}

TOPOLOGY_EDGES = [
    ("HQ_CLOUD_ALPHA","MOBILE_EDGE_01"),("HQ_CLOUD_ALPHA","MOBILE_EDGE_02"),
    ("MOBILE_EDGE_01","UAV_SWARM_01"),("MOBILE_EDGE_01","UAV_SWARM_02"),
    ("MOBILE_EDGE_01","UAV_SWARM_03"),("MOBILE_EDGE_02","UAV_SWARM_03"),
    ("MOBILE_EDGE_02","UAV_SWARM_04"),("MOBILE_EDGE_02","UAV_SWARM_05"),
    ("UAV_SWARM_01","UAV_SWARM_02"),("UAV_SWARM_04","UAV_SWARM_05"),
]


class DigitalTwin:
    def __init__(self, node_id, node_type, battery=100, lat=17.4065, lon=78.4772):
        self.node_id    = node_id
        self.node_type  = node_type
        self.battery    = float(battery)
        self.is_connected    = True
        self.workload_share  = 0.0
        self.lat = lat + random.uniform(-0.022, 0.022)
        self.lon = lon + random.uniform(-0.022, 0.022)
        self.is_compromised  = False
        self.security_status = "CLEAN"
        self.ttf_minutes     = 0.0
        self.latency_ms      = random.randint(10, 30)
        self.kill_chain_phase = 0
        self.smb_port_open   = node_type in ["Tactical_Edge","Sensor"]
        self.os_patched      = random.random() > 0.4
        self.cvss_score      = 0.0

    def is_clean(self):
        return self.security_status == "CLEAN"


class Orchestrator:
    def __init__(self):
        self.nodes = {
            "HQ_CLOUD_ALPHA": DigitalTwin("HQ_CLOUD_ALPHA","Cloud",100,17.42,78.50),
            "MOBILE_EDGE_01": DigitalTwin("MOBILE_EDGE_01","Tactical_Edge",88,17.39,78.45),
            "MOBILE_EDGE_02": DigitalTwin("MOBILE_EDGE_02","Tactical_Edge",42,17.41,78.48),
        }
        self.nodes["HQ_CLOUD_ALPHA"].os_patched = True
        for i in range(1,6):
            uid = f"UAV_SWARM_{i:02d}"
            self.nodes[uid] = DigitalTwin(uid,"Sensor",random.randint(75,95),17.40,78.47)

        self.active_kill_chain_phase = 0
        self.ioc_hits        = []
        self.timeline        = []
        self.soc_alert_queue = []
        self.ransomware_active = False
        self.encrypted_nodes   = []
        self.infected_edges    = set()
        self.mission_start     = datetime.now(timezone.utc)
        self.defender_actions  = 0
        self.nodes_saved       = 0

    def _ts(self):
        return datetime.now(timezone.utc).isoformat()

    def _elapsed(self):
        return (datetime.now(timezone.utc) - self.mission_start).total_seconds()

    def _log(self, phase, stage, node, event, severity, cvss=0.0):
        self.timeline.append({
            "id":str(uuid.uuid4())[:8],"ts":self._ts(),
            "elapsed":round(self._elapsed(),1),
            "phase":phase,"stage":stage,"node":node,
            "event":event,"severity":severity,"cvss":cvss,
        })

    def calculate_metrics(self):
        for n in self.nodes.values():
            if n.is_connected and n.battery > 0:
                rate = 0.1 + (n.workload_share/20)
                n.ttf_minutes = round(n.battery/rate,1)
                n.latency_ms  = 15+int(n.workload_share*1.2)+random.randint(0,5)
                if n.workload_share > 0:
                    n.battery = max(0, round(n.battery-(rate/10),2))
            else:
                n.ttf_minutes = 0; n.latency_ms = 0
            if n.battery <= 0: n.is_connected = False

    def smart_redistribute(self):
        self.calculate_metrics()
        cloud = self.nodes["HQ_CLOUD_ALPHA"]
        cands = [n for n in self.nodes.values() if n.node_type=="Tactical_Edge" and n.is_connected and not n.is_compromised]
        if not cloud.is_connected or cloud.is_compromised:
            pool = sum(n.battery for n in cands)
            if pool > 0:
                for n in cands: n.workload_share = (n.battery/pool)*95.0
                return f"DDIL: AI sharded across {len(cands)} secure edges."
            return "CRITICAL: Total connectivity loss."
        for n in self.nodes.values(): n.workload_share = 0
        cloud.workload_share = 100.0
        return "STABLE: HQ Cloud holding primary inference."

    def simulate_failure(self):
        for n in self.nodes.values():
            if n.node_type != "Cloud": n.is_connected = random.random() > 0.4
        self._log(0,"DDIL","NETWORK","Random DDIL connectivity failure","HIGH")
        return self.smart_redistribute()

    def advance_kill_chain(self):
        if self.active_kill_chain_phase >= len(WANNACRY_KILL_CHAIN):
            return {"message":"Kill chain complete.","phase":7,"stage":"COMPLETE","cvss":10.0}
        step = WANNACRY_KILL_CHAIN[self.active_kill_chain_phase]
        self.active_kill_chain_phase += 1
        ph   = step["phase"]
        cvss = step["cvss_base"]

        if ph == 3:
            for nid,n in self.nodes.items():
                if n.smb_port_open and not n.os_patched and n.is_clean():
                    n.security_status = "SUSPICIOUS"; n.kill_chain_phase = ph; n.cvss_score = cvss
                    self._log(ph,step["stage"],nid,"SMBv1 exploit attempt detected","HIGH",cvss)
            self.ioc_hits.append({"type":"IP","value":random.choice(WANNACRY_IOCS["ips"])["value"],
                "phase":ph,"confidence":91,"description":"SMB scanning source IP","cvss":cvss})

        elif ph == 4:
            for nid,n in self.nodes.items():
                if n.security_status == "SUSPICIOUS":
                    n.security_status = "QUARANTINED"; n.kill_chain_phase = ph; n.cvss_score = cvss
                    self._log(ph,step["stage"],nid,"DoublePulsar backdoor confirmed","CRITICAL",cvss)
            ioc = random.choice(WANNACRY_IOCS["hashes"])
            self.ioc_hits.append({"type":ioc["type"],"value":ioc["value"][:20]+"...","phase":ph,
                "confidence":ioc["confidence"],"description":ioc["description"],"cvss":cvss})

        elif ph == 5:
            for src,dst in TOPOLOGY_EDGES:
                sn,dn = self.nodes.get(src),self.nodes.get(dst)
                if sn and dn and sn.security_status in ["SUSPICIOUS","QUARANTINED"] and dn.is_clean() and dn.smb_port_open:
                    if random.random() > 0.4:
                        dn.security_status = "SUSPICIOUS"; dn.kill_chain_phase = ph; dn.cvss_score = cvss
                        self.infected_edges.add((src,dst))
                        self._log(ph,step["stage"],dst,f"Lateral move from {src} via SMB","HIGH",cvss)
            ioc = random.choice(WANNACRY_IOCS["hashes"])
            self.ioc_hits.append({"type":ioc["type"],"value":ioc["value"][:20]+"...","phase":ph,
                "confidence":ioc["confidence"],"description":ioc["description"],"cvss":cvss})

        elif ph == 6:
            ioc = WANNACRY_IOCS["domains"][0]
            self.ioc_hits.append({"type":"DOMAIN","value":ioc["value"][:45],"phase":ph,
                "confidence":ioc["confidence"],"description":ioc["description"],"cvss":cvss})
            self._log(ph,step["stage"],"NETWORK","Kill-switch DNS lookup via Tor detected","HIGH",cvss)

        elif ph == 7:
            self.ransomware_active = True
            for nid,n in self.nodes.items():
                if n.security_status in ["SUSPICIOUS","QUARANTINED"] and not n.os_patched:
                    n.security_status = "ENCRYPTED"; n.is_compromised = True
                    n.is_connected = False; n.workload_share = 0; n.cvss_score = 10.0
                    if nid not in self.encrypted_nodes: self.encrypted_nodes.append(nid)
                    self._log(ph,step["stage"],nid,"FILES ENCRYPTED — .WNCRY appended","CRITICAL",10.0)
            self.smart_redistribute()
            self.ioc_hits.append({"type":"REG","value":WANNACRY_IOCS["registry_keys"][0]["value"],
                "phase":ph,"confidence":96,"description":"WannaCry registry key found","cvss":10.0})
        else:
            self._log(ph,step["stage"],"NETWORK",step["description"],"MEDIUM",cvss)

        alert = {"message":f"[Phase {ph}/7] {step['stage']}: {step['technique']} ({step['technique_id']}) — {step['description']}",
                 "phase":ph,"stage":step["stage"],"technique_id":step["technique_id"],
                 "color":step["color"],"cvss":cvss,"cvss_vector":step["cvss_vector"]}
        self.soc_alert_queue.append(alert)
        return alert

    def soc_response(self, action, target_node=None):
        self.defender_actions += 1
        h = {"isolate":self._isolate,"patch":self._patch,"scan":self._scan,
             "restore":self._restore,"block_ioc":self._block_iocs}
        return h.get(action, lambda _:{"message":"Unknown action","success":False})(target_node)

    def _isolate(self, nid):
        if nid and nid in self.nodes:
            n = self.nodes[nid]
            n.is_connected=False; n.workload_share=0; n.security_status="QUARANTINED"
            self.smart_redistribute(); self.nodes_saved+=1
            self._log(self.active_kill_chain_phase,"SOC",nid,"Node isolated by analyst","INFO")
            return {"message":f"SOC: {nid} isolated. Workload redistributed.","success":True}
        return {"message":"Node not found.","success":False}

    def _patch(self, nid):
        targets = [nid] if nid and nid in self.nodes else list(self.nodes.keys())
        patched = []
        for tid in targets:
            n = self.nodes[tid]
            if not n.os_patched:
                n.os_patched=True; n.smb_port_open=False; patched.append(tid)
                if n.security_status in ["CLEAN","SUSPICIOUS"]: self.nodes_saved+=1
                self._log(self.active_kill_chain_phase,"SOC",tid,"MS17-010 patch applied","INFO")
        return {"message":f"SOC: Patched {len(patched)} nodes: {', '.join(patched[:3])}{'…' if len(patched)>3 else ''}","success":True}

    def _scan(self, _):
        flagged = [nid for nid,n in self.nodes.items() if n.security_status!="CLEAN"]
        self.ioc_hits.append({"type":"SCAN","value":f"{len(flagged)} anomalous nodes","phase":self.active_kill_chain_phase,"confidence":99,"description":"Active threat scan","cvss":0})
        self._log(self.active_kill_chain_phase,"SOC","NETWORK",f"Threat scan: {len(flagged)} nodes flagged","INFO")
        return {"message":f"SOC: Scan complete — {len(flagged)} flagged: {', '.join(flagged[:3])}","success":True}

    def _restore(self, nid):
        if nid and nid in self.nodes and self.nodes[nid].security_status=="ENCRYPTED":
            n=self.nodes[nid]; n.security_status="CLEAN"; n.is_compromised=False
            n.is_connected=True; n.os_patched=True
            if nid in self.encrypted_nodes: self.encrypted_nodes.remove(nid)
            self.smart_redistribute()
            self._log(self.active_kill_chain_phase,"SOC",nid,"Restored from clean backup","INFO")
            return {"message":f"SOC: {nid} restored from backup.","success":True}
        return {"message":"Node not in ENCRYPTED state.","success":False}

    def _block_iocs(self, _):
        n=len(self.ioc_hits)
        self._log(self.active_kill_chain_phase,"SOC","FW",f"{n} IOCs pushed to blocklist","INFO")
        return {"message":f"SOC: {n} IOCs pushed to firewall. SIEM updated.","success":True}

    def defender_score(self):
        total     = len(self.nodes)
        enc       = len(self.encrypted_nodes)
        clean     = sum(1 for n in self.nodes.values() if n.security_status=="CLEAN")
        patched   = sum(1 for n in self.nodes.values() if n.os_patched)
        s_surv    = round((clean/total)*40)
        s_patch   = round((patched/total)*25)
        s_action  = min(20, self.defender_actions*3)
        s_ioc     = min(15, len([i for i in self.ioc_hits if i["type"]=="SCAN"])*5)
        score     = s_surv+s_patch+s_action+s_ioc
        grade     = "A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
        avg_cvss  = round(sum(i.get("cvss",0) for i in self.ioc_hits)/max(len(self.ioc_hits),1),1)
        return {"total_score":score,"grade":grade,"survival_score":s_surv,"patch_score":s_patch,
                "action_score":s_action,"ioc_block_score":s_ioc,"nodes_encrypted":enc,"nodes_clean":clean,
                "nodes_patched":patched,"defender_actions":self.defender_actions,
                "nodes_saved":self.nodes_saved,"avg_cvss":avg_cvss,"elapsed_seconds":round(self._elapsed())}

    def export_stix(self):
        now = self._ts()
        objs = []
        objs.append({"type":"threat-actor","spec_version":"2.1","id":f"threat-actor--{uuid.uuid4()}",
            "created":now,"modified":now,"name":"Lazarus Group (APT38)",
            "aliases":["Hidden Cobra"],"threat_actor_types":["nation-state"],
            "sophistication":"advanced","resource_level":"government","primary_motivation":"disruption"})
        mal_id = f"malware--{uuid.uuid4()}"
        objs.append({"type":"malware","spec_version":"2.1","id":mal_id,"created":now,"modified":now,
            "name":"WannaCry","malware_types":["ransomware","worm"],"is_family":True,
            "description":"WannaCry using EternalBlue (MS17-010) for worm propagation"})
        for ioc in self.ioc_hits:
            t = ioc["type"]
            if t in ["MD5","SHA256"]:
                pattern = f"[file:hashes.'{t}' = '{ioc['value'].replace('...','')}'  ]"
            elif t == "IP":
                pattern = f"[network-traffic:dst_ref.type = 'ipv4-addr' AND network-traffic:dst_ref.value = '{ioc['value']}']"
            elif t == "DOMAIN":
                pattern = f"[domain-name:value = '{ioc['value'].replace('...','')}'  ]"
            elif t == "REG":
                pattern = f"[windows-registry-key:key = '{ioc['value']}']"
            else:
                continue
            objs.append({"type":"indicator","spec_version":"2.1","id":f"indicator--{uuid.uuid4()}",
                "created":now,"modified":now,"name":f"WannaCry IOC: {t}",
                "description":ioc["description"],"indicator_types":["malicious-activity"],
                "pattern":pattern,"pattern_type":"stix","valid_from":now,"confidence":ioc["confidence"]})
        for step in WANNACRY_KILL_CHAIN[:self.active_kill_chain_phase]:
            objs.append({"type":"attack-pattern","spec_version":"2.1","id":f"attack-pattern--{uuid.uuid4()}",
                "created":now,"modified":now,"name":step["technique"],"description":step["description"],
                "external_references":[{"source_name":"mitre-attack","external_id":step["technique_id"],
                    "url":f"https://attack.mitre.org/techniques/{step['technique_id'].replace('.','/')}"}]})
        return json.dumps({"type":"bundle","id":f"bundle--{uuid.uuid4()}","spec_version":"2.1","objects":objs},indent=2)

    def get_full_status(self):
        self.calculate_metrics()
        connected = [n for n in self.nodes.values() if n.is_connected]
        avg_lat   = sum(n.latency_ms for n in connected)/max(len(connected),1)
        total_wl  = sum(n.workload_share for n in self.nodes.values())
        acc       = max(0,(92.4 if total_wl>=90 else total_wl*0.9)-(avg_lat/40))
        enc       = len(self.encrypted_nodes)
        threat    = ("CRITICAL" if enc>0 else "HIGH" if self.active_kill_chain_phase>=4
                     else "MEDIUM" if self.active_kill_chain_phase>=2
                     else "LOW" if self.active_kill_chain_phase>=1 else "CLEAR")
        edges = [{"src":s,"dst":d,
                  "infected":(s,d) in self.infected_edges or (d,s) in self.infected_edges,
                  "active":bool(self.nodes.get(s) and self.nodes.get(d) and self.nodes[s].is_connected and self.nodes[d].is_connected)}
                 for s,d in TOPOLOGY_EDGES]
        return {
            "accuracy":round(acc,1),"threat_level":threat,
            "kill_chain_phase":self.active_kill_chain_phase,
            "ransomware_active":self.ransomware_active,
            "encrypted_nodes":self.encrypted_nodes,
            "ioc_count":len(self.ioc_hits),
            "recent_iocs":self.ioc_hits[-8:],
            "soc_alerts":self.soc_alert_queue[-5:],
            "mitre_matrix":MITRE_MATRIX,
            "wannacry_ttps":list(WANNACRY_ACTIVE_TTPS),
            "kill_chain_stages":[{"phase":s["phase"],"stage":s["stage"],"technique_id":s["technique_id"],
                "color":s["color"],"cvss":s["cvss_base"],"active":i<self.active_kill_chain_phase}
                for i,s in enumerate(WANNACRY_KILL_CHAIN)],
            "timeline":self.timeline[-40:],
            "topology_edges":edges,
            "defender":self.defender_score(),
            "nodes":{nid:{"node_id":n.node_id,"node_type":n.node_type,"battery":n.battery,
                "is_connected":n.is_connected,"workload_share":n.workload_share,
                "lat":n.lat,"lon":n.lon,"security_status":n.security_status,
                "kill_chain_phase":n.kill_chain_phase,"ttf_minutes":n.ttf_minutes,
                "latency_ms":n.latency_ms,"os_patched":n.os_patched,
                "smb_port_open":n.smb_port_open,"is_compromised":n.is_compromised,
                "cvss_score":n.cvss_score} for nid,n in self.nodes.items()}
        }