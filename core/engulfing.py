import pandas as pd

def body(c):
    return abs(float(c["close"]) - float(c["open"]))

def bullish_engulfing(prev, cur) -> bool:
    prev_open, prev_close = float(prev["open"]), float(prev["close"])
    cur_open, cur_close = float(cur["open"]), float(cur["close"])

    prev_bear = prev_close < prev_open
    cur_bull = cur_close > cur_open

    # Strict body engulfing:
    return (
        prev_bear and cur_bull
        and cur_open <= prev_close
        and cur_close >= prev_open
        and body(cur) >= body(prev)
    )

def bearish_engulfing(prev, cur) -> bool:
    prev_open, prev_close = float(prev["open"]), float(prev["close"])
    cur_open, cur_close = float(cur["open"]), float(cur["close"])

    prev_bull = prev_close > prev_open
    cur_bear = cur_close < cur_open

    return (
        prev_bull and cur_bear
        and cur_open >= prev_close
        and cur_close <= prev_open
        and body(cur) >= body(prev)
    )

def detect(df: pd.DataFrame):
    if len(df) < 2:
        return None
    prev, cur = df.iloc[-2], df.iloc[-1]
    if bullish_engulfing(prev, cur):
        return {"type": "BULLISH_ENGULFING", "candle": cur, "previous": prev}
    if bearish_engulfing(prev, cur):
        return {"type": "BEARISH_ENGULFING", "candle": cur, "previous": prev}
    return None
