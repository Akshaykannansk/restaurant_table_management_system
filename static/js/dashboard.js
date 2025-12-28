const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = protocol + '//' + window.location.host + '/ws/tables/';
const socket = new WebSocket(wsUrl);

socket.onopen = function (e) {
    console.log("WebSocket connected to " + wsUrl);
};

socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const tableName = data.message.table_number;
    const tableId = data.message.table_id;
    const newStatus = data.message.status; // AVAILABLE, OCCUPIED, BILL_REQUESTED, CLOSED

    console.log("Update received:", data.message);

    // Update DOM
    const card = document.querySelector(`a[href*="/table/${tableId}/"]`);
    if (card) {
        // Update Card Class
        card.className = `card table-card status-${newStatus}`;

        // Update Status Pill
        const pill = card.querySelector('.status-pill');
        if (pill) {
            pill.className = `status-pill ${newStatus.toLowerCase()}`;
            // Humanize status text logic (simple replacement)
            let humanStatus = newStatus;
            if (newStatus === 'BILL_REQUESTED') humanStatus = 'Bill Requested';
            else humanStatus = newStatus.charAt(0).toUpperCase() + newStatus.slice(1).toLowerCase();
            pill.textContent = humanStatus;
        }
    }
};

socket.onclose = function (e) {
    console.error("WebSocket closed unexpectedly");
};
