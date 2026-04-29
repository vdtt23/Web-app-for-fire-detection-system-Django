async function loadAlerts() {
    try {
        const res = await fetch('/api/alerts/');
        const data = await res.json();

        const container = document.getElementById("alert-list");
        container.innerHTML = "";

        if (data.length === 0) {
            container.innerHTML = "<p>No alerts</p>";
            return;
        }

        data.forEach(n => {
            container.innerHTML += `
                <div class="alert-box ${n.status.toLowerCase()}">
                    Node ${n.node_id} - ${n.status} <br>
                    Temp: ${n.temperature}°C |
                    Smoke: ${n.smoke} |
                    Humidity: ${n.humidity}%
                </div>
            `;
        });

    } catch (e) {
        console.error("Alert load error:", e);
    }
}

loadAlerts();
setInterval(loadAlerts, 2000);