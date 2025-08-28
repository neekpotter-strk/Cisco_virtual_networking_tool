import os
from cisco_vip_network_tool.src.parsers.cisco_parser import parse_config

def test_parse_hostname_and_interfaces():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'configs', 'sample', 'R1.config.dump')
    text = open(config_path).read()
    dev = parse_config(text)
    assert dev.hostname == 'R1'
    assert 'GigabitEthernet0/0' in dev.interfaces
    assert dev.interfaces['GigabitEthernet0/0'].ip.startswith('10.0.12.1')
