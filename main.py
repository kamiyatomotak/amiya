import datetime
import math
import os
import logging
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv

# --- 定数 ---
PROGRESS_BAR_WIDTH = 12
FILLED_SYMBOL = "🐧"
EMPTY_SYMBOL = "□"
DEFAULT_SENTENCE = "何もしないままでいいのか？"
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

    # 新しい仕様: 進行率 / 10 の切り捨てで本数を決定
    if percentage == 100.0:
        filled_width = PROGRESS_BAR_WIDTH
    else:
        filled_width = math.floor(percentage / (100 / PROGRESS_BAR_WIDTH))

    empty_width = PROGRESS_BAR_WIDTH - filled_width
    bar = FILLED_SYMBOL * filled_width + EMPTY_SYMBOL * empty_width
    # %.0f で整数表示 (これは元々四捨五入)
    return f"[{bar}] {percentage:.0f}%"

def generate_sentence(api_key: str, current_day_of_year: int, total_days_in_year: int, progress_percentage: float) -> str:
    """Google Gemini API を使用して、示唆に富んだ一文を生成します。
       日付と進行度からAIが自由に連想し、毎回異なる表現を目指します。

    Args:
        api_key: Google Gemini API キー。
        current_day_of_year: 年の開始からの経過日数。
        total_days_in_year: その年の総日数。
        progress_percentage: 年の経過率 (%)。

    Returns:
        生成された一文。エラー時はデフォルトの文章を返す。
    """
    if not api_key:
        logging.error("Gemini APIキーが設定されていません。")
        return DEFAULT_SENTENCE

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # プロンプト本体: 事実を伝え、AIの自由な解釈に委ねる
        prompt_parts = [
            f"今日は1年{total_days_in_year}日のうち{current_day_of_year}日目、{progress_percentage:.1f}%が経過しました。",
            "ITインフラエンジニアとしてのマインドを辛口で35文字程度でコメントする",
            "必ず1つの文章で、箇条書きや複数行は使わないでください。",
            "句読点を含めて全体で40文字以内が望ましいですが、言葉が溢れるなら多少の調整は許容します。",
            "あなたの独創的な感性で、他のどの日の言葉とも違う、今日だけの特別な一言をお願いします。"
        ]
        prompt = " ".join(prompt_parts)

        logging.info(f"Gemini API 呼び出し開始 (プロンプトヒント: 「今日は1年{total_days_in_year}日のうち{current_day_of_year}日目...」)")
        response = model.generate_content(prompt)
        logging.info("Gemini API 呼び出し成功.")
        generated_text = response.text.strip()

        if generated_text and "\\n" not in generated_text:
             if generated_text.startswith("*") or generated_text.startswith("・") or generated_text.startswith("-"):
                 generated_text = generated_text[1:].strip()
             return generated_text
        elif generated_text and "\\n" in generated_text: # 複数行の場合
             logging.warning(f"Gemini APIから複数行の応答がありました: {generated_text.splitlines()[0]} ...。最初の行を使用します。")
             first_line = generated_text.splitlines()[0].strip()
             if first_line.startswith("*") or first_line.startswith("・") or first_line.startswith("-"):
                 first_line = first_line[1:].strip()
             return first_line
        else: # 空の場合
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
    # 残り日数を計算
    remaining_days = total_days - day_num
    logging.info(f"年の進行状況: {day_num}/{total_days}日 ({percent:.1f}%) - 残り{remaining_days}日")

    # 2. プログレスバーを作成
    progress_bar_str = create_progress_bar(percent) # 例: "[🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜] 27%"
    logging.info(f"プログレスバー: {progress_bar_str}")

    # 3. Gemini API で一文を生成
    generated_sentence = generate_sentence(GEMINI_API_KEY, day_num, total_days, percent)
    logging.info(f"生成された/代替の文章: {generated_sentence}")

    # 4. ツイート本文を組み立て
    # 曜日を日本語で取得
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_jp = weekdays_jp[now_jst.weekday()]

    # 新しいテンプレートに合わせてフォーマット (残り日数表示を追加)
    tweet_text = (
        f"======================================\n"
        f"★本日は{now_jst.year}年{now_jst.month}月{now_jst.day}日（{weekday_jp}）★\n\n"
        f"🐧経過日数：{day_num}日 / {total_days}日（残り{remaining_days}日）\n"
        f"💻：{progress_bar_str}\n\n"
        f"{generated_sentence}"
        f"======================================\n"
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
