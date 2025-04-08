# 1. ベースイメージを選択 (Python 3.10 の軽量版)
FROM python:3.10-slim-bookworm

# 2. 作業ディレクトリを設定
WORKDIR /app

# 3. 必要なファイルをコンテナにコピー (requirements.txt を先にコピーしてキャッシュを活用)
COPY requirements.txt .

# 4. Pythonライブラリをインストール (キャッシュ無効化でイメージサイズ削減)
# --no-cache-dir: キャッシュを無効にし、イメージサイズを削減
# --upgrade pip: pip自体を最新版に更新
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. アプリケーションコードをコピー
COPY main.py .

# 6. コンテナ起動時に実行するコマンドを設定
# python -u: バッファリングを無効にし、ログがリアルタイムで出力されるようにする
CMD ["python", "-u", "main.py"] 