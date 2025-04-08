# Chrona Bot ⏳

1年の進行度を計算し、毎週月曜日の朝8時（日本時間）にX（旧Twitter）へ自動投稿するボットです。

## ✨ 機能

*   現在の年の経過日数、総日数、残り日数を計算します。
*   進行率 (%) を計算します。
*   進行率をテキストベースのプログレスバー (例: `[🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜] 27%`) で表示します。
*   Google Gemini API (`gemini-2.0-flash`) を利用して、時間の経過に関する示唆に富んだ一文を生成します。
*   上記を組み合わせた内容 (日付、経過日数/総日数/残り日数、プログレスバー、生成文) を、毎週月曜朝8時 (JST) にXへ自動投稿します。

## 使い方 (GitHub Actionsによる自動実行)

このリポジトリでは、GitHub Actions を利用して、毎週自動でツイートが投稿されるように設定されています (`.github/workflows/cron_tweet.yml`)。

**必要な設定:**

リポジトリの `Settings` > `Secrets and variables` > `Actions` に以下の5つの **Repository secrets** を設定する必要があります。

*   `X_API_KEY`: あなたのXアプリの API Key (Consumer Key)
*   `X_API_SECRET`: あなたのXアプリの API Key Secret (Consumer Secret)
*   `X_ACCESS_TOKEN`: あなたのXアプリの Access Token
*   `X_ACCESS_TOKEN_SECRET`: あなたのXアプリの Access Token Secret
*   `GEMINI_API_KEY`: あなたの Google Gemini API Key

設定が完了していれば、`on.schedule` で指定された時刻 (`0 23 * * 0` UTC) に自動的にワークフローが実行されます。
また、Actionsタブから手動で `workflow_dispatch` をトリガーして実行することも可能です。

## ローカルでの実行方法 (開発・テスト用)

1.  **リポジトリをクローン:**
    ```bash
    git clone https://github.com/neet-kuzuno/chrona-bot.git
    cd chrona-bot
    ```
2.  **Python 仮想環境を作成・有効化:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # macOS / Linux
    # venv\Scripts\activate    # Windows (Command Prompt)
    # .\.venv\Scripts\Activate.ps1 # Windows (PowerShell)
    ```
3.  **必要なライブラリをインストール:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **`.env` ファイルを作成:**
    `.env.example` をコピーして `.env` ファイルを作成し、中に実際のAPIキーを記述します。
    ```dotenv
    # X (Twitter) API v1.1a User Context
    X_API_KEY=YOUR_X_API_KEY
    X_API_SECRET=YOUR_X_API_SECRET
    X_ACCESS_TOKEN=YOUR_X_ACCESS_TOKEN
    X_ACCESS_TOKEN_SECRET=YOUR_X_ACCESS_TOKEN_SECRET

    # Google Gemini API Key
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    ```
5.  **スクリプトを実行:**
    ```bash
    python main.py
    ```

## プロジェクトドキュメント

詳細な設計や仕様については `project-docs/` ディレクトリ内の各ファイルを参照してください。 