import pytest
from cisco_vip_network_tool.src.topology.builder import Topology
from cisco_vip_network_tool.src.model.link import Link
from cisco_vip_network_tool.src.simulation.events import inject_link_fault


def test_inject_link_fault():
    # Create a simple topology with one link
    topo = Topology()
    # Add two nodes
    topo.graph.add_node('R1', type='router', device=None)
    topo.graph.add_node('R2', type='router', device=None)
    # Add an edge between R1:Gi0/0 and R2:Gi0/0
    topo.graph.add_edge(('R1', 'Gi0/0'), ('R2', 'Gi0/0'), up=True)
    # Inject fault
    result = inject_link_fault(topo, 'R1-Gi0/0-R2-Gi0/0')
    assert result is True
    assert topo.graph.edges[(('R1', 'Gi0/0'), ('R2', 'Gi0/0'))]['up'] is False

    # Try injecting a non-existent link
    result2 = inject_link_fault(topo, 'R1-Gi0/1-R2-Gi0/1')
    assert result2 is False
