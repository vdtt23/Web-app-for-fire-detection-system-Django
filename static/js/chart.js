const ctx = document.getElementById('sensorChart');

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'Temp', data: [] },
            { label: 'Smoke', data: [] },
            { label: 'Humidity', data: [] }
        ]
    },
    options: {
        responsive: true,
        animation: false
    }
});

async function loadData() {
    const res = await fetch('/api/chart/');
    const data = await res.json();

    chart.data.labels = data.labels;
    chart.data.datasets[0].data = data.temp;
    chart.data.datasets[1].data = data.smoke;
    chart.data.datasets[2].data = data.humidity;

    chart.update();
}

loadData();
setInterval(loadData, 2000);