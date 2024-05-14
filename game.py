# Game 
# Handled by game thread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import SocketPlayer

import threading


class GameHandler:
    partyLock: threading.RLock
    players: list['SocketPlayer']
    game: None

    def __init__(self):
        self.partyLock = threading.RLock()
        self.players = []
        self.game = None


    def join(self, p: 'SocketPlayer') -> bool:
        with self.partyLock:
            if self.game != None:
                raise Exception("Game is running")

            if len(self.players) >= 4:
                raise Exception("Game is full")
            
            if p in self.players:
                raise Exception("Already in game party")
            
            self.players.append(p)

        return True
    
    def leave(self, p: 'SocketPlayer') -> bool:
        with self.partyLock:
            if self.game != None:
                raise Exception("Game is running")
            
            if p not in self.players:
                raise Exception("Not in game party")
            
            self.players.remove(p)

            return True

gameHandler: GameHandler = None