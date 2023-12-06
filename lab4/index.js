import WebSocket, {WebSocketServer} from "ws";

const wss = new WebSocketServer({port: 3000});

wss.on("connection", function connection(ws) {
    let username;

    ws.on("message", function message(message) {
        const data = JSON.parse(message);

        if (data.type === "message") {
            if (!username) {
                username = data.username;
            }
            wss.clients.forEach((client) => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({type: "message", username: username, message: data.message}));
                }
            });
        }
    });
});

