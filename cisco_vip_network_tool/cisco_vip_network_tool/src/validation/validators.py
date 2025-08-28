from typing import Dict, List, Tuple, Set
from ipaddress import ip_interface, ip_network
import networkx as nx
from cisco_vip_network_tool.src.model.devices import Device
from cisco_vip_network_tool.src.topology.builder import Topology
from cisco_vip_network_tool.src.parsers.cisco_parser import parse_config, extract_link_hints

def find_duplicate_ips(devices: Dict[str, Device]) -> List[Tuple[str, str, str]]:
    """Return list of (ip, dev, iface) duplicates within the same / subnet."""
    ip_map = {}
    dups = []
    for dev in devices.values():
        for ifn, iface in dev.interfaces.items():
            if iface.ip:
                ipi = ip_interface(iface.ip)
                key = (str(ipi.ip), str(ipi.network))
                if key in ip_map:
                    dups.append((str(ipi.ip), ip_map[key], f"{dev.hostname}:{ifn}"))
                else:
                    ip_map[key] = f"{dev.hostname}:{ifn}"
    return dups

def check_vlan_labels(devices: Dict[str, Device]) -> List[str]:
    """Warn if an interface references an undefined VLAN."""
    issues = []
    for dev in devices.values():
        for ifn, iface in dev.interfaces.items():
            if iface.vlan is not None and iface.vlan not in dev.vlans:
                issues.append(f"{dev.hostname}:{ifn} references VLAN {iface.vlan} which is undefined on this device")
    return issues

def check_wrong_gateways(devices: Dict[str, Device]) -> List[str]:
    """For SVIs (e.g., VlanX with IP), ensure default gateway (if set) belongs to that VLAN subnet."""
    issues = []
    # Heuristic: devices.default_gateways maps VLAN->gw
    for dev in devices.values():
        for vlan, gw in dev.default_gateways.items():
            # find SVI interface ip for vlan
            svi_ip = None
            for ifn, iface in dev.interfaces.items():
                if ifn.lower().startswith('vlan') and iface.ip:
                    try:
                        vid = int(ifn.lower().replace('vlan', ''))
                        if vid == vlan:
                            svi_ip = iface.ip
                    except Exception:
                        pass
            if not svi_ip:
                issues.append(f"{dev.hostname} sets default-gw for VLAN {vlan} but has no SVI")
                continue
            try:
                net = ip_interface(svi_ip).network
                if ip_interface(gw).ip not in net:
                    issues.append(f"{dev.hostname} gateway {gw} not in VLAN{vlan} subnet {net}")
            except Exception:
                issues.append(f"{dev.hostname} invalid gateway format {gw}")
    return issues

def check_mtu_mismatches(topo: Topology) -> List[str]:
    """Detect links whose endpoint interface MTUs do not match."""
    issues = []
    for (a, b, data) in topo.graph.edges(data=True):
        mtu = data.get('mtu')
        if mtu is None:
            continue
        # Retrieve actual interface MTUs from node objects
        a_dev, a_if = a
        b_dev, b_if = b
        da = topo.graph.nodes[a_dev]['device']
        db = topo.graph.nodes[b_dev]['device']
        ia = da.interfaces.get(a_if).mtu
        ib = db.interfaces.get(b_if).mtu
        if ia and ib and ia != ib:
            issues.append(f"MTU mismatch {a_dev}:{a_if}({ia}) <-> {b_dev}:{b_if}({ib})")
    return issues

def detect_layer2_loops(topo: Topology) -> List[List[str]]:
    """Detect cycles as potential L2 loops. Returns list of cycles (nodes)."""
    try:
        cycles = list(nx.cycle_basis(topo.graph))
        return [[f"{n[0]}:{n[1]}" for n in cycle] for cycle in cycles]
    except Exception:
        return []

def config_issues_report(devices: Dict[str, Device], topo: Topology) -> Dict:
    """Aggregate all checks into a structured report."""
    return {
        'duplicate_ips': find_duplicate_ips(devices),
        'vlan_label_issues': check_vlan_labels(devices),
        'gateway_issues': check_wrong_gateways(devices),
        'mtu_mismatches': check_mtu_mismatches(topo),
        'l2_loops': detect_layer2_loops(topo),
    }
