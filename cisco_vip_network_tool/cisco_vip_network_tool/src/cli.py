import argparse
import os
import glob
import yaml
from typing import Dict
from cisco_vip_network_tool.src.parsers.cisco_parser import parse_config, extract_link_hints
from cisco_vip_network_tool.src.model.devices import Device, Endpoint
from cisco_vip_network_tool.src.topology.builder import build_from_devices, Topology
from cisco_vip_network_tool.src.validation.validators import config_issues_report
from cisco_vip_network_tool.src.load.load_manager import compute_link_loads, capacity_analysis
from cisco_vip_network_tool.src.simulation.node import run_day1_simulation
from cisco_vip_network_tool.src.simulation.events import inject_link_fault
from cisco_vip_network_tool.src.visualize.plot import draw_topology

def read_device_configs(conf_dir: str) -> Dict[str, Device]:
    """Read *.config.dump files and parse into Device objects keyed by hostname."""
    devices: Dict[str, Device] = {}
    for path in glob.glob(os.path.join(conf_dir, '*.config.dump')):
        text = open(path).read()
        dev = parse_config(text)
        devices[dev.hostname] = dev
    return devices

def load_endpoints(conf_dir: str) -> Dict[str, Endpoint]:
    """Load endpoints.yaml mapping hosts to VLANs and profiles."""
    ep_path = os.path.join(conf_dir, 'endpoints.yaml')
    eps: Dict[str, Endpoint] = {}
    if os.path.exists(ep_path):
        data = yaml.safe_load(open(ep_path))
        for name, spec in data.get('endpoints', {}).items():
            eps[name] = Endpoint(name=name, vlan=int(spec['vlan']), ip=spec['ip'],
                                 gw=spec['gw'], app_profile=spec['app_profile'])
    return eps

def main():
    ap = argparse.ArgumentParser(description='Cisco VIP 2025 – Net Config Validation & Simulation Tool')
    ap.add_argument('--configs', required=True, help='Directory containing *.config.dump and YAML files')
    ap.add_argument('--build-topology', action='store_true')
    ap.add_argument('--validate', action='store_true')
    ap.add_argument('--analyze-load', action='store_true')
    ap.add_argument('--simulate', action='store_true')
    ap.add_argument('--viz', action='store_true')
    ap.add_argument('--inject-fault', default=None, help='e.g., link:R1-Gi0/0-R2-Gi0/0')
    ap.add_argument('--ipc', choices=['inproc', 'tcp'], default='inproc')
    ap.add_argument('--packet-size', type=int, default=1500)
    args = ap.parse_args()

    devices = read_device_configs(args.configs)
    topo = build_from_devices(devices)
    endpoints = load_endpoints(args.configs)

    if args.inject_fault:
        if args.inject_fault.startswith('link:'):
            ok = inject_link_fault(topo, args.inject_fault.split('link:')[1])
            print(f"[fault] link {args.inject_fault} {'DOWN' if ok else 'NOT FOUND'}")

    if args.build_topology:
        print('[topology] built with', topo.graph.number_of_nodes(), 'nodes and', topo.graph.number_of_edges(), 'links')

    if args.validate:
        report = config_issues_report(devices, topo)
        print('[validate] issues report:')
        print(yaml.safe_dump(report, sort_keys=False))

    if args.analyze_load:
        link_loads = compute_link_loads(topo, endpoints, peak=True)
        print('[load] per-link kbps:', link_loads)
        findings = capacity_analysis(topo, link_loads)
        if findings:
            print('[load] recommendations:')
            print(yaml.safe_dump(findings, sort_keys=False))
        else:
            print('[load] no capacity issues detected')

    if args.simulate:
        stats = run_day1_simulation(devices, topo, log_cb=lambda m: print('[sim]', m))
        print('[sim] node stats:', stats)

    if args.viz:
        out = os.path.join('visualizations', 'topology.png')
        os.makedirs('visualizations', exist_ok=True)
        draw_topology(topo, out)
        print('[viz] wrote', out)

if __name__ == '__main__':
    main()
