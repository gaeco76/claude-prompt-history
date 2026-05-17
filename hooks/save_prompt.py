#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook
stdin JSON의 'prompt' 키에서 사용자 입력을 추출해 저장하고 SSE 서버에 즉시 알린다.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

HISTORY_FILE = os.path.expanduser("~/.claude/prompt_history.json")
NOTIFY_URL = "http://127.0.0.1:7878/api/notify"
MAX_ENTRIES = 2000


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def notify_server():
    try:
        req = urllib.request.Request(NOTIFY_URL, data=b"", method="POST")
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    # prompt 키에 사용자 입력이 직접 들어있음
    text = data.get("prompt", "").strip()

    if not text:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "")

    history = load_history()
    entry = {
        "num": len(history) + 1,
        "ts": datetime.now().isoformat(),
        "session_id": session_id,
        "cwd": cwd,
        "text": text,
    }
    history.insert(0, entry)
    if len(history) > MAX_ENTRIES:
        history = history[:MAX_ENTRIES]

    save_history(history)
    notify_server()

    print(f"[prompt-log] #{entry['num']} saved ({len(text)} chars)", file=sys.stderr)


if __name__ == "__main__":
    main()
