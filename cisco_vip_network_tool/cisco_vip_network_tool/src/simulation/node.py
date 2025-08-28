import threading
import queue
import time
import json
from typing import Dict, List, Tuple, Optional
from cisco_vip_network_tool.src.model.devices import Device
from cisco_vip_network_tool.src.topology.builder import Topology

class InProcBroker:
    """Simple in-process broker routing messages by (device,iface) tuple keys."""
    def __init__(self):
        self.queues: Dict[Tuple[str,str], queue.Queue] = {}

    def register(self, key: Tuple[str,str]):
        self.queues[key] = queue.Queue()

    def send(self, dst: Tuple[str,str], msg: Dict):
        if dst in self.queues:
            self.queues[dst].put(msg)

    def recv(self, key: Tuple[str,str], timeout: float = 0.1) -> Optional[Dict]:
        q = self.queues.get(key)
        if not q:
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

class NodeThread(threading.Thread):
    """Represents a router/switch thread that exchanges metadata 'packets' via broker."""
    def __init__(self, device: Device, topo: Topology, broker: InProcBroker, log_cb=None):
        super().__init__(daemon=True)
        self.device = device
        self.topo = topo
        self.broker = broker
        self.log_cb = log_cb or (lambda x: None)
        self.running = True
        self.stats = {'sent': 0, 'recv': 0, 'dropped': 0}

        # Register all interfaces as queue endpoints
        for ifn in self.device.interfaces:
            self.broker.register((self.device.hostname, ifn))

    def log(self, msg: str):
        self.log_cb(f"[{self.device.hostname}] {msg}")

    def run(self):
        """Main event loop: process incoming messages and perform periodic discovery."""
        t0 = time.time()
        hello_interval = 1.0
        last_hello = 0.0
        while self.running:
            now = time.time()
            # Periodic neighbor discovery (hello)
            if now - last_hello >= hello_interval:
                self._send_hello()
                last_hello = now
            # Process inbound messages on each interface
            for ifn in self.device.interfaces:
                msg = self.broker.recv((self.device.hostname, ifn), timeout=0.01)
                if msg:
                    self._handle(msg, ifn)
            # Exit after short demo window
            if now - t0 > 5.0:  # 5 seconds demo
                self.running = False
            time.sleep(0.01)

    def _send_hello(self):
        """Broadcast simple HELLO to all neighbors over up links."""
        for (u, v, data) in list(self.topo.graph.edges(data=True)):
            if not data.get('up', True):
                continue
            # Edge stored as ((dev,if),(dev,if))
            for src, dst in [(u, v), (v, u)]:
                if src[0] == self.device.hostname:
                    msg = {'type': 'HELLO', 'from': {'dev': src[0], 'if': src[1]}}
                    self.broker.send(dst, msg)
                    self.stats['sent'] += 1

    def _handle(self, msg: Dict, ifn: str):
        """Basic handler: respond to HELLO with HELLO-ACK."""
        self.stats['recv'] += 1
        if msg.get('type') == 'HELLO':
            src = msg['from']
            # MTU check demo: if packet size exceeds MTU, drop
            edge = ((src['dev'], src['if']), (self.device.hostname, ifn))
            data = self.topo.graph.edges.get(edge) or self.topo.graph.edges.get((edge[1], edge[0]))
            if data and data.get('mtu') and 1500 > data['mtu']:
                self.stats['dropped'] += 1
                self.log(f"Dropped HELLO from {src['dev']}:{src['if']} due to MTU {data['mtu']}")
                return
            # Send ACK back
            ack = {'type': 'HELLO-ACK', 'from': {'dev': self.device.hostname, 'if': ifn}}
            self.broker.send((src['dev'], src['if']), ack)
            self.stats['sent'] += 1
        elif msg.get('type') == 'HELLO-ACK':
            pass  # could update adjacency table

def run_day1_simulation(devices: Dict[str, Device], topo: Topology, log_cb=None) -> Dict[str, Dict]:
    """Spin up a NodeThread per device and run periodic hello/ack exchange for a short window."""
    broker = InProcBroker()
    threads = []
    for dev in devices.values():
        t = NodeThread(dev, topo, broker, log_cb=log_cb)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    # Collect stats
    return {t.device.hostname: t.stats for t in threads}
