# Game player
# Each separate thread

import websockets
import threading
from websockets.sync.server import ServerConnection

import game
import connections

from ceramic.game import Action, Player, GameHelper
from ceramic.state import Tile

import re

import json

class SocketPlayer(Player):
    name: str
    ws: ServerConnection

    phase: str

    actionLock: threading.RLock
    actionSem: threading.Semaphore
    
    action: Action
    actionStr: str

    def __init__(self, ws: ServerConnection):
        Player.__init__(self)

        self.name = f"Guest {ws.id}"
        self.ws = ws

        self.phase = "waiting"

        self.actionLock = threading.RLock()
        self.actionSem = threading.Semaphore()
        self.actionSem.acquire()

        self.action = None
        self.actionStr = ""



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
            if len(game.gameHandler.party) == 0:
                self.ws.send("No one in game party")
            else:
                p: SocketPlayer
                names: list[str] = [p.name for p in game.gameHandler.party]
                self.ws.send(", ".join(names))
        elif cmd.lower() == "start":
            try:
                game.gameHandler.start_game()
            except Exception as e:
                self.ws.send(e.args[0])
                

        elif cmd.lower() == "move":
            with self.actionLock:
                if self.phase != "playing":
                    self.ws.send("Not your turn")
                    return 

                match = re.match(r'^[0-9][A-E][0-5]$', args[1])

                if not match:
                    self.ws.send(
                        """Does not match regex
                        Moves should be sent like 1C3
                        First character: pile to take from
                        Second character: color
                        Third character: Line to add to (0 = floor)"""
                            )
                    return
                    
                self.actionStr = args[1]
                self.action = Action(int(args[1][0]), Tile.from_letter(args[1][1]), int(args[1][2]))
                self.actionSem.release()
        else:
            self.ws.send("Invalid command")


    def play(self, state):
        self.phase = "playing"
        self.ws.send(str(state))
        self.ws.send("Your turn!")
        ret: Action
        while True:
            self.actionSem.acquire()

            self.actionLock.acquire()
            ret = self.action
            retStr = self.actionStr
            self.actionLock.release()
            
            if GameHelper.legal(ret, state):
                self.phase = "waiting"
                break
            
            self.ws.send(f"Invalid move {retStr}")
        
        connections.connectionHandler.broadcast(f"{self.name} played {retStr}")

        return ret