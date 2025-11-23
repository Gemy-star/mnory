(function () {
    const container = document.getElementById('orderChatContainer');
    if (!container) return;

    const orderNumber = container.dataset.orderNumber;
    if (!orderNumber) return;

    const messagesList = document.getElementById('orderMessagesList');
    const form = document.getElementById('orderChatForm');
    const input = document.getElementById('orderChatInput');

    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${scheme}://${window.location.host}/ws/orders/${orderNumber}/`;

    let socket;

    function appendMessage(message, fromMe) {
        if (!messagesList || !message) return;
        const li = document.createElement('li');
        li.className = 'order-message-item mb-2 ' + (fromMe ? 'from-me text-end' : 'from-them text-start');

        const meta = document.createElement('div');
        meta.className = 'fw-semibold';
        const sender = document.createElement('span');
        sender.textContent = message.sender || '';
        const ts = document.createElement('span');
        ts.className = 'text-muted ms-1';
        ts.style.fontSize = '0.75rem';
        ts.textContent = message.created_at ? ` ${new Date(message.created_at).toLocaleString()}` : '';

        meta.appendChild(sender);
        meta.appendChild(ts);

        const body = document.createElement('div');
        body.className = 'order-message-body';
        body.textContent = message.body || '';

        li.appendChild(meta);
        li.appendChild(body);
        messagesList.appendChild(li);
        messagesList.scrollTop = messagesList.scrollHeight;
    }

    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = function () {
            // console.log('Order chat connected');
        };

        socket.onmessage = function (event) {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                return;
            }
            if (!data || data.type !== 'chat_message' || !data.message) return;
            appendMessage(data.message, false);
        };

        socket.onclose = function () {
            // Try to reconnect after a delay
            setTimeout(connect, 5000);
        };
    }

    if (form && input) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = (input.value || '').trim();
            if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;

            socket.send(JSON.stringify({ body: text }));
            input.value = '';
        });
    }

    connect();
})();
