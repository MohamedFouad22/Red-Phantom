import requests
import folium
import json
import socket
import ssl
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime
import random

class GeolocationTracker:
    def __init__(self, save_path):
        self.save_path = save_path
        self.results = {
            'target_url': '',
            'subdomains': [],
            'exposed_directories': [],
            'ssl_info': {},
            'geo_data': {},
            'screenshot_path': '',
            'threat_map_path': '',
            'scan_time': '',
            'all_files_found': []
        }
        os.makedirs(self.save_path, exist_ok=True)

    def get_geoip_info(self, domain):
        try:
            ip = socket.gethostbyname(domain)
            apis = [
                f'http://ipapi.co/{ip}/json/',
                f'http://ip-api.com/json/{ip}',
                f'https://geolocation-db.com/json/{ip}'
            ]
            geo_data = {}
            for api_url in apis:
                try:
                    r = requests.get(api_url, timeout=10)
                    if r.status_code == 200:
                        geo_data = r.json()
                        break
                except:
                    continue
            if 'ipapi.co' in api_url:
                self.results['geo_data'] = {
                    'ip': ip,
                    'city': geo_data.get('city', 'Unknown'),
                    'region': geo_data.get('region', 'Unknown'),
                    'country': geo_data.get('country_name', 'Unknown'),
                    'latitude': geo_data.get('latitude', 0),
                    'longitude': geo_data.get('longitude', 0),
                    'isp': geo_data.get('org', 'Unknown'),
                    'timezone': geo_data.get('timezone', 'Unknown')
                }
            elif 'ip-api.com' in api_url:
                self.results['geo_data'] = {
                    'ip': ip,
                    'city': geo_data.get('city', 'Unknown'),
                    'region': geo_data.get('regionName', 'Unknown'),
                    'country': geo_data.get('country', 'Unknown'),
                    'latitude': geo_data.get('lat', 0),
                    'longitude': geo_data.get('lon', 0),
                    'isp': geo_data.get('isp', 'Unknown'),
                    'timezone': geo_data.get('timezone', 'Unknown')
                }
            else:
                self.results['geo_data'] = {
                    'ip': ip,
                    'city': geo_data.get('city', 'Unknown'),
                    'country': geo_data.get('country_name', 'Unknown'),
                    'latitude': geo_data.get('latitude', 0),
                    'longitude': geo_data.get('longitude', 0),
                    'isp': 'Unknown',
                    'timezone': 'Unknown'
                }
        except:
            pass

    def subdomain_enumeration(self, domain):
        subdomains = set()
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for cert in data:
                    name = cert.get('name_value', '')
                    if name and domain in name:
                        subdomains.update([sub.strip().lower() for sub in name.split('\n')])
        except:
            pass
        common_subs = [f"www.{domain}", f"mail.{domain}", f"ftp.{domain}", f"admin.{domain}", f"blog.{domain}", f"api.{domain}"]
        for sub in common_subs:
            try:
                socket.gethostbyname(sub)
                subdomains.add(sub)
            except:
                continue
        self.results['subdomains'] = sorted(list(subdomains))[:30]

    def check_exposed_directories(self, base_url):
        directories = [
            '/admin', '/login', '/backup', '/config', '/.git', '/uploads', '/api'
        ]
        exposed = []
        all_files = []
        for directory in directories:
            test_url = f"{base_url.rstrip('/')}{directory}"
            try:
                r = requests.get(test_url, timeout=3, allow_redirects=True, verify=False)
                file_info = {
                    'path': directory,
                    'url': test_url,
                    'status': r.status_code,
                    'size': len(r.content),
                    'content_type': r.headers.get('content-type', 'Unknown')
                }
                all_files.append(file_info)
                if r.status_code in [200, 301, 302, 403]:
                    exposed.append(file_info)
            except:
                continue
        self.results['exposed_directories'] = exposed
        self.results['all_files_found'] = all_files

    def check_ssl_tls(self, domain):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    ssl_info = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert.get('version', 'Unknown'),
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'san': cert.get('subjectAltName', []),
                        'serialNumber': cert.get('serialNumber', 'Unknown'),
                        'protocol': ssock.version()
                    }
                    self.results['ssl_info'] = ssl_info
        except:
            pass

    def take_screenshot(self, url):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            time.sleep(5)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot_path = os.path.join(self.save_path, screenshot_filename)
            driver.save_screenshot(screenshot_path)
            driver.quit()
            self.results['screenshot_path'] = screenshot_path
        except:
            try:
                r = requests.get(url, timeout=10)
            except:
                pass

    def create_threat_map(self):
        if self.results['geo_data'].get('latitude') and self.results['geo_data'].get('longitude'):
            m = folium.Map(location=[self.results['geo_data']['latitude'], self.results['geo_data']['longitude']], zoom_start=12)
        else:
            m = folium.Map(location=[24.7136, 46.6753], zoom_start=5)
        if self.results['geo_data']:
            folium.Marker(
                [self.results['geo_data']['latitude'], self.results['geo_data']['longitude']],
                popup=f"{self.results['target_url']} ({self.results['geo_data'].get('ip','N/A')})",
                tooltip="Target",
                icon=folium.Icon(color='red', icon='flag', prefix='fa')
            ).add_to(m)
        for subdomain in self.results['subdomains'][:8]:
            try:
                sub_ip = socket.gethostbyname(subdomain)
                lat = self.results['geo_data'].get('latitude', 24.7136) + random.uniform(-0.3,0.3)
                lon = self.results['geo_data'].get('longitude', 46.6753) + random.uniform(-0.3,0.3)
                folium.Marker([lat, lon], popup=f"{subdomain} ({sub_ip})", tooltip=subdomain, icon=folium.Icon(color='blue', icon='globe', prefix='fa')).add_to(m)
            except:
                continue
        map_file = os.path.join(self.save_path, f"threat_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        m.save(map_file)
        self.results['threat_map_path'] = map_file

    def run_full_scan(self, url):
        if not url.startswith(('http://','https://')):
            url = 'https://' + url
        self.results['target_url'] = url
        self.results['scan_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        self.get_geoip_info(domain)
        self.subdomain_enumeration(domain)
        self.check_exposed_directories(url)
        self.check_ssl_tls(domain)
        self.take_screenshot(url)
        self.create_threat_map()
