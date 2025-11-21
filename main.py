
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime
from config import Config
from downloader import YouTubeDownloader
from dependency_manager import DependencyManager
from collapsible_frame import CollapsibleFrame
class ThemeManager:
    
    LIGHT = {
        'name': 'light',
        'bg_dark': '#f5f5f5',
        'bg_darker': '#ffffff',
        'bg_lighter': '#e8e8e8',
        'bg_hover': '#d0d0d0',
        'accent_primary': '#0078d4',
        'accent_secondary': '#106ebe',
        'accent_success': '#107c10',
        'accent_warning': '#ff8c00',
        'accent_error': '#e81123',
        'text_primary': '#323130',
        'text_secondary': '#605e5c',
        'text_bright': '#000000',
        'border': '#d1d1d1',
        'border_focus': '#0078d4',
    }
    DARK = {
        'name': 'dark',
        'bg_dark': '#1e1e1e',
        'bg_darker': '#181818',
        'bg_lighter': '#252525',
        'bg_hover': '#2d2d2d',
        'accent_primary': '#007acc',
        'accent_secondary': '#0098ff',
        'accent_success': '#4ec9b0',
        'accent_warning': '#ce9178',
        'accent_error': '#f48771',
        'text_primary': '#cccccc',
        'text_secondary': '#858585',
        'text_bright': '#ffffff',
        'border': '#3e3e3e',
        'border_focus': '#007acc',
    }
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_TITLE = 18
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_SMALL = 9
class LoadingOverlay:
    
    def __init__(self, parent, text="処理中..."):
        self.parent = parent
        self.overlay = None
        self.text = text
    def show(self):
        if self.overlay:
            return
        self.parent.update_idletasks()
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.overrideredirect(True)
        self.overlay.geometry(f"{width}x{height}+{self.parent.winfo_rootx()}+{self.parent.winfo_rooty()}")
        self.overlay.attributes('-alpha', 0.7)
        self.overlay.configure(bg='black')
        self.overlay.transient(self.parent)
        self.overlay.grab_set()
        label = ttk.Label(self.overlay, text=f"⏳ {self.text}", 
                         font=("Meiryo UI", 16, "bold"),
                         foreground="white", background="black")
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.parent.update()
    def hide(self):
        if self.overlay:
            self.overlay.grab_release()
            self.overlay.destroy()
            self.overlay = None
class YouTubeDownloaderGUI:
    
    APP_NAME = "YTGrab"
    VERSION = "2.1.0"
    AUTHOR = "Lapius"
    def __init__(self, root):
        self.root = root
        self.root.title(f"{self.APP_NAME} v{self.VERSION} by {self.AUTHOR}")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.config = Config()
        self.downloader = None
        self.is_downloading = False
        self.dep_manager = DependencyManager()
        self.theme_var = tk.StringVar(value=self.config.get("theme", "light"))
        self.current_theme = ThemeManager.LIGHT if self.theme_var.get() == "light" else ThemeManager.DARK
        self.root.configure(bg=self.current_theme['bg_dark'])
        self._init_variables()
        self._configure_styles()
        self._create_scrollable_canvas()
        self._create_widgets()
        self._load_settings()
        self.root.after(100, self._check_dependencies)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.loading = LoadingOverlay(self.root)
    def _create_scrollable_canvas(self):
        
        self.canvas = tk.Canvas(self.root, bg=self.current_theme['bg_dark'], 
                               highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", 
                                     command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Modern.TFrame")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), 
                                                       window=self.scrollable_frame, 
                                                       anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    def _on_canvas_configure(self, event):
        
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    def _on_mousewheel(self, event):
        
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _init_variables(self):
        
        self.download_path_var = tk.StringVar(value=self.config.get("download_path", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.download_type_var = tk.StringVar(value=self.config.get("download_type", "video"))
        self.video_quality_var = tk.StringVar(value=self.config.get("video_quality", "best"))
        self.audio_quality_var = tk.StringVar(value=self.config.get("audio_quality", "best"))
        self.video_format_var = tk.StringVar(value=self.config.get("video_format", "mp4"))
        self.audio_format_var = tk.StringVar(value=self.config.get("audio_format", "mp3"))
        self.download_subtitles_var = tk.BooleanVar(value=self.config.get("download_subtitles", False))
        self.auto_subtitles_var = tk.BooleanVar(value=self.config.get("auto_subtitles", False))
        self.download_thumbnail_var = tk.BooleanVar(value=self.config.get("download_thumbnail", False))
        self.embed_thumbnail_var = tk.BooleanVar(value=self.config.get("embed_thumbnail", False))
        self.filename_template_var = tk.StringVar(value=self.config.get("filename_template", "%(title)s.%(ext)s"))
        self.playlist_mode_var = tk.BooleanVar(value=self.config.get("playlist_mode", False))
        self.playlist_start_var = tk.StringVar(value="1")
        self.playlist_end_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)
        self.limit_rate_var = tk.StringVar(value=self.config.get("limit_rate", ""))
        self.concurrent_fragments_var = tk.StringVar(value=str(self.config.get("concurrent_fragments", 1)))
        self.fragment_retries_var = tk.StringVar(value=str(self.config.get("fragment_retries", 10)))
        self.no_part_var = tk.BooleanVar(value=self.config.get("no_part", False))
        self.restrict_filenames_var = tk.BooleanVar(value=self.config.get("restrict_filenames", False))
        self.no_mtime_var = tk.BooleanVar(value=self.config.get("no_mtime", False))
        self.embed_metadata_var = tk.BooleanVar(value=self.config.get("embed_metadata", True))
        self.write_info_json_var = tk.BooleanVar(value=self.config.get("write_info_json", False))
        self.embed_subs_var = tk.BooleanVar(value=self.config.get("embed_subs", False))
        self.convert_subs_var = tk.StringVar(value=self.config.get("convert_subs", "srt"))
        self.playlist_reverse_var = tk.BooleanVar(value=self.config.get("playlist_reverse", False))
        self.playlist_random_var = tk.BooleanVar(value=self.config.get("playlist_random", False))
        self.cookies_from_browser_var = tk.StringVar(value=self.config.get("cookies_from_browser", "なし"))
        self.proxy_var = tk.StringVar(value=self.config.get("proxy", ""))
    def _configure_styles(self):
        
        style = ttk.Style()
        style.theme_use('clam')
        theme = self.current_theme
        style.configure("Modern.TFrame", background=theme['bg_dark'])
        style.configure("Card.TFrame", background=theme['bg_lighter'], 
                       borderwidth=1, relief="flat")
        style.configure("Modern.TLabel", 
                       background=theme['bg_dark'],
                       foreground=theme['text_primary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL))
        style.configure("Title.TLabel",
                       background=theme['bg_dark'],
                       foreground=theme['text_bright'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_TITLE, "bold"))
        style.configure("Subtitle.TLabel",
                       background=theme['bg_lighter'],
                       foreground=theme['text_secondary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_SMALL))
        style.configure("Accent.TButton",
                       background=theme['accent_primary'],
                       foreground=theme['text_bright'],
                       borderwidth=0,
                       focuscolor=theme['accent_primary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL, "bold"))
        style.map("Accent.TButton",
                 background=[('active', theme['accent_secondary']),
                           ('disabled', theme['bg_hover'])])
        style.configure("Modern.TButton",
                       background=theme['bg_hover'],
                       foreground=theme['text_primary'],
                       borderwidth=0,
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL))
        style.map("Modern.TButton",
                 background=[('active', theme['bg_lighter'])])
        style.configure("Modern.TCombobox",
                       fieldbackground=theme['bg_lighter'],
                       background=theme['bg_lighter'],
                       foreground=theme['text_primary'],
                       borderwidth=1,
                       arrowcolor=theme['text_primary'])
        style.configure("Modern.Horizontal.TProgressbar",
                       background=theme['accent_primary'],
                       troughcolor=theme['bg_lighter'],
                       borderwidth=0,
                       thickness=8)
        style.configure("Modern.TCheckbutton",
                       background=theme['bg_lighter'],
                       foreground=theme['text_primary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL))
        style.configure("Modern.TRadiobutton",
                       background=theme['bg_lighter'],
                       foreground=theme['text_primary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL))
        style.configure("Modern.TLabelframe",
                       background=theme['bg_lighter'],
                       foreground=theme['text_primary'],
                       borderwidth=1,
                       relief="flat")
        style.configure("Modern.TLabelframe.Label",
                       background=theme['bg_lighter'],
                       foreground=theme['accent_primary'],
                       font=(ThemeManager.FONT_FAMILY, ThemeManager.FONT_SIZE_NORMAL, "bold"))
    def _switch_theme(self):
        
        if self.theme_var.get() == 'dark':
            self.current_theme = ThemeManager.DARK
        else:
            self.current_theme = ThemeManager.LIGHT
        self.config.set("theme", self.theme_var.get())
        self.config.save_config()
        self._configure_styles()
        self.root.configure(bg=self.current_theme['bg_dark'])
        self.canvas.configure(bg=self.current_theme['bg_dark'])
        self._update_entry_colors()
        if hasattr(self, 'log_text'):
            self.log_text.configure(
                bg=self.current_theme['bg_darker'],
                fg=self.current_theme['text_primary'],
                insertbackground=self.current_theme['text_bright']
            )
        self._log(f"✅ テーマを{self.theme_var.get()}モードに変更しました")
    def _update_entry_colors(self):
        
        if hasattr(self, 'url_entry'):
            self.url_entry.configure(
                bg=self.current_theme['bg_darker'],
                fg=self.current_theme['text_primary'],
                insertbackground=self.current_theme['text_bright'],
                highlightbackground=self.current_theme['border'],
                highlightcolor=self.current_theme['border_focus']
            )
        for widget in self.root.winfo_children():
            self._update_widget_colors_recursive(widget)
    def _update_widget_colors_recursive(self, widget):
        
        if isinstance(widget, tk.Entry):
            widget.configure(
                bg=self.current_theme['bg_darker'],
                fg=self.current_theme['text_primary'],
                insertbackground=self.current_theme['text_bright'],
                highlightbackground=self.current_theme['border']
            )
        elif isinstance(widget, tk.Text):
            widget.configure(
                bg=self.current_theme['bg_darker'],
                fg=self.current_theme['text_primary'],
                insertbackground=self.current_theme['text_bright']
            )
        elif isinstance(widget, tk.Canvas):
            widget.configure(bg=self.current_theme['bg_dark'])
        try:
            for child in widget.winfo_children():
                self._update_widget_colors_recursive(child)
        except:
            pass
    def _open_settings_window(self):
        
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus()
            return
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("設定")
        self.settings_window.geometry("500x300")
        self.settings_window.resizable(False, False)
        self.settings_window.configure(bg=self.current_theme['bg_dark'])
        settings_frame = ttk.Frame(self.settings_window, padding="20", style="Modern.TFrame")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(settings_frame, text="⚙️ アプリケーション設定", 
                               style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        theme_card = ttk.LabelFrame(settings_frame, text="テーマ", 
                                   padding="15", style="Modern.TLabelframe")
        theme_card.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(theme_card, text="外観テーマを選択:", 
                 style="Modern.TLabel").pack(anchor=tk.W, pady=(0, 10))
        theme_buttons_frame = ttk.Frame(theme_card, style="Modern.TFrame")
        theme_buttons_frame.pack(fill=tk.X)
        ttk.Radiobutton(theme_buttons_frame, text="☀️ ライトモード", 
                       variable=self.theme_var, 
                       value="light", 
                       command=self._switch_theme,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(theme_buttons_frame, text="🌙 ダークモード", 
                       variable=self.theme_var, 
                       value="dark", 
                       command=self._switch_theme,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT)
        info_label = ttk.Label(theme_card, 
                              text="※ テーマの変更はアプリケーション再起動後に反映されます", 
                              style="Subtitle.TLabel")
        info_label.pack(anchor=tk.W, pady=(10, 0))
        close_btn = ttk.Button(settings_frame, text="閉じる", 
                              command=self.settings_window.destroy,
                              style="Accent.TButton")
        close_btn.pack(pady=(10, 0), ipady=8, ipadx=20)
    def _check_dependencies(self):
        
        def check():
            try:
                results = self.dep_manager.ensure_dependencies(
                    progress_callback=lambda msg: self.root.after(0, lambda: self._log(msg))
                )
                if results['ytdlp']['installed']:
                    self.root.after(0, lambda: self._log("✅ yt-dlp: 利用可能"))
                else:
                    self.root.after(0, lambda: self._log("❌ yt-dlp: インストールに失敗しました"))
                if results['ffmpeg']['installed']:
                    self.root.after(0, lambda: self._log("✅ FFmpeg: 利用可能"))
                else:
                    self.root.after(0, lambda: self._log("⚠️ FFmpeg: インストールに失敗しました（一部機能が制限されます）"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ 依存関係の確認エラー: {str(e)}"))
        threading.Thread(target=check, daemon=True).start()
    def _create_widgets(self):
        
        self.scrollable_frame.columnconfigure(0, weight=1)
        main_frame = ttk.Frame(self.scrollable_frame, padding="20", style="Modern.TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        header_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        title_label = ttk.Label(header_frame, text="YTGrabs", 
                               style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        theme_frame = ttk.Frame(header_frame, style="Modern.TFrame")
        theme_frame.pack(side=tk.RIGHT)
        ttk.Label(theme_frame, text="テーマ:", style="Modern.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(theme_frame, text="☀️ ライト", variable=self.theme_var, 
                       value="light", command=self._switch_theme,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(theme_frame, text="🌙 ダーク", variable=self.theme_var, 
                       value="dark", command=self._switch_theme,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=5)
        url_card = ttk.LabelFrame(main_frame, text="URL", padding="15", 
                                 style="Modern.TLabelframe")
        url_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        url_card.columnconfigure(0, weight=1)
        url_frame = ttk.Frame(url_card, style="Modern.TFrame")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        url_frame.columnconfigure(0, weight=1)
        self.url_entry = tk.Entry(url_frame, 
                                  bg=self.current_theme['bg_darker'],
                                  fg=self.current_theme['text_primary'],
                                  insertbackground=self.current_theme['text_bright'],
                                  font=(ThemeManager.FONT_FAMILY, 11),
                                  relief="flat",
                                  borderwidth=2,
                                  highlightthickness=1,
                                  highlightbackground=self.current_theme['border'],
                                  highlightcolor=self.current_theme['border_focus'])
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), ipady=8)
        info_btn = ttk.Button(url_frame, text="📋 動画情報", 
                             command=self._get_video_info,
                             style="Modern.TButton")
        info_btn.grid(row=0, column=1, padx=(0, 10))
        playlist_btn = ttk.Button(url_frame, text="📚 プレイリスト選択", 
                                 command=self._show_playlist_selector,
                                 style="Modern.TButton")
        playlist_btn.grid(row=0, column=2)
        settings_card = ttk.LabelFrame(main_frame, text="ダウンロード設定", 
                                      padding="15", style="Modern.TLabelframe")
        settings_card.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        settings_card.columnconfigure(1, weight=1)
        row = 0
        ttk.Label(settings_card, text="タイプ", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.download_type_var = tk.StringVar(value="video")
        type_frame = ttk.Frame(settings_card, style="Modern.TFrame")
        type_frame.grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Radiobutton(type_frame, text="🎬 動画", variable=self.download_type_var, 
                       value="video", command=self._on_type_change,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(type_frame, text="🎵 音声のみ", variable=self.download_type_var, 
                       value="audio", command=self._on_type_change,
                       style="Modern.TRadiobutton").pack(side=tk.LEFT)
        row += 1
        ttk.Label(settings_card, text="動画品質", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.video_quality_var = tk.StringVar(value="1080p")
        self.video_quality_combo = ttk.Combobox(settings_card, 
                                               textvariable=self.video_quality_var,
                                               values=["4K", "1080p", "720p", "480p", "360p"],
                                               state="readonly", width=20,
                                               style="Modern.TCombobox")
        self.video_quality_combo.grid(row=row, column=1, sticky=tk.W, pady=8)
        row += 1
        ttk.Label(settings_card, text="動画フォーマット", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.video_format_var = tk.StringVar(value="mp4")
        self.video_format_combo = ttk.Combobox(settings_card, 
                                              textvariable=self.video_format_var,
                                              values=["mp4", "webm", "mkv"],
                                              state="readonly", width=20,
                                              style="Modern.TCombobox")
        self.video_format_combo.grid(row=row, column=1, sticky=tk.W, pady=8)
        row += 1
        ttk.Label(settings_card, text="音声品質", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.audio_quality_var = tk.StringVar(value="最高")
        self.audio_quality_combo = ttk.Combobox(settings_card, 
                                               textvariable=self.audio_quality_var,
                                               values=["最高", "高", "中", "低"],
                                               state="readonly", width=20,
                                               style="Modern.TCombobox")
        self.audio_quality_combo.grid(row=row, column=1, sticky=tk.W, pady=8)
        row += 1
        ttk.Label(settings_card, text="音声フォーマット", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.audio_format_var = tk.StringVar(value="mp3")
        self.audio_format_combo = ttk.Combobox(settings_card, 
                                              textvariable=self.audio_format_var,
                                              values=["mp3", "m4a", "opus"],
                                              state="readonly", width=20,
                                              style="Modern.TCombobox")
        self.audio_format_combo.grid(row=row, column=1, sticky=tk.W, pady=8)
        row += 1
        ttk.Label(settings_card, text="保存先", style="Modern.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        path_frame = ttk.Frame(settings_card, style="Modern.TFrame")
        path_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=8)
        path_frame.columnconfigure(0, weight=1)
        self.download_path_var = tk.StringVar()
        path_entry = tk.Entry(path_frame,
                             textvariable=self.download_path_var,
                             bg=self.current_theme['bg_darker'],
                             fg=self.current_theme['text_primary'],
                             insertbackground=self.current_theme['text_bright'],
                             font=(ThemeManager.FONT_FAMILY, 10),
                             relief="flat",
                             borderwidth=2,
                             highlightthickness=1,
                             highlightbackground=self.current_theme['border'],
                             highlightcolor=self.current_theme['border_focus'])
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), ipady=6)
        browse_btn = ttk.Button(path_frame, text="📁 参照", 
                               command=self._browse_folder,
                               style="Modern.TButton")
        browse_btn.grid(row=0, column=1)
        self.options_collapsible = CollapsibleFrame(main_frame, text="詳細オプション", 
                                                    style="Modern.TFrame")
        self.options_collapsible.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        options_card = self.options_collapsible.get_content_frame()
        options_card.configure(style="Card.TFrame", padding="15")
        options_card.columnconfigure(0, weight=1)
        options_card.columnconfigure(1, weight=1)
        self.download_subtitles_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="📝 字幕をダウンロード", 
                       variable=self.download_subtitles_var,
                       command=self._on_subtitle_change,
                       style="Modern.TCheckbutton").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.auto_subtitles_var = tk.BooleanVar(value=False)
        self.auto_subtitles_check = ttk.Checkbutton(options_card, 
                                                    text="🤖 自動生成字幕を含む", 
                                                    variable=self.auto_subtitles_var,
                                                    state=tk.DISABLED,
                                                    style="Modern.TCheckbutton")
        self.auto_subtitles_check.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.download_thumbnail_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="🖼️ サムネイルをダウンロード", 
                       variable=self.download_thumbnail_var,
                       style="Modern.TCheckbutton").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.embed_thumbnail_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="📎 サムネイルを埋め込む", 
                       variable=self.embed_thumbnail_var,
                       style="Modern.TCheckbutton").grid(
            row=1, column=1, sticky=tk.W, pady=5)
        self.playlist_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="📚 プレイリストモード", 
                       variable=self.playlist_mode_var,
                       command=self._on_playlist_change,
                       style="Modern.TCheckbutton").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        playlist_range_frame = ttk.Frame(options_card, style="Modern.TFrame")
        playlist_range_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(playlist_range_frame, text="範囲:", style="Modern.TLabel").pack(
            side=tk.LEFT, padx=(0, 10))
        self.playlist_start_var = tk.StringVar(value="1")
        self.playlist_start_entry = tk.Entry(playlist_range_frame,
                                            textvariable=self.playlist_start_var,
                                            width=8, state=tk.DISABLED,
                                            bg=self.current_theme['bg_darker'],
                                            fg=self.current_theme['text_primary'],
                                            insertbackground=self.current_theme['text_bright'],
                                            font=(ThemeManager.FONT_FAMILY, 10),
                                            relief="flat",
                                            borderwidth=2,
                                            highlightthickness=1,
                                            highlightbackground=self.current_theme['border'])
        self.playlist_start_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(playlist_range_frame, text="〜", style="Modern.TLabel").pack(
            side=tk.LEFT, padx=(0, 10))
        self.playlist_end_var = tk.StringVar(value="")
        self.playlist_end_entry = tk.Entry(playlist_range_frame,
                                          textvariable=self.playlist_end_var,
                                          width=8, state=tk.DISABLED,
                                          bg=self.current_theme['bg_darker'],
                                          fg=self.current_theme['text_primary'],
                                          insertbackground=self.current_theme['text_bright'],
                                          font=(ThemeManager.FONT_FAMILY, 10),
                                          relief="flat",
                                          borderwidth=2,
                                          highlightthickness=1,
                                          highlightbackground=self.current_theme['border'])
        self.playlist_end_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(playlist_range_frame, text="(空欄で最後まで)", 
                 style="Subtitle.TLabel").pack(side=tk.LEFT)
        template_frame = ttk.Frame(options_card, style="Modern.TFrame")
        template_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        template_frame.columnconfigure(1, weight=1)
        ttk.Label(template_frame, text="ファイル名:", style="Modern.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.filename_template_var = tk.StringVar(value="%(title)s.%(ext)s")
        template_entry = tk.Entry(template_frame,
                                 textvariable=self.filename_template_var,
                                 bg=self.current_theme['bg_darker'],
                                 fg=self.current_theme['text_primary'],
                                 insertbackground=self.current_theme['text_bright'],
                                 font=(ThemeManager.FONT_FAMILY, 10),
                                 relief="flat",
                                 borderwidth=2,
                                 highlightthickness=1,
                                 highlightbackground=self.current_theme['border'],
                                 highlightcolor=self.current_theme['border_focus'])
        template_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), ipady=6)
        ttk.Separator(options_card, orient='horizontal').grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        ttk.Label(options_card, text="📊 メタデータ", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        self.embed_metadata_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="メタデータを埋め込む", 
                       variable=self.embed_metadata_var,
                       style="Modern.TCheckbutton").grid(
            row=7, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.write_info_json_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="情報JSONを保存", 
                       variable=self.write_info_json_var,
                       style="Modern.TCheckbutton").grid(
            row=7, column=1, sticky=tk.W, pady=5)
        ttk.Label(options_card, text="💬 字幕詳細", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.embed_subs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="字幕を埋め込む", 
                       variable=self.embed_subs_var,
                       style="Modern.TCheckbutton").grid(
            row=9, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        sub_convert_frame = ttk.Frame(options_card, style="Modern.TFrame")
        sub_convert_frame.grid(row=9, column=1, sticky=tk.W, pady=5)
        ttk.Label(sub_convert_frame, text="変換:", style="Modern.TLabel").pack(
            side=tk.LEFT, padx=(0, 5))
        self.convert_subs_var = tk.StringVar(value="なし")
        convert_subs_combo = ttk.Combobox(sub_convert_frame, 
                                         textvariable=self.convert_subs_var,
                                         values=["なし", "srt", "ass", "vtt"],
                                         state="readonly", width=10,
                                         style="Modern.TCombobox")
        convert_subs_combo.pack(side=tk.LEFT)
        ttk.Label(options_card, text="⚡ ダウンロード制御", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=10, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        speed_frame = ttk.Frame(options_card, style="Modern.TFrame")
        speed_frame.grid(row=11, column=0, sticky=tk.W, pady=5)
        ttk.Label(speed_frame, text="速度制限:", style="Modern.TLabel").pack(
            side=tk.LEFT, padx=(0, 5))
        self.limit_rate_var = tk.StringVar(value="")
        limit_rate_entry = tk.Entry(speed_frame,
                                    textvariable=self.limit_rate_var,
                                    width=10,
                                    bg=self.current_theme['bg_darker'],
                                    fg=self.current_theme['text_primary'],
                                    font=(ThemeManager.FONT_FAMILY, 10),
                                    relief="flat",
                                    borderwidth=2,
                                    highlightthickness=1,
                                    highlightbackground=self.current_theme['border'])
        limit_rate_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(speed_frame, text="(例: 1M, 500K)", 
                 style="Subtitle.TLabel").pack(side=tk.LEFT)
        conn_frame = ttk.Frame(options_card, style="Modern.TFrame")
        conn_frame.grid(row=11, column=1, sticky=tk.W, pady=5)
        ttk.Label(conn_frame, text="同時接続:", style="Modern.TLabel").pack(
            side=tk.LEFT, padx=(0, 5))
        self.concurrent_fragments_var = tk.StringVar(value="1")
        concurrent_entry = tk.Entry(conn_frame,
                                   textvariable=self.concurrent_fragments_var,
                                   width=8,
                                   bg=self.current_theme['bg_darker'],
                                   fg=self.current_theme['text_primary'],
                                   font=(ThemeManager.FONT_FAMILY, 10),
                                   relief="flat",
                                   borderwidth=2,
                                   highlightthickness=1,
                                   highlightbackground=self.current_theme['border'])
        concurrent_entry.pack(side=tk.LEFT)
        self.fragment_retries_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="無限再試行", 
                       variable=self.fragment_retries_var,
                       style="Modern.TCheckbutton").grid(
            row=12, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.no_part_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="一時ファイルなし", 
                       variable=self.no_part_var,
                       style="Modern.TCheckbutton").grid(
            row=12, column=1, sticky=tk.W, pady=5)
        ttk.Label(options_card, text="📚 プレイリスト詳細", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=13, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.playlist_reverse_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="逆順でダウンロード", 
                       variable=self.playlist_reverse_var,
                       style="Modern.TCheckbutton").grid(
            row=14, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.playlist_random_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="ランダム順", 
                       variable=self.playlist_random_var,
                       style="Modern.TCheckbutton").grid(
            row=14, column=1, sticky=tk.W, pady=5)
        ttk.Label(options_card, text="🔐 認証・プロキシ", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=15, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        cookie_frame = ttk.Frame(options_card, style="Modern.TFrame")
        cookie_frame.grid(row=16, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        cookie_frame.columnconfigure(1, weight=1)
        ttk.Label(cookie_frame, text="Cookie:", style="Modern.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.cookies_from_browser_var = tk.StringVar(value="なし")
        cookies_combo = ttk.Combobox(cookie_frame, 
                                    textvariable=self.cookies_from_browser_var,
                                    values=["なし", "chrome", "firefox", "edge", "safari", "opera"],
                                    state="readonly", width=15,
                                    style="Modern.TCombobox")
        cookies_combo.grid(row=0, column=1, sticky=tk.W)
        proxy_frame = ttk.Frame(options_card, style="Modern.TFrame")
        proxy_frame.grid(row=17, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        proxy_frame.columnconfigure(1, weight=1)
        ttk.Label(proxy_frame, text="プロキシ:", style="Modern.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.proxy_var = tk.StringVar(value="")
        proxy_entry = tk.Entry(proxy_frame,
                              textvariable=self.proxy_var,
                              bg=self.current_theme['bg_darker'],
                              fg=self.current_theme['text_primary'],
                              font=(ThemeManager.FONT_FAMILY, 10),
                              relief="flat",
                              borderwidth=2,
                              highlightthickness=1,
                              highlightbackground=self.current_theme['border'])
        proxy_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), ipady=6)
        ttk.Label(options_card, text="🛠️ その他", 
                 style="Modern.TLabel", font=(ThemeManager.FONT_FAMILY, 10, "bold")).grid(
            row=18, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.restrict_filenames_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="安全なファイル名", 
                       variable=self.restrict_filenames_var,
                       style="Modern.TCheckbutton").grid(
            row=19, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.no_mtime_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="タイムスタンプ保持しない", 
                       variable=self.no_mtime_var,
                       style="Modern.TCheckbutton").grid(
            row=19, column=1, sticky=tk.W, pady=5)
        progress_card = ttk.LabelFrame(main_frame, text="進捗", padding="15", 
                                      style="Modern.TLabelframe")
        progress_card.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_card.columnconfigure(0, weight=1)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_card, 
                                           variable=self.progress_var, 
                                           maximum=100, mode='determinate',
                                           style="Modern.Horizontal.TProgressbar")
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_label = ttk.Label(progress_card, text="⏸️ 待機中...", 
                                     style="Modern.TLabel")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        log_card = ttk.LabelFrame(main_frame, text="ログ", padding="15", 
                                 style="Modern.TLabelframe")
        log_card.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        log_card.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_card, height=8, wrap=tk.WORD,
                               bg=self.current_theme['bg_darker'],
                               fg=self.current_theme['text_primary'],
                               insertbackground=self.current_theme['text_bright'],
                               font=(ThemeManager.FONT_FAMILY, 9),
                               relief="flat",
                               borderwidth=0,
                               padx=10, pady=10)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar = tk.Scrollbar(log_card, command=self.log_text.yview,
                                bg=self.current_theme['bg_lighter'],
                                troughcolor=self.current_theme['bg_darker'],
                                activebackground=self.current_theme['accent_primary'])
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        button_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        button_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        self.download_btn = ttk.Button(button_frame, text="⬇️ ダウンロード", 
                                       command=self._start_download,
                                       style="Accent.TButton")
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=20)
        self.cancel_btn = ttk.Button(button_frame, text="⏹️ キャンセル", 
                                     command=self._cancel_download, 
                                     state=tk.DISABLED,
                                     style="Modern.TButton")
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)
        ttk.Button(button_frame, text="📜 履歴", 
                  command=self._show_history,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)
        ttk.Button(button_frame, text="💾 設定を保存", 
                  command=self._save_settings,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)
        ttk.Button(button_frame, text="🗑️ ログクリア", 
                  command=self._clear_log,
                  style="Modern.TButton").pack(side=tk.LEFT, ipady=8, ipadx=15)
        self._on_type_change()
    def _on_type_change(self):
        
        is_video = self.download_type_var.get() == "video"
        state = "readonly" if is_video else "disabled"
        self.video_quality_combo.config(state=state)
        self.video_format_combo.config(state=state)
        state = "disabled" if is_video else "readonly"
        self.audio_quality_combo.config(state=state)
        self.audio_format_combo.config(state=state)
    def _on_subtitle_change(self):
        
        state = tk.NORMAL if self.download_subtitles_var.get() else tk.DISABLED
        self.auto_subtitles_check.config(state=state)
    def _on_playlist_change(self):
        
        state = tk.NORMAL if self.playlist_mode_var.get() else tk.DISABLED
        self.playlist_start_entry.config(state=state)
        self.playlist_end_entry.config(state=state)
    def _browse_folder(self):
        
        folder = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if folder:
            self.download_path_var.set(folder)
    def _log(self, message: str):
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    def _clear_log(self):
        
        self.log_text.delete(1.0, tk.END)
    def _load_settings(self):
        
        self.download_path_var.set(self.config.get("download_path"))
        self.download_type_var.set(self.config.get("download_type"))
        self.video_quality_var.set(self.config.get("video_quality"))
        self.audio_quality_var.set(self.config.get("audio_quality"))
        self.video_format_var.set(self.config.get("video_format"))
        self.audio_format_var.set(self.config.get("audio_format"))
        self.download_subtitles_var.set(self.config.get("download_subtitles"))
        self.auto_subtitles_var.set(self.config.get("auto_subtitles"))
        self.download_thumbnail_var.set(self.config.get("download_thumbnail"))
        self.embed_thumbnail_var.set(self.config.get("embed_thumbnail"))
        self.filename_template_var.set(self.config.get("filename_template"))
        self.playlist_mode_var.set(self.config.get("playlist_mode"))
        self._on_type_change()
        self._on_subtitle_change()
        self._on_playlist_change()
    def _save_settings(self):
        
        self.config.set("download_path", self.download_path_var.get())
        self.config.set("download_type", self.download_type_var.get())
        self.config.set("video_quality", self.video_quality_var.get())
        self.config.set("audio_quality", self.audio_quality_var.get())
        self.config.set("video_format", self.video_format_var.get())
        self.config.set("audio_format", self.audio_format_var.get())
        self.config.set("download_subtitles", self.download_subtitles_var.get())
        self.config.set("auto_subtitles", self.auto_subtitles_var.get())
        self.config.set("download_thumbnail", self.download_thumbnail_var.get())
        self.config.set("embed_thumbnail", self.embed_thumbnail_var.get())
        self.config.set("filename_template", self.filename_template_var.get())
        self.config.set("playlist_mode", self.playlist_mode_var.get())
        if self.config.save_config():
            self._log("✅ 設定を保存しました")
        self.status_label.config(text="⏸️ 待機中...")
    def _get_video_info(self):
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "URLを入力してください")
            return
        self._log(f"🔄 動画情報を取得中: {url}")
        self.loading.text = "動画情報を取得中..."
        self.loading.show()
        def get_info():
            try:
                self.downloader = YouTubeDownloader()
                info = self.downloader.get_video_info(url)
                self.root.after(0, lambda: self._show_video_info(info))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ エラー: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("エラー", str(e)))
            finally:
                self.root.after(0, self.loading.hide)
        threading.Thread(target=get_info, daemon=True).start()
    def _show_video_info(self, info: dict):
        
        if info['type'] == 'playlist':
            message = f"プレイリスト: {info['title']}\n"
            message += f"動画数: {info['count']}\n\n"
            message += "動画リスト:\n"
            for i, entry in enumerate(info['entries'][:10], 1):
                duration = entry['duration']
                minutes = duration // 60
                seconds = duration % 60
                message += f"{i}. {entry['title']} ({minutes}:{seconds:02d})\n"
            if info['count'] > 10:
                message += f"\n... 他 {info['count'] - 10} 件"
            self._log(f"📚 プレイリスト情報を取得: {info['title']} ({info['count']}件)")
        else:
            duration = info['duration']
            minutes = duration // 60
            seconds = duration % 60
            message = f"タイトル: {info['title']}\n"
            message += f"投稿者: {info['uploader']}\n"
            message += f"再生時間: {minutes}:{seconds:02d}\n"
            message += f"再生回数: {info.get('view_count', 'N/A'):,}\n"
            self._log(f"🎬 動画情報を取得: {info['title']}")
        messagebox.showinfo("動画情報", message)
    def _progress_callback(self, progress: dict):
        
        percent = progress.get('percent', 0)
        speed = progress.get('speed', 0)
        eta = progress.get('eta', 0)
        self.root.after(0, lambda: self.progress_var.set(percent))
        speed_mb = speed / 1024 / 1024 if speed else 0
        status = f"⬇️ ダウンロード中... {percent:.1f}% | 速度: {speed_mb:.2f} MB/s"
        if eta:
            eta_int = int(eta)  
            if eta_int >= 60:
                minutes = eta_int // 60
                seconds = eta_int % 60
                status += f" | 残り: {minutes}分{seconds}秒"
            else:
                status += f" | 残り: {eta_int}秒"
        self.root.after(0, lambda: self.status_label.config(text=status))
    def _start_download(self):
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "URLを入力してください")
            return
        if self.is_downloading:
            messagebox.showwarning("警告", "既にダウンロード中です")
            return
        options = {
            'download_path': self.download_path_var.get(),
            'download_type': self.download_type_var.get(),
            'video_quality': self.video_quality_var.get(),
            'audio_quality': self.audio_quality_var.get(),
            'video_format': self.video_format_var.get(),
            'audio_format': self.audio_format_var.get(),
            'download_subtitles': self.download_subtitles_var.get(),
            'auto_subtitles': self.auto_subtitles_var.get(),
            'subtitle_languages': ['ja', 'en'],
            'download_thumbnail': self.download_thumbnail_var.get(),
            'embed_thumbnail': self.embed_thumbnail_var.get(),
            'filename_template': self.filename_template_var.get(),
            'playlist_mode': self.playlist_mode_var.get(),
            'limit_rate': self.limit_rate_var.get(),
            'concurrent_fragments': self.concurrent_fragments_var.get(),
            'fragment_retries': self.fragment_retries_var.get(),
            'no_part': self.no_part_var.get(),
            'restrict_filenames': self.restrict_filenames_var.get(),
            'no_mtime': self.no_mtime_var.get(),
            'embed_metadata': self.embed_metadata_var.get(),
            'write_info_json': self.write_info_json_var.get(),
            'embed_subs': self.embed_subs_var.get(),
            'convert_subs': self.convert_subs_var.get(),
            'playlist_reverse': self.playlist_reverse_var.get(),
            'playlist_random': self.playlist_random_var.get(),
            'cookies_from_browser': self.cookies_from_browser_var.get(),
            'proxy': self.proxy_var.get(),
        }
        if self.playlist_mode_var.get():
            if hasattr(self, 'selected_playlist_items') and self.selected_playlist_items:
                options['playlist_items'] = self.selected_playlist_items
                self.selected_playlist_items = None
                self.playlist_start_entry.config(state=tk.NORMAL)
                self.playlist_start_var.set("1")
            else:
                try:
                    start = int(self.playlist_start_var.get()) if self.playlist_start_var.get() else 1
                    end = int(self.playlist_end_var.get()) if self.playlist_end_var.get() else None
                    options['playlist_start'] = start
                    options['playlist_end'] = end
                except ValueError:
                    if self.playlist_start_var.get() == "選択済み":
                         pass 
                    else:
                        messagebox.showerror("エラー", "プレイリスト範囲は数値で入力してください")
                        return
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self._log(f"🚀 ダウンロード開始: {url}")
        self.status_label.config(text="⏳ ダウンロード準備中...")
        self.loading.text = "ダウンロード準備中..."
        self.loading.show()
        def download():
            try:
                self.downloader = YouTubeDownloader(progress_callback=self._progress_callback)
                self.root.after(0, self.loading.hide)
                result = self.downloader.download(url, options)
                self.root.after(0, lambda: self._download_complete(result, url, options))
            except Exception as e:
                self.root.after(0, self.loading.hide)
                self.root.after(0, lambda: self._download_error(str(e)))
        threading.Thread(target=download, daemon=True).start()
    def _cancel_download(self):
        
        if self.downloader:
            self.downloader.cancel()
            self._log("⏹️ ダウンロードをキャンセルしました")
    def _download_complete(self, result: dict, url: str, options: dict):
        
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if result['success']:
            if result['type'] == 'playlist':
                self._log(f"✅ プレイリストのダウンロードが完了: {result['title']}")
                self._log(f"📊 ダウンロード数: {len(result['files'])}件")
                if result['files']:
                    first_file = result['files'][0]
                    self.config.add_to_history(
                        url, result['title'], first_file['file_path'],
                        options['download_type'], 
                        f"Playlist ({len(result['files'])} files)"
                    )
                messagebox.showinfo("完了", f"プレイリストのダウンロードが完了しました\n{len(result['files'])}件")
            else:
                self._log(f"✅ ダウンロード完了: {result['title']}")
                self._log(f"📁 保存先: {result['file_path']}")
                quality = options.get('video_quality' if options['download_type'] == 'video' else 'audio_quality')
                self.config.add_to_history(
                    url, result['title'], result['file_path'],
                    options['download_type'], quality
                )
                messagebox.showinfo("完了", f"ダウンロードが完了しました\n{result['title']}")
            self.status_label.config(text="✅ 完了")
            self.progress_var.set(100)
        else:
            self._log(f"❌ エラー: {result['error']}")
            self.status_label.config(text="❌ エラー")
            messagebox.showerror("エラー", result['error'])
    def _download_error(self, error: str):
        
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_label.config(text="❌ エラー")
        self._log(f"❌ エラー: {error}")
        messagebox.showerror("エラー", error)
    def _show_history(self):
        
        history = self.config.get_history()
        if not history:
            messagebox.showinfo("履歴", "ダウンロード履歴はありません")
            return
        history_window = tk.Toplevel(self.root)
        history_window.title("ダウンロード履歴")
        history_window.geometry("800x500")
        history_window.configure(bg=self.current_theme['bg_dark'])
        tree_frame = ttk.Frame(history_window, padding="20", style="Modern.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style()
        style.configure("Modern.Treeview",
                       background=self.current_theme['bg_lighter'],
                       foreground=self.current_theme['text_primary'],
                       fieldbackground=self.current_theme['bg_lighter'],
                       font=(ThemeManager.FONT_FAMILY, 9))
        style.configure("Modern.Treeview.Heading",
                       background=self.current_theme['bg_hover'],
                       foreground=self.current_theme['text_bright'],
                       font=(ThemeManager.FONT_FAMILY, 10, "bold"))
        tree = ttk.Treeview(tree_frame, columns=("title", "type", "quality", "date"), 
                           show="headings", height=15, style="Modern.Treeview")
        tree.heading("title", text="タイトル")
        tree.heading("type", text="タイプ")
        tree.heading("quality", text="品質")
        tree.heading("date", text="日時")
        tree.column("title", width=350)
        tree.column("type", width=100)
        tree.column("quality", width=120)
        tree.column("date", width=180)
        scrollbar = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview,
                                bg=self.current_theme['bg_lighter'],
                                troughcolor=self.current_theme['bg_darker'],
                                activebackground=self.current_theme['accent_primary'])
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            tree.insert("", tk.END, values=(
                entry['title'],
                entry['download_type'],
                entry['quality'],
                timestamp
            ))
        button_frame = ttk.Frame(history_window, padding="20", style="Modern.TFrame")
        button_frame.pack(fill=tk.X)
        def clear_history():
            if messagebox.askyesno("確認", "履歴をクリアしますか?"):
                self.config.clear_history()
                history_window.destroy()
                messagebox.showinfo("完了", "履歴をクリアしました")
        ttk.Button(button_frame, text="🗑️ 履歴をクリア", 
                  command=clear_history,
                  style="Modern.TButton").pack(side=tk.LEFT, ipady=6, ipadx=15)
        ttk.Button(button_frame, text="✖️ 閉じる", 
                  command=history_window.destroy,
                  style="Modern.TButton").pack(side=tk.RIGHT, ipady=6, ipadx=15)
    def _start_download(self):
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "URLを入力してください")
            return
        if self.is_downloading:
            messagebox.showwarning("警告", "既にダウンロード中です")
            return
        options = {
            'download_path': self.download_path_var.get(),
            'download_type': self.download_type_var.get(),
            'video_quality': self.video_quality_var.get(),
            'audio_quality': self.audio_quality_var.get(),
            'video_format': self.video_format_var.get(),
            'audio_format': self.audio_format_var.get(),
            'download_subtitles': self.download_subtitles_var.get(),
            'auto_subtitles': self.auto_subtitles_var.get(),
            'subtitle_languages': ['ja', 'en'],
            'download_thumbnail': self.download_thumbnail_var.get(),
            'embed_thumbnail': self.embed_thumbnail_var.get(),
            'filename_template': self.filename_template_var.get(),
            'playlist_mode': self.playlist_mode_var.get(),
        }
        if self.playlist_mode_var.get():
            try:
                start = int(self.playlist_start_var.get()) if self.playlist_start_var.get() else 1
                end = int(self.playlist_end_var.get()) if self.playlist_end_var.get() else None
                options['playlist_start'] = start
                options['playlist_end'] = end
            except ValueError:
                messagebox.showerror("エラー", "プレイリスト範囲は数値で入力してください")
                return
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self._log(f"🚀 ダウンロード開始: {url}")
        self.status_label.config(text="⏳ ダウンロード準備中...")
        def download():
            try:
                self.downloader = YouTubeDownloader(progress_callback=self._progress_callback)
                result = self.downloader.download(url, options)
                self.root.after(0, lambda: self._download_complete(result, url, options))
            except Exception as e:
                self.root.after(0, lambda: self._download_error(str(e)))
        threading.Thread(target=download, daemon=True).start()
    def _cancel_download(self):
        
        if self.downloader:
            self.downloader.cancel()
            self._log("⏹️ ダウンロードをキャンセルしました")
    def _download_complete(self, result: dict, url: str, options: dict):
        
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if result['success']:
            if result['type'] == 'playlist':
                self._log(f"✅ プレイリストのダウンロードが完了: {result['title']}")
                self._log(f"📊 ダウンロード数: {len(result['files'])}件")
                if result['files']:
                    first_file = result['files'][0]
                    self.config.add_to_history(
                        url, result['title'], first_file['file_path'],
                        options['download_type'], 
                        f"Playlist ({len(result['files'])} files)"
                    )
                messagebox.showinfo("完了", f"プレイリストのダウンロードが完了しました\n{len(result['files'])}件")
            else:
                self._log(f"✅ ダウンロード完了: {result['title']}")
                self._log(f"📁 保存先: {result['file_path']}")
                quality = options.get('video_quality' if options['download_type'] == 'video' else 'audio_quality')
                self.config.add_to_history(
                    url, result['title'], result['file_path'],
                    options['download_type'], quality
                )
                messagebox.showinfo("完了", f"ダウンロードが完了しました\n{result['title']}")
            self.status_label.config(text="✅ 完了")
            self.progress_var.set(100)
        else:
            self._log(f"❌ エラー: {result['error']}")
            self.status_label.config(text="❌ エラー")
            messagebox.showerror("エラー", result['error'])
    def _download_error(self, error: str):
        
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_label.config(text="❌ エラー")
        self._log(f"❌ エラー: {error}")
        messagebox.showerror("エラー", error)
    def _show_history(self):
        
        history = self.config.get_history()
        if not history:
            messagebox.showinfo("履歴", "ダウンロード履歴はありません")
            return
        history_window = tk.Toplevel(self.root)
        history_window.title("ダウンロード履歴")
        history_window.geometry("800x500")
        history_window.configure(bg=self.current_theme['bg_dark'])
        tree_frame = ttk.Frame(history_window, padding="20", style="Modern.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style()
        style.configure("Modern.Treeview",
                       background=self.current_theme['bg_lighter'],
                       foreground=self.current_theme['text_primary'],
                       fieldbackground=self.current_theme['bg_lighter'],
                       font=(ThemeManager.FONT_FAMILY, 9))
        style.configure("Modern.Treeview.Heading",
                       background=self.current_theme['bg_hover'],
                       foreground=self.current_theme['text_bright'],
                       font=(ThemeManager.FONT_FAMILY, 10, "bold"))
        tree = ttk.Treeview(tree_frame, columns=("title", "type", "quality", "date"), 
                           show="headings", height=15, style="Modern.Treeview")
        tree.heading("title", text="タイトル")
        tree.heading("type", text="タイプ")
        tree.heading("quality", text="品質")
        tree.heading("date", text="日時")
        tree.column("title", width=350)
        tree.column("type", width=100)
        tree.column("quality", width=120)
        tree.column("date", width=180)
        scrollbar = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview,
                                bg=self.current_theme['bg_lighter'],
                                troughcolor=self.current_theme['bg_darker'],
                                activebackground=self.current_theme['accent_primary'])
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            tree.insert("", tk.END, values=(
                entry['title'],
                entry['download_type'],
                entry['quality'],
                timestamp
            ))
        button_frame = ttk.Frame(history_window, padding="20", style="Modern.TFrame")
        button_frame.pack(fill=tk.X)
        def clear_history():
            if messagebox.askyesno("確認", "履歴をクリアしますか?"):
                self.config.clear_history()
                history_window.destroy()
                messagebox.showinfo("完了", "履歴をクリアしました")
        ttk.Button(button_frame, text="🗑️ 履歴をクリア", 
                  command=clear_history,
                  style="Modern.TButton").pack(side=tk.LEFT, ipady=6, ipadx=15)
        ttk.Button(button_frame, text="✖️ 閉じる", 
                  command=history_window.destroy,
                  style="Modern.TButton").pack(side=tk.RIGHT, ipady=6, ipadx=15)
    def _show_playlist_selector(self):
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "URLを入力してください")
            return
        self._log("🔄 プレイリスト情報を取得中...")
        self.loading.text = "プレイリスト情報を取得中..."
        self.loading.show()
        def fetch_info():
            try:
                import subprocess
                import json
                if getattr(sys, 'frozen', False):
                    app_dir = os.path.dirname(sys.executable)
                else:
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                ytdlp_path = os.path.join(app_dir, "dependencies", "yt-dlp.exe")
                if not os.path.exists(ytdlp_path):
                    ytdlp_path = "yt-dlp"
                cmd = [
                    ytdlp_path, 
                    "--flat-playlist", 
                    "--dump-single-json",
                    url
                ]
                proxy = self.proxy_var.get()
                if proxy:
                    cmd.extend(["--proxy", proxy])
                cookies = self.cookies_from_browser_var.get()
                if cookies and cookies != "なし":
                    cmd.extend(["--cookies-from-browser", cookies])
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    errors='ignore',
                    startupinfo=startupinfo
                )
                if result.returncode != 0:
                    raise Exception(result.stderr)
                info = json.loads(result.stdout)
                if 'entries' not in info:
                    raise Exception("プレイリストが見つかりませんでした")
                self.root.after(0, lambda: self._show_selection_dialog(info))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ エラー: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("エラー", f"プレイリスト情報の取得に失敗しました:\n{str(e)}"))
            finally:
                self.root.after(0, self.loading.hide)
        threading.Thread(target=fetch_info, daemon=True).start()
    def _show_selection_dialog(self, info):
        
        self._log(f"✅ プレイリスト情報を取得しました: {len(info['entries'])}件")
        dialog = tk.Toplevel(self.root)
        dialog.title(f"プレイリスト選択: {info.get('title', 'Unknown')}")
        dialog.geometry("600x500")
        dialog.configure(bg=self.current_theme['bg_dark'])
        main_frame = ttk.Frame(dialog, padding="10", style="Modern.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="ダウンロードする動画を選択してください:", 
                 style="Modern.TLabel").pack(anchor=tk.W, pady=(0, 10))
        list_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        canvas = tk.Canvas(list_frame, bg=self.current_theme['bg_darker'], 
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Modern.TFrame")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.video_vars = []
        def toggle_all():
            state = all_var.get()
            for var, _ in self.video_vars:
                var.set(state)
        all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_frame, text="すべて選択/解除", 
                       variable=all_var, command=toggle_all,
                       style="Modern.TCheckbutton").pack(anchor=tk.W, pady=5)
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        for i, entry in enumerate(info['entries']):
            if not entry: continue
            var = tk.BooleanVar(value=True)
            title = entry.get('title', 'Unknown')
            duration = entry.get('duration')
            duration_str = f" ({int(duration//60)}:{int(duration%60):02d})" if duration else ""
            frame = ttk.Frame(scrollable_frame, style="Modern.TFrame")
            frame.pack(fill=tk.X, pady=2)
            cb = ttk.Checkbutton(frame, text=f"{i+1}. {title}{duration_str}", 
                                variable=var,
                                style="Modern.TCheckbutton")
            cb.pack(anchor=tk.W)
            self.video_vars.append((var, i + 1))
        btn_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        btn_frame.pack(fill=tk.X)
        def on_ok():
            selected_indices = [str(idx) for var, idx in self.video_vars if var.get()]
            if not selected_indices:
                messagebox.showwarning("警告", "動画が選択されていません")
                return
            self.playlist_mode_var.set(True)
            self._on_playlist_change()
            self.selected_playlist_items = ",".join(selected_indices)
            self._log(f"✅ {len(selected_indices)}件の動画を選択しました")
            self.playlist_start_var.set("選択済み")
            self.playlist_start_entry.config(state=tk.DISABLED)
            dialog.destroy()
            if messagebox.askyesno("確認", "選択した動画をダウンロードしますか？"):
                self._start_download()
        ttk.Button(btn_frame, text="キャンセル", command=dialog.destroy,
                  style="Modern.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="OK", command=on_ok,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
    def _on_closing(self):
        
        if self.is_downloading:
            if not messagebox.askokcancel("確認", "ダウンロード中です。終了してもよろしいですか？"):
                return
            self._cancel_download()
        self._save_settings()
        self.root.destroy()
    def main(self):
        
        self.root.mainloop()
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    app.main()
