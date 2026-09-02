# AI Trading Agent V1

Telegram-only trading analyst for XAU/USD.

## Strategy

1. At the start of a new UTC trading day, scan Daily candles and build Daily POI candidates.
2. Priority POIs:
   - Daily Order Block (configurable)
   - OCL / previous Daily Low or High (configurable)
3. Wait until price enters a Daily POI.
4. Only then inspect the latest CLOSED M15 candle.
5. Entry confirmation is ONLY a bullish/bearish engulfing candle.
6. Candidate setup is sent to Groq for final validation.
7. Telegram receives VALID / INVALID / WAIT.
8. Maximum 2 signals per day.
9. No broker connection and no automatic order execution.

## Important

This V1 is an engineering prototype, not a guarantee of profitability. Validate the POI definitions and backtest before using live signals.

## Environment variables

Copy `.env.example` to `.env`:

- GROQ_API_KEY
- TWELVE_DATA_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Optional:
- SYMBOL=XAU/USD
- TIMEZONE=UTC
- DAILY_LOOKBACK=80
- M15_LOOKBACK=50
- POLL_SECONDS=60
- POI_TOLERANCE=0.001
- MAX_TRADES_PER_DAY=2
- GROQ_MODEL=openai/gpt-oss-20b
- MIN_AI_CONFIDENCE=70

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Telegram

Create the bot with @BotFather, then get the chat ID by sending a message to the bot and calling:

`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

Do not commit `.env`.

## Deployment

The app is a long-running Python worker. Use any platform that supports a persistent Python process. Keep the process alive; do not use a short-lived serverless function.

## Notes on POI logic

The exact institutional definition of "OCL" varies by methodology. This project therefore keeps OCL configurable. The default implementation uses the previous Daily candle's Low for bullish POI and High for bearish POI. Change `core/daily_poi.py` if your definition is different.

The Daily Order Block detector is deliberately conservative and rule-based:
- bullish OB: last bearish Daily candle before a bullish displacement candle
- bearish OB: last bullish Daily candle before a bearish displacement candle

Displacement is configurable through `OB_DISPLACEMENT_ATR` in config.py.

The AI never creates a POI from scratch. Python creates objective candidates; Groq only validates context and the engulfing setup.

## Telegram commands V1.1

/start, /status, /poi, /analysis, /help are supported via Telegram long polling.
