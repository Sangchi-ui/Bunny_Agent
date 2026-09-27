import pytest
from unittest.mock import patch
from app.tools import system_monitor

def test_get_cpu_usage():
    result = system_monitor.get_cpu_usage()
    assert "success" in result
    assert "data" in result
    assert "error" in result
    assert result["success"] is True
    assert "overall_percent" in result["data"]
    assert "per_core_percent" in result["data"]

def test_get_ram_usage():
    result = system_monitor.get_ram_usage()
    assert result["success"] is True
    assert "total" in result["data"]
    assert "percent" in result["data"]

def test_get_disk_usage():
    result = system_monitor.get_disk_usage()
    assert result["success"] is True
    assert "total" in result["data"]
    assert "percent" in result["data"]

import sys
from unittest.mock import MagicMock

def test_get_gpu_usage_mock_gputil():
    # Mocking GPUtil to return an empty list (no GPU) via sys.modules
    mock_gputil = MagicMock()
    mock_gputil.getGPUs.return_value = []
    
    with patch.dict(sys.modules, {'GPUtil': mock_gputil}):
        result = system_monitor.get_gpu_usage()
        assert result["success"] is True
        assert result["data"]["available"] is False
        assert "No GPU found" in result["data"]["message"]

@patch("app.tools.system_monitor.psutil.cpu_percent")
def test_get_cpu_usage_exception(mock_cpu):
    # Test fallback exception handling
    mock_cpu.side_effect = Exception("Mock psutil failure")
    result = system_monitor.get_cpu_usage()
    assert result["success"] is False
    assert result["data"] is None
    assert "Mock psutil failure" in result["error"]

def test_get_top_processes():
    result = system_monitor.get_top_processes(n=2)
    assert result["success"] is True
    assert "top_by_memory" in result["data"]
    assert "top_by_cpu" in result["data"]
    assert len(result["data"]["top_by_memory"]) <= 2

def test_get_network_status():
    result = system_monitor.get_network_status()
    assert result["success"] is True
    assert "network_up" in result["data"]
