import os
import base64
from cryptography.fernet import Fernet

class EncryptionTool:

    def __init__(self, key_file="encryption.key"):
        self.key_file = key_file
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)

    def load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as file:
                return file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as file:
                file.write(key)
            return key

    def encrypt_file(self, file_path):
        if not os.path.exists(file_path):
            return False, "File not found"

        with open(file_path, "rb") as file:
            data = file.read()

        encrypted = self.cipher.encrypt(data)

        with open(file_path + ".enc", "wb") as enc_file:
            enc_file.write(encrypted)

        return True, file_path + ".enc"

    def decrypt_file(self, file_path):
        if not os.path.exists(file_path):
            return False, "Encrypted file missing"

        with open(file_path, "rb") as file:
            encrypted = file.read()

        try:
            decrypted = self.cipher.decrypt(encrypted)
        except:
            return False, "Invalid encryption key"

        original_name = file_path.replace(".enc", "")

        with open(original_name, "wb") as dec_file:
            dec_file.write(decrypted)

        return True, original_name

    def encrypt_folder(self, folder_path):
        if not os.path.isdir(folder_path):
            return False, "Folder not found"

        for root, _, files in os.walk(folder_path):
            for file in files:
                full = os.path.join(root, file)
                self.encrypt_file(full)

        return True, "Folder encrypted"

    def decrypt_folder(self, folder_path):
        if not os.path.isdir(folder_path):
            return False, "Folder not found"

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".enc"):
                    full = os.path.join(root, file)
                    self.decrypt_file(full)

        return True, "Folder decrypted"
