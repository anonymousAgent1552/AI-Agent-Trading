import time
import traceback
import pandas as pd

import config
from core.market_data import get_daily, get_m5, latest_closed_m5
from core.daily_poi import build_pois, price_in_poi
from core.engulfing import detect
from core.ai_agent import validate_setup
from core.state import load_state, save_state, reset_if_new_day
from telegram.bot import send_message, get_updates, set_commands, help_text, format_status

def fmt(x):
    return f"{float(x):.2f}"

def format_signal(setup, ai):
    p = setup["poi"]
    e = setup["engulfing"]
    c = e["candle"]
    direction = ai["direction"]

    return (
        f"🟡 XAU/USD | M5 SETUP\\n\\n"
        f"📍 DAILY POI\\n"
        f"{p['kind']} | {p['direction']}\\n"
        f"Zone: {fmt(p['low'])} - {fmt(p['high'])}\\n"
        f"Source: {p['source_time']}\\n\\n"
        f"📊 PRICE ACTION\\n"
        f"{e['type']}\\n"
        f"M5 close: {fmt(c['close'])}\\n"
        f"Candle: {c['datetime']}\\n\\n"
        f"🧠 AI VALIDATION\\n"
        f"Decision: {ai['decision']}\\n"
        f"Direction: {direction}\\n"
        f"Confidence: {ai['confidence']}%\\n"
        f"Reason: {ai['reason']}\\n"
        f"Risk: {ai['risk_note']}\\n\\n"
        f"Signals today: {setup['signals_today']}/{config.MAX_TRADES_PER_DAY}"
    )

def scan_once(state):
    daily = get_daily()
    pois = build_pois(daily)

    m5 = get_m5()
    closed = m5[m5["datetime"] + pd.Timedelta(minutes=5) <= pd.Timestamp.now(tz="UTC")].copy()
    if len(closed) < 2:
        return state

    latest = closed.iloc[-1]
    price = float(latest["close"])

    active = [p for p in pois if price_in_poi(price, p)]
    if not active:
        state["last_scan"] = str(latest["datetime"])
        save_state(state)
        return state

    engulf = detect(closed)
    if not engulf:
        state["last_scan"] = str(latest["datetime"])
        save_state(state)
        return state

    if state["signals"] >= config.MAX_TRADES_PER_DAY:
        return state

    candle_time = str(engulf["candle"]["datetime"])
    signal_key = f"{state['date']}|{candle_time}|{engulf['type']}"
    if signal_key == state.get("last_signal_key"):
        return state

    poi = active[0]

    # Direction coherence before spending Groq tokens.
    expected = "BUY" if poi.direction == "BULLISH" else "SELL"
    detected_direction = "BUY" if engulf["type"] == "BULLISH_ENGULFING" else "SELL"
    if expected != detected_direction:
        state["last_signal_key"] = signal_key
        state["last_scan"] = candle_time
        save_state(state)
        return state

    # Deterministic risk plan. Groq validates; it does not invent SL/TP.
    entry = float(engulf["candle"]["close"])
    if detected_direction == "BUY":
        sl = float(engulf["candle"]["low"]) - config.SL_BUFFER
        risk = entry - sl
        tp = entry + (risk * config.RISK_REWARD)
    else:
        sl = float(engulf["candle"]["high"]) + config.SL_BUFFER
        risk = sl - entry
        tp = entry - (risk * config.RISK_REWARD)
    if risk <= 0:
        return state

    setup = {
        "symbol": config.SYMBOL,
        "strategy": "DAILY_POI_PLUS_M5_ENGULFING",
        "poi": poi.to_dict(),
        "trade_plan": {"entry": entry, "sl": sl, "tp": tp, "rr": config.RISK_REWARD, "sl_buffer": config.SL_BUFFER},
        "engulfing": {
            "type": engulf["type"],
            "candle": {
                "datetime": str(engulf["candle"]["datetime"]),
                "open": float(engulf["candle"]["open"]),
                "high": float(engulf["candle"]["high"]),
                "low": float(engulf["candle"]["low"]),
                "close": float(engulf["candle"]["close"]),
            },
            "previous": {
                "open": float(engulf["previous"]["open"]),
                "high": float(engulf["previous"]["high"]),
                "low": float(engulf["previous"]["low"]),
                "close": float(engulf["previous"]["close"]),
            },
        },
        "signals_today": state["signals"] + 1,
    }

    ai = validate_setup(setup)

    state["last_signal_key"] = signal_key
    state["last_scan"] = candle_time

    if ai["decision"] == "VALID" and ai["confidence"] >= config.MIN_AI_CONFIDENCE:
        state["signals"] += 1
        setup["signals_today"] = state["signals"]
        send_message(format_signal(setup, ai))
    else:
        send_message(
            f"⚪ XAU/USD | SETUP REJECTED\\n"
            f"POI: {poi.kind} {poi.direction}\\n"
            f"PA: {engulf['type']}\\n"
            f"AI: {ai['decision']} | {ai['confidence']}%\\n"
            f"Reason: {ai['reason']}"
        )

    save_state(state)
    return state

def validate_env():
    missing = []
    for name, value in [
        ("GROQ_API_KEY", config.GROQ_API_KEY),
        ("TWELVE_DATA_API_KEY", config.TWELVE_DATA_API_KEY),
        ("TELEGRAM_BOT_TOKEN", config.TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHAT_ID", config.TELEGRAM_CHAT_ID),
    ]:
        if not value:
            missing.append(name)
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))

def worker_main():
    validate_env()
    print("AI Trading Agent V1 started.")
    state = reset_if_new_day(load_state())
    save_state(state)

    while True:
        try:
            state = reset_if_new_day(state)
            save_state(state)
            state = scan_once(state)
        except Exception as exc:
            print(f"[ERROR] {exc}")
            traceback.print_exc()
        time.sleep(config.POLL_SECONDS)

def health_check():
    return {"groq": "🟢 CONFIGURED" if config.GROQ_API_KEY else "🔴 MISSING", "market_data": "🟢 CONFIGURED" if config.TWELVE_DATA_API_KEY else "🔴 MISSING"}

def handle_command(text, chat_id, state):
    cmd=text.strip().split()[0].lower().split("@")[0]
    if cmd=="/start": send_message("🤖 AI Trading Agent aktif.\n\nKetik /status untuk cek bot.\nKetik /help untuk command.",chat_id)
    elif cmd=="/status": send_message(format_status(state,health_check()),chat_id)
    elif cmd=="/help": send_message(help_text(),chat_id)
    elif cmd=="/poi":
        try:
            pois=build_pois(get_daily()); lines=["📍 DAILY POI CANDIDATES\n"]
            for x in pois[:6]: lines.append(f"{x.kind} | {x.direction}\nZone: {fmt(x.low)} - {fmt(x.high)}\nSource: {x.source_time}\n")
            send_message("\n".join(lines),chat_id)
        except Exception as e: send_message(f"❌ POI error: {e}",chat_id)
    elif cmd=="/analysis":
        try:
            before=state.get("signals",0); state=scan_once(state)
            send_message("✅ Analysis selesai. Signal valid sudah dikirim." if state.get("signals",0)>before else "ℹ️ Analysis selesai. Belum ada setup valid yang memenuhi rule.",chat_id)
        except Exception as e: send_message(f"❌ Analysis error: {e}",chat_id)
    return state

def main():
    validate_env(); print("AI Trading Agent V1.1 started.")
    state=reset_if_new_day(load_state()); save_state(state); set_commands()
    offset=None; last_scan=0
    while True:
        try:
            for update in get_updates(offset,2):
                offset=update["update_id"]+1; msg=update.get("message",{}); text=msg.get("text",""); chat_id=msg.get("chat",{}).get("id")
                if text.startswith("/") and chat_id is not None and (not config.TELEGRAM_CHAT_ID or str(chat_id)==str(config.TELEGRAM_CHAT_ID)):
                    state=reset_if_new_day(state); state=handle_command(text,chat_id,state); save_state(state)
            now=__import__("time").time()
            if now-last_scan>=config.POLL_SECONDS:
                state=reset_if_new_day(state); state=scan_once(state); last_scan=now
        except Exception as e:
            print(f"[ERROR] {e}"); traceback.print_exc()
        time.sleep(1)

if __name__ == "__main__":
    main()
