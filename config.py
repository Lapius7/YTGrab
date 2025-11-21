import json
import os
import sys
import base64
from datetime import datetime
from typing import Dict, List, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
class Config:
    def __init__(self, config_file: str = "config.dat"):
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.app_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_file = os.path.join(self.data_dir, config_file)
        self.cipher = self._get_cipher()
        self.settings = self._load_config()
    def _get_cipher(self) -> Fernet:
        key_file = os.path.join(self.data_dir, ".key")
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                return Fernet(key)
            except Exception:
                pass
        import platform
        import hashlib
        machine_id = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
        salt = hashlib.sha256(machine_id.encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"YouTubeDownloader-SecureConfig-2024"))
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_file, 2)  
        except Exception as e:
            print(f"キーファイルの保存エラー: {e}")
        return Fernet(key)
    def _encrypt_data(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode('utf-8'))
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode('utf-8')
    def _get_default_settings(self) -> Dict[str, Any]:
        return {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads", "YouTube"),
            "video_quality": "1080p",
            "audio_quality": "最高",
            "video_format": "mp4",
            "audio_format": "mp3",
            "download_type": "video",  
            "download_subtitles": False,
            "auto_subtitles": False,
            "subtitle_languages": ["ja", "en"],
            "download_thumbnail": False,
            "embed_thumbnail": False,
            "filename_template": "%(title)s.%(ext)s",
            "playlist_mode": False,
            "playlist_start": 1,
            "playlist_end": None,
            "max_downloads": None,
            "download_history": []
        }
    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._decrypt_data(encrypted_data)
                loaded_settings = json.loads(decrypted_data)
                default_settings = self._get_default_settings()
                default_settings.update(loaded_settings)
                return default_settings
            except Exception as e:
                print(f"設定ファイルの読み込みエラー: {e}")
                return self._get_default_settings()
        return self._get_default_settings()
    def save_config(self) -> bool:
        try:
            json_data = json.dumps(self.settings, ensure_ascii=False, indent=2)
            encrypted_data = self._encrypt_data(json_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"設定ファイルの保存エラー: {e}")
            return False
    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)
    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
    def add_to_history(self, url: str, title: str, file_path: str, 
                      download_type: str, quality: str) -> None:
        history_entry = {
            "url": url,
            "title": title,
            "file_path": file_path,
            "download_type": download_type,
            "quality": quality,
            "timestamp": datetime.now().isoformat()
        }
        if "download_history" not in self.settings:
            self.settings["download_history"] = []
        self.settings["download_history"].insert(0, history_entry)
        if len(self.settings["download_history"]) > 100:
            self.settings["download_history"] = self.settings["download_history"][:100]
        self.save_config()
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        history = self.settings.get("download_history", [])
        return history[:limit]
    def clear_history(self) -> None:
        self.settings["download_history"] = []
        self.save_config()
