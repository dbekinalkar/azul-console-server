# Game player
# Each separate thread

import websockets
from websockets.sync.server import ServerConnection

class SocketPlayer:
    name: str
    ws: ServerConnection

    def __init__(self, ws: ServerConnection):
        self.name = f"Guest {ws.id}"
        self.ws = ws

    def listen(self) -> None:
        message: websockets.Data
        for message in self.ws:
            self.ws.send(message)