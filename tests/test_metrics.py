from core.metrics import (
    get_cpu_metrics,
    get_memory_metrics,
    get_disk_metrics,
    get_network_metrics,
    get_system_info,
    get_all_metrics,
)


# --- CPU Tests ---

def test_get_cpu_metrics_returns_dict():
    result = get_cpu_metrics()
    assert isinstance(result, dict)


def test_get_cpu_metrics_required_keys():
    result = get_cpu_metrics()
    for key in ["percent", "per_core", "core_count", "physical_cores", "load_avg"]:
        assert key in result, f"Missing key: {key}"


def test_cpu_percent_is_float():
    result = get_cpu_metrics()
    assert isinstance(result["percent"], float)


def test_cpu_percent_in_valid_range():
    result = get_cpu_metrics()
    assert 0.0 <= result["percent"] <= 100.0


def test_cpu_per_core_is_list():
    result = get_cpu_metrics()
    assert isinstance(result["per_core"], list)


def test_cpu_load_avg_has_three_values():
    result = get_cpu_metrics()
    assert len(result["load_avg"]) == 3


# --- Memory Tests ---

def test_get_memory_metrics_returns_dict():
    result = get_memory_metrics()
    assert isinstance(result, dict)


def test_memory_required_keys():
    result = get_memory_metrics()
    for key in ["total", "used", "percent", "total_gb", "used_gb", "available_gb"]:
        assert key in result, f"Missing key: {key}"


def test_memory_percent_in_valid_range():
    result = get_memory_metrics()
    assert 0.0 <= result["percent"] <= 100.0


def test_memory_total_gb_is_positive():
    result = get_memory_metrics()
    assert result["total_gb"] > 0


def test_memory_used_less_than_total():
    result = get_memory_metrics()
    assert result["used"] <= result["total"]


# --- Disk Tests ---

def test_get_disk_metrics_returns_dict():
    result = get_disk_metrics()
    assert isinstance(result, dict)


def test_disk_has_partitions_key():
    result = get_disk_metrics()
    assert "partitions" in result


def test_disk_partitions_is_list():
    result = get_disk_metrics()
    assert isinstance(result["partitions"], list)


def test_disk_partition_has_required_fields():
    result = get_disk_metrics()
    if result["partitions"]:
        partition = result["partitions"][0]
        for key in ["mountpoint", "percent", "total_gb", "used_gb", "free_gb"]:
            assert key in partition, f"Missing key: {key}"


def test_disk_percent_in_valid_range():
    result = get_disk_metrics()
    for partition in result["partitions"]:
        assert 0.0 <= partition["percent"] <= 100.0


# --- Network Tests ---

def test_get_network_metrics_returns_dict():
    result = get_network_metrics()
    assert isinstance(result, dict)


def test_network_has_interfaces_key():
    result = get_network_metrics()
    assert "interfaces" in result


def test_network_interfaces_is_list():
    result = get_network_metrics()
    assert isinstance(result["interfaces"], list)


def test_network_interface_has_required_fields():
    result = get_network_metrics()
    for iface in result["interfaces"]:
        for key in ["interface", "bytes_sent", "bytes_recv", "sent_mb", "recv_mb"]:
            assert key in iface, f"Missing key: {key}"


# --- System Info Tests ---

def test_get_system_info_returns_dict():
    result = get_system_info()
    assert isinstance(result, dict)


def test_system_info_has_hostname():
    result = get_system_info()
    assert "hostname" in result
    assert len(result["hostname"]) > 0


def test_system_info_has_uptime():
    result = get_system_info()
    assert "uptime_seconds" in result
    assert result["uptime_seconds"] > 0


# --- Combined Metrics Tests ---

def test_get_all_metrics_returns_dict():
    result = get_all_metrics()
    assert isinstance(result, dict)


def test_get_all_metrics_has_all_sections():
    result = get_all_metrics()
    for key in ["system", "cpu", "memory", "disk", "network", "timestamp"]:
        assert key in result, f"Missing section: {key}"
