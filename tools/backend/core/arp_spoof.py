from utils.legal_warning import legal_warning

class ARPSpoof:
    def start(self, target_ip="127.0.0.1"):
        legal_warning("ARP Spoofing Tool")
        print(f"Simulating ARP spoofing on {target_ip} (Educational use only)")
        # هنا الكود الأصلي لو تحب تضيف packet sending
