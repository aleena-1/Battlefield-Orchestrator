import random

class DigitalTwin:
    def __init__(self, node_id, node_type, battery=100, lat=17.4065, lon=78.4772):
        self.node_id = node_id
        self.node_type = node_type
        self.battery = float(battery)
        self.is_connected = True
        self.workload_share = 0.0
        self.lat = lat + (random.uniform(-0.02, 0.02))
        self.lon = lon + (random.uniform(-0.02, 0.02))
        self.is_compromised = False
        self.security_status = "CLEAN"  # CLEAN -> SUSPICIOUS -> QUARANTINED
        self.ttf_minutes = 0.0
        self.latency_ms = random.randint(10, 30)

class Orchestrator:
    def __init__(self):
        # Your original core nodes
        self.nodes = {
            "HQ_CLOUD_ALPHA": DigitalTwin("HQ_CLOUD_ALPHA", "Cloud", 100, 17.42, 78.50),
            "MOBILE_EDGE_01": DigitalTwin("MOBILE_EDGE_01", "Tactical_Edge", 88, 17.39, 78.45),
            "MOBILE_EDGE_02": DigitalTwin("MOBILE_EDGE_02", "Tactical_Edge", 42, 17.41, 78.48),
        }
        
        # FEATURE: Drone Swarm (Scaling your Sensor tier)
        for i in range(1, 6):
            u_id = f"UAV_SWARM_{i:02d}"
            self.nodes[u_id] = DigitalTwin(u_id, "Sensor", random.randint(75, 95), 17.40, 78.47)
        
        # Your MITRE CTI Profiles
        self.threat_actors = {
            "DDoS": "T1498 - Network Denial of Service",
            "MitM": "T1557 - Adversary-in-the-Middle",
            "Malware": "T1587 - Malware Injection",
            "Jamming": "Electronic Warfare: Signal Jamming"
        }

    def calculate_metrics(self):
        """Merges your TTF logic with new Latency & Drain features."""
        for node in self.nodes.values():
            if node.is_connected and node.battery > 0:
                # Your DAA Logic: Higher workload = faster battery decay
                consumption_rate = 0.1 + (node.workload_share / 20)
                node.ttf_minutes = round(node.battery / consumption_rate, 1)
                
                # FEATURE: Network Latency Jitter
                node.latency_ms = 15 + int(node.workload_share * 1.2) + random.randint(0, 5)
                
                # FEATURE: Continuous Drain (for real-time simulation)
                if node.workload_share > 0:
                    node.battery = max(0, round(node.battery - (consumption_rate / 10), 2))
            else:
                node.ttf_minutes = 0
                node.latency_ms = 0
            
            if node.battery <= 0:
                node.is_connected = False

    def smart_redistribute(self):
        """Your original DAA Strategy but applied to the full Swarm."""
        self.calculate_metrics()
        cloud = self.nodes["HQ_CLOUD_ALPHA"]
        
        candidates = [n for n in self.nodes.values() 
                      if n.node_type == "Tactical_Edge" 
                      and n.is_connected 
                      and not n.is_compromised]

        if not cloud.is_connected or cloud.is_compromised:
            total_battery_pool = sum(n.battery for n in candidates)
            if total_battery_pool > 0:
                for node in candidates:
                    node.workload_share = (node.battery / total_battery_pool) * 95.0
                return f"DDIL EVENT: AI Sharded across {len(candidates)} secure edges."
            return "CRITICAL: Total Connectivity Loss."
        else:
            for n in self.nodes.values(): n.workload_share = 0
            cloud.workload_share = 100.0
            return "STABLE: HQ Cloud holding Primary Inference."

    def trigger_kill_chain(self):
        """FEATURE: CTI Ransomware Kill-Chain (Phased Attack)."""
        target_id = random.choice(["MOBILE_EDGE_01", "MOBILE_EDGE_02"])
        target = self.nodes[target_id]
        attack = random.choice(list(self.threat_actors.keys()))
        
        if target.security_status == "CLEAN":
            target.security_status = "SUSPICIOUS"
            return f"CTI WARN: Suspicious activity on {target_id}. Monitoring {attack} tactics..."
        else:
            target.security_status = "QUARANTINED"
            target.is_compromised = True
            target.is_connected = False
            target.workload_share = 0
            self.smart_redistribute()
            return f"CTI ALERT: {self.threat_actors[attack]} confirmed on {target_id}. ISOLATED."

    def simulate_failure(self):
        for node in self.nodes.values():
            if node.node_type != "Sensor":
                node.is_connected = random.random() > 0.4
        return self.smart_redistribute()