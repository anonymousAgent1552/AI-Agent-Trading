import json
from groq import Groq
import config

SYSTEM_PROMPT = """
You are a strict trading setup validator.
You do NOT invent market data, POIs, prices, entries, or confirmations.
Python has already detected the Daily POI and a closed M15 engulfing candle.
Your job is only to validate whether the setup is internally coherent.

Strategy:
- Daily POI is the location filter.
- M15 engulfing is the ONLY entry confirmation.
- Do not request other indicators.
- Do not add extra confirmation rules.
- If direction conflicts with the POI or engulfing, reject.
- If data is insufficient, reject.
- Never guarantee profit.

Return JSON only:
{
  "decision": "VALID" | "INVALID",
  "confidence": 0-100,
  "direction": "BUY" | "SELL" | "NONE",
  "reason": "short reason",
  "risk_note": "short risk note"
}
"""

def validate_setup(setup: dict) -> dict:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing.")

    client = Groq(api_key=config.GROQ_API_KEY)

    completion = client.chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0,
        max_completion_tokens=180,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(setup, separators=(",", ":"))}
        ],
    )

    text = completion.choices[0].message.content.strip()
    # Strip markdown fences if model ever returns them.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    data = json.loads(text)

    required = {"decision", "confidence", "direction", "reason", "risk_note"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"Groq response missing fields: {missing}")

    data["confidence"] = int(data["confidence"])
    return data
