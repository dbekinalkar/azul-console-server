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

class Command:
    usage: str
    details: str

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        pass

class NameCommand(Command):
    usage: str = "name [name]"
    details: str = "Use to change / view name"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        if len(args) <= 1:
            player.ws.send(f"Current Name: {player.name}")
            return True
        
        match = re.match(r'^([a-zA-Z0-9]|_|-){1,15}$', args[1])

        if not match:
            player.ws.send("Illegal characters in name or name too long / short")
            return False

        player.name = args[1]
        player.ws.send(f"Name updated to {player.name}")

        return True

class JoinCommand(Command):
    usage: str = "join"
    details: str = "Join the game party"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        try: 
            game.gameHandler.join(player)
            player.ws.send("Joined game")
            return True
        except Exception as  e:
            player.ws.send(e.args[0])
            return False

class LeaveCommand(Command):
    usage: str = "leave"
    details: str = "Leave the game party"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        try:
            game.gameHandler.leave(player)
            player.ws.send("Left game")
            return True
        except Exception as e:
            player.ws.send(e.args[0])
            return False


class PartyCommand(Command):
    usage: str = "party [clear]"
    details: str = "View / clear the game party"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        if len(args) > 1 and args[1].lower() == "clear":
            try:
                game.gameHandler.clear_party()
                player.ws.send("Party cleared")
                return True
            except Exception as e:
                player.ws.send(e.args[0])
                return False


        if len(game.gameHandler.party) == 0:
            player.ws.send("No one in game party")
            return True
        
        p: 'SocketPlayer'
        names: list[str] = [p.name for p in game.gameHandler.party]
        player.ws.send("Party: " + ", ".join(names))
        return False

class StartCommand(Command):
    usage: str = "start"
    details: str = "Start the Azul game"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        try:
            game.gameHandler.start_game()
            return True
        except Exception as e:
            player.ws.send(e.args[0])
            return False
        
class StopCommand(Command):
    usage: str = "stop"
    details: str = "Stop the Azul game"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        try:
            game.gameHandler.stop_game()
            return True
        except Exception as e:
            player.ws.send(e.args[0])
            return False

class StateCommand(Command):
    usage: str = "state"
    details: str = "View the game state"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        if not game.gameHandler.game:
            player.ws.send("No current game")
            return False
        
        player.ws.send(str(game.gameHandler.game.state))
        return True

class MoveCommand(Command):
    usage: str = "move [pile][color][row]"
    details: str = "Use in a game to input a move"

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        with player.actionLock:
            if player.phase != "playing":
                player.ws.send("Not your turn")
                return False
            
            if len(args) <= 1:
                player.ws.send(self.details)
                return False

            match = re.match(r'^[0-9][A-E][0-5]$', args[1])

            if not match:
                player.ws.send(
                    "Does not match regex\n"
                    "Moves should be sent like 1C3\n"
                    "First character: pile to take from (0 = middle)\n"
                    "Second character: color\n"
                    "Third character: Line to add to (0 = floor)"
                        )
                return False
                
            player.actionStr = args[1]
            player.action = Action(int(args[1][0]), Tile.from_letter(args[1][1]), int(args[1][2]))
            player.actionSem.release()

            return True
        
class HelpCommand(Command):
    usage: str = "help"
    details: str = "Gives details on all commands"

    commands: dict[str, Command]
    usageLen: int

    def __init__(self, commands: dict[str, Command]):
        self.commands = commands
        self.usageLen = max([len(cmdObj.usage) for cmdObj in commands.values()])

    def execute(self, args: list[str], player: 'SocketPlayer') -> bool:
        if len(args) <= 1:
            player.ws.send("\n".join([f"{cmdObj.usage:{self.usageLen}} {cmdObj.details}" for cmdObj in self.commands.values()]))
            return True
        
        cmd: str = args[1].lower()

        if not cmd in commands:
            player.ws.send("Not a valid command")
            return False
        
        cmdObj: Command = self.commands.get(cmd)
        player.ws.send(f"{cmdObj.usage:{self.usageLen}} {cmdObj.details}")
        return True



commands: dict[str, Command] = {
    "name": NameCommand(),
    "join": JoinCommand(),
    "leave": LeaveCommand(),
    "party": PartyCommand(),
    "start": StartCommand(),
    "state": StateCommand(),
    "move": MoveCommand(),
}

commands["help"] = HelpCommand(commands)

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


    def process(self, msg: str) -> bool:
        args: list[str] = msg.split(' ')
        cmd: str = args[0].lower()
        
        if cmd not in commands:
            self.ws.send("Invalid Command")
            return False

        cmdObj: Command = commands.get(cmd)

        return cmdObj.execute(args, self)


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