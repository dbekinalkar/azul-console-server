# Game player
# Each separate thread

import websockets
from websockets.sync.server import ServerConnection

import game

class SocketPlayer:
    name: str
    ws: ServerConnection

    def __init__(self, ws: ServerConnection):
        self.name = f"Guest {ws.id}"
        self.ws = ws

    def listen(self) -> None:
        message: websockets.Data
        for message in self.ws:
            self.process(message)


    def process(self, msg: str):
        args: list[str] = msg.split(' ')
        cmd: str = args[0]
        if cmd.lower() == "name":
            if len(args) <= 1:
                self.ws.send("Pass in name as argument")

            self.name = args[1]
            self.ws.send(f"Name updated to {self.name}")
        elif cmd.lower() == "join":
            try: 
                game.gameHandler.join(self)
                self.ws.send("Joined game")
            except Exception as  e:
                self.ws.send(e.args[0])
        elif cmd.lower() == "leave":
            try:
                game.gameHandler.leave(self)
                self.ws.send("Left game")
            except Exception as e:
                self.ws.send(e.args[0])
        elif cmd.lower() == "party":
            if len(game.gameHandler.players) == 0:
                self.ws.send("No one in game party")
            else:
                p: SocketPlayer
                names: list[str] = [p.name for p in game.gameHandler.players]
                self.ws.send(", ".join(names))
        else:
            self.ws.send("Invalid command")