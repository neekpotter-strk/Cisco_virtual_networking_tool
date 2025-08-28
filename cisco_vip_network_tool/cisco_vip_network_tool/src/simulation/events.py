from typing import Dict, Tuple
from cisco_vip_network_tool.src.topology.builder import Topology

def inject_link_fault(topo: Topology, spec: str) -> bool:
    """Turn down a link specified as 'R1-Gi0/0-R2-Gi0/0'. Returns True if found."""
    try:
        a, b, c, d = spec.split('-')
        key1 = ((a, b), (c, d))
        key2 = ((c, d), (a, b))
        if topo.graph.has_edge(*key1):
            topo.graph.edges[key1]['up'] = False
            return True
        if topo.graph.has_edge(*key2):
            topo.graph.edges[key2]['up'] = False
            return True
        return False
    except Exception:
        return False
