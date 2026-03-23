const POLL_INTERVAL = 5000;

function colorForPercent(pct) {
    if (pct >= 85) return 'red';
    if (pct >= 65) return 'yellow';
    return 'green';
}

function formatUptime(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const parts = [];
    if (d > 0) parts.push(`${d}d`);
    if (h > 0) parts.push(`${h}h`);
    parts.push(`${m}m`);
    return parts.join(' ');
}

function setBar(barId, percent) {
    const bar = document.getElementById(barId);
    if (!bar) return;
    bar.style.width = `${Math.min(percent, 100)}%`;
    bar.className = `progress-fill ${colorForPercent(percent)}`;
}

function updateCPU(cpu) {
    document.getElementById('cpu-percent').textContent = `${cpu.percent}%`;
    setBar('cpu-bar', cpu.percent);
    document.getElementById('cpu-cores').textContent =
        `${cpu.physical_cores} physical / ${cpu.core_count} logical`;
    const load = cpu.load_avg.map(v => v.toFixed(2)).join(' / ');
    document.getElementById('cpu-load').textContent = load;
}

function updateMemory(mem) {
    document.getElementById('mem-percent').textContent = `${mem.percent}%`;
    setBar('mem-bar', mem.percent);
    document.getElementById('mem-used').textContent =
        `${mem.used_gb} GB / ${mem.total_gb} GB`;
    document.getElementById('mem-available').textContent = `${mem.available_gb} GB`;
    document.getElementById('mem-swap').textContent =
        mem.swap_total > 0
            ? `${mem.swap_percent}% (${(mem.swap_used / 1024**3).toFixed(1)} GB used)`
            : 'None';
}

function updateDisk(disk) {
    const container = document.getElementById('disk-partitions');
    container.innerHTML = disk.partitions.map(p => `
        <div class="disk-row">
            <div class="disk-label">${p.mountpoint} <span style="color:var(--muted)">(${p.fstype})</span></div>
            <div class="metric-row">
                <span class="metric-label">${p.used_gb} GB / ${p.total_gb} GB</span>
                <span class="metric-value" style="color:${colorForPercent(p.percent) === 'red' ? 'var(--red)' : colorForPercent(p.percent) === 'yellow' ? 'var(--yellow)' : 'var(--text)'}">${p.percent}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill ${colorForPercent(p.percent)}" style="width:${p.percent}%"></div>
            </div>
        </div>
    `).join('');
}

function updateNetwork(network) {
    const container = document.getElementById('network-interfaces');
    container.innerHTML = network.interfaces.map(iface => `
        <div class="net-row">
            <span class="net-iface">${iface.interface}</span>
            <span style="color:var(--muted)">↓ ${iface.recv_mb} MB  ↑ ${iface.sent_mb} MB</span>
        </div>
    `).join('') || '<div style="color:var(--muted)">No interfaces found</div>';
}

function updateStatus(ok) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (ok) {
        dot.className = '';
        text.textContent = 'live';
    } else {
        dot.className = 'error';
        text.textContent = 'error';
    }
}

async function fetchAndUpdate() {
    try {
        const response = await fetch('/api/metrics');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        document.getElementById('hostname').textContent = data.system.hostname;
        document.getElementById('timestamp').textContent = data.timestamp;
        document.getElementById('uptime').textContent =
            `up ${formatUptime(data.system.uptime_seconds)}`;

        updateCPU(data.cpu);
        updateMemory(data.memory);
        updateDisk(data.disk);
        updateNetwork(data.network);
        updateStatus(true);
    } catch (err) {
        console.error('Failed to fetch metrics:', err);
        updateStatus(false);
    }
}

// Initial fetch, then poll
fetchAndUpdate();
setInterval(fetchAndUpdate, POLL_INTERVAL);