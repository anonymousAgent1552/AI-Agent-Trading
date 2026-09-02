import requests
import config

def api(method, payload=None):
    r=requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}",json=payload or {},timeout=30); r.raise_for_status(); return r.json()

def send_message(text, chat_id=None):
    target=chat_id or config.TELEGRAM_CHAT_ID
    return api("sendMessage", {"chat_id":target,"text":text,"disable_web_page_preview":True})

def get_updates(offset=None, timeout=5):
    payload={"timeout":timeout}
    if offset is not None: payload["offset"]=offset
    return api("getUpdates",payload).get("result",[])

def set_commands():
    return api("setMyCommands", {"commands":[{"command":"start","description":"Start bot"},{"command":"status","description":"Bot status"},{"command":"poi","description":"Show Daily POI"},{"command":"analysis","description":"Run analysis"},{"command":"help","description":"Show commands"}]})

def format_status(state, health):
    return (f"🤖 AI TRADING AGENT\n\nStatus: 🟢 ONLINE\nSymbol: {config.SYMBOL}\nStrategy: Daily POI + M15 Engulfing\n\nSignals today: {state.get('signals',0)}/{config.MAX_TRADES_PER_DAY}\nGroq: {health['groq']}\nMarket Data: {health['market_data']}\nLast scan: {state.get('last_scan') or '-'}")

def help_text(): return "📚 COMMANDS\n\n/start - Start bot\n/status - Bot health + signal count\n/poi - Current Daily POI\n/analysis - Run one analysis cycle\n/help - Commands"
