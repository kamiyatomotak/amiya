import datetime
import math
import os
import logging
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv

# --- 定数 ---
PROGRESS_BAR_WIDTH = 10
FILLED_SYMBOL = "🟩"
EMPTY_SYMBOL = "⬜"
DEFAULT_SENTENCE = "時間は静かに流れ続けます。"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# --- ロギング設定 ---
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# --- 環境変数読み込み ---
# ローカル開発環境(.envファイル)とGitHub ActionsのSecretsの両方に対応
load_dotenv()

# --- APIキーの取得 ---
# 環境変数から取得できなかった場合はNoneが入る
# X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN") # 投稿には使用しないためコメントアウト
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 関数 ---

def get_year_progress(target_date: datetime.date) -> tuple[int, int, float]:
    """指定された日付の年の進行状況を計算します。

    Args:
        target_date: 進行状況を計算する対象の日付。

    Returns:
        以下の要素を含むタプル:
        - current_day_of_year: 年の開始からの経過日数 (1-365 or 366)。
        - total_days_in_year: その年の総日数。
        - progress_percentage: 年の経過率 (%) (0.0 から 100.0)。
    """
    year = target_date.year
    start_of_year = datetime.date(year, 1, 1)
    end_of_year = datetime.date(year, 12, 31)
    total_days_in_year = (end_of_year - start_of_year).days + 1
    current_day_of_year = (target_date - start_of_year).days + 1
    # ゼロ除算を避ける (念のため)
    if total_days_in_year == 0:
        return current_day_of_year, total_days_in_year, 0.0
    progress_percentage = (current_day_of_year / total_days_in_year) * 100.0
    return current_day_of_year, total_days_in_year, progress_percentage

def create_progress_bar(percentage: float) -> str:
    """テキストベースのプログレスバーを作成します。

    Args:
        percentage: 進行率 (%) (0.0 から 100.0)。

    Returns:
        プログレスバーを表す文字列 (例: "[🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜] 27%")。
    """
    # パーセンテージが0未満または100超の場合は丸める
    percentage = max(0.0, min(100.0, percentage))
    # round() を使用して四捨五入する
    filled_width = round(PROGRESS_BAR_WIDTH * percentage / 100)
    # filled_width がバーの幅を超えないように念のため制限
    filled_width = min(PROGRESS_BAR_WIDTH, filled_width)
    empty_width = PROGRESS_BAR_WIDTH - filled_width
    bar = FILLED_SYMBOL * filled_width + EMPTY_SYMBOL * empty_width
    # %.0f で整数表示 
    return f"[{bar}] {percentage:.0f}%"

def generate_sentence(api_key: str) -> str:
    """Google Gemini API を使用して、示唆に富んだ一文を生成します。

    Args:
        api_key: Google Gemini API キー。

    Returns:
        生成された一文。エラー時はデフォルトの文章を返す。
    """
    if not api_key:
        logging.error("Gemini APIキーが設定されていません。")
        return DEFAULT_SENTENCE

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash') 
        prompt = "AIが時間の観測者として、1年の進行度に寄り添う短い一文を日本語で生成して。哲学的な表現で、句読点含めて40文字以内にして。"
        logging.info("Gemini API 呼び出し開始...")
        response = model.generate_content(prompt)
        logging.info("Gemini API 呼び出し成功.")
        # response.text でテキスト部分を取得
        generated_text = response.text.strip()
        # 簡単なバリデーション（空でないかなど）
        if generated_text:
             return generated_text
        else:
             logging.warning("Gemini APIから空の応答がありました。デフォルトの文章を使用します。")
             return DEFAULT_SENTENCE

    except Exception as e:
        logging.error(f"Gemini APIエラー: {e}")
        return DEFAULT_SENTENCE

def post_tweet(api_key: str, api_secret: str, access_token: str, access_token_secret: str, text: str) -> bool:
    """X (Twitter) API v2 (User Context認証) を使用してツイートを投稿します。

    Args:
        api_key: X API Key (Consumer Key).
        api_secret: X API Key Secret (Consumer Secret).
        access_token: X Access Token.
        access_token_secret: X Access Token Secret.
        text: 投稿するツイート本文。

    Returns:
        投稿が成功した場合は True、失敗した場合は False。
    """
    # 必要なキーが揃っているかチェック
    if not all([api_key, api_secret, access_token, access_token_secret]):
        logging.error("X APIの認証情報 (API Key/Secret, Access Token/Secret) が不足しています。")
        return False

    try:
        # TweepyのClient初期化 (OAuth 1.0a User Context)
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        logging.info("X API 呼び出し開始 (ツイート投稿)...")
        response = client.create_tweet(text=text)
        logging.info(f"ツイート投稿成功: {response.data['id']}")
        return True
    except tweepy.errors.TweepyException as e:
        logging.error(f"X API (Tweepy) エラー: {e}")
        # エラーレスポンスの詳細もログに出力してみる
        if hasattr(e, 'api_codes') and hasattr(e, 'api_messages'):
            logging.error(f"APIエラーコード: {e.api_codes}, メッセージ: {e.api_messages}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"APIレスポンス: {e.response.text}")
        return False
    except Exception as e:
        logging.error(f"予期せぬエラー (ツイート投稿時): {e}")
        return False

# --- メイン処理 ---
if __name__ == "__main__":
    logging.info("Chrona Bot 処理開始...")

    # APIキーの存在チェック (投稿に必要なキーをチェック)
    required_keys = [X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, GEMINI_API_KEY]
    if not all(required_keys):
        missing_keys = []
        if not X_API_KEY: missing_keys.append("X_API_KEY")
        if not X_API_SECRET: missing_keys.append("X_API_SECRET")
        if not X_ACCESS_TOKEN: missing_keys.append("X_ACCESS_TOKEN")
        if not X_ACCESS_TOKEN_SECRET: missing_keys.append("X_ACCESS_TOKEN_SECRET")
        if not GEMINI_API_KEY: missing_keys.append("GEMINI_API_KEY")
        logging.critical(f"必要なAPIキー ({', '.join(missing_keys)}) が環境変数に設定されていません。処理を中断します。")
        exit(1) # エラー終了

    # 1. 年の進行状況を計算
    now_jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) # JSTで現在日時を取得
    today_jst = now_jst.date() # 日付部分
    logging.info(f"対象日時: {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')} (JST)")
    day_num, total_days, percent = get_year_progress(today_jst)
    logging.info(f"年の進行状況: {day_num}/{total_days}日 ({percent:.1f}%)")

    # 2. プログレスバーを作成
    progress_bar_str = create_progress_bar(percent) # 例: "[🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜] 27%"
    logging.info(f"プログレスバー: {progress_bar_str}")

    # 3. Gemini API で一文を生成
    generated_sentence = generate_sentence(GEMINI_API_KEY)
    logging.info(f"生成された/代替の文章: {generated_sentence}")

    # 4. ツイート本文を組み立て
    # 曜日を日本語で取得
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_jp = weekdays_jp[now_jst.weekday()]

    # 新しいテンプレートに合わせてフォーマット
    tweet_text = (
        f"本日は{now_jst.year}年{now_jst.month}月{now_jst.day}日（{weekday_jp}）\n\n"
        f"⏳ 経過日数：{day_num}日 / {total_days}日\n"
        f"📈 進行度：{progress_bar_str}\n\n"
        f"{generated_sentence}"
    )
    logging.info(f"生成されたツイート本文:\n{tweet_text}")

    # 5. Xにツイート投稿
    logging.info("ツイート投稿処理を開始します...")
    success = post_tweet(
        api_key=X_API_KEY,
        api_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
        text=tweet_text
    )

    if success:
        logging.info("ツイート投稿が正常に完了しました。")
    else:
        logging.error("ツイート投稿に失敗しました。")
        exit(1) # エラー終了

    logging.info("Chrona Bot 処理完了。") 