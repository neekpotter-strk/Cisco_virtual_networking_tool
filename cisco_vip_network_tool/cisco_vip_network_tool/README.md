# Cisco VIP 2025 – Networking Config Validation & Simulation Tool (MVP)

Production-ready, modular Python MVP to parse router/switch configs, build a topology,
validate configuration, analyze load, and simulate Day‑1 events + faults (link‑down, MTU).

## Folder Structure
```
cisco_vip_network_tool/
├── configs/
│   └── sample/
│       ├── endpoints.yaml
│       ├── traffic_profiles.yaml
│       ├── R1.config.dump
│       ├── R2.config.dump
│       └── SW1.config.dump
├── logs/
├── src/
│   ├── cli.py
│   ├── model/
│   │   ├── __init__.py
│   │   ├── devices.py
│   │   └── link.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── cisco_parser.py
│   ├── topology/
│   │   ├── __init__.py
│   │   └── builder.py
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validators.py
│   ├── load/
│   │   ├── __init__.py
│   │   └── load_manager.py
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── node.py
│   │   └── events.py
│   └── visualize/
│       ├── __init__.py
│       └── plot.py
├── tests/
│   ├── __init__.py
│   └── test_parser.py
├── visualizations/
├── requirements.txt
├── run.sh
└── README.md
```

## Quick Start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline on sample configs
export PYTHONPATH=./src:$PYTHONPATH
python3 src/cli.py --configs ./configs/sample --build-topology --validate --analyze-load --simulate --viz

# Or use the helper
./run.sh
```

## Quick Start (Windows PowerShell)
```powershell
python -m venv .venv
[Activate.ps1](http://_vscodecontentref_/0)
pip install -r requirements.txt

# Run the full pipeline on sample configs
$env:PYTHONPATH = ".\\src"
python [cli.py](http://_vscodecontentref_/1) --configs .\\configs\\sample --build-topology --validate --analyze-load --simulate --viz

# Or use the helper
./run.sh
```

## CLI Usage
```
python3 src/cli.py --configs <dir> [--build-topology] [--validate] [--analyze-load] [--simulate] [--viz]
                   [--inject-fault link:R1-Gi0/0-R2-Gi0/0] [--ipc inproc|tcp] [--packet-size 1500]
```

## Notes
- IPC is implemented **in-process** by default for portability; TCP mode scaffolding is included.
- Graph visualization uses matplotlib; Graphviz DOT export is also provided.
- Scapy hooks are included as optional (disabled by default) for real packet crafting.

## Future C++ High-Performance Plan (Optional)
- Reimplement `simulation.node` and `simulation.events` in C++ with `asio` for TCP IPC,
  and `spdlog` for logging. Bind to Python via `pybind11` to keep the existing Python CLI.
