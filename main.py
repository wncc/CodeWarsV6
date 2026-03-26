import threading

from server import Server
import game


def _run_server():
    Server()


if __name__ == "__main__":
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    game.main()
