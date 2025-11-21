
import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path
class DependencyManager:
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.deps_dir = os.path.join(self.app_dir, "dependencies")
        os.makedirs(self.deps_dir, exist_ok=True)
        self.ytdlp_path = os.path.join(self.deps_dir, "yt-dlp.exe")
        self.ffmpeg_path = os.path.join(self.deps_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.deps_dir, "ffprobe.exe")
    def check_ytdlp(self) -> bool:
        
        if os.path.exists(self.ytdlp_path):
            return True
        try:
            result = subprocess.run(['yt-dlp', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    def check_ffmpeg(self) -> bool:
        
        if os.path.exists(self.ffmpeg_path):
            return True
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    def download_ytdlp(self, progress_callback=None) -> bool:
        
        try:
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
            if progress_callback:
                progress_callback("yt-dlpをダウンロード中...")
            urllib.request.urlretrieve(url, self.ytdlp_path)
            if progress_callback:
                progress_callback("yt-dlpのダウンロードが完了しました")
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"yt-dlpのダウンロードエラー: {str(e)}")
            return False
    def download_ffmpeg(self, progress_callback=None) -> bool:
        
        try:
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            zip_path = os.path.join(self.deps_dir, "ffmpeg.zip")
            if progress_callback:
                progress_callback("FFmpegをダウンロード中...")
            urllib.request.urlretrieve(url, zip_path)
            if progress_callback:
                progress_callback("FFmpegを展開中...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.deps_dir)
            extracted_dir = None
            for item in os.listdir(self.deps_dir):
                item_path = os.path.join(self.deps_dir, item)
                if os.path.isdir(item_path) and item.startswith("ffmpeg"):
                    extracted_dir = item_path
                    break
            if extracted_dir:
                bin_dir = os.path.join(extracted_dir, "bin")
                if os.path.exists(bin_dir):
                    src_ffmpeg = os.path.join(bin_dir, "ffmpeg.exe")
                    if os.path.exists(src_ffmpeg):
                        shutil.copy2(src_ffmpeg, self.ffmpeg_path)
                    src_ffprobe = os.path.join(bin_dir, "ffprobe.exe")
                    if os.path.exists(src_ffprobe):
                        shutil.copy2(src_ffprobe, self.ffprobe_path)
                shutil.rmtree(extracted_dir)
            os.remove(zip_path)
            if progress_callback:
                progress_callback("FFmpegのダウンロードが完了しました")
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"FFmpegのダウンロードエラー: {str(e)}")
            return False
    def setup_environment(self):
        
        if self.deps_dir not in os.environ['PATH']:
            os.environ['PATH'] = self.deps_dir + os.pathsep + os.environ['PATH']
    def ensure_dependencies(self, progress_callback=None) -> dict:
        
        results = {
            'ytdlp': {'installed': False, 'downloaded': False},
            'ffmpeg': {'installed': False, 'downloaded': False}
        }
        if self.check_ytdlp():
            results['ytdlp']['installed'] = True
        else:
            if progress_callback:
                progress_callback("yt-dlpが見つかりません。ダウンロードを開始します...")
            results['ytdlp']['downloaded'] = self.download_ytdlp(progress_callback)
            results['ytdlp']['installed'] = results['ytdlp']['downloaded']
        if self.check_ffmpeg():
            results['ffmpeg']['installed'] = True
        else:
            if progress_callback:
                progress_callback("FFmpegが見つかりません。ダウンロードを開始します...")
            results['ffmpeg']['downloaded'] = self.download_ffmpeg(progress_callback)
            results['ffmpeg']['installed'] = results['ffmpeg']['downloaded']
        self.setup_environment()
        return results
