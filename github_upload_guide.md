# GitHubへのアップロード手順

このプロジェクトをGitHubにアップロードするための手順です。
不要なファイル（ビルド生成物、個人設定、依存ライブラリなど）を除外するための `.gitignore` ファイルは既に作成済みです。

## 1. アップロードされるファイル
以下のファイルがGitHubにアップロードされます（ソースコードとドキュメントのみ）：
- `main.py`
- `downloader.py`
- `config.py`
- `dependency_manager.py`
- `collapsible_frame.py`
- `build.bat`
- `requirements.txt`
- `README.md`
- `.gitignore`

## 2. 除外されるファイル（アップロードされません）
- `dist/` (生成されたexeファイル)
- `build/` (ビルド中間ファイル)
- `data/` (あなたの設定ファイルや暗号化キー)
- `dependencies/` (自動ダウンロードされるyt-dlpなど)
- `__pycache__/` (Pythonキャッシュ)

## 3. アップロード手順

コマンドプロンプトまたはPowerShellで以下のコマンドを順番に実行してください。

### ステップ 1: Gitの初期化
```bash
git init
```

### ステップ 2: ファイルの追加
```bash
git add .
```
※ `.gitignore` があるため、必要なファイルだけが自動的に選ばれます。

### ステップ 3: コミット（保存）
```bash
git commit -m "Initial commit: YTGrab v2.1.0"
```

### ステップ 4: GitHubリポジトリの作成
1. GitHubにログインし、右上の「+」アイコンから「New repository」を選択します。
2. Repository name（例: `YTGrab`）を入力します。
3. "Public"（公開）か "Private"（非公開）を選択します。
4. "Create repository" をクリックします。

### ステップ 5: リモートリポジトリの登録とプッシュ
GitHubの画面に表示されたコマンド（`…or push an existing repository from the command line` の部分）をコピーして実行します。通常は以下のようになります：

```bash
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

これでアップロード完了です！
他の人がこのリポジトリをダウンロードして使う場合は、`build.bat` を実行するか、Python環境で `main.py` を実行すれば、必要な依存関係は自動的にダウンロードされます。
