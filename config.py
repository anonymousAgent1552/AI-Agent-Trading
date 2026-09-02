import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SYMBOL = os.getenv("SYMBOL", "XAU/USD")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

DAILY_LOOKBACK = int(os.getenv("DAILY_LOOKBACK", "80"))
M15_LOOKBACK = int(os.getenv("M15_LOOKBACK", "50"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
POI_TOLERANCE = float(os.getenv("POI_TOLERANCE", "0.001"))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "2"))

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MIN_AI_CONFIDENCE = int(os.getenv("MIN_AI_CONFIDENCE", "70"))

OB_ATR_PERIOD = int(os.getenv("OB_ATR_PERIOD", "14"))
OB_DISPLACEMENT_ATR = float(os.getenv("OB_DISPLACEMENT_ATR", "1.2"))
