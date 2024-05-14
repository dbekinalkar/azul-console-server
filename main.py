import argparse
import websockets
from websockets.sync.server import ServerConnection, WebSocketServer, serve

from player import SocketPlayer
import game
import connections

# connections: list[SocketPlayer] = []

def socket_handler(ws: ServerConnection) -> None:
    player: SocketPlayer = SocketPlayer(ws)
    connections.connectionHandler.add(player)
    player.listen()

def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Azul server to host games.")
    parser.add_argument("port", nargs='?', type=int, default=3000, help="Port number (default: 3000)")
    args: argparse.Namespace = parser.parse_args()
    return args

def main() -> None:
    args: argparse.Namespace = parse_args()

    print(f'Accepting connections at port {args.port}')

    game.gameHandler = game.GameHandler()
    connections.connectionHandler = connections.ConnectionHandler()

    server: WebSocketServer
    with serve(socket_handler, "", args.port) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()