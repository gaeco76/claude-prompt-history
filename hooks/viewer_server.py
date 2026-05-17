#!/usr/bin/env python3
"""
Claude Code Prompt History - HTTP 서버 (SSE 실시간 갱신)
macOS LaunchAgent로 자동 시작, localhost:7878
"""
import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 7878
HISTORY_FILE = os.path.expanduser("~/.claude/prompt_history.json")

# SSE 클라이언트 큐 목록
_clients_lock = threading.Lock()
_clients: list[queue.Queue] = []


def _push_update():
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait("update")
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


def _read_history() -> bytes:
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return f.read().encode("utf-8")
    except Exception:
        pass
    return b"[]"


HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Claude Code Prompt History</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0d1117;color:#c9d1d9;font-family:'SF Mono','Fira Code',Consolas,monospace;font-size:13px;min-height:100vh}
  header{position:sticky;top:0;z-index:100;background:#161b22;border-bottom:1px solid #30363d;padding:12px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  h1{font-size:15px;color:#58a6ff;white-space:nowrap}
  #search{flex:1;min-width:200px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;padding:6px 12px;font-size:13px;font-family:inherit;outline:none}
  #search:focus{border-color:#58a6ff}
  #count{color:#8b949e;white-space:nowrap;font-size:12px}
  .pill{font-size:11px;padding:3px 10px;border-radius:20px;border:1px solid #30363d;color:#8b949e;white-space:nowrap;transition:all .3s}
  .pill.live{border-color:#3fb950;color:#3fb950}
  .pill.err{border-color:#f85149;color:#f85149}
  .pill.flash{border-color:#d2a679;color:#d2a679}
  main{padding:16px 20px;max-width:1200px;margin:0 auto}
  .entry{background:#161b22;border:1px solid #21262d;border-radius:8px;margin-bottom:10px;overflow:hidden;transition:border-color .15s}
  .entry:hover{border-color:#30363d}
  .entry.new-flash{border-color:#3fb95060;animation:flash .6s ease-out}
  @keyframes flash{0%{border-color:#3fb950}100%{border-color:#21262d}}
  .entry-header{display:flex;align-items:center;gap:10px;padding:7px 14px;background:#0d1117;border-bottom:1px solid #21262d;flex-wrap:wrap}
  .ts{color:#3fb950;font-size:11px;white-space:nowrap}
  .session{color:#8b949e;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px}
  .num{margin-left:auto;color:#484f58;font-size:11px}
  .copy-btn{background:none;border:1px solid #30363d;border-radius:4px;color:#8b949e;padding:2px 8px;font-size:11px;cursor:pointer;font-family:inherit;transition:all .15s}
  .copy-btn:hover{border-color:#58a6ff;color:#58a6ff}
  .entry-body{padding:12px 14px;white-space:pre-wrap;word-break:break-word;line-height:1.65;color:#e6edf3;max-height:300px;overflow-y:auto}
  .entry-body::-webkit-scrollbar{width:4px}
  .entry-body::-webkit-scrollbar-thumb{background:#30363d;border-radius:2px}
  mark{background:rgba(240,230,140,.25);border-radius:2px;color:inherit}
  #empty{text-align:center;color:#484f58;padding:60px 0;font-size:14px}
  #statusbar{text-align:center;color:#484f58;font-size:11px;padding:16px 0 28px}
</style>
</head>
<body>
<header>
  <h1>&#9654; Claude Code Prompt History</h1>
  <input id="search" type="text" placeholder="검색..." oninput="filterRender()">
  <span id="count"></span>
  <span class="pill live" id="pill">&#9679; LIVE</span>
</header>
<main id="list"></main>
<div id="statusbar"></div>
<script>
let allData=[], filtered=[], prevLen=0;

const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const hl=(t,q)=>{const s=esc(t);if(!q)return s;return s.replace(new RegExp(q.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&'),'gi'),m=>`<mark>${m}</mark>`)};
const fmtTs=iso=>{try{const d=new Date(iso),p=n=>String(n).padStart(2,'0');return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}catch{return iso}};

function filterRender(){
  const q=document.getElementById('search').value.trim().toLowerCase();
  filtered=q?allData.filter(e=>e.text.toLowerCase().includes(q)):[...allData];
  render(q);
}

function render(q=''){
  const list=document.getElementById('list');
  document.getElementById('count').textContent=filtered.length+' / '+allData.length+'개';
  if(!filtered.length){list.innerHTML='<div id="empty">저장된 입력이 없습니다</div>';return}
  const isNew=allData.length>prevLen;
  list.innerHTML=filtered.map((e,i)=>`
    <div class="entry${i===0&&isNew?' new-flash':''}" data-i="${i}">
      <div class="entry-header">
        <span class="ts">${fmtTs(e.ts)}</span>
        <span class="session" title="${esc(e.session_id||'')}">sid:${esc((e.session_id||'?').slice(-12))}</span>
        <button class="copy-btn" onclick="copyEntry(${i})">복사</button>
        <span class="num">#${e.num}</span>
      </div>
      <div class="entry-body">${hl(e.text,q)}</div>
    </div>`).join('');
}

async function fetchData(){
  try{
    const r=await fetch('/api/history');
    if(!r.ok)throw new Error();
    const d=await r.json();
    prevLen=allData.length;
    allData=d;
    filterRender();
    document.getElementById('statusbar').textContent='마지막 갱신: '+new Date().toLocaleString('ko-KR');
    const p=document.getElementById('pill');
    p.className='pill live'; p.textContent='● LIVE';
  }catch{
    const p=document.getElementById('pill');
    p.className='pill err'; p.textContent='✕ 연결 끊김';
  }
}

function copyEntry(i){
  navigator.clipboard.writeText(filtered[i].text).then(()=>{
    const btn=document.querySelector(`[data-i="${i}"] .copy-btn`);
    if(btn){btn.textContent='완료!';setTimeout(()=>btn.textContent='복사',1500)}
  });
}

// SSE 연결 - 서버 push 시 즉시 갱신
function connectSSE(){
  const es=new EventSource('/api/events');
  es.onmessage=()=>{
    const p=document.getElementById('pill');
    p.className='pill flash'; p.textContent='● 갱신 중...';
    fetchData();
  };
  es.onerror=()=>{
    const p=document.getElementById('pill');
    p.className='pill err'; p.textContent='✕ 재연결 중...';
    es.close();
    setTimeout(connectSSE, 3000);
  };
}

fetchData();
connectSSE();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/history":
            self._send(200, "application/json; charset=utf-8", _read_history())
        elif self.path == "/api/events":
            self._handle_sse()
        else:
            self._send(404, "text/plain", b"Not Found")

    def do_POST(self):
        if self.path == "/api/notify":
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            _push_update()
            self._send(200, "text/plain", b"ok")
        else:
            self._send(404, "text/plain", b"Not Found")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        q: queue.Queue = queue.Queue(maxsize=10)
        with _clients_lock:
            _clients.append(q)

        try:
            while True:
                try:
                    q.get(timeout=25)
                    self.wfile.write(b"data: update\n\n")
                except queue.Empty:
                    # heartbeat
                    self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
        except Exception:
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[prompt-history] http://localhost:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
