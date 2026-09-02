import pandas as pd
from core.engulfing import bullish_engulfing, bearish_engulfing

def candle(o,h,l,c):
    return pd.Series({"open":o,"high":h,"low":l,"close":c})

def test_bullish():
    prev = candle(10, 10.5, 9, 9.5)
    cur = candle(9.4, 11, 9.2, 10.8)
    assert bullish_engulfing(prev, cur)

def test_bearish():
    prev = candle(10, 11, 9.8, 10.7)
    cur = candle(10.8, 10.9, 9, 9.2)
    assert bearish_engulfing(prev, cur)
