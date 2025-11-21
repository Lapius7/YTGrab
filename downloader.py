
import os
import yt_dlp
from typing import Callable, Optional, Dict, Any
class YouTubeDownloader:
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.is_cancelled = False
    def cancel(self):
        
        self.is_cancelled = True
    def _progress_hook(self, d: Dict[str, Any]):
        
        if self.is_cancelled:
            raise Exception("ダウンロードがキャンセルされました")
        if self.progress_callback and d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            if total > 0:
                percent = (downloaded / total) * 100
            else:
                percent = 0
            self.progress_callback({
                'status': 'downloading',
                'percent': percent,
                'downloaded': downloaded,
                'total': total,
                'speed': speed,
                'eta': eta
            })
    def get_video_info(self, url: str) -> Dict[str, Any]:
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    return {
                        'type': 'playlist',
                        'title': info.get('title', 'Unknown Playlist'),
                        'count': len(info['entries']),
                        'entries': [
                            {
                                'title': entry.get('title', 'Unknown'),
                                'duration': entry.get('duration', 0),
                                'url': entry.get('webpage_url', '')
                            }
                            for entry in info['entries'] if entry
                        ]
                    }
                else:
                    return {
                        'type': 'video',
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'description': info.get('description', ''),
                        'uploader': info.get('uploader', 'Unknown'),
                        'view_count': info.get('view_count', 0)
                    }
        except Exception as e:
            raise Exception(f"動画情報の取得に失敗しました: {str(e)}")
    def download(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        
        self.is_cancelled = False
        download_path = options.get('download_path', '.')
        os.makedirs(download_path, exist_ok=True)
        ydl_opts = {
            'outtmpl': os.path.join(download_path, options.get('filename_template', '%(title)s.%(ext)s')),
            'progress_hooks': [self._progress_hook],
            'quiet': False,
            'no_warnings': False,
        }
        if options.get('limit_rate'):
            ydl_opts['ratelimit'] = options.get('limit_rate')
        if options.get('concurrent_fragments'):
            try:
                ydl_opts['concurrent_fragment_downloads'] = int(options.get('concurrent_fragments'))
            except ValueError:
                pass
        if options.get('fragment_retries'):
            ydl_opts['fragment_retries'] = float('inf')
        if options.get('no_part'):
            ydl_opts['nopart'] = True
        if options.get('restrict_filenames'):
            ydl_opts['restrictfilenames'] = True
        if options.get('no_mtime'):
            ydl_opts['updatetime'] = False
        if options.get('cookies_from_browser') and options.get('cookies_from_browser') != 'なし':
            ydl_opts['cookiesfrombrowser'] = (options.get('cookies_from_browser'),)
        if options.get('proxy'):
            ydl_opts['proxy'] = options.get('proxy')
        if options.get('embed_metadata'):
            ydl_opts['addmetadata'] = True
        if options.get('write_info_json'):
            ydl_opts['writeinfojson'] = True
        download_type = options.get('download_type', 'video')
        if download_type == 'audio':
            audio_format = options.get('audio_format', 'mp3')
            audio_quality = options.get('audio_quality', '最高')
            quality_map = {
                '最高': '0',
                '高': '2',
                '中': '5',
                '低': '9'
            }
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': quality_map.get(audio_quality, '0'),
            }]
        else:
            video_quality = options.get('video_quality', '1080p')
            video_format = options.get('video_format', 'mp4')
            quality_map = {
                '4K': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            }
            ydl_opts['format'] = quality_map.get(video_quality, 'best')
            if video_format != 'mp4':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': video_format,
                }]
            else:
                ydl_opts['merge_output_format'] = 'mp4'
        if options.get('download_subtitles', False):
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = options.get('subtitle_languages', ['ja', 'en'])
            if options.get('auto_subtitles', False):
                ydl_opts['writeautomaticsub'] = True
            if options.get('embed_subs', False):
                ydl_opts['embedsubtitles'] = True
            convert_subs = options.get('convert_subs')
            if convert_subs and convert_subs != 'なし':
                ydl_opts['subtitlesformat'] = convert_subs
        if options.get('download_thumbnail', False):
            ydl_opts['writethumbnail'] = True
        if options.get('embed_thumbnail', False):
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
            })
        if options.get('playlist_mode', False):
            if options.get('playlist_items'):
                ydl_opts['playlist_items'] = options.get('playlist_items')
            else:
                playlist_start = options.get('playlist_start', 1)
                playlist_end = options.get('playlist_end')
                if playlist_start:
                    ydl_opts['playliststart'] = playlist_start
                if playlist_end:
                    ydl_opts['playlistend'] = playlist_end
            if options.get('playlist_reverse'):
                ydl_opts['playlistreverse'] = True
            if options.get('playlist_random'):
                ydl_opts['playlistrandom'] = True
        else:
            ydl_opts['noplaylist'] = True
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    downloaded_files = []
                    for entry in info['entries']:
                        if entry:
                            downloaded_files.append({
                                'title': entry.get('title', 'Unknown'),
                                'file_path': ydl.prepare_filename(entry)
                            })
                    return {
                        'success': True,
                        'type': 'playlist',
                        'title': info.get('title', 'Unknown Playlist'),
                        'files': downloaded_files
                    }
                else:
                    return {
                        'success': True,
                        'type': 'video',
                        'title': info.get('title', 'Unknown'),
                        'file_path': ydl.prepare_filename(info)
                    }
        except Exception as e:
            if self.is_cancelled:
                return {
                    'success': False,
                    'error': 'ダウンロードがキャンセルされました'
                }
            return {
                'success': False,
                'error': str(e)
            }
