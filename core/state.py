import json
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = Path("data/state.json")

def load_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {"date": "", "signals": 0, "last_signal_key": "", "last_scan": ""}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def reset_if_new_day(state):
    today = datetime.now(timezone.utc).date().isoformat()
    if state.get("date") != today:
        state = {"date": today, "signals": 0, "last_signal_key": "", "last_scan": ""}
    return state
