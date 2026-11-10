import socket

HOST = '0.0.0.0'
PORT = 5000
BUFFER_SIZE = 4096

clients = {}   # (ip, port) -> nickname
names = {}     # nickname -> (ip, port)


def send(sock, addr, text):
    """Send one datagram (one message) to a client."""
    sock.sendto(text.encode('utf-8'), addr)


def broadcast(sock, text, exclude=None):
    """Send a message to every registered client, except the address `exclude`."""
    for addr in list(clients):
        if addr != exclude:
            send(sock, addr, text)


def handle_datagram(sock, addr, text):
    text = text.strip()
    if not text:
        return

    # Unknown sender: the only accepted message is "/join <nickname>"
    if addr not in clients:
        parts = text.split()
        if len(parts) != 2 or parts[0] != '/join':
            send(sock, addr, "Send '/join <nickname>' first.")
        elif parts[1] in names:
            send(sock, addr, f"Nickname '{parts[1]}' is already taken.")
        else:
            nick = parts[1]
            clients[addr] = nick
            names[nick] = addr
            print(f"[SERVER] {nick} joined from {addr[0]}:{addr[1]}")
            send(sock, addr, f"Welcome {nick}! Commands: /list, /msg <user> <text>, /quit")
            broadcast(sock, f"*** {nick} joined the chat ***", exclude=addr)
        return

    nick = clients[addr]
    if text == '/quit':
        del clients[addr]
        del names[nick]
        send(sock, addr, "Goodbye!")
        broadcast(sock, f"*** {nick} left the chat ***")
        print(f"[SERVER] {nick} left")
    elif text == '/list':
        send(sock, addr, "Online: " + ", ".join(sorted(names)))
    elif text.startswith('/msg '):
        parts = text.split(' ', 2)
        if len(parts) < 3:
            send(sock, addr, "Usage: /msg <user> <text>")
        elif parts[1] not in names:
            send(sock, addr, f"User '{parts[1]}' not found.")
        else:
            send(sock, names[parts[1]], f"[private from {nick}] {parts[2]}")
            send(sock, addr, f"[private to {parts[1]}] {parts[2]}")
    elif text.startswith('/'):
        send(sock, addr, "Unknown command.")
    else:
        broadcast(sock, f"[{nick}] {text}")


def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[SERVER] UDP chat listening on {HOST}:{PORT}")

    try:
        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except ConnectionResetError:
                continue  # Windows: ICMP "port unreachable" from a client that vanished
            handle_datagram(sock, addr, data.decode('utf-8', errors='replace'))
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        sock.close()


if __name__ == '__main__':
    run_server()
