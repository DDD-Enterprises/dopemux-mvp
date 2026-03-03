import os
import pytest
from dopemux.port_config import get_conport_port, get_conport_url

def test_get_conport_port_default():
    # Clear env vars that might interfere
    if 'DOPEMUX_CONPORT_PORT' in os.environ:
        del os.environ['DOPEMUX_CONPORT_PORT']
    if 'DOPEMUX_PORT_BASE' in os.environ:
        del os.environ['DOPEMUX_PORT_BASE']
        
    assert get_conport_port() == 3004
    assert get_conport_port('A') == 3004

def test_get_conport_port_override():
    os.environ['DOPEMUX_CONPORT_PORT'] = '4004'
    try:
        assert get_conport_port() == 4004
    finally:
        del os.environ['DOPEMUX_CONPORT_PORT']

def test_get_conport_port_multi_instance():
    # Instance B should be port_base(3030) + 4 = 3034
    assert get_conport_port('B') == 3034
    # Instance C should be port_base(3060) + 4 = 3064
    assert get_conport_port('C') == 3064

def test_get_conport_url():
    if 'DOPEMUX_CONPORT_PORT' in os.environ:
        del os.environ['DOPEMUX_CONPORT_PORT']
    assert get_conport_url() == "http://localhost:3004"
    assert get_conport_url('B') == "http://localhost:3034"
