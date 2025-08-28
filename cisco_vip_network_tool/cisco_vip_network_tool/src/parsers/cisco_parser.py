import re
from typing import Dict, List, Tuple
from ipaddress import ip_interface
from cisco_vip_network_tool.src.model.devices import Device, Interface

LINK_TAG = re.compile(r"LINK:([A-Za-z0-9_-]+):([^\s]+)-([A-Za-z0-9_-]+):([^\s]+)")  # LINK:R1:Gi0/0-R2:Gi0/0

def _mask_to_prefix(mask: str) -> int:
    """Convert dotted mask to prefix length."""
    parts = [int(x) for x in mask.split('.')]
    bits = ''.join(f"{p:08b}" for p in parts)
    return bits.count('1')

def parse_config(text: str) -> Device:
    """Parse a Cisco-like config dump into a Device object.
    Supports interfaces (ip, mtu, bandwidth), routing (ospf/bgp), VLANs, and interface descriptions.
    """
    # Hostname
    m = re.search(r"^hostname\s+(\S+)", text, re.M)
    hostname = m.group(1) if m else "UNKNOWN"

    # Type (heuristic: presence of 'router ospf' -> router; otherwise switch unless only VLANs)
    dev_type = "router" if re.search(r"^router\s+(ospf|bgp)", text, re.M) else "switch"

    device = Device(hostname=hostname, type=dev_type)

    # VLANs (simple)
    for vm in re.finditer(r"(?m)^vlan\s+(\d+)(?:\n\s+name\s+(\S+))?", text):
        vid = int(vm.group(1))
        vname = vm.group(2) or f"VLAN{vid}"
        device.vlans[vid] = {"name": vname}

    # Interfaces
    for im in re.finditer(r"(?ms)^interface\s+(\S+)(.+?)(?=^!|^interface|\Z)", text):
        ifname = im.group(1)
        body = im.group(2)
        iface = Interface(name=ifname)

        # description
        dm = re.search(r"\n\s*description\s+(.+)", body)
        if dm:
            iface.description = dm.group(1).strip()

        # ip address (dotted mask) or ip address/prefix style
        ipm = re.search(r"\n\s*ip address\s+(\S+)\s+(\S+)", body)
        if ipm:
            ip = ipm.group(1); mask = ipm.group(2)
            try:
                prefix = _mask_to_prefix(mask)
                iface.ip = f"{ip}/{prefix}"
            except Exception:
                pass
        else:
            ipm2 = re.search(r"\n\s*ip address\s+(\S+)", body)
            if ipm2 and '/' in ipm2.group(1):
                iface.ip = ipm2.group(1)

        # mtu
        mtum = re.search(r"\n\s*mtu\s+(\d+)", body)
        if mtum:
            iface.mtu = int(mtum.group(1))

        # bandwidth
        bwm = re.search(r"\n\s*bandwidth\s+(\d+)", body)
        if bwm:
            iface.bandwidth_kbps = int(bwm.group(1))

        # L2 access VLAN
        vlm = re.search(r"\n\s*switchport access vlan\s+(\d+)", body)
        if vlm:
            iface.vlan = int(vlm.group(1))

        device.interfaces[ifname] = iface

    # Routing protocols (basic)
    for rm in re.finditer(r"(?ms)^router\s+ospf\s+(\d+)(.+?)(?=^!|^router|\Z)", text):
        pid = rm.group(1)
        body = rm.group(2)
        nets = re.findall(r"\n\s*network\s+(\S+)\s+(\S+)\s+area\s+(\S+)", body)
        device.routing.setdefault("ospf", {"process": pid, "networks": []})
        for ip, wildcard, area in nets:
            device.routing["ospf"]["networks"].append({"ip": ip, "wildcard": wildcard, "area": area})

    for rm in re.finditer(r"(?ms)^router\s+bgp\s+(\d+)(.+?)(?=^!|^router|\Z)", text):
        asn = rm.group(1)
        body = rm.group(2)
        neighbors = re.findall(r"\n\s*neighbor\s+(\S+)\s+remote-as\s+(\d+)", body)
        device.routing.setdefault("bgp", {"asn": asn, "neighbors": []})
        for n, nas in neighbors:
            device.routing["bgp"]["neighbors"].append({"neighbor": n, "asn": nas})

    return device

def extract_link_hints(device: Device) -> List[Tuple[str, str, str, str]]:
    """From interface descriptions like
    'LINK:R1:Gi0/0-R2:Gi0/0' return tuples (R1,Gi0/0,R2,Gi0/0).
    """
    hints = []
    for ifname, iface in device.interfaces.items():
        if iface.description:
            m = LINK_TAG.search(iface.description)
            if m:
                a_dev, a_if, b_dev, b_if = m.group(1), m.group(2), m.group(3), m.group(4)
                hints.append((a_dev, a_if, b_dev, b_if))
    return hints
