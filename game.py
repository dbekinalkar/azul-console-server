# Game 
# Handled by game thread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import SocketPlayer

import threading
import connections

from ceramic.game import Game
from ceramic.rules import Rules 

def run_game(gameHandler: 'GameHandler'):
    connections.connectionHandler.broadcast(f"Starting game")
    try:
        gameHandler.game.roll_game()
    except Exception as e:
        print(str(e))
        gameHandler.game = None
    else:
        connections.connectionHandler.broadcast(f"The winner is {gameHandler.game.state.winning_player()}")
    

class GameHandler:
    partyLock: threading.RLock
    party: list['SocketPlayer']
    game: Game

    def __init__(self):
        self.partyLock = threading.RLock()
        self.party = []
        self.game = None


    def join(self, p: 'SocketPlayer') -> bool:
        with self.partyLock:
            if self.game != None:
                raise Exception("Game is running")

            if len(self.party) >= 4:
                raise Exception("Game is full")
            
            if p in self.party:
                raise Exception("Already in game party")
            
            self.party.append(p)

        return True
    
    def leave(self, p: 'SocketPlayer') -> bool:
        with self.partyLock:
            if self.game != None:
                raise Exception("Game is running")
            
            if p not in self.party:
                raise Exception("Not in game party")
            
            self.party.remove(p)

            return True
    
    def start_game(self) -> bool:
        with self.partyLock:
            if len(self.party) < 2:
                raise Exception("Not enough members in game party")
            
            self.game = Game(Rules.BASE)
            self.game.add_players([p for p in self.party])

            gameThread: threading.Thread = threading.Thread(target=run_game, args=([self]), name="Game Thread")
            gameThread.start()

            return True

gameHandler: GameHandler = None