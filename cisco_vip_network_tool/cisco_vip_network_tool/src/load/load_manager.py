from typing import Dict, List, Tuple
from collections import defaultdict
import networkx as nx
from cisco_vip_network_tool.src.model.devices import Device, Endpoint
from cisco_vip_network_tool.src.topology.builder import Topology

# Default per-app kbps (regular, peak)
APP_DEFAULTS = {
    'HTTP': (500, 1500),
    'VoIP': (100, 200),
    'Video': (2000, 5000),
    'DB': (1000, 3000),
}

def compute_link_loads(topo: Topology, endpoints: Dict[str, Endpoint], peak: bool = False) -> Dict:
    """Compute aggregate kbps per link using shortest paths between endpoints and their gateways.

    This is a simplified traffic model.

    Returns mapping: edge_key -> load_kbps.

    """
    # Build helper index from device names to their VLAN SVIs for gateway mapping
    vlan_gw = {}
    for dev, data in topo.graph.nodes(data=True):
        d = data.get('device')
        if not d:
            continue
        for ifn, iface in d.interfaces.items():
            if ifn.lower().startswith('vlan') and iface.ip:
                try:
                    vlan = int(ifn.lower().replace('vlan', ''))
                    vlan_gw[(dev, vlan)] = (dev, ifn)
                except Exception:
                    pass

    # Aggregate loads
    loads = defaultdict(int)
    for ep in endpoints.values():
        rate = APP_DEFAULTS.get(ep.app_profile, (500, 1500))[1 if peak else 0]
        # Find the gateway node for the VLAN
        gw_key = None
        for (dev, vlan), ifkey in vlan_gw.items():
            if vlan == ep.vlan:
                gw_key = ifkey  # (dev, ifn)
                break
        if not gw_key:
            continue
        # Path from 'host' to gateway is modeled as a single hop edge (host -> switch:VlanX)
        # For backbone traffic between gateways, we route using graph shortest path
        # Here we just add load on edges that are on path from gateway's device to others if needed.
        # Simplification: traffic terminates at gateway (northbound traffic not modeled here).
        # Add load on access edge (ep -> gw)
        loads[(f"HOST:{ep.name}", f"{gw_key[0]}:{gw_key[1]}")] += rate

    return dict(loads)

def capacity_analysis(topo: Topology, link_loads: Dict) -> List[Dict]:
    """Compare loads vs link bandwidth and recommend alternatives (k-shortest paths placeholder)."""
    findings = []
    for (u, v), load in link_loads.items():
        # Backbone link keys in topo use ((dev,if),(dev,if)) – here we also have host edges.
        if isinstance(u, tuple) and isinstance(v, tuple) and topo.graph.has_edge(u, v):
            cap = topo.graph.edges[u, v].get('bandwidth_kbps', 100000)
            if load > cap:
                findings.append({
                    'edge': (u, v),
                    'load_kbps': load, 'capacity_kbps': cap,
                    'recommendation': 'Enable secondary path or QoS to reclassify lower-priority traffic.'
                })
        else:
            # Host access edge capacity assumed high; skip
            pass
    return findings
