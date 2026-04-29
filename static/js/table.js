async function loadTable() {
    try {
        const res = await fetch('/api/nodes/');
        const data = await res.json();

        const tbody = document.querySelector(".node-table tbody");
        if (!tbody) return;

        tbody.innerHTML = "";

        data.forEach(n => {
            const row = `
                <tr class="row-${n.status.toLowerCase()}">
                    <td>${n.node_id}</td>
                    <td>${n.temperature}</td>
                    <td>${n.smoke}</td>
                    <td>${n.humidity}</td>
                    <td class="status ${n.status.toLowerCase()}">${n.status}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (e) {
        console.error("Table load error:", e);
    }
}

// First load
loadTable();

// Update per 2s
setInterval(loadTable, 2000);