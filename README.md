# Claude Code Prompt History

Claude Code 터미널에서 입력한 모든 프롬프트를 자동 저장하고, 실시간 웹앱으로 조회하는 도구입니다.

## 기능

- 모든 터미널 세션, 모든 모델에서 입력한 프롬프트 자동 저장
- 최신순 정렬, 실시간 갱신 (SSE)
- 검색, 클립보드 복사
- macOS 재시작 후에도 자동 실행 (LaunchAgent)

## 구조

```
hooks/
├── save_prompt.py      # UserPromptSubmit hook - 입력 저장 + SSE 알림
└── viewer_server.py    # HTTP 서버 (localhost:7878)
launchagent/
└── com.claude.prompt-history.plist  # macOS 자동 시작 설정
install.sh              # 설치 스크립트
```

## 설치

```bash
bash install.sh
```

`~/.claude/settings.json` 에 hook이 등록되어 있어야 합니다:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/save_prompt.py"
      }]
    }]
  }
}
```

## 사용

브라우저에서 [http://localhost:7878](http://localhost:7878) 접속

데이터 파일: `~/.claude/prompt_history.json`
