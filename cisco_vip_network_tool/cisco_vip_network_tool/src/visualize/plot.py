from typing import Dict, Tuple
import os
import matplotlib.pyplot as plt
import networkx as nx
from cisco_vip_network_tool.src.topology.builder import Topology

def draw_topology(topo: Topology, out_path: str):
    """Draw a simple spring-layout topology to a PNG file."""
    G = nx.Graph()
    labels = {}
    for (u, v, data) in topo.graph.edges(data=True):
        G.add_edge(u, v)
    pos = nx.spring_layout(G, seed=42)
    plt.figure()
    nx.draw(G, pos, with_labels=True)
    plt.title('Network Topology')
    plt.savefig(out_path, dpi=160, bbox_inches='tight')
    plt.close()
