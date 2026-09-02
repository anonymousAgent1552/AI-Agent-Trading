from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import config

@dataclass
class POI:
    kind: str
    direction: str
    low: float
    high: float
    source_time: str
    priority: int
    note: str = ""

    def to_dict(self):
        return asdict(self)

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def _body(c):
    return abs(float(c["close"]) - float(c["open"]))

def detect_order_blocks(df: pd.DataFrame):
    """
    Conservative rule:
    bullish OB = last bearish candle before bullish displacement
    bearish OB = last bullish candle before bearish displacement
    Zone = full candle range.
    """
    out = []
    a = atr(df, config.OB_ATR_PERIOD)

    for i in range(config.OB_ATR_PERIOD + 1, len(df) - 1):
        cur = df.iloc[i]
        nxt = df.iloc[i + 1]
        atr_value = a.iloc[i]
        if pd.isna(atr_value) or atr_value <= 0:
            continue

        nxt_body = _body(nxt)

        if cur["close"] < cur["open"] and nxt["close"] > nxt["open"]:
            if nxt_body >= float(atr_value) * config.OB_DISPLACEMENT_ATR:
                out.append(POI(
                    "DAILY_OB", "BULLISH",
                    float(cur["low"]), float(cur["high"]),
                    str(cur["datetime"]), 1,
                    "Last bearish candle before bullish displacement"
                ))

        if cur["close"] > cur["open"] and nxt["close"] < nxt["open"]:
            if nxt_body >= float(atr_value) * config.OB_DISPLACEMENT_ATR:
                out.append(POI(
                    "DAILY_OB", "BEARISH",
                    float(cur["low"]), float(cur["high"]),
                    str(cur["datetime"]), 1,
                    "Last bullish candle before bearish displacement"
                ))
    return out

def detect_ocl(df: pd.DataFrame):
    """
    Default OCL interpretation:
    previous Daily candle's Low for bullish context and High for bearish context.
    Kept isolated so the user's exact OCL definition can be swapped later.
    """
    if len(df) < 2:
        return []

    prev = df.iloc[-2]
    return [
        POI("DAILY_OCL_LOW", "BULLISH",
            float(prev["low"]), float(prev["low"]),
            str(prev["datetime"]), 2,
            "Previous Daily Low; configurable OCL definition"),
        POI("DAILY_OCL_HIGH", "BEARISH",
            float(prev["high"]), float(prev["high"]),
            str(prev["datetime"]), 2,
            "Previous Daily High; configurable OCL definition"),
    ]

def build_pois(daily_df: pd.DataFrame):
    # Exclude the currently forming Daily candle.
    now = pd.Timestamp.now(tz="UTC")
    closed = daily_df[daily_df["datetime"] + pd.Timedelta(days=1) <= now].copy()
    if len(closed) < 20:
        closed = daily_df.copy()

    pois = detect_order_blocks(closed)
    pois.extend(detect_ocl(closed))

    # Keep recent candidates only, to avoid an ever-growing POI list.
    pois = sorted(pois, key=lambda x: x.source_time, reverse=True)[:20]
    return pois

def price_in_poi(price: float, poi: POI, tolerance: float = None):
    tolerance = config.POI_TOLERANCE if tolerance is None else tolerance
    if poi.low == poi.high:
        pad = price * tolerance
        return abs(price - poi.low) <= pad
    pad = (poi.high - poi.low) * tolerance
    return (poi.low - pad) <= price <= (poi.high + pad)

def nearest_active_pois(price: float, pois, limit=3):
    scored = []
    for p in pois:
        if price_in_poi(price, p):
            distance = 0.0
        else:
            distance = min(abs(price-p.low), abs(price-p.high))
        scored.append((distance, p))
    scored.sort(key=lambda x: (x[0], x[1].priority))
    return [p for _, p in scored[:limit]]
