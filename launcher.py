"""
Betty Companion: the control window. Staff use it instead of bettycomplaunch.bat.

    BettyCompanion.exe              this window
    BettyCompanion.exe --backend    the program itself (betty_companion.main), started and stopped by this window
    python launcher.py              the same, from the source folder

The window runs the program as a second process and talks to it through pipes: commands one per line on its stdin
(start, pause, test, live, status, quit), status events as JSON lines on its stdout (betty_companion section 7).
When the window closes, its end of the pipe closes and the program shuts down, so it never runs unwatched.

Tabs: Controls (Start / Pause / Stop, the live / test switch), System (this run's and the previous run's log, the
errors explained, what staff had to do, and Settings: pairing with the relay), Data (today's racecard files and
meetings), Runners (every UK & Irish horse runner today). The bar at the bottom always shows whether it's ready to
automate (hover for why not) and whether Gemini is online.
"""
import collections
import ctypes
import ctypes.wintypes as wt
import datetime
import glob
import json
import os
import queue
import re
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from functools import lru_cache
from tkinter import messagebox, ttk

from PIL import Image, ImageDraw, ImageFilter, ImageTk

import app_paths

WINDOW_TITLE = "Betty Companion"
REQUIRED_SCREEN = (1366, 768)
GEMINI_CHECK_SECS = 300   # the free Gemini check, every 5 minutes (and on a click)
DATA_REFRESH_SECS = 60    # racecards, meetings and runners
HEALTH_SECS = 5           # the ready light
LOG_TAIL_SECS = 1.5
STOP_WAIT_SECS = 15       # Stop: the program gets this long to finish before it is ended
CREATE_NO_WINDOW = 0x08000000

GREEN, RED, AMBER, GREY = "#2E7D32", "#C62828", "#F9A825", "#78909C"
LIVE_COLOUR, TEST_COLOUR = "#E65100", "#4A148C"  # the overlay's colours: orange = live, purple = test
BAR_BG = "#263238"
SWITCH_OFF = "#B0BEC5"


def app_version() -> str:
    """VERSION inside the build (written by build_release.py), else __version__ in betty_companion.py."""
    try:
        with open(os.path.join(app_paths.bundle_dir(), "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        pass
    try:
        with open(os.path.join(app_paths.app_dir(), "betty_companion.py"), encoding="utf-8") as f:
            m = re.search(r'^__version__\s*=\s*"([^"]+)"', f.read(4096), re.MULTILINE)
            return m.group(1) if m else "?"
    except OSError:
        return "?"


# --- Checks for the ready light (all cheap enough for every few seconds) ---

def screen_size() -> tuple[int, int]:
    user32 = ctypes.windll.user32
    return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))


def betty_open() -> bool:
    """A visible full-size window of Betty's program (bets.exe) is open."""
    betty_exe = os.environ.get("BETTY_EXE", "bets.exe").strip().lower()
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def visit(hwnd, _):
        rect = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if user32.IsWindowVisible(hwnd) and rect.right - rect.left > 200:
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            handle = kernel32.OpenProcess(0x1000, False, pid.value)
            if handle:
                buf, size = ctypes.create_unicode_buffer(260), wt.DWORD(260)
                kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
                kernel32.CloseHandle(handle)
                if os.path.basename(buf.value).lower() == betty_exe:
                    found.append(hwnd)
                    return False
        return True

    user32.EnumWindows(visit, 0)
    return bool(found)


# --- Today's racecards, meetings and runners (read on a background thread) ---

def racecard_files(day: datetime.date | None = None) -> list[dict]:
    """Today's horse and greyhound feed files in Betty's Events folder: file, sport, when Betty last wrote it, size, races."""
    import betty_feed
    events_dir = betty_feed.events_folder()
    prefix = betty_feed.feed_prefix(day or datetime.date.today())
    try:
        names = sorted(f for f in os.listdir(events_dir) if f.startswith(prefix) and f.lower().endswith(".dat"))
    except OSError:
        return []
    files = []
    for name in names:
        path = os.path.join(events_dir, name)
        sport = betty_feed.RACING_SPORTS.get(betty_feed.feed_sport(path))
        if not sport:
            continue
        try:
            with open(path, "rb") as f:
                races = betty_feed.decode_feed(f.read())
            real = [r for r in races if r["country"] != "VR"]
            if not real:
                continue  # a virtual-only feed
            files.append({"file": name, "sport": sport, "modified": os.path.getmtime(path),
                          "size": os.path.getsize(path), "races": len(real), "error": ""})
        except (OSError, ValueError, struct.error) as e:
            files.append({"file": name, "sport": sport, "modified": 0, "size": 0, "races": 0, "error": str(e)})
    return files


def meeting_groups(meetings: list[dict]) -> dict[str, list[dict]]:
    """todays_meetings() split four ways for the Data tab; virtual racing is left out, Australia is international."""
    groups: dict[str, list[dict]] = {"horse_home": [], "horse_intl": [], "dog_home": [], "dog_intl": []}
    for m in meetings:
        if m["region"] == "Virtual":
            continue
        kind = "horse" if m["sport"] == "Horses" else "dog"
        groups[f"{kind}_{'home' if m['region'] == 'UK/IRE' else 'intl'}"].append(m)
    return groups


class RacecardReader:
    """Keeps one feed reader and one off-time reader, so each refresh only re-reads what Betty has changed."""

    def __init__(self):
        self.card = None
        self.offs = None

    def uk_irish_runners(self) -> list[dict]:
        import betty_feed
        if self.card is None:
            from meetings_manager import meetings_manager
            self.card = betty_feed.BettyFeedCard(category_resolver=lambda m: meetings_manager.resolve_meeting(m)[0])
            self.offs = betty_feed.BettyOffTimes()
        runners = [dict(r) for r in self.card.get_runners() if r.get("category") == "domestic"]
        try:
            self.offs.mark(runners)
        except Exception:
            pass
        return sorted(runners, key=lambda r: (r["minutes"], r["meeting"], r["number"]))

    def read(self) -> dict:
        import betty_feed
        out = {"event": "_data", "files": [], "groups": meeting_groups([]), "runners": [], "error": "",
               "events_dir": betty_feed.events_folder()}
        try:
            out["files"] = racecard_files()
            out["groups"] = meeting_groups(betty_feed.todays_meetings())
            out["runners"] = self.uk_irish_runners()
        except Exception as e:
            out["error"] = f"{type(e).__name__}: {e}"
        return out


# --- The program, as a second process ---

class Backend:
    """betty_companion run with --backend: commands in on its stdin, status events (dicts) out to `inbox`."""

    def __init__(self, inbox: queue.Queue):
        self.inbox = inbox
        self.proc: subprocess.Popen | None = None
        self.stderr_tail: collections.deque = collections.deque(maxlen=40)
        self.quitting = False

    @staticmethod
    def command() -> list[str]:
        override = os.environ.get("BETTY_BACKEND_CMD")  # the free tests' stand-in program
        if override:
            return json.loads(override)
        if app_paths.is_frozen():
            return [sys.executable, "--backend"]
        return [sys.executable, os.path.join(app_paths.app_dir(), "betty_companion.py"), "--backend"]

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    @property
    def pid(self) -> int | None:
        return self.proc.pid if self.proc else None

    def launch(self):
        self.quitting = False
        self.stderr_tail.clear()
        self.proc = subprocess.Popen(self.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, cwd=app_paths.app_dir(), creationflags=CREATE_NO_WINDOW)
        threading.Thread(target=self._read_events, args=(self.proc,), daemon=True).start()
        threading.Thread(target=self._read_errors, args=(self.proc,), daemon=True).start()

    def _read_events(self, proc: subprocess.Popen):
        for raw in proc.stdout:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                event = {"event": "noise", "text": line}
            self.inbox.put(event)
        code = proc.wait()
        time.sleep(0.2)  # the last stderr lines
        self.inbox.put({"event": "exited", "code": code, "expected": self.quitting, "pid": proc.pid,
                        "stderr": list(self.stderr_tail)})

    def _read_errors(self, proc: subprocess.Popen):
        for raw in proc.stderr:
            self.stderr_tail.append(raw.decode("utf-8", "replace").rstrip())

    def send(self, command: str) -> bool:
        if not self.alive():
            return False
        try:
            self.proc.stdin.write((command + "\n").encode("utf-8"))
            self.proc.stdin.flush()
            return True
        except OSError:
            return False

    def stop(self, wait: float = STOP_WAIT_SECS):
        """Stop: 'quit' (the watcher off, a wager in hand let go), then `wait` seconds before the process is ended."""
        if not self.alive():
            return
        self.quitting = True
        proc = self.proc
        if not self.send("quit"):
            proc.kill()
            return

        def _end():
            try:
                proc.wait(timeout=wait)
            except subprocess.TimeoutExpired:
                proc.kill()
        threading.Thread(target=_end, daemon=True).start()


# --- Logs and the staff journal (logs/ next to the exe) ---

def session_logs() -> list[str]:
    """Session logs, newest first."""
    return sorted(glob.glob(os.path.join(app_paths.log_dir(), "session_*.log")), reverse=True)


def read_journal(days: int = 30) -> list[dict]:
    """logs/staff_journal.jsonl: wagers left for staff and selections staff typed, newest first."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    entries = []
    try:
        with open(os.path.join(app_paths.log_dir(), "staff_journal.jsonl"), encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("date", "") >= cutoff:
                    entries.append(e)
    except OSError:
        pass
    return sorted(entries, key=lambda e: (e.get("date", ""), e.get("time", "")), reverse=True)


# Logs from 28 Oct start each line with its time ('15:35:25 [!] Wager ...'); older ones don't
STAFF_LINE = re.compile(r"^(?:(?P<time>\d{2}:\d{2}:\d{2}) )?\[!\] Wager (?P<wager>\S+) needs staff: (?P<reason>.+)$")
SHOT_NAME = re.compile(r"^staff_(.+)_(\d{8})_(\d{6})\.png$")


def staff_screenshots() -> dict[str, dict]:
    """logs/staff_<wager>_<date>_<time>.png by wager: {path, date, time}."""
    shots = {}
    for path in glob.glob(os.path.join(app_paths.log_dir(), "staff_*.png")):
        m = SHOT_NAME.match(os.path.basename(path))
        if m:
            d, t = m.group(2), m.group(3)
            shots[m.group(1)] = {"path": path, "date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "time": f"{t[:2]}:{t[2:4]}:{t[4:]}"}
    return shots


def staff_from_logs(paths: list[str]) -> list[dict]:
    """Wagers left for staff in these logs (runs before the journal existed), timed by their screenshot, else by
    the log line's own time."""
    shots = staff_screenshots()
    found, seen = [], set()
    for path in paths:
        stamp = re.search(r"session_(\d{8})_(\d{6})", path)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = STAFF_LINE.match(line.strip())
                    if not m or (m["wager"], m["reason"]) in seen:
                        continue
                    seen.add((m["wager"], m["reason"]))
                    shot = shots.get(m["wager"], {})
                    date = shot.get("date") or (f"{stamp.group(1)[:4]}-{stamp.group(1)[4:6]}-{stamp.group(1)[6:]}" if stamp else "")
                    found.append({"kind": "staff", "wager": m["wager"], "reason": m["reason"], "date": date,
                                  "time": shot.get("time") or m["time"] or "", "screenshot": shot.get("path"), "from_log": True})
        except OSError:
            continue
    return found


# --- Drawn widgets: rounded buttons, the live / test switch, status dots ---
# Drawn with Pillow at SS times the size and scaled down, so the edges are smooth (tk's own canvas shapes are jagged),
# onto the parent's background colour, so nothing relies on transparency.

SS = 4
BUTTON_PAD = 4  # room around a button for its shadow


def _rgb(widget: tk.Misc, colour: str) -> tuple[int, int, int]:
    r, g, b = widget.winfo_rgb(colour)
    return r >> 8, g >> 8, b >> 8


def _mix(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    """a moved t of the way to b."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _background(widget: tk.Misc) -> str:
    """The colour behind a widget placed in `widget` (a tk or ttk frame)."""
    try:
        return widget.cget("background")
    except tk.TclError:  # ttk: the theme's colour
        return ttk.Style(widget).lookup(widget.winfo_class(), "background") or "SystemButtonFace"


@lru_cache(maxsize=None)
def _button_image(w: int, h: int, fill: tuple, bg: tuple, border: tuple | None, shadow: bool) -> Image.Image:
    """A rounded button w x h with a soft top-lit gradient and a drop shadow, BUTTON_PAD inside its image."""
    pad, radius = BUTTON_PAD * SS, 9 * SS
    size = ((w + 2 * BUTTON_PAD) * SS, (h + 2 * BUTTON_PAD) * SS)
    box = (pad, pad, pad + w * SS - 1, pad + h * SS - 1)
    img = Image.new("RGB", size, bg)
    if shadow:
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((box[0], box[1] + 2 * SS, box[2], box[3] + 2 * SS), radius, fill=60)
        img.paste((0, 0, 0), mask=mask.filter(ImageFilter.GaussianBlur(2.5 * SS)))
    top = _mix(fill, (255, 255, 255), 0.14)
    column = Image.new("RGB", (1, size[1]))
    column.putdata([_mix(top, fill, min(1.0, max(0.0, (y - pad) / (h * SS)))) for y in range(size[1])])
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius, fill=255)
    img.paste(column.resize(size), mask=mask)
    if border:
        ImageDraw.Draw(img).rounded_rectangle(box, radius, outline=border, width=SS)
    return img.resize((w + 2 * BUTTON_PAD, h + 2 * BUTTON_PAD), Image.LANCZOS)


@lru_cache(maxsize=None)
def _switch_image(w: int, h: int, on: tuple, off: tuple, bg: tuple, t: float) -> Image.Image:
    """The switch t of the way from off (0, knob left, grey track) to on (1, knob right, coloured track)."""
    size = (w * SS, h * SS)
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), size[1] // 2, fill=_mix(off, on, t))
    inset = 3 * SS
    knob = size[1] - 2 * inset
    x = inset + round(t * (size[0] - size[1]))
    shadow = Image.new("L", size, 0)
    ImageDraw.Draw(shadow).ellipse((x, inset + SS, x + knob, inset + knob + SS), fill=70)
    img.paste((0, 0, 0), mask=shadow.filter(ImageFilter.GaussianBlur(1.5 * SS)))
    draw.ellipse((x, inset, x + knob, inset + knob), fill=(255, 255, 255))
    return img.resize((w, h), Image.LANCZOS)


@lru_cache(maxsize=None)
def _dot_image(d: int, fill: tuple, bg: tuple) -> Image.Image:
    img = Image.new("RGB", (d * SS, d * SS), bg)
    ImageDraw.Draw(img).ellipse((0, 0, d * SS - 1, d * SS - 1), fill=fill)
    return img.resize((d, d), Image.LANCZOS)


class RoundButton(tk.Canvas):
    """
    A rounded button with a soft shadow, and hover, pressed and disabled shades. Takes configure(text=, state=) like
    a tk.Button. `primary` buttons are filled with `colour`; the others are white with a thin border.
    """

    def __init__(self, parent, text: str, command, colour: str = "#FFFFFF", fg: str = "#263238",
                 width: int | None = None, height: int = 32, font=("Segoe UI Semibold", 10), primary: bool = False):
        self.bg = _background(parent)
        self.font = tkfont.Font(parent, font=font)
        self.fixed_width, self.h = width, height
        self.w = width or 0
        super().__init__(parent, height=height + 2 * BUTTON_PAD, bg=self.bg, highlightthickness=0, bd=0, cursor="hand2")
        self.command, self.colour, self.fg, self.primary = command, colour, fg, primary
        self.text, self.state, self.look = text, "normal", "normal"
        self.photos: dict[str, ImageTk.PhotoImage] = {}
        self.image = self.create_image(0, 0, anchor="nw")
        self.label = self.create_text(0, 0, text=text, font=self.font)
        self.bind("<Enter>", lambda e: self._look("hover"))
        self.bind("<Leave>", lambda e: self._look("normal"))
        self.bind("<ButtonPress-1>", lambda e: self._look("pressed"))
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def _draw(self):
        self.w = self.fixed_width or self.font.measure(self.text) + 36
        bg = _rgb(self, self.bg)
        fill = _rgb(self, self.colour)
        border = None if self.primary else _rgb(self, "#CFD8DC")
        hover = _mix(fill, (255, 255, 255), 0.1) if self.primary else _mix(fill, (0, 0, 0), 0.04)
        shades = {"normal": fill, "hover": hover, "pressed": _mix(fill, (0, 0, 0), 0.14 if self.primary else 0.08),
                  "disabled": _mix(fill, bg, 0.55)}
        self.photos = {look: ImageTk.PhotoImage(_button_image(self.w, self.h, shade, bg, border, look != "disabled"))
                       for look, shade in shades.items()}
        tk.Canvas.configure(self, width=self.w + 2 * BUTTON_PAD)
        self.coords(self.label, BUTTON_PAD + self.w / 2, BUTTON_PAD + self.h / 2)
        self._paint()

    def _paint(self):
        look = "disabled" if self.state == "disabled" else self.look
        self.itemconfigure(self.image, image=self.photos[look])
        fg = _mix(_rgb(self, self.fg), _rgb(self, self.bg), 0.45) if self.state == "disabled" else _rgb(self, self.fg)
        self.itemconfigure(self.label, text=self.text, fill="#%02x%02x%02x" % fg)
        tk.Canvas.configure(self, cursor="arrow" if self.state == "disabled" else "hand2")

    def _look(self, look: str):
        self.look = look
        self._paint()

    def _release(self, e):
        inside = 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height()
        self._look("hover" if inside else "normal")
        if inside and self.state != "disabled" and self.command:
            self.command()

    def configure(self, cnf=None, **kw):
        text, state = kw.pop("text", None), kw.pop("state", None)
        if kw or cnf:
            super().configure(cnf, **kw)
        if text is not None and text != self.text:
            self.text = text
            self._draw()
        if state is not None and state != self.state:
            self.state = state
            self._paint()

    config = configure

    def cget(self, key):
        return {"text": self.text, "state": self.state}.get(key) or super().cget(key)

    __getitem__ = cget


class Switch(tk.Canvas):
    """A phone-style on / off switch. A click calls `command`; set() moves it (with a short slide)."""
    FRAMES = 7

    def __init__(self, parent, command, on_colour: str, off_colour: str = SWITCH_OFF, width: int = 46, height: int = 26):
        bg = _background(parent)
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        on, off, back = _rgb(self, on_colour), _rgb(self, off_colour), _rgb(self, bg)
        self.frames = [ImageTk.PhotoImage(_switch_image(width, height, on, off, back, i / (self.FRAMES - 1)))
                       for i in range(self.FRAMES)]
        self.pos, self.target = 0, None
        self.image = self.create_image(0, 0, anchor="nw", image=self.frames[0])
        self.bind("<Button-1>", lambda e: command())

    def set(self, on: bool):
        target = self.FRAMES - 1 if on else 0
        if self.target is None:  # the first time: no slide
            self.pos = target
            self.itemconfigure(self.image, image=self.frames[target])
        if target != self.target:
            self.target = target
            self._slide()

    def _slide(self):
        if self.pos == self.target:
            return
        self.pos += 1 if self.target > self.pos else -1
        self.itemconfigure(self.image, image=self.frames[self.pos])
        self.after(16, self._slide)


# --- The window ---

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.inbox: queue.Queue = queue.Queue()
        self.backend = Backend(self.inbox)
        self.version = app_version()
        self.state = "stopped"          # stopped | loading | ready | stopping
        self.watcher: dict = {}         # the last 'state' event
        self.want_test = False          # the mode button: Live by default
        self.start_when_ready = False
        self.closing = False
        self.fatal = ""
        self.gemini = {"ok": None, "text": "checking..."}
        self.gemini_busy = False
        self.data: dict = {}
        self.data_busy = False
        self.reader = RacecardReader()
        self.live_errors: list[dict] = []
        self.pairing: dict | None = None
        self.log_path = ""
        self.log_offset = 0
        self.backend_log = ""
        self._image = None
        self.dot_photos: dict[str, ImageTk.PhotoImage] = {}
        self.records: list[dict] = []
        self.staff_rows: dict[str, dict] = {}
        self.error_rows: dict[str, dict] = {}

        root.title(WINDOW_TITLE)
        root.geometry("900x600")
        root.minsize(760, 500)
        try:
            root.iconbitmap(os.path.join(app_paths.bundle_dir(), "assets", "betty.ico"))
        except tk.TclError:
            pass
        style = ttk.Style(root)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=22)
        style.configure("Big.TLabel", font=("Segoe UI", 11))
        style.configure("Head.TLabel", font=("Segoe UI", 11, "bold"))

        self._build_status_bar()
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self._build_controls()
        self._build_system()
        self._build_data()
        self._build_runners()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(100, self._drain)
        root.after(200, self.check_health)
        root.after(300, self.check_gemini)
        root.after(400, self.refresh_data)
        root.after(500, self.reload_records)
        root.after(600, self.save_betty_drive)
        root.after(600, self._tail_log)
        self._show_program()
        self._show_relay()

    # --- Building the tabs ---

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BAR_BG)
        bar.pack(side="bottom", fill="x")
        self.ready_dot = tk.Canvas(bar, width=16, height=16, bg=BAR_BG, highlightthickness=0)
        self.ready_dot.pack(side="left", padx=(10, 6), pady=6)
        self.ready_text = tk.Label(bar, text="Checking", fg="#FFFFFF", bg=BAR_BG, font=("Segoe UI Semibold", 10))
        self.ready_text.pack(side="left")
        self.ready_detail = ""  # why it isn't ready, shown on hover
        self.ready_tip: tk.Toplevel | None = None
        for w in (self.ready_dot, self.ready_text):
            w.bind("<Enter>", lambda e: self._show_ready_tip())
            w.bind("<Leave>", lambda e: self._hide_ready_tip())
        tk.Label(bar, text=self.version and f"v{self.version}", fg="#B0BEC5", bg=BAR_BG,
                 font=("Segoe UI", 9)).pack(side="right", padx=10)
        self.gemini_text = tk.Label(bar, text="Gemini: checking...", fg="#FFFFFF", bg=BAR_BG,
                                    font=("Segoe UI", 10), cursor="hand2")
        self.gemini_text.pack(side="right", padx=(0, 16))
        self.gemini_dot = tk.Canvas(bar, width=16, height=16, bg=BAR_BG, highlightthickness=0, cursor="hand2")
        self.gemini_dot.pack(side="right", padx=(10, 6))
        for w in (self.gemini_text, self.gemini_dot):
            w.bind("<Button-1>", lambda e: self.check_gemini(force=True))

    def _dot(self, canvas: tk.Canvas, colour: str):
        if colour not in self.dot_photos:
            self.dot_photos[colour] = ImageTk.PhotoImage(_dot_image(12, _rgb(canvas, colour), _rgb(canvas, BAR_BG)))
        canvas.delete("all")
        canvas.create_image(8, 8, image=self.dot_photos[colour])

    def _show_ready_tip(self):
        self._hide_ready_tip()
        if not self.ready_detail:
            return
        tip = self.ready_tip = tk.Toplevel(self.root)
        tip.wm_overrideredirect(True)
        tk.Label(tip, text=self.ready_detail, bg="#37474F", fg="#FFFFFF", font=("Segoe UI", 9), justify="left",
                 padx=10, pady=6).pack()
        tip.update_idletasks()
        tip.geometry(f"+{self.ready_dot.winfo_rootx()}+{self.ready_dot.winfo_rooty() - tip.winfo_height() - 10}")

    def _hide_ready_tip(self):
        if self.ready_tip is not None:
            self.ready_tip.destroy()
            self.ready_tip = None

    def _build_controls(self):
        tab = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(tab, text="  Controls  ")

        buttons = tk.Frame(tab)
        buttons.pack(fill="x")
        big = {"width": 132, "height": 44, "font": ("Segoe UI Semibold", 12), "primary": True}
        self.start_btn = RoundButton(buttons, "\u25B6  Start", self.on_start, colour="#2E7D32", fg="#FFFFFF", **big)
        self.pause_btn = RoundButton(buttons, "\u275A\u275A  Pause", self.on_pause, colour="#F9A825", fg="#212121", **big)
        self.stop_btn = RoundButton(buttons, "\u25A0  Stop", self.on_stop, colour="#C62828", fg="#FFFFFF", **big)
        for b in (self.start_btn, self.pause_btn, self.stop_btn):
            b.pack(side="left", padx=(0, 6))

        mode = tk.Frame(buttons)
        mode.pack(side="right")
        self.mode_switch = Switch(mode, self.on_mode, on_colour=LIVE_COLOUR)
        self.mode_switch.pack(side="right", padx=(10, 0))
        self.mode_title = tk.Label(mode, font=("Segoe UI Semibold", 11), anchor="e")
        self.mode_title.pack(anchor="e")
        self.mode_caption = tk.Label(mode, font=("Segoe UI", 9), fg="#546E7A", anchor="e")
        self.mode_caption.pack(anchor="e")
        for w in (self.mode_title, self.mode_caption):
            w.configure(cursor="hand2")
            w.bind("<Button-1>", lambda e: self.on_mode())
        self.loading = ttk.Progressbar(tab, mode="indeterminate")

        info = ttk.Frame(tab)
        info.pack(fill="x", pady=(16, 8))
        self.info: dict[str, ttk.Label] = {}
        for row, (key, label) in enumerate([("program", "Program"), ("watcher", "Watcher"), ("screen", "Betty shows"),
                                            ("wager", "Wager"), ("message", "Last message"),
                                            ("outcome", "Last outcome"), ("reader", "Slip reader")]):
            ttk.Label(info, text=label, style="Head.TLabel", width=13).grid(row=row, column=0, sticky="nw", pady=2)
            self.info[key] = ttk.Label(info, text="", style="Big.TLabel", wraplength=640, justify="left")
            self.info[key].grid(row=row, column=1, sticky="w", pady=2)

    def _build_settings(self, inner: ttk.Notebook):
        """System > Settings: pairing this till with the relay."""
        tab = ttk.Frame(inner, padding=10)
        inner.add(tab, text=" Settings ")
        relay = ttk.LabelFrame(tab, text=" Relay: the slip reader's connection ", padding=10)
        relay.pack(fill="x")
        self.relay_status = ttk.Label(relay, text="", style="Big.TLabel", wraplength=780, justify="left")
        self.relay_status.grid(row=0, column=0, columnspan=4, sticky="w")
        self.relay_form = ttk.Frame(relay)
        self.relay_form.grid(row=1, column=0, columnspan=4, sticky="we", pady=(8, 0))
        ttk.Label(self.relay_form, text="Relay address").grid(row=0, column=0, sticky="w")
        import relay_link
        self.relay_url = tk.StringVar(value=relay_link.default_relay_url())
        ttk.Entry(self.relay_form, textvariable=self.relay_url, width=46).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Label(self.relay_form, text="Till name").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.till_name = tk.StringVar(value=relay_link.default_till_name())
        ttk.Entry(self.relay_form, textvariable=self.till_name, width=22).grid(row=0, column=3, padx=6, sticky="w")
        self.relay_code = tk.Label(relay, text="", font=("Consolas", 26, "bold"), fg="#0D47A1")
        self.relay_code.grid(row=2, column=0, columnspan=4, sticky="w")
        actions = ttk.Frame(relay)
        actions.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.pair_btn = RoundButton(actions, "Pair this till", self.on_pair, colour="#0D47A1", fg="#FFFFFF", primary=True)
        self.pair_btn.pack(side="left")
        self.unpair_btn = RoundButton(actions, "Unpair", self.on_unpair)
        self.unpair_btn.pack(side="left", padx=6)

    def _tree(self, parent, columns: list[tuple[str, str, int]], height: int = 10) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, stretch=key == columns[-1][0] or width > 150, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        tree.frame = frame
        return tree

    def _build_system(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text="  System  ")
        inner = ttk.Notebook(tab)
        inner.pack(fill="both", expand=True)
        self.system_tabs = inner

        # Log: this run's or the previous run's
        log_tab = ttk.Frame(inner, padding=6)
        inner.add(log_tab, text=" Log ")
        top = ttk.Frame(log_tab)
        top.pack(fill="x")
        self.log_choice = tk.StringVar(value="current")
        ttk.Radiobutton(top, text="Current log", value="current", variable=self.log_choice,
                        command=self.show_log).pack(side="left")
        ttk.Radiobutton(top, text="Previous log", value="previous", variable=self.log_choice,
                        command=self.show_log).pack(side="left", padx=10)
        self.log_name = ttk.Label(top, text="", foreground="#546E7A")
        self.log_name.pack(side="left", padx=10)
        RoundButton(top, "Open logs folder", lambda: self._open(app_paths.log_dir())).pack(side="right")
        body = ttk.Frame(log_tab)
        body.pack(fill="both", expand=True, pady=(6, 0))
        self.log_text = tk.Text(body, wrap="none", font=("Consolas", 9), state="disabled", bg="#FAFAFA")
        ys = ttk.Scrollbar(body, orient="vertical", command=self.log_text.yview)
        xs = ttk.Scrollbar(body, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        self.log_text.pack(fill="both", expand=True)

        # Errors, explained
        err_tab = ttk.Frame(inner, padding=6)
        inner.add(err_tab, text=" Errors ")
        pane = ttk.PanedWindow(err_tab, orient="vertical")
        pane.pack(fill="both", expand=True)
        self.error_tree = self._tree(pane, [("when", "When", 130), ("what", "What happened", 560)], height=8)
        pane.add(self.error_tree.frame, weight=1)
        self.error_text = tk.Text(pane, wrap="word", font=("Segoe UI", 10), height=10, state="disabled",
                                  padx=8, pady=6, bg="#FAFAFA")
        self.error_text.tag_configure("title", font=("Segoe UI", 12, "bold"))
        self.error_text.tag_configure("head", font=("Segoe UI", 10, "bold"))
        pane.add(self.error_text, weight=1)
        self.error_tree.bind("<<TreeviewSelect>>", lambda e: self.show_error())

        # Staff entries: wagers left for staff, selections staff typed (with the slip as the reader saw it)
        staff_tab = ttk.Frame(inner, padding=6)
        inner.add(staff_tab, text=" Staff entries ")
        pane = ttk.PanedWindow(staff_tab, orient="vertical")
        pane.pack(fill="both", expand=True)
        self.staff_tree = self._tree(pane, [("when", "When", 130), ("wager", "Wager", 90), ("kind", "What", 130),
                                            ("summary", "Details", 440)], height=7)
        pane.add(self.staff_tree.frame, weight=1)
        detail = ttk.Frame(pane)
        pane.add(detail, weight=2)
        self.staff_text = tk.Text(detail, wrap="word", font=("Segoe UI", 10), width=46, state="disabled",
                                  padx=8, pady=6, bg="#FAFAFA")
        self.staff_text.tag_configure("head", font=("Segoe UI", 10, "bold"))
        self.staff_text.pack(side="left", fill="both", expand=False)
        right = ttk.Frame(detail)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.staff_image = ttk.Label(right, text="", anchor="center")
        self.staff_image.pack(fill="both", expand=True)
        self.open_image_btn = RoundButton(right, "Open full size", self.open_staff_image)
        self.open_image_btn.pack(anchor="e", pady=(4, 0))
        self.staff_tree.bind("<<TreeviewSelect>>", lambda e: self.show_staff())

        self._build_settings(inner)

    def _build_data(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text="  Data  ")
        top = ttk.Frame(tab)
        top.pack(fill="x")
        ttk.Label(top, text="Racecard files today", style="Head.TLabel").pack(side="left")
        self.files_status = ttk.Label(top, text="", style="Big.TLabel")
        self.files_status.pack(side="left", padx=12)
        RoundButton(top, "Refresh", lambda: self.refresh_data(force=True)).pack(side="right")
        self.files_tree = self._tree(tab, [("file", "File", 140), ("sport", "Sport", 100), ("races", "Races", 60),
                                           ("updated", "Betty last wrote it", 160), ("size", "Size", 300)], height=4)
        self.files_tree.frame.pack(fill="x", pady=(6, 10))
        grid = ttk.Frame(tab)
        grid.pack(fill="both", expand=True)
        self.meeting_trees: dict[str, ttk.Treeview] = {}
        self.meeting_heads: dict[str, ttk.Label] = {}
        for i, (key, title) in enumerate([("horse_home", "Horses: UK & Irish"), ("horse_intl", "Horses: international"),
                                          ("dog_home", "Greyhounds: UK & Irish"),
                                          ("dog_intl", "Greyhounds: international")]):
            box = ttk.Frame(grid)
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            self.meeting_heads[key] = ttk.Label(box, text=title, style="Head.TLabel")
            self.meeting_heads[key].pack(anchor="w")
            tree = self._tree(box, [("meeting", "Meeting", 170), ("races", "Races", 50), ("first", "First", 60),
                                    ("last", "Last", 60)], height=6)
            tree.frame.pack(fill="both", expand=True)
            self.meeting_trees[key] = tree
        for c in (0, 1):
            grid.columnconfigure(c, weight=1)
        for r in (0, 1):
            grid.rowconfigure(r, weight=1)

    def _build_runners(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text="  Runners  ")
        top = ttk.Frame(tab)
        top.pack(fill="x")
        ttk.Label(top, text="Find").pack(side="left")
        self.runner_find = tk.StringVar()
        self.runner_find.trace_add("write", lambda *a: self.show_runners())
        ttk.Entry(top, textvariable=self.runner_find, width=24).pack(side="left", padx=6)
        ttk.Label(top, text="Meeting").pack(side="left", padx=(12, 0))
        self.runner_meeting = tk.StringVar(value="All meetings")
        self.meeting_box = ttk.Combobox(top, textvariable=self.runner_meeting, state="readonly", width=22,
                                        values=["All meetings"])
        self.meeting_box.pack(side="left", padx=6)
        self.meeting_box.bind("<<ComboboxSelected>>", lambda e: self.show_runners())
        self.hide_off = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Hide races that are off", variable=self.hide_off,
                        command=self.show_runners).pack(side="left", padx=12)
        self.runner_count = ttk.Label(top, text="", foreground="#546E7A")
        self.runner_count.pack(side="right")
        self.runner_tree = self._tree(tab, [("time", "Time", 60), ("meeting", "Meeting", 160), ("number", "No.", 50),
                                            ("runner", "Runner", 260), ("off", "Off", 120)], height=20)
        self.runner_tree.frame.pack(fill="both", expand=True, pady=(6, 0))
        self.runner_tree.tag_configure("off", foreground="#90A4AE")

    # --- Events from the program and the background checks ---

    def _drain(self):
        try:
            while True:
                self.handle(self.inbox.get_nowait())
        except queue.Empty:
            pass
        try:
            self.root.after(100, self._drain)
        except tk.TclError:  # the window was closed while handling an event
            pass

    def handle(self, ev: dict):
        kind = ev.get("event")
        if kind == "hello":
            self.backend_log = ev.get("log") or ""
            self.fatal = ""
            if self.log_choice.get() == "current":
                self.root.after(300, self.show_log)
        elif kind == "ready":
            self.state = "ready"
            self.info["reader"].configure(text=self._reader_text(ev))
            self.backend.send("test" if self.want_test else "live")  # the button decides, not .env
            if self.start_when_ready:
                self.start_when_ready = False
                self._go()
        elif kind == "state":
            self.watcher = ev
            if self.state == "ready":  # Shift+` on the till changes it too (before 'ready': .env's mode; the button wins)
                self.want_test = bool(ev.get("test_mode"))
        elif kind == "message":
            self.info["message"].configure(text=ev.get("text", ""))
            text = ev.get("text", "")
            if ev.get("error") and not re.match(r"Wager \S+ (needs staff|sent to the manager)", text):
                self._add_error(text)  # a wager for staff is listed from the journal, with its reason
        elif kind == "outcome":
            self.info["outcome"].configure(text=ev.get("text", ""))
        elif kind in ("staff", "manual"):
            self.root.after(300, self.reload_records)
        elif kind in ("error", "fatal"):
            self._add_error(ev.get("text", ""))
            if kind == "fatal":
                self.fatal = ev.get("text", "")
        elif kind == "step_aside":
            self._step_aside()
        elif kind == "exited":
            self._on_exit(ev)
        elif kind == "_gemini":
            self.gemini_busy = False
            self.gemini = ev
            self._show_gemini()
            self.show_ready()
        elif kind == "_data":
            self.data_busy = False
            self.data = ev
            self.show_data()
            self.show_runners()
            self.show_ready()
        elif kind == "_pairing":
            self._pairing_update(ev)
        elif kind == "_betty_drive":
            if ev["root"]:
                self.refresh_data(force=True)
            else:
                self._add_error("Betty's Events and DBF folders weren't found on any drive, so this till's drive "
                                "wasn't saved. Check the manager till's share is connected (net use), then reopen.")
        self._show_program()

    def _reader_text(self, ev: dict) -> str:
        route = ev.get("route")
        readers = ", then ".join(ev.get("readers") or []) or "none"
        where = {"relay": "through the relay", "keys": "with the Gemini keys in .env",
                 "none": "not set up: every slip goes to staff"}.get(route, "")
        return f"{readers} ({where})" if route != "none" else where

    def _add_error(self, text: str, when: str | None = None):
        if text:
            self.live_errors.append({"date": datetime.date.today().isoformat(), "time": when or time.strftime("%H:%M:%S"),
                                     "text": text})
            self.show_errors()

    def _on_exit(self, ev: dict):
        if ev.get("pid") != self.backend.pid:
            return  # an earlier run's report, after a new one started
        expected = ev.get("expected") or self.fatal  # after 'fatal' the program ends by itself
        self.state = "stopped"
        self.watcher = {}
        self.start_when_ready = False
        if not expected and not self.closing:
            tail = "\n".join(ev.get("stderr") or [])[-1500:]
            self._add_error(f"The program stopped unexpectedly (exit code {ev.get('code')})." + (f"\n\n{tail}" if tail else ""))
            self._raise()
        if self.closing:
            self.root.destroy()

    # --- Controls ---

    def on_start(self):
        if self.state in ("loading", "stopping"):
            return
        reasons = self.not_ready_reasons(ignore_program=True)
        if reasons and not messagebox.askyesno(WINDOW_TITLE, "Not ready to automate:\n\n- " + "\n- ".join(reasons)
                                               + "\n\nStart anyway?", icon="warning"):
            return
        if self.backend.alive() and self.state == "ready":
            self._go()
            return
        self.start_when_ready = True
        self.state = "loading"
        self.fatal = ""
        try:
            self.backend.launch()
        except OSError as e:
            self.state = "stopped"
            self.start_when_ready = False
            self._add_error(f"The program couldn't be started: {e}")
            messagebox.showerror(WINDOW_TITLE, f"The program couldn't be started:\n{e}")
        self._show_program()

    def _go(self):
        """Ready: the mode, then the window steps aside for Betty and the watcher starts."""
        self.backend.send("test" if self.want_test else "live")
        self._step_aside()
        self.backend.send("start")

    def _step_aside(self):
        """The till has one screen: minimise, and let the program give Betty the keyboard."""
        try:
            if self.backend.pid:
                ctypes.windll.user32.AllowSetForegroundWindow(self.backend.pid)
        except Exception:
            pass
        self.root.iconify()

    def _raise(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_pause(self):
        self.backend.send("pause")

    def on_stop(self):
        if not self.backend.alive():
            return
        if (self.watcher.get("watcher") or self.watcher.get("busy")) and not messagebox.askyesno(
                WINDOW_TITLE, "Betty Companion is running. Stop it?\n\nThe overlay closes too.", icon="warning"):
            return
        self.state = "stopping"
        self.start_when_ready = False
        self.backend.stop()
        self._show_program()

    def on_mode(self):
        self.want_test = not self.want_test
        if not self.want_test and self.backend.alive() and not messagebox.askyesno(
                WINDOW_TITLE, "Switch to LIVE?\n\nChecked wagers will be PLACED (F12).", icon="warning"):
            self.want_test = True
            return
        self.backend.send("test" if self.want_test else "live")
        self._show_program()

    def on_close(self):
        if self.backend.alive():
            if not messagebox.askyesno(WINDOW_TITLE, "Betty Companion is running.\n\nStop it and close?", icon="warning"):
                return
            self.closing = True
            self.state = "stopping"
            self.backend.stop()
            self._show_program()
            self.root.after(int((STOP_WAIT_SECS + 3) * 1000), self.root.destroy)  # in case the exit report never comes
            return
        self.closing = True
        self.root.destroy()

    def _show_program(self):
        alive = self.backend.alive()
        w = self.watcher
        program = {"stopped": "Stopped", "loading": "Loading the program...", "ready": "Running",
                   "stopping": "Stopping..."}[self.state]
        if self.fatal:
            program += f" - {self.fatal}"
        self.info["program"].configure(text=program)
        if self.state == "loading":
            self.loading.pack(fill="x", pady=(10, 0), after=self.start_btn.master)
            self.loading.start(12)
        else:
            self.loading.stop()
            self.loading.pack_forget()
        if not alive or not w:
            watcher = "Off"
        elif w.get("paused_for_staff"):
            watcher = "Paused: staff are using the till (back on after a minute with no activity)"
        else:
            watcher = "On" if w.get("watcher") else "Off (paused)"
        self.info["watcher"].configure(text=watcher)
        self.info["screen"].configure(text=(w.get("screen") or "") if alive else "")
        self.info["wager"].configure(text=(w.get("wager") or "none") if alive else "")
        if not alive and self.state == "stopped":
            self.info["reader"].configure(text=self.info["reader"].cget("text") or "Shown when the program starts")
        self.start_btn.configure(state="normal" if self.state in ("stopped", "ready") else "disabled")
        self.pause_btn.configure(state="normal" if alive and self.state == "ready" else "disabled")
        self.stop_btn.configure(state="normal" if alive and self.state != "stopping" else "disabled")
        self.mode_switch.set(not self.want_test)
        if self.want_test:
            self.mode_title.configure(text="Test", fg=TEST_COLOUR)
            self.mode_caption.configure(text="stops before placing")
        else:
            self.mode_title.configure(text="Live", fg=LIVE_COLOUR)
            self.mode_caption.configure(text="places bets")

    # --- The ready light and the Gemini check ---

    def not_ready_reasons(self, ignore_program: bool = False) -> list[str]:
        reasons = []
        if self.fatal and not ignore_program:
            reasons.append(self.fatal)
        if screen_size() != REQUIRED_SCREEN:
            w, h = screen_size()
            reasons.append(f"the screen is {w} x {h} (it must be 1366 x 768)")
        if not betty_open():
            reasons.append("Betty isn't open")
        if self.data and not self.data.get("files"):
            reasons.append(f"no racecards for today in {self.data.get('events_dir') or 'Events'}")
        if not app_paths.find_tesseract():
            reasons.append("Tesseract (screen reading) is missing")
        if self.gemini.get("ok") is False:
            reasons.append("Gemini is offline")
        elif self.gemini.get("ok") is None:
            reasons.append("still checking Gemini")
        return reasons

    def check_health(self):
        self.show_ready()
        if not self.closing:
            self.root.after(HEALTH_SECS * 1000, self.check_health)

    def show_ready(self):
        try:
            reasons = self.not_ready_reasons()
        except Exception as e:
            reasons = [f"check failed: {e}"]
        self.ready_detail = "Not ready to automate:\n- " + "\n- ".join(reasons) if reasons else ""
        if reasons:
            self._dot(self.ready_dot, RED)
            self.ready_text.configure(text="Not ready")
        else:
            self._dot(self.ready_dot, GREEN)
            on = self.backend.alive() and self.watcher.get("watcher")
            self.ready_text.configure(text="Running" if on else "Ready")

    def check_gemini(self, force: bool = False):
        if not self.gemini_busy:
            self.gemini_busy = True
            if force:
                self.gemini_text.configure(text="Gemini: checking...")
            threading.Thread(target=lambda: self.inbox.put({"event": "_gemini", **gemini_check()}), daemon=True).start()
        if not force and not self.closing:
            self.root.after(GEMINI_CHECK_SECS * 1000, self.check_gemini)

    def _show_gemini(self):
        ok = self.gemini.get("ok")
        self._dot(self.gemini_dot, GREEN if ok else RED if ok is False else GREY)
        self.gemini_text.configure(text=f"Gemini: {self.gemini.get('text', '')}"[:110])

    # --- The relay ---

    def _show_relay(self):
        import relay_link
        link = relay_link.saved_link()
        has_keys = any(os.environ.get(k, "").strip() for k in ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 12)])
        pairing = self.pairing is not None
        if link:
            text = f"Paired as '{link['name']}' with {link['url']}. Slips are read through the relay."
        elif pairing:
            text = ("On your phone, open the relay's /admin page and approve this code. Check the digits match. "
                    "Waiting for approval...")
        elif has_keys:
            text = ("Not paired. Slips are read with the Gemini keys in this PC's .env file. Pair the till to use the "
                    "relay instead (the relay is used from then on).")
        else:
            text = "Not paired, and no Gemini key on this PC: every slip would go to staff. Pair this till with the relay."
        self.relay_status.configure(text=text)
        if link or pairing:
            self.relay_form.grid_remove()
        else:
            self.relay_form.grid()
        if pairing:
            self.relay_code.grid()
        else:
            self.relay_code.configure(text="")
            self.relay_code.grid_remove()
        self.pair_btn.configure(text="Cancel pairing" if pairing else "Pair this till", state="disabled" if link else "normal")
        self.unpair_btn.configure(state="normal" if link else "disabled")

    def on_pair(self):
        import relay_link
        if self.pairing is not None:  # Cancel
            self.pairing = None
            self._show_relay()
            return
        url, name = self.relay_url.get(), self.till_name.get()
        self.pair_btn.configure(state="disabled")

        def _start():
            try:
                self.inbox.put({"event": "_pairing", "started": relay_link.start_pairing(url, name)})
            except relay_link.RelayError as e:
                self.inbox.put({"event": "_pairing", "error": str(e)})
        threading.Thread(target=_start, daemon=True).start()

    def _pairing_update(self, ev: dict):
        import relay_link
        if ev.get("error"):
            self.pairing = None
            self._show_relay()
            messagebox.showerror(WINDOW_TITLE, f"Pairing didn't work:\n\n{ev['error']}")
            return
        if ev.get("started"):
            self.pairing = ev["started"]
            self.pairing["deadline"] = time.time() + self.pairing.get("expires_in", 600)
            code = self.pairing["code"]
            self.relay_code.configure(text=f"{code[:3]} {code[3:]}")
            self._show_relay()
            self.root.after(3000, self._poll_pairing)
            return
        status = ev.get("status")
        if self.pairing is None or status == "pending":
            return
        self.pairing = None
        self._show_relay()
        if status == "paired":
            link = relay_link.saved_link()
            messagebox.showinfo(WINDOW_TITLE, f"Paired as '{link['name'] if link else ''}'.\n\n"
                                              "Slips are read through the relay from the next one.")
            self.check_gemini(force=True)
            self.save_betty_drive()
        else:
            messagebox.showwarning(WINDOW_TITLE, {"rejected": "The code was rejected on the relay.",
                                                  "expired": "The code expired before it was approved. Try again.",
                                                  }.get(status, f"Pairing ended: {status}."))

    def _poll_pairing(self):
        import relay_link
        pairing = self.pairing
        if pairing is None:
            return
        if time.time() > pairing["deadline"]:
            self.inbox.put({"event": "_pairing", "status": "expired"})
            return

        def _poll():
            try:
                self.inbox.put({"event": "_pairing", "status": relay_link.poll_pairing(pairing)})
            except relay_link.RelayError:
                self.inbox.put({"event": "_pairing", "status": "pending"})  # the internet blinked: try again
        threading.Thread(target=_poll, daemon=True).start()
        self.root.after(3000, self._poll_pairing)

    def on_unpair(self):
        import relay_link
        if not messagebox.askyesno(WINDOW_TITLE, "Unpair this till?\n\nIt stops reading slips through the relay. "
                                                 "Also revoke it on the relay's /admin page if it won't be paired again."):
            return
        try:
            relay_link.forget_link()
        except relay_link.RelayError as e:
            messagebox.showerror(WINDOW_TITLE, str(e))
        self._show_relay()
        self.check_gemini(force=True)

    # --- System: logs, errors, staff entries ---

    def show_log(self):
        logs = session_logs()
        if self.log_choice.get() == "current":
            path = logs[0] if logs else ""
        else:
            path = logs[1] if len(logs) > 1 else ""
        self.log_path, self.log_offset = path, 0
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        if not path:
            self.log_name.configure(text="No log yet" if self.log_choice.get() == "current" else "No previous log")
            return
        self.log_name.configure(text=f"{os.path.basename(path)}  (last written "
                                     f"{time.strftime('%d %b %H:%M', time.localtime(os.path.getmtime(path)))})")
        self._append_log(first=True)

    def _append_log(self, first: bool = False):
        try:
            size = os.path.getsize(self.log_path)
            if size < self.log_offset:
                self.log_offset = 0
            if size == self.log_offset:
                return
            with open(self.log_path, "rb") as f:
                start = max(self.log_offset, size - 2_000_000) if first else self.log_offset
                f.seek(start)
                text = f.read().decode("utf-8", "replace")
            self.log_offset = size
        except OSError:
            return
        at_end = self.log_text.yview()[1] > 0.98
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.configure(state="disabled")
        if first or at_end:
            self.log_text.see("end")

    def _tail_log(self):
        if self.log_choice.get() == "current":
            logs = session_logs()
            if logs and logs[0] != self.log_path:
                self.show_log()  # a new run started a new log
            elif self.log_path:
                self._append_log()
        elif not self.log_path:
            self.show_log()
        if not self.closing:
            self.root.after(int(LOG_TAIL_SECS * 1000), self._tail_log)

    def reload_records(self):
        """The staff journal (plus wagers for staff in the logs from before the journal), and the errors."""
        journal = read_journal()
        logged = staff_from_logs(session_logs())  # logs are kept 30 days, a few MB in all
        known = {e.get("wager") for e in journal if e.get("kind") == "staff"}
        self.records = journal + [e for e in logged if e["wager"] not in known]
        self.records.sort(key=lambda e: (e.get("date", ""), e.get("time", "")), reverse=True)
        self.show_staff_list()
        self.show_errors()

    def show_errors(self):
        rows = [{"date": e["date"], "time": e["time"], "text": e["text"]} for e in self.live_errors]
        for e in self.records:
            if e.get("kind") == "staff":
                rows.append({"date": e.get("date", ""), "time": e.get("time", ""),
                             "text": f"Wager {e.get('wager')} left for staff: {e.get('reason', '')}"})
        rows.sort(key=lambda r: (r["date"], r["time"]), reverse=True)
        tree = self.error_tree
        selected = tree.selection()
        tree.delete(*tree.get_children())
        self.error_rows = {}
        for i, r in enumerate(rows):
            iid = f"e{i}"
            self.error_rows[iid] = r
            when = f"{_day_label(r['date'])} {r['time'][:5]}".strip()
            tree.insert("", "end", iid=iid, values=(when, r["text"].splitlines()[0][:200]))
        if selected and selected[0] in self.error_rows:
            tree.selection_set(selected[0])
        self.tabs.tab(1, text=f"  System ({len(rows)})  " if rows else "  System  ")

    def show_error(self):
        sel = self.error_tree.selection()
        if not sel:
            return
        import error_guide
        row = self.error_rows[sel[0]]
        guide = error_guide.explain(row["text"])
        t = self.error_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", guide["title"] + "\n", "title")
        t.insert("end", "\nWhat happened\n", "head")
        t.insert("end", row["text"] + "\n")
        t.insert("end", "\nWhat it means\n", "head")
        t.insert("end", guide["meaning"] + "\n")
        t.insert("end", "\nWhat to do\n", "head")
        t.insert("end", guide["action"] + "\n")
        t.configure(state="disabled")

    def show_staff_list(self):
        tree = self.staff_tree
        tree.delete(*tree.get_children())
        self.staff_rows = {}
        for i, e in enumerate(self.records):
            iid = f"s{i}"
            self.staff_rows[iid] = e
            when = f"{_day_label(e.get('date', ''))} {e.get('time', '')[:5]}".strip()
            if e.get("kind") == "manual":
                m = e.get("matched") or {}
                kind = "Typed by staff"
                summary = (f"#{e.get('selection')}: read '{(e.get('read') or {}).get('name', '')}', "
                           f"entered {m.get('name', '')} ({m.get('time', '')} {m.get('meeting', '')})")
            else:
                kind = "Left for staff"
                summary = e.get("reason", "")
            tree.insert("", "end", iid=iid, values=(when, e.get("wager") or "", kind, summary))

    def show_staff(self):
        sel = self.staff_tree.selection()
        if not sel:
            return
        e = self.staff_rows[sel[0]]
        t = self.staff_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        mode = " (test mode)" if e.get("test_mode") else ""
        if e.get("kind") == "manual":
            read, typed, m = e.get("read") or {}, e.get("typed") or {}, e.get("matched") or {}
            t.insert("end", f"Selection #{e.get('selection')} of wager {e.get('wager')}{mode}\n\n", "head")
            for head, d in (("The reader read", read), ("Staff typed", typed)):
                t.insert("end", head + "\n", "head")
                t.insert("end", f"  {d.get('name') or '-'}\n  time {d.get('time') or '-'}   meeting "
                                f"{d.get('meeting') or '-'}   price {d.get('price') or 'SP'}\n\n")
            t.insert("end", "It matched\n", "head")
            t.insert("end", f"  {m.get('name')} #{m.get('number') or '-'}, {m.get('meeting')} {m.get('time')}, "
                            f"{m.get('price') or 'SP'}\n")
            image = e.get("image")
        else:
            t.insert("end", f"Wager {e.get('wager')} left for staff{mode}\n\n", "head")
            t.insert("end", e.get("reason", "") + "\n\n")
            import error_guide
            guide = error_guide.explain(e.get("reason", ""))
            t.insert("end", "What to do\n", "head")
            t.insert("end", guide["action"] + "\n")
            if e.get("from_log"):
                t.insert("end", "\n(From the log of a run before the staff journal.)\n")
            image = e.get("screenshot")
        t.configure(state="disabled")
        self._show_image(image)

    def _show_image(self, path: str | None):
        self.staff_image_path = path if path and os.path.exists(path) else None
        if not self.staff_image_path:
            self._image = None
            self.staff_image.configure(image="", text="No picture saved")
            self.open_image_btn.configure(state="disabled")
            return
        from PIL import Image, ImageTk
        img = Image.open(self.staff_image_path)
        self.root.update_idletasks()
        box = (max(200, self.staff_image.winfo_width() - 8), max(150, self.staff_image.winfo_height() - 8))
        img.thumbnail(box)
        self._image = ImageTk.PhotoImage(img)
        self.staff_image.configure(image=self._image, text="")
        self.open_image_btn.configure(state="normal")

    def open_staff_image(self):
        if getattr(self, "staff_image_path", None):
            self._open(self.staff_image_path)

    @staticmethod
    def _open(path: str):
        try:
            if path == app_paths.log_dir():
                os.makedirs(path, exist_ok=True)
            os.startfile(path)
        except OSError as e:
            messagebox.showerror(WINDOW_TITLE, f"Couldn't open {path}:\n{e}")

    # --- Data and Runners ---

    def save_betty_drive(self):
        """
        Once the till is paired, finds the drive with Betty's Events and DBF (C:\\ on the manager till, the mapped
        share on a cashier till) and saves it for this build (betty_paths.json); used from then on. Done once.
        """
        import betty_feed
        import relay_link
        if relay_link.saved_link() and not betty_feed.saved_betty_root():
            threading.Thread(target=lambda: self.inbox.put({"event": "_betty_drive", "root": betty_feed.save_betty_root()}),
                             daemon=True).start()

    def refresh_data(self, force: bool = False):
        if not self.data_busy:
            self.data_busy = True
            threading.Thread(target=lambda: self.inbox.put(self.reader.read()), daemon=True).start()
        if not force and not self.closing:
            self.root.after(DATA_REFRESH_SECS * 1000, self.refresh_data)

    def show_data(self):
        files = self.data.get("files") or []
        tree = self.files_tree
        tree.delete(*tree.get_children())
        now = time.time()
        for f in files:
            updated = "can't be read: " + f["error"] if f["error"] else _ago(now - f["modified"])
            tree.insert("", "end", values=(f["file"], f["sport"], f["races"], updated, f"{f['size'] / 1e6:.1f} MB"))
        if self.data.get("error"):
            self.files_status.configure(text=f"Couldn't read the racecards: {self.data['error']}", foreground=RED)
        elif not files:
            self.files_status.configure(text=f"None found for today in {self.data.get('events_dir') or 'Events'}: is Betty running?", foreground=RED)
        else:
            newest = max(f["modified"] for f in files)
            self.files_status.configure(text=f"{len(files)} file(s) in {self.data.get('events_dir')}, last written "
                                             f"{_ago(now - newest)}", foreground=GREEN)
        titles = {"horse_home": "Horses: UK & Irish", "horse_intl": "Horses: international",
                  "dog_home": "Greyhounds: UK & Irish", "dog_intl": "Greyhounds: international"}
        for key, tree in self.meeting_trees.items():
            rows = (self.data.get("groups") or {}).get(key, [])
            tree.delete(*tree.get_children())
            for m in rows:
                tree.insert("", "end", values=(m["meeting"], m["races"], m["first"], m["last"]))
            self.meeting_heads[key].configure(text=f"{titles[key]} ({len(rows)})")

    def show_runners(self):
        runners = self.data.get("runners") or []
        meetings = sorted({r["meeting"] for r in runners})
        self.meeting_box.configure(values=["All meetings"] + meetings)
        if self.runner_meeting.get() not in ["All meetings"] + meetings:
            self.runner_meeting.set("All meetings")
        find = self.runner_find.get().strip().lower()
        meeting = self.runner_meeting.get()
        tree = self.runner_tree
        tree.delete(*tree.get_children())
        shown = 0
        for r in runners:
            off = r.get("off_mins")
            if meeting != "All meetings" and r["meeting"] != meeting:
                continue
            if find and find not in r["name"].lower() and find not in r["meeting"].lower():
                continue
            if off is not None and self.hide_off.get():
                continue
            off_text = f"off {int(off) // 60:02d}:{int(off) % 60:02d}" if off is not None else ""
            tree.insert("", "end", values=(r["time_str"], r["meeting"], r["number"], r["name"], off_text),
                        tags=("off",) if off is not None else ())
            shown += 1
        races = len({(r["meeting"], r["time_str"]) for r in runners})
        self.runner_count.configure(text=f"{shown} shown of {len(runners)} UK & Irish horse runners in {races} races "
                                         f"at {len(meetings)} meetings")


def gemini_check() -> dict:
    """The status bar's Gemini check, free: the relay's /ping when paired, else the key in .env."""
    import relay_link
    link = relay_link.saved_link()
    if link:
        return relay_link.check_relay(link["url"], link["pass"])
    for name in ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 12)]:
        key = os.environ.get(name, "").strip()
        if key:
            return relay_link.check_gemini_key(key)
    return {"ok": False, "text": "no slip reader set up: pair this till (System, Settings)"}


def _ago(secs: float) -> str:
    secs = max(0, int(secs))
    if secs < 90:
        return f"{secs} s ago"
    if secs < 5400:
        return f"{secs // 60} min ago"
    return f"{secs // 3600} h ago"


def _day_label(date: str) -> str:
    today = datetime.date.today()
    if date == today.isoformat():
        return "Today"
    if date == (today - datetime.timedelta(days=1)).isoformat():
        return "Yesterday"
    try:
        return datetime.date.fromisoformat(date).strftime("%d %b")
    except ValueError:
        return date


# --- Start-up ---

_single_instance = None  # held for the whole run


def already_open() -> bool:
    """A launcher is already open on this PC: bring it to the front instead of opening a second one."""
    global _single_instance
    kernel32, user32 = ctypes.windll.kernel32, ctypes.windll.user32
    _single_instance = kernel32.CreateMutexW(None, False, "Local\\BettyCompanionLauncher")
    if kernel32.GetLastError() != 183:  # ERROR_ALREADY_EXISTS
        return False
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    return True


def _attach_std_streams():
    """A windowed exe starts with no sys.stdin/stdout/stderr even when the launcher gave it pipes on 0, 1 and 2."""
    for name, fd, mode in (("stdin", 0, "r"), ("stdout", 1, "w"), ("stderr", 2, "w")):
        if getattr(sys, name) is None:
            try:
                setattr(sys, name, open(fd, mode, encoding="utf-8", closefd=False,
                                        **({"buffering": 1} if mode == "w" else {})))
            except OSError:
                pass


def run():
    if "--backend" in sys.argv:
        _attach_std_streams()
        import betty_companion
        betty_companion.main()
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # the real screen size, and sharp text
    except Exception:
        pass
    if already_open():
        return
    from dotenv import load_dotenv
    load_dotenv(app_paths.env_file())  # GEMINI keys (no relay), RELAY_URL, BETTY_EVENTS_DIR...
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    run()
