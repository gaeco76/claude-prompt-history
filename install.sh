#!/usr/bin/env bash
# Claude Code Prompt History - 설치 스크립트

set -e

HOOKS_DIR="$HOME/.claude/hooks"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
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

echo "[4/4] settings.json hook 확인..."
SETTINGS="$HOME/.claude/settings.json"
if ! grep -q "save_prompt.py" "$SETTINGS" 2>/dev/null; then
  echo "⚠️  ~/.claude/settings.json 에 아래 hook을 수동으로 추가하세요:"
  echo '  "hooks": { "UserPromptSubmit": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/save_prompt.py" }] }] }'
else
  echo "   hook 이미 등록됨 ✓"
fi

echo ""
echo "완료! 브라우저에서 http://localhost:7878 접속하세요."
