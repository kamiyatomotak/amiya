# Chrona Bot 技術仕様

## 1. 技術スタック

*   **プログラミング言語:** Python (バージョン 3.9 以上を推奨)
*   **主要ライブラリ:**
    *   `tweepy>=4.14.0`: X API v2 との連携用
    *   `python-dotenv`: ローカル開発環境での環境変数管理用 (.env ファイル)
    *   `google-generativeai`: Google Gemini API との連携用
    *   (必要に応じて `requests` など標準ライブラリも利用)
*   **実行環境:** Docker (Ubuntu 22.04 LTS ベースイメージ) - GitHub Actions 上
*   **CI/CD・自動実行:** GitHub Actions
*   **ローカル開発環境:** Python 仮想環境 (`.venv` を推奨)

## 2. 開発手法

*   **バージョン管理:** Git / GitHub
*   **開発スタイル:** シンプルさを重視。単一の Python スクリプト (`main.py`) で主要ロジックを実装。
*   **テスト:** ローカル環境での手動実行による基本的な動作確認 (`.env` ファイル使用)。GitHub Actions での実行シミュレーション。

## 3. コーディング規約 (推奨)

*   **スタイルガイド:** PEP 8 に準拠する。
*   **コメント:**
    *   主要な関数やクラスには日本語で Docstring を記述する。
    *   複雑なロジックや設定値には適宜コメントを追加する。
*   **エラーハンドリング:**
    *   `try...except` ブロックを使用して、API 呼び出しや予期せぬエラーを適切に捕捉する。
    *   エラー発生時は、`logging` モジュールを使用して詳細な情報をログに出力する。
    *   可能な限り、エラー発生時でもプログラムが異常終了しないように設計する (例: Gemini API エラー時は代替テキストを使用、X API エラー時はログ出力して終了)。
*   **設定値:**
    *   API キーなどの機密情報は環境変数から読み込む (`os.getenv`)。
    *   テキストメーターの幅や記号など、変更の可能性がある設定値はスクリプト冒頭で定数として定義する。
*   **ログ:**
    *   標準ライブラリの `logging` モジュールを使用する。
    *   フォーマット: `%(asctime)s - %(levelname)s - %(message)s`
    *   レベル: `INFO` 以上を出力。
    *   主要な処理ステップ (計算開始、API 呼び出し、投稿など) やエラー発生時にログを出力する。

## 4. データベース設計

*   このプロジェクトではデータベースは使用しない。

## 5. API 利用詳細

### 5.1. X API (v2 / OAuth 1.0a User Context)

*   **認証 (ツイート投稿):** OAuth 1.0a User Context
    *   必要なキー (環境変数名):
        *   `X_API_KEY` (Consumer Key)
        *   `X_API_SECRET` (Consumer Secret)
        *   `X_ACCESS_TOKEN` (Access Token)
        *   `X_ACCESS_TOKEN_SECRET` (Access Token Secret)
*   **認証 (Bearer Token):** `X_BEARER_TOKEN` は現在の実装ではツイート投稿に使用していない。
*   **エンドポイント:** `POST /2/tweets` (tweepy経由で利用)
*   **ライブラリ:** `tweepy` (`tweepy.Client` を使用)
*   **注意点:** Free プランの投稿制限 (月1500件) 内で運用する。

### 5.2. Google Gemini API

*   **認証:** API Key (環境変数 `GEMINI_API_KEY` から読み込み)
*   **モデル:** `gemini-2.0-flash`
*   **ライブラリ:** `google-generativeai`
*   **プロンプト:**
    *   「今年の時間の流れや季節の移り変わりについて、X(旧Twitter)に投稿するための、短く、示唆に富む一文を日本語で生成してください。句読点を含めて40文字程度でお願いします。」
*   **エラーハンドリング:** API 呼び出し失敗時は、固定の代替文言 (`時間は静かに流れ続けます。`) を使用し、エラーログを記録する。
*   **コスト:** `gemini-2.0-flash` モデルの料金体系を確認し、予算内に収まるか注意する (無料枠の範囲内で収まる可能性が高い)。

## 6. セキュリティ

*   API キー (X 用の4つのキー, Gemini API Key) は GitHub Secrets に登録し、ワークフロー内で環境変数として Docker コンテナに渡す。
*   ローカル開発用の `.env` ファイルは `.gitignore` に追加し、リポジトリにコミットしない。
*   コード内に機密情報を直接記述しない。
*   仮想環境 (`.venv`) も `.gitignore` に追加し、リポジトリにコミットしない。 