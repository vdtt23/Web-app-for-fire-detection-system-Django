const ctx = document.getElementById('sensorChart');
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

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Temp',
                data: [],
                borderColor: COLORS.temp.line,
                backgroundColor: COLORS.temp.fill,
                borderWidth: 3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: COLORS.temp.line,
                fill: true,
                tension: 0.35,
                cubicInterpolationMode: 'monotone',
                borderCapStyle: 'round',
                borderJoinStyle: 'round'
            },
            {
                label: 'Smoke',
                data: [],
                borderColor: COLORS.smoke.line,
                backgroundColor: COLORS.smoke.fill,
                borderWidth: 3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: COLORS.smoke.line,
                fill: true,
                tension: 0.35,
                cubicInterpolationMode: 'monotone',
                borderCapStyle: 'round',
                borderJoinStyle: 'round'
            },
            {
                label: 'Humidity',
                data: [],
                borderColor: COLORS.humidity.line,
                backgroundColor: COLORS.humidity.fill,
                borderWidth: 3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: COLORS.humidity.line,
                fill: true,
                tension: 0.35,
                cubicInterpolationMode: 'monotone',
                borderCapStyle: 'round',
                borderJoinStyle: 'round'
            }
        ]
    },
    options: {
        devicePixelRatio: DPR,
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: {
            mode: 'index',
            intersect: false
        },
        elements: {
            line: {
                capBezierPoints: true
            }
        },
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'line',
                    padding: 16,
                    font: {
                        size: 14,
                        weight: '600'
                    },
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
                grid: {
                    color: 'rgba(148, 163, 184, 0.16)'
                },
                ticks: {
                    autoSkip: true,
                    maxTicksLimit: 8,
                    maxRotation: 0,
                    color: '#64748b',
                    font: {
                        size: 12
                    }
                }
            },
            y: {
                min: 0,
                max: 100,
                grid: {
                    color: 'rgba(148, 163, 184, 0.2)'
                },
                ticks: {
                    stepSize: 10,
                    color: '#64748b',
                    font: {
                        size: 12
                    }
                }
            }
        }
    }
});

function scheduleResize() {
    requestAnimationFrame(() => {
        chart.options.devicePixelRatio = window.devicePixelRatio || 1;
        chart.resize();
        chart.update('none');
    });
}

const sidebar = document.querySelector('.sidebar');
if (sidebar) {
    sidebar.addEventListener('transitionend', scheduleResize);
    sidebar.addEventListener('mouseenter', scheduleResize);
    sidebar.addEventListener('mouseleave', scheduleResize);
}

window.addEventListener('resize', scheduleResize);

async function loadData() {
    const res = await fetch('/api/chart/');
    const data = await res.json();

    chart.data.labels = data.labels;
    chart.data.datasets[0].data = data.temp;
    chart.data.datasets[1].data = data.smoke;
    chart.data.datasets[2].data = data.humidity;

    chart.update('none');
}

loadData();
setInterval(loadData, 2000);