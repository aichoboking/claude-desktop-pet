# -*- coding: utf-8 -*-
"""
Claude Code Desktop Pet  -  fluffy sprite cat, true per-pixel transparency.

Renders illustrated sprite poses in a Win32 layered window (UpdateLayeredWindow),
so the fluffy soft edges stay transparent, empty areas are click-through, and the
cat is draggable. Character is chosen at random from whichever sprite sets exist
(baek 백이, kkam 깜이).

Poses:  idle 식빵 / sleep 자는식빵 / crawl 살금살금 / react 신남(작업 이벤트)
It speaks ONLY on Claude Code work events written into pet_event.json.

Quit / pet:  right-click -> 메뉴.   Drag: 고양이를 끌기.   Double-click: 쓰다듬기.
"""
import os, sys, json, math, random, time, traceback, subprocess
from ctypes import (windll, Structure, WINFUNCTYPE, byref, memmove, c_int,
                    c_uint, c_void_p, c_ubyte, c_ssize_t, c_size_t, POINTER,
                    c_wchar_p)
from ctypes.wintypes import (HWND, UINT, WPARAM, LPARAM, POINT, HDC, HBITMAP,
                             DWORD, BOOL, WORD, LONG, HANDLE, HINSTANCE, LPVOID)

HERE   = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):                 # running as a bundled .exe
    BASE = sys._MEIPASS                            # bundled read-only data (sprites)
    DATA = os.path.join(os.environ.get("LOCALAPPDATA",
                        os.path.dirname(sys.executable)), "ClaudePet")
    os.makedirs(DATA, exist_ok=True)
    # customization: if a "sprites" folder sits next to the .exe, use those
    # images instead of the bundled ones -> swap images = new character.
    _ext = os.path.join(os.path.dirname(sys.executable), "sprites")
    SPR  = _ext if os.path.isdir(_ext) else os.path.join(BASE, "sprites")
else:
    BASE = DATA = HERE
    SPR = os.path.join(BASE, "sprites")
EVENT  = os.path.join(DATA, "pet_event.json")
ERRLOG = os.path.join(DATA, "pet_error.log")

def log_err(msg):
    try:
        with open(ERRLOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

try:
    import winsound
except Exception:
    winsound = None

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ config
W, H      = 260, 190
FPS_MS    = 45
NAMES     = {"baek": "백이", "kkam": "깜이"}
GRACE_SEC     = 8      # wait before an alert actually shows (skips the terminal you're in)
ACTIVE_WINDOW = 75     # after you type in a project, don't nag that project for this long
MESSAGES  = {
    "done":    ["작업 다 끝냈다냥!", "미션 클리어! 완료했다냥",
                "짠— 다 됐다냥!", "작업 완료다냥!"],
    "waiting": ["네 차례라냥! 입력이 필요하다냥", "답을 기다린다냥~",
                "결정해줘야 한다냥!", "네 입력이 필요하다냥"],
    "check":   ["확인해달라냥!", "결과 좀 봐달라냥~",
                "확인할 게 있다냥", "리뷰 부탁한다냥"],
    "auto":    ["이 작업 확인해달라냥!", "여기 봐달라냥!",
                "이 터미널 확인해줘냥!"],
}
FEED_MSG  = ["냠냠 맛있다냥!", "잘 먹었다냥~", "더 줘도 된다냥!", "배부르다냥~"]
PET_MSG   = ["기분 좋다냥~", "골골골…", "한 번 더 쓰다듬어달라냥"]
GREET_MSG = {
    "morning":   ["좋은 아침이다냥!", "오늘도 화이팅이다냥!"],
    "noon":      ["점심 먹었냥?", "점심시간이다냥~"],
    "afternoon": ["나른한 오후다냥…", "커피 한잔 어떠냥?"],
    "evening":   ["오늘 하루 고생했다냥", "저녁이다냥~"],
    "night":     ["늦었다냥, 잘 자라냥…", "이제 쉬어야 한다냥"],
}
TALK_MSG = {
    "greet": ["안녕이라냥!", "만나서 반갑다냥~", "집사님 보고 싶었다냥!",
              "오늘도 함께라 좋다냥"],
    "quote": ["오늘도 럭키비키잖아냥~", "야호! 잘 풀리는 날이다냥",
              "중꺾마! 꺾여도 그냥 하는 거다냥", "갓생 살아보자고냥",
              "행복은 셀프다냥", "노빠꾸로 가보자냥",
              "지금의 네가 제일 잘하고 있다냥", "될 일은 된다냥, 걱정 말라냥",
              "오늘의 나, 개열일 예정이라냥"],
    "about": ["오늘도 콘텐츠 만드느라 고생 많다냥.", "네가 만든 카드뉴스, 반응 좋을 거다냥!",
              "보고서 쓰는 너, 진짜 멋지다냥.", "우리 집사님은 홍보 천재라냥!",
              "무리하지 말라냥, 집사님도 소중하다냥."],
    "small": ["물 한잔 마시고 오라냥~", "잠깐 스트레칭 한번 하자냥!",
              "창밖 구경하는 거 좋아하냥?", "간식 먹고 싶다냥…",
              "커피 한잔 어떠냥?"],
}

def period_now():
    h = time.localtime().tm_hour
    if 5 <= h < 11:  return "morning"
    if 11 <= h < 14: return "noon"
    if 14 <= h < 18: return "afternoon"
    if 18 <= h < 22: return "evening"
    return "night"
try:
    F_MSG  = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
    F_NAME = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 11)
except Exception:
    F_MSG = F_NAME = ImageFont.load_default()

# ------------------------------------------------------------------ sprites
def available_chars():
    return [c for c in ("baek", "kkam")
            if os.path.exists(os.path.join(SPR, f"{c}_idle.png"))]

def load_poses(char):
    poses = {}
    for p in ("idle", "sleep", "crawl", "crawl_r", "react", "eat", "happy"):
        fp = os.path.join(SPR, f"{char}_{p}.png")
        if os.path.exists(fp):
            poses[p] = Image.open(fp).convert("RGBA")
    poses.setdefault("crawl_r", poses["crawl"].transpose(Image.FLIP_LEFT_RIGHT))
    poses.setdefault("sleep", poses["idle"])
    poses.setdefault("react", poses["idle"])
    return poses

CHARS = available_chars()
if not CHARS:
    raise RuntimeError("no sprite sets found in " + SPR)
ALLPOSES = {c: load_poses(c) for c in CHARS}

# CLI: pet.pyw [baek|kkam] [slot]  — run two instances (slot 0 / 1) for an
# independently-movable, separately-draggable duo. slot 0 is the "owner" that
# shows the single shared speech bubble & plays the sound.
_arg_char = sys.argv[1] if len(sys.argv) > 1 else None
CHAR = _arg_char if _arg_char in CHARS else random.choice(CHARS)
try:
    SLOT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
except ValueError:
    SLOT = 0
OWNER = (SLOT == 0)
POSES = ALLPOSES[CHAR]
CNAME = NAMES.get(CHAR, CHAR)

# duo owner: partner char passed as a 3rd arg -> wider window, both names in the
# label, and the shared bubble nudged toward the partner so it reads as ONE
# bubble sitting over the pair.
PARTNER = sys.argv[3] if (OWNER and len(sys.argv) > 3 and sys.argv[3] in CHARS) else None
if PARTNER:
    W = 340
    CAT_X = W - 130
    BUB_DX = -78
    CNAME = f"{NAMES.get(CHAR, CHAR)} & {NAMES.get(PARTNER, PARTNER)}"
else:
    CAT_X = W // 2
    BUB_DX = 0

def _load(name):
    p = os.path.join(SPR, name)
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None
FOOD = _load("food.png")
BOWL = _load("bowl.png")

# ------------------------------------------------------------------ Win32
user32, gdi32, kernel32 = windll.user32, windll.gdi32, windll.kernel32
LRESULT = c_ssize_t
ULW_ALPHA = 0x02
AC_SRC_OVER, AC_SRC_ALPHA = 0x00, 0x01
WS_POPUP = 0x80000000
WS_EX_LAYERED, WS_EX_TOPMOST = 0x00080000, 0x00000008
WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x00000080, 0x08000000
SW_SHOWNOACTIVATE = 4
HWND_TOPMOST = HWND(-1)
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
CS_DBLCLKS = 0x0008
WM_DESTROY, WM_TIMER = 0x0002, 0x0113
WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
WM_LBUTTONDBLCLK, WM_RBUTTONUP = 0x0203, 0x0205
TPM_RETURNCMD, TPM_NONOTIFY = 0x0100, 0x0080
MF_STRING, MF_SEPARATOR, MF_GRAYED = 0x0000, 0x0800, 0x0001

class BLENDFUNCTION(Structure):
    _fields_ = [("BlendOp", c_ubyte), ("BlendFlags", c_ubyte),
                ("SourceConstantAlpha", c_ubyte), ("AlphaFormat", c_ubyte)]
class SIZE(Structure):
    _fields_ = [("cx", LONG), ("cy", LONG)]
class WNDCLASS(Structure):
    _fields_ = [("style", UINT), ("lpfnWndProc", c_void_p),
                ("cbClsExtra", c_int), ("cbWndExtra", c_int),
                ("hInstance", HINSTANCE), ("hIcon", HANDLE), ("hCursor", HANDLE),
                ("hbrBackground", HANDLE), ("lpszMenuName", c_wchar_p),
                ("lpszClassName", c_wchar_p)]
class BITMAPINFOHEADER(Structure):
    _fields_ = [("biSize", DWORD), ("biWidth", LONG), ("biHeight", LONG),
                ("biPlanes", WORD), ("biBitCount", WORD), ("biCompression", DWORD),
                ("biSizeImage", DWORD), ("biXPelsPerMeter", LONG),
                ("biYPelsPerMeter", LONG), ("biClrUsed", DWORD),
                ("biClrImportant", DWORD)]
class BITMAPINFO(Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", DWORD * 3)]
class MSG(Structure):
    _fields_ = [("hwnd", HWND), ("message", UINT), ("wParam", WPARAM),
                ("lParam", LPARAM), ("time", DWORD), ("pt", POINT)]

WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)

user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
user32.CreateWindowExW.restype = HWND
user32.CreateWindowExW.argtypes = [DWORD, c_wchar_p, c_wchar_p, DWORD, c_int,
                                   c_int, c_int, c_int, HWND, HANDLE, HINSTANCE,
                                   LPVOID]
user32.UpdateLayeredWindow.argtypes = [HWND, HDC, POINTER(POINT), POINTER(SIZE),
                                       HDC, POINTER(POINT), DWORD,
                                       POINTER(BLENDFUNCTION), DWORD]
user32.UpdateLayeredWindow.restype = BOOL
user32.SetWindowPos.argtypes = [HWND, HWND, c_int, c_int, c_int, c_int, UINT]
user32.GetDC.restype = HDC
user32.GetDC.argtypes = [HWND]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateDIBSection.restype = HBITMAP
gdi32.CreateDIBSection.argtypes = [HDC, POINTER(BITMAPINFO), UINT,
                                   POINTER(c_void_p), HANDLE, DWORD]
gdi32.SelectObject.restype = HANDLE
gdi32.SelectObject.argtypes = [HDC, HANDLE]
user32.SetTimer.restype = c_size_t
user32.SetTimer.argtypes = [HWND, c_size_t, UINT, LPVOID]

# 64-bit safety: give every handle-taking call proper argtypes
for _fn, _args, _res in [
    (user32.RegisterClassW, [POINTER(WNDCLASS)], WORD),
    (user32.ShowWindow, [HWND, c_int], BOOL),
    (user32.KillTimer, [HWND, c_size_t], BOOL),
    (user32.DestroyWindow, [HWND], BOOL),
    (user32.SetCapture, [HWND], HWND),
    (user32.ReleaseCapture, [], BOOL),
    (user32.GetCursorPos, [POINTER(POINT)], BOOL),
    (user32.SetForegroundWindow, [HWND], BOOL),
    (user32.CreatePopupMenu, [], HANDLE),
    (user32.AppendMenuW, [HANDLE, UINT, c_size_t, c_wchar_p], BOOL),
    (user32.TrackPopupMenu, [HANDLE, UINT, c_int, c_int, c_int, HWND, c_void_p], c_int),
    (user32.DestroyMenu, [HANDLE], BOOL),
    (user32.GetMessageW, [POINTER(MSG), HWND, UINT, UINT], c_int),
    (user32.TranslateMessage, [POINTER(MSG)], BOOL),
    (user32.DispatchMessageW, [POINTER(MSG)], LRESULT),
    (user32.GetSystemMetrics, [c_int], c_int),
    (kernel32.GetModuleHandleW, [c_wchar_p], HANDLE),
]:
    _fn.argtypes = _args
    _fn.restype = _res

# ------------------------------------------------------------------ state
state = {
    "pose": "idle", "t0": time.time(), "frame": 0,
    "bubble_text": "", "bubble_proj": "", "bubble_until": 0.0,
    "hop": 0.0, "crawl_start": 0.0, "crawl_end": 0.0, "crawl_dir": -1,
    "next_crawl": time.time() + random.randint(8, 16),
    "sleep_until": 0.0, "last_mtime": 0.0, "wx": 0, "wy": 0,
    "drag": False, "dxoff": 0, "dyoff": 0, "greet_period": None,
    "eat_start": 0.0, "eat_until": 0.0, "happy_until": 0.0,
    "pending": {}, "deferred": {}, "remind_idx": 0,
    "active_project": "", "active_at": 0.0, "scale": 1.0,
}
def _mtime():
    try: return os.path.getmtime(EVENT)
    except OSError: return 0.0
state["last_mtime"] = _mtime()

def play_sound():
    if winsound and OWNER:                      # only the owner cat beeps
        try: winsound.MessageBeep(0x00000040)
        except Exception: pass

def write_event(t, **extra):                    # menu actions go through the event
    try:                                        # file so both duo instances react
        payload = {"type": t, "ts": time.time()}; payload.update(extra)
        with open(EVENT, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False)
    except Exception:
        pass

def say(text, dur=6, project="", react=True, sound=True):
    state["bubble_text"] = text
    state["bubble_proj"] = project or ""
    state["bubble_until"] = time.time() + dur
    state["hop"] = 1.0
    if react:
        state["pose"] = "react"
    if sound:
        play_sound()

def clear_pending(project=None):
    if project and (project in state["pending"] or project in state["deferred"]):
        state["pending"].pop(project, None)   # multi-terminal: clear that project
        state["deferred"].pop(project, None)
    else:
        state["pending"].clear()              # single/unknown session: clear all
        state["deferred"].clear()

def speak(kind, text=None, project=None):     # queue a per-project alert (shown after grace)
    txt = text or random.choice(MESSAGES.get(kind, MESSAGES["auto"]))
    state["deferred"][project or "my pet"] = {"text": txt, "at": time.time() + GRACE_SEC}

def feed():
    now = time.time()
    state["eat_start"] = now
    state["eat_until"] = now + 5.0
    state["pose"] = "eat" if "eat" in POSES else "react"
    say(random.choice(FEED_MSG), dur=5.5, react=False)

def become_solo(char):                          # collapse to a single cat of `char`
    global CHAR, POSES, CNAME, PARTNER, BUB_DX
    if char in CHARS:
        CHAR = char; POSES = ALLPOSES[char]
    PARTNER = None; BUB_DX = 0; CNAME = NAMES.get(CHAR, CHAR)
    state["pose"] = "idle"; state["eat_until"] = 0.0; state["happy_until"] = 0.0
    say(f"{CNAME} 등장이다냥~", dur=4, sound=False)

def become_duo():                               # owner spawns the partner (once)
    global PARTNER, CNAME, BUB_DX
    if len(CHARS) < 2 or PARTNER is not None:
        return
    other = next(c for c in CHARS if c != CHAR)
    PARTNER = other; BUB_DX = -70
    CNAME = f"{NAMES.get(CHAR, CHAR)} & {NAMES.get(other, other)}"
    try:
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable, other, "1"], close_fds=True)
        else:
            subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0]), other, "1"],
                             close_fds=True)
    except Exception:
        pass
    say(f"{CNAME} 등장이다냥~", dur=4, sound=False)

def talk():
    cat = random.choice(list(TALK_MSG.keys()))
    say(random.choice(TALK_MSG[cat]), dur=6)

def toggle_size():
    state["scale"] = 0.5 if state["scale"] >= 1.0 else 1.0

def greet(period):
    msgs = GREET_MSG.get(period)
    if msgs:
        say(random.choice(msgs))

def pet_hop():                                  # petting -> blissful "happy" pose
    clear_pending()
    state["pose"] = "happy" if "happy" in POSES else "react"
    state["happy_until"] = time.time() + 3.5
    say(random.choice(PET_MSG), dur=4, sound=False, react=False)

def check_event():
    m = _mtime()
    if m and m != state["last_mtime"]:
        state["last_mtime"] = m
        try:
            d = json.load(open(EVENT, encoding="utf-8"))
            t = d.get("type", "done")
            if t == "feed":
                feed()
            elif t == "talk":
                talk()
            elif t == "pet":
                pet_hop()
            elif t == "size":
                toggle_size()
            elif t == "solo":                  # collapse to one cat (partner quits)
                if OWNER:
                    become_solo(d.get("char") or CHAR)
                else:
                    user32.DestroyWindow(_hwnd)
            elif t == "duo":                   # owner brings the partner back
                if OWNER:
                    become_duo()
            elif t == "clear":                 # user is active in this project's terminal
                proj = d.get("project")
                if proj:
                    state["active_project"] = proj; state["active_at"] = time.time()
                clear_pending(proj)
            else:
                speak(t, d.get("message"), d.get("project"))
        except Exception:
            speak("done")

def update_pose(now):
    p = state["pose"]
    if p == "happy":
        if now >= state["happy_until"]:
            state["pose"] = "idle"; state["next_crawl"] = now + random.randint(12, 26)
    elif p == "eat":
        if now >= state["eat_until"]:
            state["pose"] = "idle"; state["next_crawl"] = now + random.randint(12, 26)
    elif p == "react":
        if now > state["bubble_until"] and state["hop"] <= 0.05:
            state["pose"] = "idle"; state["next_crawl"] = now + random.randint(12, 26)
    elif p == "idle":
        if now >= state["next_crawl"]:
            if random.random() < 0.4:
                state["pose"] = "sleep"; state["sleep_until"] = now + random.randint(14, 26)
                state["next_crawl"] = now + random.randint(20, 36)
            else:
                state["pose"] = "crawl"; state["crawl_start"] = now
                state["crawl_end"] = now + 5.0; state["crawl_dir"] = random.choice((-1, 1))
    elif p == "sleep":
        if now >= state["sleep_until"]:
            state["pose"] = "idle"; state["next_crawl"] = now + random.randint(10, 22)
    elif p == "crawl":
        if now >= state["crawl_end"]:
            state["pose"] = "idle"; state["next_crawl"] = now + random.randint(14, 30)

# ------------------------------------------------------------------ drawing
def heart(draw, cx, cy, s, col):
    draw.pieslice([cx-s, cy-s, cx, cy], 0, 360, fill=col)
    draw.pieslice([cx, cy-s, cx+s, cy], 0, 360, fill=col)
    draw.polygon([(cx-s, cy-s*0.3), (cx+s, cy-s*0.3), (cx, cy+s*1.3)], fill=col)

def bubble(draw, cx, top, text, label):
    tw = draw.textlength(text, font=F_MSG)
    lw = draw.textlength(label, font=F_NAME)
    w = max(tw, lw) + 28
    h = 46
    x1, y1, x2, y2 = cx-w/2, top-h, cx+w/2, top
    x1 = max(4, min(x1, W-4-w)); x2 = x1 + w
    cx2 = x1 + w/2
    draw.rounded_rectangle([x1, y1, x2, y2], radius=14,
                           fill=(255, 255, 255, 245), outline=(226, 160, 180, 255), width=2)
    draw.polygon([(cx2-8, y2-2), (cx2+8, y2-2), (cx2, y2+11)], fill=(255, 255, 255, 245))
    draw.text((cx2, y1+13), label, font=F_NAME, fill=(176, 106, 134, 255), anchor="mm")
    draw.text((cx2, y1+31), text, font=F_MSG, fill=(74, 58, 68, 255), anchor="mm")

def render(now):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    f = state["frame"]
    s = state["scale"]
    bob = math.sin(f * 0.08) * 2 * s
    hop_e = abs(math.sin(f * 0.42)) * 15 * state["hop"] * s
    ground = H - 12
    pose = state["pose"]

    dx = 0
    if pose == "crawl":
        p = (now - state["crawl_start"]) / 5.0
        dx = state["crawl_dir"] * math.sin(min(p, 1.0) * math.pi) * 30 * s
        spr = POSES["crawl_r"] if state["crawl_dir"] > 0 else POSES["crawl"]
    else:
        spr = POSES.get(pose, POSES["idle"])
    if s != 1.0:
        spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.LANCZOS)

    sw, sh = spr.size
    cx = CAT_X + dx
    top = ground + bob - hop_e - sh
    if pose == "eat":
        top += math.sin(f * 0.5) * 3 * s
    img.alpha_composite(spr, (int(cx - sw / 2), int(top)))

    if state["hop"] > 0.12:
        for i in range(3):
            hx = cx + math.sin((f * 0.1) + i * 2) * 16
            hy = top - 10 - ((f * 2 + i * 22) % 46)
            heart(draw, hx, hy, 5 + i, (240, 122, 154, 235))

    if pose == "sleep":
        for i in range(3):
            zx = cx + sw * 0.30 + i * 11
            zy = top + 6 - i * 12 - (math.sin(f * 0.06 + i) * 2)
            draw.text((zx, zy), "Z", font=F_NAME, fill=(120, 170, 230, 230))

    if OWNER and now < state["bubble_until"]:      # only the owner shows the bubble
        proj = state["bubble_proj"]
        tag = (proj if len(proj) <= 16 else proj[:15] + "…") if proj else "my pet"
        bubble(draw, cx + BUB_DX, top - 6, state["bubble_text"], f"{CNAME}  ·  {tag}")
    return img

# ------------------------------------------------------------------ layered window plumbing
_screen_dc = user32.GetDC(None)
_mem_dc = gdi32.CreateCompatibleDC(_screen_dc)
_bmi = BITMAPINFO()
_bmi.bmiHeader.biSize = 40
_bmi.bmiHeader.biWidth = W
_bmi.bmiHeader.biHeight = -H          # top-down
_bmi.bmiHeader.biPlanes = 1
_bmi.bmiHeader.biBitCount = 32
_bmi.bmiHeader.biCompression = 0
_bits = c_void_p()
_dib = gdi32.CreateDIBSection(_mem_dc, byref(_bmi), 0, byref(_bits), None, 0)
gdi32.SelectObject(_mem_dc, _dib)
_blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

def push(img):
    # PIL RGBA -> premultiplied BGRA bytes
    r, g, b, a = img.split()
    from PIL import Image as _I
    bgra = _I.merge("RGBA", (b, g, r, a))
    import numpy as np
    arr = np.asarray(bgra).astype(np.uint16)
    al = arr[..., 3]
    arr[..., 0] = arr[..., 0] * al // 255
    arr[..., 1] = arr[..., 1] * al // 255
    arr[..., 2] = arr[..., 2] * al // 255
    data = arr.astype(np.uint8).tobytes()
    memmove(_bits, data, len(data))
    size = SIZE(W, H); psrc = POINT(0, 0)
    user32.UpdateLayeredWindow(_hwnd, _screen_dc, None, byref(size),
                               _mem_dc, byref(psrc), 0, byref(_blend), ULW_ALPHA)

def show_menu():
    hmenu = user32.CreatePopupMenu()
    if "baek" in CHARS:
        user32.AppendMenuW(hmenu, MF_STRING, 10, "백이만 보기")
    if "kkam" in CHARS:
        user32.AppendMenuW(hmenu, MF_STRING, 11, "깜이만 보기")
    if len(CHARS) >= 2:
        user32.AppendMenuW(hmenu, MF_STRING, 12, "두마리 보기")
    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(hmenu, MF_STRING, 4, "대화하기")
    user32.AppendMenuW(hmenu, MF_STRING, 1, "쓰다듬기")
    user32.AppendMenuW(hmenu, MF_STRING, 3, "먹이주기")
    user32.AppendMenuW(hmenu, MF_STRING, 5, "알림 지우기")
    user32.AppendMenuW(hmenu, MF_STRING, 6,
                       "크기 키우기" if state["scale"] < 1.0 else "크기 줄이기")
    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(hmenu, MF_STRING, 2, "펫 종료")
    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, 99, "made by @ai_chobo_king")
    pt = POINT(); user32.GetCursorPos(byref(pt))
    user32.SetForegroundWindow(_hwnd)
    cmd = user32.TrackPopupMenu(hmenu, TPM_RETURNCMD | TPM_NONOTIFY,
                                pt.x, pt.y, 0, _hwnd, None)
    user32.DestroyMenu(hmenu)
    if cmd == 1: write_event("pet")
    elif cmd == 4: write_event("talk")
    elif cmd == 3: write_event("feed")
    elif cmd == 5: write_event("clear")
    elif cmd == 6: write_event("size")
    elif cmd == 10: write_event("solo", char="baek")
    elif cmd == 11: write_event("solo", char="kkam")
    elif cmd == 12: write_event("duo")
    elif cmd == 2: user32.DestroyWindow(_hwnd)

def wndproc(hwnd, msg, wp, lp):
    if msg == WM_TIMER:
        now = time.time(); state["frame"] += 1
        if state["frame"] % 9 == 0: check_event()
        per = period_now()                       # time-based greeting
        if per != state["greet_period"]:
            state["greet_period"] = per
            greet(per)
        update_pose(now)
        if state["hop"] > 0: state["hop"] = max(0.0, state["hop"] - 0.035)
        if state["frame"] % 50 == 0:             # re-assert always-on-top so it can't get buried
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
        # promote deferred alerts once their grace passes — but never nag the
        # project you're actively typing in (that terminal holds/clears itself).
        promoted = False
        for k in list(state["deferred"].keys()):
            info = state["deferred"][k]
            if now < info["at"]:
                continue
            if k == state["active_project"] and now - state["active_at"] < ACTIVE_WINDOW:
                info["at"] = now + GRACE_SEC     # you're here; keep holding it
                continue
            state["pending"][k] = info["text"]
            del state["deferred"][k]
            promoted = True
        if promoted:
            play_sound()                          # one gentle sound when an alert surfaces
        # pending alerts: a QUIET standing bubble, cycling projects, until acknowledged
        pend = state["pending"]
        if pend and now >= state["bubble_until"]:
            keys = list(pend.keys())
            k = keys[state["remind_idx"] % len(keys)]
            state["remind_idx"] += 1
            state["bubble_text"] = pend[k]
            state["bubble_proj"] = "" if k == "my pet" else k
            state["bubble_until"] = now + 6
        try: push(render(now))
        except Exception: log_err(traceback.format_exc())
        return 0
    if msg == WM_LBUTTONDOWN:
        pt = POINT(); user32.GetCursorPos(byref(pt))
        state["drag"] = True
        state["dxoff"] = pt.x - state["wx"]; state["dyoff"] = pt.y - state["wy"]
        user32.SetCapture(hwnd); return 0
    if msg == WM_MOUSEMOVE and state["drag"]:
        pt = POINT(); user32.GetCursorPos(byref(pt))
        state["wx"] = pt.x - state["dxoff"]; state["wy"] = pt.y - state["dyoff"]
        user32.SetWindowPos(hwnd, HWND_TOPMOST, state["wx"], state["wy"], 0, 0,
                            SWP_NOSIZE | SWP_NOACTIVATE); return 0
    if msg == WM_LBUTTONUP:
        state["drag"] = False; user32.ReleaseCapture(); return 0
    if msg == WM_LBUTTONDBLCLK:
        write_event("pet"); return 0
    if msg == WM_RBUTTONUP:
        try: show_menu()
        except Exception: log_err(traceback.format_exc())
        return 0
    if msg == WM_DESTROY:
        user32.KillTimer(hwnd, 1); user32.PostQuitMessage(0); return 0
    return user32.DefWindowProcW(hwnd, msg, wp, lp)

_wndproc_cb = WNDPROC(wndproc)

def main():
    global _hwnd
    hInst = kernel32.GetModuleHandleW(None)
    cls = WNDCLASS()
    cls.style = CS_DBLCLKS
    cls.lpfnWndProc = cast_wndproc()
    cls.hInstance = hInst
    cls.lpszClassName = "ClaudePetWnd"
    user32.RegisterClassW(byref(cls))

    sw = user32.GetSystemMetrics(0); sh = user32.GetSystemMetrics(1)
    state["wx"] = sw - W - 30 - SLOT * 150; state["wy"] = sh - H - 60
    _hwnd = user32.CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        "ClaudePetWnd", "Claude Pet", WS_POPUP,
        state["wx"], state["wy"], W, H, None, None, hInst, None)
    user32.ShowWindow(_hwnd, SW_SHOWNOACTIVATE)
    push(render(time.time()))
    user32.SetTimer(_hwnd, 1, FPS_MS, None)

    msg = MSG()
    while user32.GetMessageW(byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(byref(msg))
        user32.DispatchMessageW(byref(msg))

from ctypes import cast, c_void_p as _cvp
def cast_wndproc():
    return cast(_wndproc_cb, _cvp)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_err(traceback.format_exc())
