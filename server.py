import socket
import resolver

HOST = "8.8.8.8"
PORT = 53

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[DNS SERVER] Listening on {HOST}:{PORT}")

    while True:
        data, addr = sock.recvfrom(512)
        client_ip, client_port = addr
        response = resolver.resolve(data, client_ip)
        sock.sendto(response, addr)

if __name__ == "__main__":
    run()
