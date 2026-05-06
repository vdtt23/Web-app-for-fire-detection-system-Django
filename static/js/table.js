let selectedNodeId = null;

const nodeSelectEl = document.getElementById("history-node-select");
const startDateEl = document.getElementById("history-start-date");
const endDateEl = document.getElementById("history-end-date");
const applyBtnEl = document.getElementById("history-apply-btn");
const clearBtnEl = document.getElementById("history-clear-btn");
const exportBtnEl = document.getElementById("history-export-btn");

function getNodeIdsFromRenderedTable() {
    const rows = document.querySelectorAll("#latest-node-table tbody tr");
    const ids = [];

    rows.forEach(row => {
        const firstCell = row.querySelector("td");
        const nodeId = Number(firstCell ? firstCell.textContent.trim() : "");
        if (Number.isFinite(nodeId) && nodeId > 0) ids.push(nodeId);
    });

    return Array.from(new Set(ids)).sort((a, b) => a - b);
}

function statusClass(status) {
    return String(status || "").toLowerCase();
}

function buildHistoryQueryParams() {
    const params = new URLSearchParams();
    if (startDateEl && startDateEl.value) params.set("start_date", startDateEl.value);
    if (endDateEl && endDateEl.value) params.set("end_date", endDateEl.value);
    return params;
}

async function fetchNodeHistory(nodeId) {
    const params = buildHistoryQueryParams();
    const query = params.toString();
    const res = await fetch(`/api/nodes/${nodeId}/history/${query ? `?${query}` : ""}`, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
    });
    if (!res.ok) throw new Error(`History API error: ${res.status}`);
    return res.json();
}

function toCsvValue(value) {
    const text = String(value ?? "").replace(/"/g, '""');
    return `"${text}"`;
}

function downloadCsv(fileName, content) {
    const blob = new Blob(["\ufeff" + content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

async function loadNodeHistory(nodeId) {
    const historyBody = document.getElementById("node-history-body");
    const historyTitle = document.getElementById("history-title");
    const historySubtitle = document.getElementById("history-subtitle");

    if (!historyBody || !historyTitle || !historySubtitle) return;

    try {
        const data = await fetchNodeHistory(nodeId);

        historyTitle.textContent = `Node ${nodeId} History`;
        historySubtitle.textContent = `Showing the latest ${data.length} records.`;

        if (!data.length) {
            historyBody.innerHTML = '<tr><td colspan="5" class="history-empty">No history for this node yet.</td></tr>';
            return;
        }

        historyBody.innerHTML = data.map(n => `
            <tr class="row-${statusClass(n.status)}">
                <td>${n.created_at}</td>
                <td>${n.temperature}</td>
                <td>${n.smoke}</td>
                <td>${n.humidity}</td>
                <td class="status ${statusClass(n.status)}">${n.status}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("History load error:", e);
        historyBody.innerHTML = '<tr><td colspan="5" class="history-empty">Failed to load node history.</td></tr>';
    }
}

function syncNodeDropdown(nodes) {
    if (!nodeSelectEl) return;
    const incoming = nodes.map(n => Number(n.node_id));

    nodeSelectEl.innerHTML = '<option value="">Select node</option>';

    incoming.sort((a, b) => a - b).forEach(nodeId => {
        const option = document.createElement("option");
        option.value = String(nodeId);
        option.textContent = `Node ${nodeId}`;
        if (selectedNodeId === nodeId) option.selected = true;
        nodeSelectEl.appendChild(option);
    });
}

function bootstrapNodeDropdown() {
    if (!nodeSelectEl) return;
    const ids = getNodeIdsFromRenderedTable();
    if (!ids.length) return;

    syncNodeDropdown(ids.map(node_id => ({ node_id })));
}

async function loadTable() {
    try {
        const res = await fetch('/api/nodes/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' },
        });
        if (!res.ok) throw new Error(`Nodes API error: ${res.status}`);
        const data = await res.json();
        if (!Array.isArray(data)) throw new Error('Nodes API returned non-array response');

        const tbody = document.querySelector("#latest-node-table tbody");
        if (!tbody) return;

        syncNodeDropdown(data);

        tbody.innerHTML = "";

        tbody.innerHTML = data.map(n => `
            <tr class="row-${statusClass(n.status)} ${selectedNodeId === n.node_id ? "is-selected" : ""}" data-node-id="${n.node_id}">
                <td>${n.node_id}</td>
                <td>${n.temperature}</td>
                <td>${n.smoke}</td>
                <td>${n.humidity}</td>
                <td class="status ${statusClass(n.status)}">${n.status}</td>
            </tr>
        `).join("");

        tbody.querySelectorAll("tr[data-node-id]").forEach(row => {
            row.addEventListener("click", () => {
                const nodeId = Number(row.getAttribute("data-node-id"));
                selectedNodeId = nodeId;
                if (nodeSelectEl) nodeSelectEl.value = String(nodeId);
                tbody.querySelectorAll("tr").forEach(r => r.classList.remove("is-selected"));
                row.classList.add("is-selected");
                loadNodeHistory(nodeId);
            });
        });

        if (selectedNodeId !== null) {
            const stillExists = data.some(n => n.node_id === selectedNodeId);
            if (stillExists) {
                loadNodeHistory(selectedNodeId);
            }
        }
    } catch (e) {
        console.error("Table load error:", e);
        bootstrapNodeDropdown();
    }
}

if (nodeSelectEl) {
    nodeSelectEl.addEventListener("change", () => {
        const nodeId = Number(nodeSelectEl.value);
        selectedNodeId = Number.isFinite(nodeId) && nodeId > 0 ? nodeId : null;

        const tbody = document.querySelector("#latest-node-table tbody");
        if (tbody) {
            tbody.querySelectorAll("tr").forEach(r => {
                const rowNodeId = Number(r.getAttribute("data-node-id"));
                r.classList.toggle("is-selected", selectedNodeId === rowNodeId);
            });
        }

        if (selectedNodeId !== null) {
            loadNodeHistory(selectedNodeId);
        }
    });
}

if (applyBtnEl) {
    applyBtnEl.addEventListener("click", () => {
        if (selectedNodeId !== null) {
            loadNodeHistory(selectedNodeId);
        }
    });
}

if (clearBtnEl) {
    clearBtnEl.addEventListener("click", () => {
        if (startDateEl) startDateEl.value = "";
        if (endDateEl) endDateEl.value = "";

        if (selectedNodeId !== null) {
            loadNodeHistory(selectedNodeId);
        }
    });
}

if (exportBtnEl) {
    exportBtnEl.addEventListener("click", async () => {
        if (selectedNodeId === null) {
            alert("Please select a node before exporting history.");
            return;
        }

        try {
            const data = await fetchNodeHistory(selectedNodeId);
            if (!data.length) {
                alert("No history data to export for current filters.");
                return;
            }

            const header = ["Time", "Temp", "Smoke", "Humidity", "Status"];
            const rows = data.map(n => [
                n.created_at,
                n.temperature,
                n.smoke,
                n.humidity,
                n.status,
            ]);

            const csv = [header, ...rows]
                .map(row => row.map(toCsvValue).join(","))
                .join("\n");

            const start = startDateEl && startDateEl.value ? startDateEl.value : "all";
            const end = endDateEl && endDateEl.value ? endDateEl.value : "all";
            const filename = `node-${selectedNodeId}-history-${start}-to-${end}.csv`;
            downloadCsv(filename, csv);
        } catch (e) {
            console.error("Export history error:", e);
            alert("Failed to export history.");
        }
    });
}

// First load
bootstrapNodeDropdown();
loadTable();

// Update per 2s
setInterval(loadTable, 2000);