@echo off
echo ========================================
echo YouTube Downloader - Build Script
echo ========================================
echo.

REM PyInstallerがインストールされているか確認
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstallerがインストールされていません。
    echo インストールしています...
    pip install pyinstaller
    if errorlevel 1 (
        echo PyInstallerのインストールに失敗しました。
        pause
        exit /b 1
    )
)

echo.
echo .exeファイルを作成中...
echo.

REM PyInstallerでビルド
pyinstaller --onefile ^
    --windowed ^
    --name "YouTubeDownloader" ^
    --icon NONE ^
    --add-data "dependency_manager.py;." ^
    main.py

if errorlevel 1 (
    echo.
    echo ビルドに失敗しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo ビルドが完了しました！
echo.
echo 実行ファイル: dist\YouTubeDownloader.exe
echo.
echo 注意:
echo - 初回起動時にyt-dlpとFFmpegを自動ダウンロードします
echo - インターネット接続が必要です
echo - ダウンロードには数分かかる場合があります
echo ========================================
echo.

pause
