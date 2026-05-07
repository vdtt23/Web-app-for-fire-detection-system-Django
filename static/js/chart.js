const DPR = window.devicePixelRatio || 1;

const COLORS = {
    temp: {
        line: '#0ea5e9',
        fill: 'rgba(14, 165, 233, 0.12)'
    },
    smoke: {
        line: '#f43f5e',
        fill: 'rgba(244, 63, 94, 0.12)'
    },
    humidity: {
        line: '#f59e0b',
        fill: 'rgba(245, 158, 11, 0.14)'
    }
};

const charts = {};  // node_id -> Chart instance

function makeDataset(label, color, fillColor) {
    return {
        label,
        data: [],
        borderColor: color,
        backgroundColor: fillColor,
        borderWidth: 2.5,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: color,
        fill: true,
        tension: 0.35,
        cubicInterpolationMode: 'monotone',
        borderCapStyle: 'round',
        borderJoinStyle: 'round'
    };
}

function createNodeChart(nodeId) {
    const grid = document.getElementById('node-charts-grid');
    if (!grid) return;

    const card = document.createElement('div');
    card.className = 'card chart-card node-chart-card';
    card.id = `card-node-${nodeId}`;
    card.innerHTML = `
        <div class="node-chart-header">
            <span class="node-chart-title">Node ${nodeId}</span>
            <span class="node-chart-badge" id="badge-node-${nodeId}">--</span>
        </div>
        <div class="node-chart-wrap">
            <canvas id="chart-node-${nodeId}"></canvas>
        </div>
    `;
    grid.appendChild(card);

    const ctx = document.getElementById(`chart-node-${nodeId}`);
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                makeDataset('Temp (C)', COLORS.temp.line, COLORS.temp.fill),
                makeDataset('Smoke', COLORS.smoke.line, COLORS.smoke.fill),
                makeDataset('Humidity (%)', COLORS.humidity.line, COLORS.humidity.fill),
            ]
        },
        options: {
            devicePixelRatio: DPR,
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'line',
                        padding: 14,
                        font: { size: 12, weight: '600' },
                        color: '#334155'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    padding: 10,
                    displayColors: true,
                    callbacks: {
                        label(context) {
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.16)' },
                    ticks: { autoSkip: true, maxTicksLimit: 6, maxRotation: 0, color: '#64748b', font: { size: 11 } }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(148, 163, 184, 0.2)' },
                    ticks: { stepSize: 20, color: '#64748b', font: { size: 11 } }
                }
            }
        }
    });

    charts[nodeId] = chart;
}

async function updateNodeChart(nodeId) {
    try {
        const res = await fetch(`/api/chart/${nodeId}/`);
        const data = await res.json();
        const chart = charts[nodeId];
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.temp;
        chart.data.datasets[1].data = data.smoke;
        chart.data.datasets[2].data = data.humidity;
        chart.update('none');
    } catch (e) {}
}

async function updateAllCharts() {
    try {
        const res = await fetch('/api/nodes/');
        const nodes = await res.json();

        // Sort nodes by node_id ascending
        nodes.sort((a, b) => a.node_id - b.node_id);

        const grid = document.getElementById('node-charts-grid');

        for (const node of nodes) {
            const nodeId = node.node_id;
            if (!charts[nodeId]) {
                createNodeChart(nodeId);
            }
            const badge = document.getElementById(`badge-node-${nodeId}`);
            if (badge) {
                badge.textContent = node.status;
                badge.className = `node-chart-badge status-${node.status.toLowerCase()}`;
            }
        }

        // Re-order cards in the DOM to match sorted node_id order
        if (grid) {
            nodes.forEach(node => {
                const card = document.getElementById(`card-node-${node.node_id}`);
                if (card) grid.appendChild(card);
            });
        }

        for (const nodeId of Object.keys(charts).map(Number).sort((a, b) => a - b)) {
            await updateNodeChart(nodeId);
        }
    } catch (e) {}
}

function scheduleResize() {
    requestAnimationFrame(() => {
        for (const chart of Object.values(charts)) {
            chart.options.devicePixelRatio = window.devicePixelRatio || 1;
            chart.resize();
            chart.update('none');
        }
    });
}

const sidebar = document.querySelector('.sidebar');
if (sidebar) {
    sidebar.addEventListener('transitionend', scheduleResize);
    sidebar.addEventListener('mouseenter', scheduleResize);
    sidebar.addEventListener('mouseleave', scheduleResize);
}

window.addEventListener('resize', scheduleResize);

updateAllCharts();
setInterval(updateAllCharts, 2000);
