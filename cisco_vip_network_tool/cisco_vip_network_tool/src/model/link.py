from dataclasses import dataclass
from typing import Optional

@dataclass
class Link:
    """Represents a link between two device interfaces."""
    a_dev: str
    a_if: str
    b_dev: str
    b_if: str
    bandwidth_kbps: int = 100000
    latency_ms: float = 1.0
    mtu: Optional[int] = None
    up: bool = True  # used for fault injection
