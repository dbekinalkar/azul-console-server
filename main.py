import argparse

def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Azul server to host games.")
    parser.add_argument("port", nargs='?', type=int, default=3000, help="Port number (default: 3000)")
    args: argparse.Namespace = parser.parse_args()
    return args

def main() -> None:
    args: argparse.Namespace = parse_args()

    print(f'Accepting connections at port {args.port}')

if __name__ == '__main__':
    main()