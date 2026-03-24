import os
import yaml
from pathlib import Path
from typing import Optional

HOSTS_CONFIG = Path(os.getenv("HOSTS_CONFIG", "hosts.yaml"))


def load_hosts() -> list[dict]:
    """Read hosts from YAML. Returns [] if file does not exist."""
    if not HOSTS_CONFIG.exists():
        return []
    with open(HOSTS_CONFIG) as f:
        data = yaml.safe_load(f) or {}
    return data.get("hosts", [])


def save_hosts(hosts: list[dict]) -> None:
    """Persist hosts list to YAML. Writes to a temp file first so a crash
    during serialization never corrupts the live file, then copies into the
    bind-mounted target (os.replace fails on Docker bind mounts)."""
    HOSTS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    tmp = HOSTS_CONFIG.with_suffix(".tmp")
    with open(tmp, "w") as f:
        yaml.dump({"hosts": hosts}, f, default_flow_style=False)
    with open(HOSTS_CONFIG, "w") as f:
        f.write(tmp.read_text())


def get_host(host_id: str) -> Optional[dict]:
    return next((h for h in load_hosts() if h["id"] == host_id), None)


def add_host(host: dict) -> None:
    hosts = load_hosts()
    if any(h["id"] == host["id"] for h in hosts):
        raise ValueError(f"Host id '{host['id']}' already exists")
    hosts.append(host)
    save_hosts(hosts)


def remove_host(host_id: str) -> bool:
    hosts = load_hosts()
    new_hosts = [h for h in hosts if h["id"] != host_id]
    if len(new_hosts) == len(hosts):
        return False  # not found
    save_hosts(new_hosts)
    return True
