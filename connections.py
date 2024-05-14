from websockets.sync.server import ServerConnection

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import SocketPlayer

import threading

class ConnectionHandler:
    connections: list['SocketPlayer']
    connectionLock: threading.RLock

    def __init__(self):
        self.connections = []
        self.connectionLock = threading.RLock()

    def add(self, p: 'SocketPlayer'):
        with self.connectionLock:
            if p in self.connections:
                raise Exception("Already in connections")
            
            self.connections.append(p)
    

    def broadcast(self, msg: str):
        with self.connectionLock:
            conn: SocketPlayer
            for conn in self.connections:
                conn.ws.send(msg)
        

    def close(self, p: 'SocketPlayer'):
        with self.connectionLock:
            if p not in self.connections:
                raise Exception("Not in connections")
            
            self.connections.remove(p)


connectionHandler: ConnectionHandler = None