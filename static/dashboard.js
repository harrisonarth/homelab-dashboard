let activeTab = 'all';
let hosts = [];

// ── Bootstrap ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await loadHosts();
    renderTabBar();
    switchTab('all');
    startPolling();
});

// ── Host list ────────────────────────────────────────────
async function loadHosts() {
    const res = await fetch('/api/hosts');
    hosts = await res.json();
}

// ── Tab bar ──────────────────────────────────────────────
function renderTabBar() {
    const bar = document.getElementById('tab-bar');
    bar.innerHTML = '';

    bar.appendChild(makeTab('all', 'All'));

    hosts.forEach(h => {
        bar.appendChild(makeTab(h.id, h.name));
    });
}

function makeTab(id, label) {
    const t = document.createElement('div');
    t.className = 'tab';
    t.dataset.id = id;
    t.textContent = label;
    t.addEventListener('click', () => switchTab(id));
    return t;
}

function switchTab(id) {
    activeTab = id;

    document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.id === id);
    });

    document.getElementById('view-all').classList.toggle('hidden', id !== 'all');
    document.getElementById('view-host').classList.toggle('hidden', id === 'all');

    // Fetch immediately on switch — don't wait for next poll cycle
    poll();
}

// ── Polling ──────────────────────────────────────────────
function startPolling() {
    setInterval(poll, 5000);
}

async function poll() {
    if (activeTab === 'all') {
        await pollAll();
    } else {
        await pollHost(activeTab);
    }
}

// ── All view ─────────────────────────────────────────────
async function pollAll() {
    const res = await fetch('/api/all-metrics');
    const data = await res.json();
    renderHostGrid(Object.values(data));

    // Keep header clock updated using local host metrics
    const local = data['local'];
    if (local && !local.error) {
        document.getElementById('timestamp').textContent = local.metrics.timestamp;
        document.getElementById('uptime').textContent =
            `up ${formatUptime(local.metrics.system.uptime_seconds)}`;
        updateStatus(true);
    }
}

function renderHostGrid(results) {
    const grid = document.getElementById('host-grid');
    grid.innerHTML = `
        <table class="host-table">
            <colgroup>
                <col class="col-status">
                <col class="col-name">
                <col class="col-metric">
                <col class="col-metric">
                <col class="col-metric">
            </colgroup>
            <thead>
                <tr>
                    <th class="col-left"></th>
                    <th class="col-left">Host</th>
                    <th class="col-right">CPU</th>
                    <th class="col-right">MEM</th>
                    <th class="col-right">DISK</th>
                </tr>
            </thead>
            <tbody id="host-table-body"></tbody>
        </table>
    `;
    const tbody = document.getElementById('host-table-body');
    results.forEach(r => {
        const row = makeHostRow(r);
        row.addEventListener('click', () => switchTab(r.host_id));
        tbody.appendChild(row);
    });
}

function makeHostRow(result) {
    const row = document.createElement('tr');

    if (result.error) {
        row.innerHTML = `
            <td class="col-left"><span class="offline-badge"></span></td>
            <td class="col-left col-name">${result.host_name}</td>
            <td class="col-right col-error" colspan="3">${result.error}</td>
        `;
        return row;
    }

    const m = result.metrics;
    const rootDisk = m.disk?.partitions?.find(p => p.mountpoint === '/') ?? m.disk?.partitions?.[0];

    row.innerHTML = `
        <td class="col-left"><span class="online-badge"></span></td>
        <td class="col-left col-name">${result.host_name}</td>
        <td class="col-right">${m.cpu.percent.toFixed(1)}%</td>
        <td class="col-right">${m.memory.percent.toFixed(1)}%</td>
        <td class="col-right">${rootDisk ? rootDisk.percent.toFixed(1) + '%' : 'n/a'}</td>
    `;
    return row;
}

// ── Host detail view ─────────────────────────────────────
async function pollHost(hostId) {
    const res = await fetch(`/api/hosts/${hostId}/metrics`);
    const data = await res.json();

    const header = document.getElementById('host-detail-header');
    if (data.error) {
        header.innerHTML = `<span class="offline-badge"></span> ${data.host_name} — <span class="offline">${data.error}</span>`;
        updateStatus(false);
        return;
    }

    header.innerHTML = `<span class="online-badge"></span> ${data.host_name}`;
    updateDashboard(data.metrics);
}

// ── Render functions (unchanged) ─────────────────────────
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
    document.getElementById('cpu-percent').textContent = `${cpu.percent.toFixed(2)}%`;
    setBar('cpu-bar', cpu.percent);
    document.getElementById('cpu-cores').textContent =
        `${cpu.physical_cores} physical / ${cpu.core_count} logical`;
    const load = cpu.load_avg.map(v => v.toFixed(2)).join(' / ');
    document.getElementById('cpu-load').textContent = load;
}

function updateMemory(mem) {
    document.getElementById('mem-percent').textContent = `${mem.percent.toFixed(2)}%`;
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
                <span class="metric-value" style="color:${colorForPercent(p.percent) === 'red' ? 'var(--red)' : colorForPercent(p.percent) === 'yellow' ? 'var(--yellow)' : 'var(--text)'}">${p.percent.toFixed(2)}%</span>
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
            <span class="net-stats">↓ ${iface.recv_mb} MB  ↑ ${iface.sent_mb} MB</span>
        </div>
    `).join('') || '<div style="color:var(--muted)">No interfaces found</div>';
}

function updateStatus(ok) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (ok) {
        dot.className = '';
        text.textContent = 'online';
    } else {
        dot.className = 'error';
        text.textContent = 'error';
    }
}

function updateDashboard(metrics) {
    document.getElementById('timestamp').textContent = metrics.timestamp;
    document.getElementById('uptime').textContent =
        `up ${formatUptime(metrics.system.uptime_seconds)}`;

    updateCPU(metrics.cpu);
    updateMemory(metrics.memory);
    updateDisk(metrics.disk);
    updateNetwork(metrics.network);
    updateStatus(true);
}
