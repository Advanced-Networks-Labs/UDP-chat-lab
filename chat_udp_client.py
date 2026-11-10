import argparse
import socket
import threading

BUFFER_SIZE = 4096


def receive_loop(sock, goodbye):
    """Print every datagram coming from the server."""
    while True:
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
        except OSError:
            return
        text = data.decode('utf-8', errors='replace')
        print(text, flush=True)
        if text == "Goodbye!":
            goodbye.set()
            return


def run_client(host, port, nickname):
    server = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    goodbye = threading.Event()
    threading.Thread(target=receive_loop, args=(sock, goodbye), daemon=True).start()

    sock.sendto(f"/join {nickname}".encode('utf-8'), server)   # registration datagram

    try:
        while True:
            try:
                text = input()
            except EOFError:
                text = '/quit'
            sock.sendto(text.encode('utf-8'), server)
            if text.strip() == '/quit':
                goodbye.wait(timeout=2)   # UDP: the "Goodbye!" reply may be lost
                break
    except KeyboardInterrupt:
        sock.sendto(b'/quit', server)
    finally:
        sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP chat client')
    parser.add_argument('nickname')
    parser.add_argument('host', nargs='?', default='127.0.0.1')
    parser.add_argument('port', nargs='?', type=int, default=5000)
    args = parser.parse_args()
    run_client(args.host, args.port, args.nickname)
