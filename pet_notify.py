# -*- coding: utf-8 -*-
"""
Writes a signal file that the desktop pet watches.

Usage:
    python pet_notify.py <type> [message] [topic]
      type   : done | waiting | feed | talk | clear
      message: optional bubble text (else a random line for that type)
      topic  : optional short project/topic name shown as "이름 · <topic>"

Project resolution (so multiple terminals label their own alerts):
      explicit <topic> arg  >  $PET_PROJECT env  >  folder name of the
      session's cwd (from the hook's stdin JSON).
Set PET_PROJECT per terminal (before launching claude) to name that window,
e.g.  export PET_PROJECT="AI펫"   /   $env:PET_PROJECT = "X관련 PPT"

Examples:
    python pet_notify.py done "리포트 완성했다냥" "X관련 PPT"
    python pet_notify.py waiting      # (Notification hook; picks up env/cwd)
    python pet_notify.py clear        # (UserPromptSubmit hook; clears that project)
"""
import os, sys, json, time

HERE  = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):                 # bundled .exe: share event file location
    DATA = os.path.join(os.environ.get("LOCALAPPDATA",
                        os.path.dirname(sys.executable)), "ClaudePet")
    os.makedirs(DATA, exist_ok=True)
else:
    DATA = HERE
kind  = sys.argv[1] if len(sys.argv) > 1 else "done"
msg   = sys.argv[2] if len(sys.argv) > 2 else None
topic = sys.argv[3] if len(sys.argv) > 3 else None

# read the hook's stdin JSON (if any) for this session's cwd
cwd = None
try:
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw and raw.strip():
            cwd = json.loads(raw).get("cwd")
except Exception:
    pass

project = topic or os.environ.get("PET_PROJECT")
if not project and cwd:
    project = os.path.basename(os.path.normpath(cwd))

EV = os.path.join(DATA, "pet_event.json")

# the automatic (Stop-hook) alert must not clobber a fresh explicit alert
if kind == "auto":
    try:
        if os.path.exists(EV) and time.time() - os.path.getmtime(EV) < 3:
            prev = json.load(open(EV, encoding="utf-8"))
            if prev.get("type") in ("done", "waiting", "check"):
                sys.exit(0)
    except Exception:
        pass

payload = {"type": kind, "ts": time.time()}
if msg:     payload["message"] = msg
if project: payload["project"] = project

with open(EV, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)
