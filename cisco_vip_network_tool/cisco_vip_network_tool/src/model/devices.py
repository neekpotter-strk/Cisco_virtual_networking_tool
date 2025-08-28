from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Interface:
    """Represents a L3 or L2 interface on a device."""
    name: str
    ip: Optional[str] = None              # e.g., '10.0.12.1/24'
    mtu: Optional[int] = None
    bandwidth_kbps: Optional[int] = None  # capacity in kbps
    vlan: Optional[int] = None            # access VLAN for L2 ports
    description: Optional[str] = None     # used for link inference

@dataclass
class Device:
    """Base device class."""
    hostname: str
    type: str                              # 'router' or 'switch'
    interfaces: Dict[str, Interface] = field(default_factory=dict)
    routing: Dict[str, Dict] = field(default_factory=dict)     # {'ospf': {...}, 'bgp': {...}}
    vlans: Dict[int, Dict] = field(default_factory=dict)       # {10: {'name': 'Users'}}
    default_gateways: Dict[int, str] = field(default_factory=dict)  # VLAN -> gateway IP/CIDR

@dataclass
class Endpoint:
    """Represents an endpoint/host connected to an access VLAN."""
    name: str
    vlan: int
    ip: str
    gw: str
    app_profile: str                       # e.g., 'HTTP', 'VoIP'
