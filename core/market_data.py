import requests
import pandas as pd
from datetime import datetime, timezone
import config

BASE_URL = "https://api.twelvedata.com/time_series"

class DataError(RuntimeError):
    pass

def get_candles(symbol: str, interval: str, outputsize: int) -> pd.DataFrame:
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": config.TWELVE_DATA_API_KEY,
        "timezone": "UTC",
        "order": "ASC",
    }
    r = requests.get(BASE_URL, params=params, timeout=20)
    r.raise_for_status()
    payload = r.json()

    if payload.get("status") == "error":
        raise DataError(payload.get("message", "Twelve Data error"))

    values = payload.get("values", [])
    if not values:
        raise DataError("No candle data returned.")

    df = pd.DataFrame(values)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df

def get_daily():
    return get_candles(config.SYMBOL, "1day", config.DAILY_LOOKBACK)

def get_m15():
    return get_candles(config.SYMBOL, "15min", config.M15_LOOKBACK)

def latest_closed_m15(df: pd.DataFrame) -> pd.Series:
    now = pd.Timestamp.now(tz="UTC")
    completed = df[df["datetime"] + pd.Timedelta(minutes=15) <= now]
    if completed.empty:
        raise DataError("No closed M15 candle available.")
    return completed.iloc[-1]
