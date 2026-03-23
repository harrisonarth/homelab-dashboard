import psutil
from datetime import datetime

def get_cpu_metrics(): 
    """
    Return CPU usage metrics.
    """
    return {
        "percent": psutil.cpu_percent(interval=0.5),
        "per_core": psutil.cpu_percent(interval=0.5, percpu=True),
        "core_count": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "load_avg": list(psutil.getloadavg()),
    }

def get_memory_metrics(): 
    """
    Return RAM usage metrics.
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent,
    }

def get_disk_metrics():
    """
    Return disk usage for all mounted partitions.
    Skips pseudo-filesystems like tmpfs, devtmpfs.
    """
    real_fs_types = {'ext4', 'ext3', 'xfs', 'btrfs', 'zfs', 'ntfs', 'vfat', 'fuseblk'}
    partitions = []

    for part in psutil.disk_partitions():
        if part.fstype not in real_fs_types:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
            })
        except PermissionError:
            continue  # some mounts aren't readable
    
    # Disk I/O counters
    io = psutil.disk_io_counters()
    if io:
        disk_io = {
            "read_bytes": io.read_bytes,
            "write_bytes": io.write_bytes,
            "read_count": io.read_count,
            "write_count": io.write_count,
        }

    return {
        "partitions": partitions,
        "io": disk_io,
    }

def get_network_metrics():
    """
    Return network I/O stats per interface.
    Skips loopback.
    """
    net_io = psutil.net_io_counters(pernic=True)
    interfaces = []

    for iface, stats in net_io.items():
        if iface == 'lo':
            continue
        interfaces.append({
            "interface": iface,
            "bytes_sent": stats.bytes_sent,
            "bytes_recv": stats.bytes_recv,
            "packets_sent": stats.packets_sent,
            "packets_recv": stats.packets_recv,
            "sent_mb": round(stats.bytes_sent / (1024 ** 2), 2),
            "recv_mb": round(stats.bytes_recv / (1024 ** 2), 2),
        })

    return {"interfaces": interfaces}

def get_system_info():
    """
    Return static system information.
    """
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    return {
        "hostname": __import__('socket').gethostname(),
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": int(
            (datetime.now() - boot_time).total_seconds()
        ),
    }

def get_all_metrics():
    """
    Collect all host metrics in a single call.
    Returns a dict suitable for JSON serialization.
    """
    return {
        "system": get_system_info(),
        "cpu": get_cpu_metrics(),
        "memory": get_memory_metrics(),
        "disk": get_disk_metrics(),
        "network": get_network_metrics(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }