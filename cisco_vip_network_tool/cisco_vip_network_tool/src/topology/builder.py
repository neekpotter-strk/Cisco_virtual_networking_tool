from typing import Dict, List, Tuple
import networkx as nx
from cisco_vip_network_tool.src.model.devices import Device, Interface, Endpoint
from cisco_vip_network_tool.src.model.link import Link

class Topology:
    """Holds the built topology graph with devices, links, and endpoints."""
    def __init__(self):
        self.graph = nx.Graph()
        self.endpoints: Dict[str, Endpoint] = {}

    def add_device(self, device: Device):
        """Add device node with attributes for visualization."""
        self.graph.add_node(device.hostname, type=device.type, device=device)

    def add_link(self, link: Link):
        """Add an edge with capacity/latency/mtu/up attributes."""
        self.graph.add_edge(
            (link.a_dev, link.a_if),
            (link.b_dev, link.b_if),
            bandwidth_kbps=link.bandwidth_kbps,
            latency_ms=link.latency_ms,
            mtu=link.mtu,
            up=link.up
        )

    def add_endpoint(self, ep: Endpoint):
        """Track endpoint metadata; endpoints connect via VLAN to a switch SVI or access port."""
        self.endpoints[ep.name] = ep

    def neighbors(self, node_key):
        return self.graph.neighbors(node_key)

def build_from_devices(devices: Dict[str, Device]) -> Topology:
    """Construct a topology using link hints from interface descriptions."""
    topo = Topology()
    for dev in devices.values():
        topo.add_device(dev)

    # Build links using description hints
    # When we see 'LINK:R1:Gi0/0-R2:Gi0/0' on either side, create a link.
    added = set()
    for dev in devices.values():
        for ifname, iface in dev.interfaces.items():
            if not iface.description:
                continue
            if 'LINK:' not in iface.description:
                continue
            # Normalize order to avoid duplicate edges
            desc = iface.description
            try:
                tag = desc.split('LINK:')[1]
                left, right = tag.split('-')
                a_dev, a_if = left.split(':')[0], left.split(':')[1]
                b_dev, b_if = right.split(':')[0], right.split(':')[1]
                key = tuple(sorted([(a_dev, a_if), (b_dev, b_if)]))
                if key in added:
                    continue
                # Determine link attributes
                a = devices.get(a_dev).interfaces.get(a_if)
                b = devices.get(b_dev).interfaces.get(b_if)
                mtu = None
                if a and a.mtu and b and b.mtu:
                    mtu = min(a.mtu, b.mtu)
                bw = (a.bandwidth_kbps or 100000) if a else 100000
                link = Link(a_dev=a_dev, a_if=a_if, b_dev=b_dev, b_if=b_if,
                            bandwidth_kbps=bw, mtu=mtu, up=True)
                topo.add_link(link)
                added.add(key)
            except Exception:
                continue

    return topo
