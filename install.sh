#!/usr/bin/env bash
# Claude Code Prompt History - 설치 스크립트

set -e

HOOKS_DIR="$HOME/.claude/hooks"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
SETTINGS="$HOME/.claude/settings.json"
PLIST="com.claude.prompt-history.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/4] hooks 디렉토리 생성..."
mkdir -p "$HOOKS_DIR"

echo "[2/4] 스크립트 복사..."
cp "$SCRIPT_DIR/hooks/save_prompt.py" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/hooks/viewer_server.py" "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/save_prompt.py" "$HOOKS_DIR/viewer_server.py"

echo "[3/4] LaunchAgent 등록..."
# __HOME__ placeholder를 실제 $HOME 경로로 치환해서 복사
sed "s|__HOME__|$HOME|g" "$SCRIPT_DIR/launchagent/$PLIST" > "$LAUNCH_AGENTS/$PLIST"
launchctl unload "$LAUNCH_AGENTS/$PLIST" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS/$PLIST"

echo "[4/4] settings.json hook 등록..."
python3 - <<'PYEOF'
import json, os, sys

settings_path = os.path.expanduser("~/.claude/settings.json")
hook_command = "python3 ~/.claude/hooks/save_prompt.py"
new_hook = {
    "matcher": "",
    "hooks": [{"type": "command", "command": hook_command}]
}

# 파일 읽기 (없으면 빈 객체)
if os.path.exists(settings_path):
    with open(settings_path, "r") as f:
        settings = json.load(f)
else:
    settings = {}

# hooks.UserPromptSubmit 에 추가 또는 업데이트
hooks = settings.setdefault("hooks", {})
ups = hooks.setdefault("UserPromptSubmit", [])

# 이미 save_prompt.py hook이 있으면 경로만 갱신
for entry in ups:
    for h in entry.get("hooks", []):
        if "save_prompt.py" in h.get("command", ""):
            h["command"] = hook_command
            print("   hook 경로 갱신 ✓")
            break
    else:
        continue
    break
else:
    ups.append(new_hook)
    print("   hook 신규 등록 ✓")

with open(settings_path, "w") as f:
    json.dump(settings, f, ensure_ascii=False, indent=2)
PYEOF

echo ""
echo "완료! 브라우저에서 http://localhost:7878 접속하세요."
