__version__ = "1.1.4"
APP_NAME = f"Betty Companion v{__version__}"


import pyautogui  # type: ignore
import pytesseract
import keyboard  # type: ignore
import time
import os
import queue
import math
import itertools
from dotenv import load_dotenv
import app_paths
import relay_link

# Load variables from .env (next to the exe when packaged, else in the project folder) into os.environ
load_dotenv(app_paths.env_file())

import re
import base64
import io
import json
import requests
import ctypes
import sys
import tkinter as tk
import threading
import atexit
import glob
from difflib import SequenceMatcher
from typing import Any
from PIL import Image, ImageEnhance, ImageOps
import numpy as np


# --backend: run by the launcher window. stdout then carries only status events for it (backend_event); the console
# text goes to the session log alone, which the launcher shows. Commands come in on stdin (backend_command_loop).
BACKEND_MODE = "--backend" in sys.argv
SESSION_LOG = ""  # this run's log file (empty in the free tests)


class ConsoleTeeLogger:
    """Duplicates stdout and stderr to a per-session log file in logs/ with immediate flush on every write.
    `original_stream` None (--backend): the log file only. Each line in the file starts with the time it was
    written ('15:35:25 [!] ...'; user, 28 Oct); blank lines and the console stay as printed."""
    _lock = threading.Lock()  # stdout and stderr write one file: one lock and one line start between them
    _at_line_start = True

    def __init__(self, filepath: str, original_stream: Any):
        self.original_stream = original_stream
        self.log_file = open(filepath, 'a', encoding='utf-8', buffering=1)

    @classmethod
    def _stamped(cls, data: str) -> str:
        stamp, out = time.strftime('%H:%M:%S '), []
        for piece in data.splitlines(keepends=True):
            if cls._at_line_start and piece.strip():
                out.append(stamp)
            out.append(piece)
            cls._at_line_start = piece.endswith(('\n', '\r'))
        return ''.join(out)

    def write(self, data: str):
        with self._lock:
            if self.original_stream is not None:
                try:
                    self.original_stream.write(data)
                    self.original_stream.flush()
                except Exception:
                    pass
            try:
                self.log_file.write(ConsoleTeeLogger._stamped(data))
                self.log_file.flush()
            except Exception:
                pass

    def flush(self):
        with self._lock:
            try:
                self.original_stream.flush()
            except Exception:
                pass
            try:
                self.log_file.flush()
            except Exception:
                pass

    def isatty(self):
        return getattr(self.original_stream, 'isatty', lambda: False)()

    def close(self):
        try:
            self.flush()
            self.log_file.close()
        except Exception:
            pass


_console_ctrl_callback = None  # the console-close handler given to Windows, kept alive for the whole run


def _init_session_logging():
    global _console_ctrl_callback, SESSION_LOG
    try:
        log_dir = app_paths.log_dir()
        os.makedirs(log_dir, exist_ok=True)
        # Prune session logs older than 30 days
        cutoff = time.time() - (30 * 86400)
        for log_path in glob.glob(os.path.join(log_dir, "session_*.log")):
            try:
                if os.path.getmtime(log_path) < cutoff:
                    os.remove(log_path)
            except Exception:
                pass

        session_file = os.path.join(log_dir, f"session_{time.strftime('%Y%m%d_%H%M%S')}.log")
        SESSION_LOG = session_file
        tee_out = ConsoleTeeLogger(session_file, None if BACKEND_MODE else sys.stdout)
        tee_err = ConsoleTeeLogger(session_file, None if BACKEND_MODE else sys.stderr)
        sys.stdout = tee_out
        sys.stderr = tee_err

        atexit.register(tee_out.close)
        atexit.register(tee_err.close)

        def _console_ctrl_handler(ctrl_type):
            try:
                tee_out.flush()
                tee_err.flush()
            except Exception:
                pass
            return False

        try:
            _handler_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)
            # Held by the module: Windows keeps only a pointer, and a local callback freed on return made closing
            # the console call freed memory instead of flushing the log
            _console_ctrl_callback = _handler_type(_console_ctrl_handler)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_ctrl_callback, True)
        except Exception:
            pass
    except Exception as e:
        print(f"[-] Could not initialize session log: {e}")


if os.environ.get("BETTY_HEADLESS") != "1":  # free tests import the program: their fake errors stay out of logs/
    _init_session_logging()


def _open_event_stream():
    """The real stdout, for --backend's status events (None outside --backend, or when the launcher gave no pipe)."""
    if not BACKEND_MODE:
        return None
    if sys.__stdout__ is not None:
        return sys.__stdout__
    try:  # a windowed build starts without sys.stdout even when the launcher passed a pipe on handle 1
        return open(1, "w", encoding="utf-8", buffering=1, closefd=False)
    except OSError:
        return None


_event_stream = _open_event_stream()
_event_lock = threading.Lock()


def backend_event(kind: str, **data):
    """One status line for the launcher, as JSON on stdout (--backend only, where stdout carries nothing else)."""
    if _event_stream is None:
        return
    line = json.dumps({"event": kind, "time": time.strftime('%H:%M:%S'), **data}, default=str)
    with _event_lock:
        try:
            _event_stream.write(line + "\n")
            _event_stream.flush()
        except Exception:
            pass

# Modular Rules Engine (Scalable Multi-Bookmaker Discrepancy & House Rules System)
from rules_engine import (
    bookmaker_rules_mgr,
    resolve_bookmaker_discrepancies,
    set_notification_callback,
    clean_horse_name,
    parse_race_time_to_minutes,
    normalize_bet_type,
    resolve_plain_forecast,
    is_unnamed_favourite,
    is_greyhound_or_trap_selection,
    calculate_bet_cost_pence,
    race_time_options,
    selection_names,
    _without_names,
)

# Betty local racecard feeds (C:\Events)
from betty_feed import BettyFeedCard, BettyOffTimes, DOMESTIC_COUNTRIES, DOG_SPORTS

# Centralized Meetings Directory Manager (Virtual, Greyhound, International & Aliases)
from meetings_manager import meetings_manager

# --- 0. WINDOWS DPI AWARENESS & DYNAMIC SCREEN METRICS ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_screen_resolution() -> tuple[int, int]:
    """
    Returns (width, height) of the primary screen as Windows reports it, or (1024, 576) on error.
    Always the real size: a SCREEN_RESOLUTION setting can no longer pick the wrong click coordinates.
    """
    try:
        w = int(ctypes.windll.user32.GetSystemMetrics(0))
        h = int(ctypes.windll.user32.GetSystemMetrics(1))
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        pass
    return (1024, 576)


# --- 1. ENGINE SETUP ---
TESSERACT_EXE = app_paths.find_tesseract()  # shipped with the program first, then an installed one
if TESSERACT_EXE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
else:
    print(f"[-] Tesseract not found (no tesseract\\ folder next to the program, nor {app_paths.INSTALLED_TESSERACT}): "
          "screens can't be read.")

# --- CREDENTIALS & API CONFIGURATION ---

def _env_list(name: str, default: str = "") -> list[str]:
    """Comma/semicolon-separated .env value as a list, blanks dropped."""
    return [v.strip() for v in re.split(r'[,;]+', os.environ.get(name, default)) if v.strip()]


def _key_list(*names: str) -> list[str]:
    keys = []
    for n in names:
        k = os.environ.get(n, "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or None          # the paid Google project
GEMINI_FREE_KEYS = _key_list(*[f"GEMINI_API_KEY_{i}" for i in range(2, 12)])     # free-tier projects

# --- 2. CALIBRATION COORDINATES ---

SLIP_REGION = (491, 78, 365, 505)  # INVARIANT: Preserved per project constraints

# Betty's bet list on Choose Bet and Stake (F8) at 1366x768, the only screen size the program runs at
F8_ROW_HEIGHT_1368 = 34.67                     # row height
F8_NUM_ROWS = 11                               # selectable bet rows on a page
F8_BET_LIST_REGION_1368 = (8, 127, 279, 381)   # the 11 rows of a page


# --- GLOBAL DAEMON & CACHE STATE ---
SESSION = requests.Session()
watcher_busy = False    # the watcher is acting on Betty: Esc aborts it
abort_event = threading.Event()


def trigger_abort():
    """
    The operator pressed Esc: flag the watcher's current action for abort. Called only by HumanInputMonitor
    for an Esc a person pressed (Windows marks this program's own key presses as injected, so they never abort).
    """
    with _watcher_state_lock:
        if not watcher_busy or abort_event.is_set():
            return
        abort_event.set()
    print("\n[!] ESC PRESSED: Aborting the current action!")
    STATUS_HUD.update("Aborted by operator (ESC pressed).", title=f"{APP_NAME} - [!] ABORTED", bg='#B00020', badge="[Aborted]")


def interruptible_sleep(seconds: float) -> bool:
    """
    Sleeps for `seconds` in 20ms slices, checking `abort_event.is_set()`.
    Returns True if full duration elapsed, False immediately if ESC was pressed.
    """
    if abort_event.is_set():
        return False
    t0 = time.time()
    while time.time() - t0 < seconds:
        if abort_event.is_set():
            return False
        time.sleep(min(0.02, max(0.001, seconds - (time.time() - t0))))
    return not abort_event.is_set()


# pyautogui waits 0.1 s after every key press and mouse action by default: half that (user, 26 Oct: Betty keeps keys
# pressed before it has drawn the screen they are for). The fixed waits below were halved with it; F12 keeps its own.
pyautogui.PAUSE = 0.05


def click_betty_cell(x: int, y: int):
    """
    Performs a snappy Win32 click with calibrated mouse dwell time so
    legacy Betty GDI interface controls register the click reliably without latency.
    """
    pyautogui.moveTo(x, y)
    interruptible_sleep(0.02)
    pyautogui.mouseDown(x, y)
    interruptible_sleep(0.035)
    pyautogui.mouseUp(x, y)
    interruptible_sleep(0.02)

# --- VISION READER CHAIN (see reader_tiers) ---
# Ranked on Roger's slips with scratch/ocr_eval (2026-10-20): gemini-4-argon reads handwritten names best (76%,
# Flash 61%) with no wrong slips. Accuracy before speed: every slip starts at the top of the chain.
GEMINI_PAID_MODELS = _env_list("GEMINI_PAID_MODELS", "gemini-4-argon")
GEMINI_FREE_MODELS = _env_list("GEMINI_FREE_MODELS", "gemini-3.8-flash")
SLIP_READER = os.environ.get("SLIP_READER", "waterfall").strip().lower()  # waterfall | gemini (see reader_tiers)
# SLIP_READER=gemini only (evaluation runs): every Gemini key, these models in order
VLM_WATERFALL_MODELS = _env_list("GEMINI_MODELS", "gemini-4-argon,gemini-pro-latest,gemini-3.8-flash,gemini-3.5-flash")
SCAN_TIMEOUT_SECS = 90     # timed-out requests are still billed: keep these generous
RECHECK_TIMEOUT_SECS = 45


# --- FLICKER-RESILIENT MULTI-SAMPLING UTILITIES ---


# Terminal Post-Time Red Text Bounding Region (Displayed when meetings exhaust on Betty's terminal)
# When all meetings for a race time are dequeued with 'right', Betty closes the cyan panel and returns
# to the main edit screen where the time renders in RED (RGB: 255, 0, 0) and the yellow box is absent.


# Centered Error / Warning Modal Dialogs (e.g. Error 2119 Insufficient extra bets)
# Features red modal border and yellow [ Continue ] button.
# Calibrated for both 1024x576 native and 1366x768 scaled display environments.


IDLE_MESSAGE = "Ready. ` = watcher on/off, Shift+` = test mode, Esc = stop now."
IDLE_BADGE = "[` watcher]"


class CompactHUD:
    """
    Persistent, always-on-top, non-intrusive floating status HUD.
    Docks in the bottom-right corner, staying on screen at all times
    to provide live status updates to the operator.
    Uses a thread-safe Queue processed by Tkinter's root.after() loop.
    """
    def __init__(self):
        self.queue = queue.Queue()
        self.root = None
        self.top_frame = None
        self.lbl_title = None
        self.lbl_status = None
        self.lbl_badge = None
        self.lbl_mode = None     # watcher ON/OFF, TEST MODE and the screen Betty is on
        self.lbl_outcome = None  # last wager outcome
        self.rect = (0, 0, 0, 0)  # screen box of the HUD, so clicks on it are not taken as staff using Betty
        self.home: tuple[int, int] | None = None  # its bottom-right corner position, set when the window opens
        self._reset_timer = None
        self._drag_x = 0
        self._drag_y = 0
        if os.environ.get("BETTY_HEADLESS") == "1":
            return  # free tests: no window over Betty (updates just queue up unread)
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

    def _run_tk(self):
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.93)

            width, height = 330, 112
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            # Bottom-right corner (x >= 1030, y >= 652 at 1366x768): the one strip of Betty the program never reads
            # or clicks - clear of the slip image, the summary/betslip panel (to y 640) and the bottom buttons (x < 1022)
            x = screen_w - width - 6
            y = screen_h - height - 4
            self.home = (x, y)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.root.configure(bg='#0D47A1')

            # Top frame: Title and [` watcher] / [Error] badge
            self.top_frame = tk.Frame(self.root, bg='#0D47A1')
            self.top_frame.pack(fill='x', padx=10, pady=(6, 0))

            self.lbl_title = tk.Label(
                self.top_frame, text=APP_NAME, font=('Segoe UI', 9, 'bold'),
                fg='#FFFFFF', bg='#0D47A1', anchor='w'
            )
            self.lbl_title.pack(side='left')

            self.lbl_badge = tk.Label(
                self.top_frame, text=IDLE_BADGE, font=('Segoe UI', 8, 'bold'),
                fg='#90CAF9', bg='#0D47A1', anchor='e'
            )
            self.lbl_badge.pack(side='right')

            # Watcher line: ON/OFF, TEST MODE, current screen
            self.lbl_mode = tk.Label(
                self.root, text="WATCHER OFF", font=('Segoe UI', 8, 'bold'),
                fg='#FFFFFF', bg='#0D47A1', anchor='w'
            )
            self.lbl_mode.pack(fill='x', padx=10)

            # Live status message (current step) with auto-wrapping
            self.lbl_status = tk.Label(
                self.root, text=IDLE_MESSAGE, font=('Segoe UI', 8),
                fg='#ECEFF1', bg='#0D47A1', anchor='w', justify='left', wraplength=310
            )
            self.lbl_status.pack(fill='both', expand=True, padx=10, pady=(1, 0))

            # Last outcome
            self.lbl_outcome = tk.Label(
                self.root, text="Last: -", font=('Segoe UI', 7),
                fg='#CFD8DC', bg='#0D47A1', anchor='w', justify='left', wraplength=310
            )
            self.lbl_outcome.pack(fill='x', padx=10, pady=(0, 5))

            # Allow operator to click and drag the HUD anywhere on screen
            def _start_drag(event):
                self._drag_x = event.x
                self._drag_y = event.y

            def _do_drag(event):
                if not self.root:
                    return
                new_x = self.root.winfo_x() + (event.x - self._drag_x)
                new_y = self.root.winfo_y() + (event.y - self._drag_y)
                self.root.geometry(f"+{new_x}+{new_y}")

            for widget in (self.root, self.top_frame, self.lbl_title, self.lbl_badge, self.lbl_mode, self.lbl_status, self.lbl_outcome):
                if widget is not None:
                    widget.bind("<Button-1>", _start_drag)
                    widget.bind("<B1-Motion>", _do_drag)

            # Display immediately on launch and keep on top
            self.root.deiconify()
            self.root.lift()
            self._poll_queue()
            self.root.mainloop()
        except Exception as e:
            print(f"[-] HUD initialization error: {e}")

    def _poll_queue(self):
        root = self.root
        if not root:
            return
        try:
            while True:
                task = self.queue.get_nowait()
                action = task.get('action')
                if action in ['update', 'idle']:
                    title = task.get('title')
                    msg = task.get('msg', '')
                    bg = task.get('bg')
                    badge = task.get('badge')
                    if bg:
                        root.configure(bg=bg)
                        for lbl in (self.top_frame, self.lbl_title, self.lbl_mode, self.lbl_status, self.lbl_outcome):
                            if lbl: lbl.configure(bg=bg)
                        if self.lbl_badge:
                            self.lbl_badge.configure(bg=bg)
                            if badge is None:
                                badge_color = '#FFCDD2' if bg == '#B00020' else ('#C8E6C9' if bg == '#1B5E20' else ('#FFE0B2' if bg == '#E65100' else '#90CAF9'))
                                self.lbl_badge.configure(fg=badge_color)
                    if badge is not None and self.lbl_badge:
                        badge_color = '#FFCDD2' if bg == '#B00020' else ('#C8E6C9' if bg == '#1B5E20' else ('#FFE0B2' if bg == '#E65100' else '#90CAF9'))
                        self.lbl_badge.configure(text=badge, fg=badge_color)
                    if title and self.lbl_title:
                        self.lbl_title.configure(text=title)
                    if self.lbl_status:
                        self.lbl_status.configure(text=msg)
                    root.lift()
                    root.attributes('-topmost', True)
                elif action == 'mode':
                    if self.lbl_mode: self.lbl_mode.configure(text=task.get('text', ''))
                elif action == 'outcome':
                    if self.lbl_outcome: self.lbl_outcome.configure(text=task.get('text', ''))
                elif action == 'home' and self.home:
                    root.geometry(f"+{self.home[0]}+{self.home[1]}")
                    root.update_idletasks()
        except queue.Empty:
            pass
        try:
            self.rect = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height())
        except Exception:
            pass
        root.after(40, self._poll_queue)

    def contains(self, x: int, y: int) -> bool:
        rx, ry, rw, rh = self.rect
        return rx <= x < rx + rw and ry <= y < ry + rh

    def snap_home(self, timeout: float = 0.5):
        """
        Back to the bottom-right corner if it was dragged away, and wait until it is there, so the next screenshot
        of Betty is clear of it. Dragged over View Wagers' summary panel it hid Payment (9.2448382 and 9.2448383,
        23 Oct). Does nothing when it is already home.
        """
        if not self.root or not self.home or self.rect[:2] == self.home:
            return
        print(f"[*] Status panel was moved to {self.rect[0]},{self.rect[1]}: putting it back in the corner.")
        self.queue.put({'action': 'home'})
        t0 = time.time()
        while self.rect[:2] != self.home and time.time() - t0 < timeout:
            time.sleep(0.04)

    def set_mode(self, text: str):
        """Watcher line: ON/OFF, TEST MODE and the screen Betty is on."""
        self.queue.put({'action': 'mode', 'text': text})

    def set_outcome(self, text: str):
        self.queue.put({'action': 'outcome', 'text': f"Last: {text}"})
        backend_event("outcome", text=text)

    def reset_to_idle(self, delay_ms=0):
        """Schedules or immediately resets the HUD back to the Idle / Ready state."""
        if self._reset_timer:
            try: self._reset_timer.cancel()
            except Exception: pass
            self._reset_timer = None

        def _do_reset():
            self.queue.put({
                'action': 'idle',
                'title': APP_NAME,
                'msg': IDLE_MESSAGE,
                'badge': IDLE_BADGE,
                'bg': '#0D47A1'
            })

        if delay_ms > 0:
            self._reset_timer = threading.Timer(delay_ms / 1000.0, _do_reset)
            self._reset_timer.daemon = True
            self._reset_timer.start()
        else:
            _do_reset()

    def update(self, msg, title=None, bg=None, bg_color=None, badge=None):
        effective_bg = bg or bg_color
        if self._reset_timer:
            try: self._reset_timer.cancel()
            except Exception: pass
            self._reset_timer = None
        self.queue.put({'action': 'update', 'msg': msg, 'title': title, 'bg': effective_bg, 'badge': badge})
        backend_event("message", text=msg, error=effective_bg == '#B00020')  # red = an error (notify)


STATUS_HUD = CompactHUD()


def notify(message, is_error=False, title=None, bg_color=None, sound=False):
    """
    Updates the persistent compact HUD with live status or error notifications.
    """
    if title is None:
        title = f"{APP_NAME} - Error" if is_error else APP_NAME

    if bg_color is None:
        bg_color = '#B00020' if is_error else '#0D47A1'

    badge = "[Error]" if is_error else None
    STATUS_HUD.update(message, title=title, bg=bg_color, badge=badge)
    if is_error:
        STATUS_HUD.reset_to_idle(delay_ms=6000)


# Wire modular rules engine notifications directly into Betty Companion floating HUD banner
set_notification_callback(lambda msg, err=False, col=None: notify(msg, is_error=err, bg_color=col))


def similar(a, b):
    """Calculates string similarity for fuzzy matching."""
    return SequenceMatcher(None, a, b).ratio()


def format_time_for_betty(time_str: str, digits_only: bool = False) -> str:
    """
    Formats the race time string for input into Betty.
    If digits_only is True, formats as '1415'; otherwise '14:15'.

    CRITICAL DOMAIN SAFETY INVARIANT:
    In Betty POS, pressing '.' (period/dot) at the selection entering screen deletes
    the last entered selection from the slip! Under NO circumstances may format_time_for_betty
    ever return a period ('.'). Any '.' is converted to ':' or stripped.
    """
    if not time_str:
        return ""
    mins, norm_str = parse_race_time_to_minutes(time_str)
    raw = norm_str if norm_str else time_str.strip().replace('.', ':')
    if digits_only:
        return re.sub(r'[^0-9]', '', raw)
    # Strictly allow only digits and colons, ensuring no '.' or stray characters can be typed
    return re.sub(r'[^0-9:]', '', raw)


# --- 3. RACECARD: BETTY'S OWN LOCAL FEEDS ---
# Pre-flight checks every selection against the card Betty itself holds (C:\Events SIS / TRP / Tote feeds),
# so runner names, race times, meetings and saddle-cloth numbers are exactly what Betty will show.
racecard_manager = BettyFeedCard(category_resolver=lambda m: meetings_manager.resolve_meeting(m)[0])
# Greyhounds: every feed Betty labels "DOG" or "ADOGS" (today SIS DGB00, TRP Dogs BFTV5, Australian BFTST, the virtual
# dogs BFBI2), found as Betty adds them. BETTY_DOG_FEEDS (e.g. "DGB00,BFTV5") fixes the list instead. Its tracks count as greyhound tracks by name.
greyhound_card = BettyFeedCard(feeds=tuple(_env_list("BETTY_DOG_FEEDS", "")) or None, sports=DOG_SPORTS, greyhounds=True)
meetings_manager.live_greyhound_source = greyhound_card.get_meetings
# When each race actually went off: Betty's off slips (C:\DBF\transact.DBF, BETTY_DBF_DIR), marked on the runners
race_offs = BettyOffTimes()
# How long past its scheduled time a race Betty hasn't sent off yet still counts as waiting for the off. Betty's off
# slips, UK/IRE races 13-26 Oct: horses a minute late on average, 99% within 12 min, the latest 22; dogs 90% within
# 70 s; virtual races on time. Betty marking a race off later than this was a catch-up after a pause, not the race.
LATE_OFF_LIMIT_MINS = {'domestic': 25, 'international': 25, 'greyhound': 5, 'virtual': 2}
DOG_TIME_AGREE_MINS = 2


def still_to_run(r: dict, struck_mins: float | None) -> bool:
    """
    The race of runner `r` had not gone off when the bet was struck (`struck_mins` from midnight, seconds as a
    fraction; None = unknown, every race counts). Betty's off slip decides when Betty marked the race off by then
    (`race_offs.mark`). Otherwise a race past its scheduled time is still to run only while Betty sends its races off
    and it is no more than LATE_OFF_LIMIT_MINS late: a race going off late. Anything else: the scheduled time decides.
    """
    if struck_mins is None:
        return True
    off = r.get('off_mins')
    if off is not None and off <= struck_mins:
        return False
    if r['minutes'] >= int(struck_mins):
        return True
    late = struck_mins - r['minutes']
    return bool(r.get('offs_tracked')) and late <= LATE_OFF_LIMIT_MINS.get(r.get('category', 'domestic'), 0)


def match_trap_on_dog_card(track: str, written_time: str, trap: int, struck_mins: float | None = None) -> dict | None:
    """
    A trap bet on Betty's greyhound card: the race at `track` within DOG_TIME_AGREE_MINS of the written time (morning
    or evening, whichever exists), not off before the bet was struck. Returns the runner only when exactly one race
    fits and the trap is not vacant; otherwise None (staff).
    """
    mins, _ = parse_race_time_to_minutes(written_time)
    if mins is None or not track:
        return None
    times = {mins} | ({mins + 720} if mins < 720 else set())
    want = re.sub(r'[^a-z]', '', track.lower())[:4]
    # marked afresh: the card may have been re-read since pre-flight marked it, and a dog race running late isn't off
    hits = [r for r in race_offs.mark(greyhound_card.get_runners())
            if r.get('number') == trap and r.get('minutes') is not None
            and re.sub(r'[^a-z]', '', r['meeting'].lower())[:4] == want
            and any(abs(r['minutes'] - t) <= DOG_TIME_AGREE_MINS for t in times)
            and still_to_run(r, struck_mins)]
    races = {(r['meeting'], r['time_str']) for r in hits}
    if len(races) != 1 or hits[0]['name'].strip().lower() == 'vacant':
        return None
    return hits[0]

# Matching thresholds (name similarity 0..1, see name_similarity)
NAME_ACCEPT = 0.92            # Stage 1: name alone identifies the runner anywhere on the card
NAME_ACCEPT_WITH_TIME = 0.80  # Stage 1: slightly weaker name, but its race time agrees with the written time
RACE_ACCEPT = 0.55            # Stage 2: best name within the race(s) at the written time...
RACE_MARGIN = 0.15            # ...and clearly better than every other runner in those races
NAME_MARGIN = 0.06            # Stage 1: best name must beat the next different runner by this much
TIME_AGREE_MINS = 10          # written time within this many minutes of the race = agreeing
NAME_VETO = 0.70              # Stage 2 is vetoed when a runner elsewhere fits the name this well and clearly better
# Who wins when a selection could be several runners (house rule): UK/IRE horse racing, then greyhounds (UK, Irish or
# Australian), then international horse racing, then virtual. A meeting written on the slip searches its own tier first.
CATEGORY_ORDER = ("domestic", "greyhound", "international", "virtual")
HINTED_TIERS = ("greyhound", "international", "virtual")
TIER_PENALTY = 0.15           # Stage 3: a lower-tier guess must fit this much better per tier to outrank a higher one


def name_similarity(a: str, b: str) -> float:
    """Similarity of two cleaned names; also compares with spaces removed ('One Hundredneighty' = 'Onehundredneighty')."""
    if not a or not b:
        return 0.0
    return max(SequenceMatcher(None, a, b).ratio(),
               SequenceMatcher(None, a.replace(' ', ''), b.replace(' ', '')).ratio())


MEETING_PLACEHOLDERS = {'', 'unknown', 'none', 'null', '?', '-', 'tbc', 'not specified'}
# 'N/A' and 'NA' are how customers write Newton Abbot. They mean "nothing written" only in the reader's own `meeting`
# field (a meeting written in full); in raw_meeting_hint, the customer's letters exactly as written, they are the
# meeting (1.0.0: 'N/A' was dropped, so a number bet at Newton Abbot had no meeting)
READER_ONLY_PLACEHOLDERS = {'n/a', 'na'}


def _real_meeting(value: Any, as_written: bool = True) -> str:
    """A meeting value with reader placeholders ('UNKNOWN', 'None', '?') treated as nothing written. `as_written`
    False: the reader's own full-name field, where 'N/A' is a placeholder too."""
    text = str(value or '').strip()
    low = text.lower()
    if low in MEETING_PLACEHOLDERS or (not as_written and low in READER_ONLY_PLACEHOLDERS):
        return ''
    return text


CLOTH_NUMBER_WORDS = {'no', 'no.', 'nos', 'num', 'number'}  # 'no 6' = cloth number 6, never a meeting


def _hinted_meeting(horse: dict) -> str:
    """Meeting written on the slip. The customer's own letter(s) such as 'N' or 'Y' (raw_meeting_hint) come first;
    a meeting name the reader filled in is used only when nothing was written. The 'no' of a cloth number is not a
    meeting (9.2453102, 26 Oct: '5.30 no 6' gave the meeting 'no')."""
    hint = _real_meeting(horse.get('raw_meeting_hint'))
    if hint.lower() in CLOTH_NUMBER_WORDS and selection_number(horse) is not None:
        hint = ''
    return hint or _real_meeting(horse.get('meeting'), as_written=False)


# (card meeting, written meeting) -> _meeting_matches. Cleared at each pre-flight: the answer can change with the
# meetings directory and the day's dog card. Each fuzzy lookup took ~3 ms, and the pre-flight asks once per runner
# (9.2455858, 28 Oct: 70 s on 'checking selections against Betty's card')
_meeting_match_cache: dict[tuple[str, str], bool] = {}


def _meeting_matches(runner_meeting: str, hinted: str) -> bool:
    """True when the card meeting fits what was written. A 1-2 letter hint is read against the card itself
    (e.g. 'N' at 4.28 = whichever 'N...' meeting has a race then), never guessed from a fixed list."""
    if not hinted:
        return False
    key = (runner_meeting, hinted)
    if key not in _meeting_match_cache:
        _meeting_match_cache[key] = _meeting_matches_uncached(runner_meeting, hinted)
    return _meeting_match_cache[key]


def _meeting_matches_uncached(runner_meeting: str, hinted: str) -> bool:
    if meetings_manager.are_meetings_equivalent(runner_meeting, hinted):
        return True
    h = re.sub(r'[^a-z]', '', hinted.lower())
    card = re.sub(r'[^a-z]', '', runner_meeting.lower())
    if not h:
        return False
    # Acronym check for multi-word meetings (e.g. 'PP' for Portman Park, 'DR' for Down Royal)
    words = [w for w in re.split(r'[^a-zA-Z]+', runner_meeting) if w]
    acronym = ''.join(w[0].lower() for w in words)
    if h == acronym:
        return True
    if len(h) <= 2:
        return card.startswith(h)
    return card.startswith(h[:4])


def match_runner_to_racecard(horse: dict, runners: list[dict], slip_meetings: set[str] | list[str] | None = None) -> tuple[bool, dict | None, list[dict]]:
    """
    Identifies a slip selection on the racecard, in the order a cashier would:
      1. NAME FIRST: find the written name anywhere on today's card (the card supplies the race and time,
         so a misread time does not matter when the name is clear).
      2. TIME NEXT: if the name is unclear, find the race(s) at the written time (and meeting hint) and pick
         the runner in those races whose name best fits the handwriting, provided it clearly stands out.
      3. Otherwise no confident match: returns the best 3 guesses for re-checking / staff confirmation.
    Domestic (UK/IRE) races are searched first, then international, then virtual.
    Returns: (is_confident_match, matched_runner, top_3_candidates)
    """
    raw_name = horse.get('name', '')
    raw_time = str(horse.get('raw_time') or horse.get('written_time') or horse.get('time', '')).strip()

    # Even Money prefix disambiguation (e.g. 'E- Flight Tracker' -> 'Flight Tracker' with odds 'Evs')
    m_lead = re.match(r'^(?:E\s*[\-\/\.]?|Evs\b|Evens\b)\s+(.+)$', raw_name, re.IGNORECASE)
    if m_lead:
        cand_name = m_lead.group(1).strip()
        full_e_match = any(clean_horse_name(r['name']) == clean_horse_name(raw_name) for r in runners)
        cand_match = any(clean_horse_name(r['name']) == clean_horse_name(cand_name) for r in runners)
        if not full_e_match and cand_match:
            raw_name = cand_name
            horse['name'] = cand_name
            if not horse.get('price') or str(horse.get('price', '')).lower() in ['sp', 'none', '']:
                horse['price'] = 'Evs'

    target = clean_horse_name(raw_name)
    if not target or not runners:
        return False, None, []
    target_mins, _ = parse_race_time_to_minutes(raw_time)
    hinted = _hinted_meeting(horse)

    def time_gap(r: dict) -> int | None:
        return abs(r['minutes'] - target_mins) if target_mins is not None and r.get('minutes') is not None else None

    # A meeting written on the slip that names a greyhound / international / virtual track is searched first
    hinted_cat = _hinted_tier(hinted)
    order = ([hinted_cat] if hinted_cat else []) + [c for c in CATEGORY_ORDER if c != hinted_cat]

    scored: list[tuple[float, dict]] = []  # filled tier by tier, so a domestic match never scores the virtual card
    best_name_overall = 0.0
    best_name_higher = 0.0     # best name fit in the tiers above: a lower tier locks only when it clearly beats it
    race_at_time_seen = False  # once a higher tier has a race at the written time, lower tiers may only match by name
    for category in order:
        tier = sorted(((name_similarity(target, clean_horse_name(r['name'])), r)
                       for r in runners if r.get('category', 'domestic') == category), key=lambda x: x[0], reverse=True)
        scored.extend(tier)
        if not tier:
            continue

        # Stage 1: name first
        best_s, best_r = tier[0]
        best_name_overall = max(best_name_overall, best_s)
        best_clean = clean_horse_name(best_r['name'])
        same_name = [r for s, r in tier if clean_horse_name(r['name']) == best_clean]
        next_s = next((s for s, r in tier if clean_horse_name(r['name']) != best_clean), 0.0)
        if len(same_name) > 1 and target_mins is not None:
            best_r = min(same_name, key=lambda r: time_gap(r) or 0)
        gap = time_gap(best_r)
        # A written meeting letter that fits another meeting racing at the written time contradicts a weaker name match
        meeting_conflict = bool(hinted) and not _meeting_matches(best_r['meeting'], hinted) and any(
            _meeting_matches(r['meeting'], hinted) and (tg := time_gap(r)) is not None and tg <= TIME_AGREE_MINS
            for _, r in tier)
        if best_s - next_s >= NAME_MARGIN and best_s - best_name_higher >= NAME_MARGIN and (
            best_s >= NAME_ACCEPT
            or (best_s >= NAME_ACCEPT_WITH_TIME and gap is not None and gap <= TIME_AGREE_MINS and not meeting_conflict)
        ):
            horse['_match_stage'] = f"name ({best_s:.2f})"
            return True, best_r, []

        # Stage 2: the race(s) at the written time
        if target_mins is not None and not race_at_time_seen:
            for window in (0, TIME_AGREE_MINS):
                in_window = [(s, r) for s, r in tier if (tg := time_gap(r)) is not None and tg <= window]
                if hinted:
                    at_meeting = [(s, r) for s, r in in_window if _meeting_matches(r['meeting'], hinted)]
                    in_window = at_meeting or in_window
                if not in_window:
                    continue
                race_at_time_seen = True
                race_best_s, race_best_r = in_window[0]
                race_next_s = in_window[1][0] if len(in_window) > 1 else 0.0
                # Name beats a misread time: a runner elsewhere whose name fits clearly better vetoes the race pick
                name_beats_time = best_name_overall >= NAME_VETO and best_name_overall - race_best_s >= RACE_MARGIN
                if (race_best_s >= RACE_ACCEPT and race_best_s - race_next_s >= RACE_MARGIN and not name_beats_time
                        and race_best_s - best_name_higher >= NAME_MARGIN):
                    horse['_match_stage'] = f"race at written time ({race_best_s:.2f} vs next {race_next_s:.2f})"
                    return True, race_best_r, []
                break  # the closest race(s) were ambiguous: do not widen onto other races
        best_name_higher = max(best_name_higher, best_s)

    # Stage 3: best 3 guesses across the card (name fit, nudged by agreeing time / meeting)
    def guess_score(item):
        s, r = item
        gap = time_gap(r)
        bonus = 0.08 if gap is not None and gap <= TIME_AGREE_MINS else (0.04 if gap is not None and gap <= 30 else 0.0)
        if _meeting_matches(r['meeting'], hinted):
            bonus += 0.05
        return s + bonus - TIER_PENALTY * order.index(r.get('category', 'domestic'))

    ranked = sorted(scored, key=guess_score, reverse=True)
    # Two guesses from the race(s) at the written time (meeting hint respected), the rest by name across the card
    race_guesses = []
    if target_mins is not None:
        in_window = [(s, r) for s, r in ranked if (tg := time_gap(r)) is not None and tg <= TIME_AGREE_MINS
                     and r.get('category', 'domestic') == order[0]]
        at_meeting = [(s, r) for s, r in in_window if _meeting_matches(r['meeting'], hinted)]
        race_guesses = [r for _, r in sorted(at_meeting or in_window, key=lambda x: x[0], reverse=True)[:2]]
    top3 = list(race_guesses)
    for _, r in ranked:
        if len(top3) >= 3:
            break
        if r not in top3:
            top3.append(r)
    top3.sort(key=lambda r: guess_score((name_similarity(target, clean_horse_name(r['name'])), r)), reverse=True)
    return False, None, top3


def written_race_times(horse: dict) -> set[int]:
    """Every time (minutes from midnight) a selection's written time can mean: 9-11 o'clock morning or evening
    (race_time_options), so 'No 4 9.40' finds the 21:40 dogs too (review R22)."""
    return set().union(*(race_time_options(str(horse.get(k) or '')) for k in ('raw_time', 'time')))


def selection_number(horse: dict) -> int | None:
    """Cloth / trap number when a selection is written as a number instead of a name ('No 8', '#4', 'T3', '5')."""
    m = re.match(r'^(?:no\.?|n\.?|#|trap|tr|t\.?|cloth)?\s*(\d{1,2})$', str(horse.get('name') or '').strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_clock_minutes(clock: str | None) -> float | None:
    """A 24-hour clock time ('13:05', '9:40', '13:05:30') in minutes from midnight, seconds as a fraction; None if
    unreadable."""
    m = re.match(r'^\s*(\d{1,2})[:.](\d{2})(?::(\d{2}))?\s*$', clock or '')
    if not m or int(m.group(1)) >= 24 or int(m.group(2)) >= 60:
        return None
    return int(m.group(1)) * 60 + int(m.group(2)) + (int(m.group(3)) / 60 if m.group(3) else 0)


def _hinted_tier(hinted: str | None) -> str | None:
    """The tier a meeting written on the slip belongs to, when it isn't UK/IRE horse racing (searched first)."""
    cat = meetings_manager.resolve_meeting(hinted)[0] if hinted else None
    return cat if cat in HINTED_TIERS else None


def match_number_to_racecard(horse: dict, runners: list[dict], struck_mins: float | None = None) -> tuple[bool, dict | None, list[dict]]:
    """
    A selection written as a cloth number: the runner with that number in the race at the written time, at the
    meeting written on the slip (letters read against the meetings racing then, e.g. 'So' = Southwell).
    Locked only when exactly one race fits: the written meeting must be identified, or the race must be the only
    one at that exact time. No readable time, or several races fitting, returns the possible runners for staff.
    Races already off when the bet was struck are never candidates. The written price is never used.
    Returns: (is_confident_match, matched_runner, candidates)
    """
    number = selection_number(horse)
    if number is None:
        return False, None, []
    times = written_race_times(horse)
    hinted = _hinted_meeting(horse)
    hinted_cat = _hinted_tier(hinted)
    order = ([hinted_cat] if hinted_cat else []) + [c for c in CATEGORY_ORDER if c != hinted_cat]

    for category in order:
        tier = [r for r in runners if r.get('category', 'domestic') == category and r.get('minutes') is not None and still_to_run(r, struck_mins)]
        numbered = [r for r in tier if r.get('number') == number]
        at_meeting = [r for r in numbered if _meeting_matches(r['meeting'], hinted)] if hinted else numbered
        if not at_meeting:
            continue
        if not times:
            # No readable time: never guessed. Staff choose from the races at that meeting with this number.
            return False, None, sorted(at_meeting, key=lambda r: r['minutes'])[:6]
        for window in (0, TIME_AGREE_MINS):
            fit = [r for r in at_meeting if any(abs(r['minutes'] - m) <= window for m in times)]
            if not fit:
                continue
            races_then = {(r['meeting'], r['time_str']) for r in tier if any(abs(r['minutes'] - m) <= window for m in times)}
            if len(fit) == 1 and (hinted or (window == 0 and len(races_then) == 1)):
                horse['_match_stage'] = f"number #{number} at the written time" + (f" and meeting '{hinted}'" if hinted else "")
                return True, fit[0], []
            return False, None, sorted(fit, key=lambda r: min(abs(r['minutes'] - m) for m in times))[:6]
        return False, None, sorted(at_meeting, key=lambda r: min(abs(r['minutes'] - m) for m in times))[:6]
    return False, None, []


# Rule 1.8.4 time clashes, the shop's order (user, 23 Oct): UK/IRE horses, international horses, dogs, virtual
TIME_CLASH_ORDER = ('domestic', 'international', 'greyhound', 'virtual')


def void_selection(race: dict) -> dict:
    """A void selection (VS) for the race `race` (any runner of it): entered with 'v' on that race, settled by Betty
    as a non-runner. Used for a card number that isn't in the race (user, 23 Oct; Rule 1.8.4)."""
    return {'name': 'Void Selection', 'meeting': race['meeting'], 'time_str': race['time_str'], 'minutes': race['minutes'],
            'number': None, 'category': race.get('category'), 'void': True}


def favourite_of(race: dict) -> dict:
    """The SP favourite of the race `race` (any runner of it): entered through Betty's folder as 'The Favourite'
    (Rule 1.8.4 "meeting and time are given, but no selection"; a 'fav' written)."""
    return {'name': 'The Favourite', 'meeting': race['meeting'], 'time_str': race['time_str'], 'minutes': race['minutes'],
            'number': None, 'category': race.get('category'), 'feed': race.get('feed'), 'favourite': True}


def unnamed_by_timing_rule(horse: dict, pools: list[list[dict]], struck_mins: float | None,
                           favourite: bool = False) -> tuple[list[dict], str]:
    """
    House rule for an un-named selection (a number or trap), as the rules file says (STATE_UNNAMED_UNTIMED_OR_MISTIMED;
    BetAnsells Rule 1.8.4). `pools` are tried in order (horses first unless a trap is written). Returns (runners, how):
      - the written race is clear but the number isn't in it: a void selection for that race;
      - untimed: the next race at that meeting off after the bet was struck (a void selection if the number isn't in it);
      - incorrectly timed (the meeting has no race then): a race at another meeting at that time with that number takes
        precedence, ranked UK/IRE horses, international, dogs, virtual; several in the first rank -> all of them (the
        caller divides the stake); none -> the next race at the written meeting.
    A race at the written meeting and time already off when the bet was struck (a late bet) is that runner, entered as
    written for Betty's late-selection box. ([], '') when the rule doesn't decide: a meeting not racing, a late bet
    whose number isn't in the race, or the rule not set.
    """
    action, cite = bookmaker_rules_mgr.get_state_action("STATE_UNNAMED_UNTIMED_OR_MISTIMED")
    if action != "NEXT_RACE_AT_MEETING_UNLESS_TIME_FITS_OTHER_MEETING":
        return [], ''
    number, hinted = selection_number(horse), _hinted_meeting(horse)
    if number is None and not favourite:
        return [], ''
    clock = time.localtime()
    now = struck_mins if struck_mins is not None else clock.tm_hour * 60 + clock.tm_min + clock.tm_sec / 60
    times = written_race_times(horse)

    def fits(r: dict, window: int = TIME_AGREE_MINS) -> bool:
        return any(abs(r['minutes'] - m) <= window for m in times)

    seen, every = set(), []
    for pool in pools:
        for r in pool:
            if r.get('minutes') is not None and id(r) not in seen:
                seen.add(id(r))
                every.append(r)
    at_meeting_all = [r for r in every if hinted and _meeting_matches(r['meeting'], hinted)]
    at_meeting_ids = {id(r) for r in at_meeting_all}
    if times:
        timed = [r for r in at_meeting_all if fits(r)]
        if timed:
            races = {(r['meeting'], r['time_str']) for r in timed}
            live = [r for r in timed if still_to_run(r, now)]
            if favourite:  # the favourite of the race written, if it's still to run
                return ([favourite_of(live[0])], f"{cite}: the favourite of the race written") if len(races) == 1 and live else ([], '')
            if len(races) == 1 and live and not any(r.get('number') == number for r in live):
                return [void_selection(live[0])], f"{cite}: #{number} is not in the {live[0]['time_str']} at {live[0]['meeting']}"
            late = next((r for r in timed if r.get('number') == number), None)
            if len(races) == 1 and not live and late:
                # A late bet: the race written was off before the bet was struck. It is entered as written and Betty's
                # late-selection box ("apply Void Selection processing?" -> Yes) voids it (user, 26 Oct; 9.2453119)
                return [late], "a late bet: the race was off when the bet was struck (Betty's late-selection box voids it)"
            return [], ''  # correctly timed (several races, or the number is there): not this rule
        # A race at the very time written beats races only near it, whatever their kind (9.2455858, 28 Oct: trap 1
        # at 3.13 was split over horse races at 15:06, 15:16 and 15:21, not the Sunderland dogs at 15:13)
        for window in (0, TIME_AGREE_MINS):
            other = [r for r in every if id(r) not in at_meeting_ids and (favourite or r.get('number') == number)
                     and fits(r, window) and still_to_run(r, now)]
            for tier in TIME_CLASH_ORDER:
                group = {(r['meeting'], r['time_str']): r for r in other if r.get('category', 'domestic') == tier}
                if group:
                    where = f"no race at {hinted} then" if hinted else "no meeting written"
                    split = f", stake divided over {len(group)} races" if len(group) > 1 else ""
                    found = [favourite_of(r) for r in group.values()] if favourite else list(group.values())
                    return found, f"{cite}: {where}, the time takes precedence{split}"
    elif favourite and not hinted:  # no meeting, time or race at all: the earliest race still to run, horse or dog
        first = sorted((r for r in every if r.get('category') in ('domestic', 'greyhound') and still_to_run(r, now)),
                       key=lambda r: r['minutes'])
        return ([favourite_of(first[0])], f"{cite}: no meeting or time, the earliest race still to run") if first else ([], '')
    for pool in pools:
        at_meeting = [r for r in pool if r.get('minutes') is not None and hinted and _meeting_matches(r['meeting'], hinted)]
        if not at_meeting or len({r['meeting'] for r in at_meeting}) != 1:
            continue  # the meeting isn't racing in this pool (or the letters fit several): try the next pool
        upcoming = sorted({(r['minutes'], r['time_str']) for r in at_meeting if still_to_run(r, now)})
        if not upcoming:
            return [], ''
        race = [r for r in at_meeting if r['time_str'] == upcoming[0][1]]
        how = f"{cite}: {'untimed' if not times else 'incorrectly timed'}, on for the next race at {race[0]['meeting']}"
        if favourite:
            return [favourite_of(race[0])], how
        runner = next((r for r in race if r.get('number') == number), None)
        return ([runner], how) if runner else ([void_selection(race[0])], how + f" (#{number} not in it)")
    return [], ''


TRAP_WRITTEN = re.compile(r'^(?:trap|tr|t)\.?\s*\d', re.IGNORECASE)  # 'T3', 'Tr 3', 'Trap 3': a dog
# The greyhound rules' single bets (Rule 1.21.7): an untimed trap with no meeting goes to the next UK race only in these
SINGLE_BETS = {'single', 'straight forecast', 'reversed forecast', 'combination forecast'}


def number_bet_is_dog(horse: dict, runners: list[dict]) -> bool:
    """
    A number bet as the shop reads it (user, 27 Oct): T / Tr / Trap written is always a dog. 'No.' or a bare number
    is a horse, unless the meeting written races only dogs today: 'No 3 7.30 Romford' names a dog race by its meeting
    and time, so the house rules make it trap 3 there. At a meeting racing both (Doncaster, Newcastle), 'No.' / a bare
    number is the horse, unless the slip says dogs or only the dogs race there at the time written.
    """
    if TRAP_WRITTEN.match(str(horse.get('name') or '').strip()):
        return True
    hinted = _hinted_meeting(horse)
    if not hinted:
        return False
    # Each meeting once, not each of the card's 13,000 runners (9.2455858: 'Sund' matched no horse runner, so
    # every one was compared)
    meetings = {(r.get('category') == 'greyhound', r['meeting']) for r in runners}
    horses_there = any(not dog and _meeting_matches(m, hinted) for dog, m in meetings)
    dogs_there = any(dog and _meeting_matches(m, hinted) for dog, m in meetings)
    if horses_there and dogs_there:
        # 9.2458296 (30 Oct): '6 £2w 4.28 NCLE' under 'DOG'S' was taken for a Newcastle horse; with no horse race at
        # Newcastle then, Rule 1.8.4 split it over four races abroad instead of the Newcastle dogs at 16:28
        return bool(horse.get('_slip_says_dogs')) or _only_dogs_race_then(horse, hinted, runners)
    if horses_there:
        return False
    return dogs_there or bool(is_greyhound_or_trap_selection(dict(horse))[2])


def _only_dogs_race_then(horse: dict, hinted: str, runners: list[dict]) -> bool:
    """At a meeting racing horses and dogs: a dog race there is at the written time and no horse race is near it."""
    times = written_race_times(horse)
    if not times:
        return False

    def near(r: dict, window: int) -> bool:
        return (r.get('minutes') is not None and any(abs(r['minutes'] - m) <= window for m in times)
                and _meeting_matches(r['meeting'], hinted))
    dogs = any(r.get('category') == 'greyhound' and near(r, DOG_TIME_AGREE_MINS) for r in runners)
    return dogs and not any(r.get('category') != 'greyhound' and near(r, TIME_AGREE_MINS) for r in runners)


def trap_by_dog_rules(horse: dict, dogs: list[dict], struck_mins: float | None, single: bool) -> tuple[list[dict], str]:
    """
    A trap the dog card didn't place by its written meeting and time, settled by the greyhound rules (1.21.6, 1.21.7;
    user, 27 Oct). Only UK meetings shown race by race (BAGS/BEGS) move a bet to another race. Returns (runners, how):
      - the race written already off when the bet was struck: that runner, entered as written for Betty's late-selection
        box (a bet on a race already run is void, never moved);
      - a UK meeting written: its next race to go off, or the race at the written time at another UK meeting when that
        goes off first;
      - no dog meeting written: the one UK race at the written time; with none, or no time, a single bet (or single
        forecast) goes on the next UK race to go off.
    A trap not in the race (or a vacant trap) is a void selection. ([], why) for staff: an overseas meeting with the
    wrong time (Rule 1.21.6), several races fitting, or a multiple the rules can't place.
    """
    number, hinted = selection_number(horse), _hinted_meeting(horse)
    clock = time.localtime()
    now = struck_mins if struck_mins is not None else clock.tm_hour * 60 + clock.tm_min + clock.tm_sec / 60
    times = set()
    for m, _ in (parse_race_time_to_minutes(str(horse.get(k) or '')) for k in ('raw_time', 'time')):
        if m is not None:
            times |= {m} | ({m + 720} if m < 720 else set())

    def races_of(rows: list[dict]) -> list[list[dict]]:
        by_race: dict[tuple, list[dict]] = {}
        for r in rows:
            by_race.setdefault((r['meeting'], r['time_str']), []).append(r)
        return sorted(by_race.values(), key=lambda rs: rs[0]['minutes'])

    def trap_in(race: list[dict], how: str) -> tuple[list[dict], str]:
        runner = next((r for r in race if r.get('number') == number and r['name'].strip().lower() != 'vacant'), None)
        return ([runner], how) if runner else ([void_selection(race[0])], how + f" (trap {number} not in it)")

    def fits(r: dict) -> bool:
        return any(abs(r['minutes'] - t) <= DOG_TIME_AGREE_MINS for t in times)

    dogs = [r for r in dogs if r.get('minutes') is not None]
    uk = [r for r in dogs if r.get('country') in ('UK', 'GB')]
    at_meeting = [r for r in dogs if hinted and _meeting_matches(r['meeting'], hinted)]
    if len({r['meeting'] for r in at_meeting}) > 1:
        return [], f"'{hinted}' fits several dog meetings ({', '.join(sorted({r['meeting'] for r in at_meeting}))})"
    timed = races_of([r for r in (at_meeting or uk) if fits(r)])
    if len(timed) > 1:
        return [], f"several dog races fit {'/'.join(sorted({r[0]['time_str'] for r in timed}))} and no single meeting is written"
    if timed:
        race = timed[0]
        if not still_to_run(race[0], now):
            late = next((r for r in race if r.get('number') == number), None)
            return ([late], "a late bet: the race was off when the bet was struck (void: Rule 1.21.7)") if late else (
                [], f"the {race[0]['time_str']} at {race[0]['meeting']} was off before the bet was struck and has no trap {number}")
        return trap_in(race, f"Rule 1.21.6: the {race[0]['time_str']} at {race[0]['meeting']}")
    if at_meeting:
        meeting = at_meeting[0]['meeting']
        if at_meeting[0].get('country') not in ('UK', 'GB'):
            return [], f"{meeting} isn't a UK meeting shown race by race: a trap there needs its right time (Rule 1.21.6)"
        upcoming = races_of([r for r in at_meeting if still_to_run(r, now)])
        if not upcoming:
            return [], f"no race left at {meeting}"
        elsewhere = races_of([r for r in uk if r['meeting'] != meeting and fits(r) and still_to_run(r, now)])
        if len(elsewhere) == 1 and elsewhere[0][0]['minutes'] < upcoming[0][0]['minutes']:
            return trap_in(elsewhere[0], "Rule 1.21.7: the race at the time written goes off before the next at "
                                         f"{meeting}")
        why = 'untimed' if not times else 'incorrectly timed'
        return trap_in(upcoming[0], f"Rule 1.21.7: {why}, on for the next race at {meeting}")
    if not single:
        return [], "a trap in a multiple with no meeting and no race at its time: the rules can't place it"
    upcoming = races_of([r for r in uk if still_to_run(r, now)])
    if not upcoming:
        return [], "no UK dog race left today"
    if len(upcoming) > 1 and upcoming[1][0]['minutes'] == upcoming[0][0]['minutes']:
        return [], f"two UK dog races are next at {upcoming[0][0]['time_str']}"
    return trap_in(upcoming[0], f"Rule 1.21.7: {'untimed' if not times else 'no race at that time'}, on for the next "
                                "UK dog race to go off")


def without_thousands_commas(text: str) -> str:
    """'£1,000.00' -> '£1000.00': money read with a thousands comma didn't parse (review R20)."""
    return re.sub(r'(?<=\d),(?=\d{3}(?!\d))', '', text or '')


def parse_currency_string_to_pence(raw_str: str) -> int | None:
    """Parses customer written currency strings like '60 -', '7 - 00', '7.00', '£7', '14 - 50', '50p' into pence."""
    if not raw_str:
        return None
    raw = without_thousands_commas(raw_str.strip().lower())

    # 1. Pounds and pence separated by dash, dot, or colon, optionally followed by 'p' (e.g. '7 - 00', '7 - 50p', '7.00',
    # '14-50', '£2.50'; '6 : 20' in the Lucky 15/31/63 coupon's Total Stake box, its colon printed)
    m1 = re.search(r'£?\s*(\d{1,4})\s*[-–—.:]\s*(\d{2})\s*p?\b', raw)
    if m1:
        pounds = int(m1.group(1))
        pence = int(m1.group(2))
        return pounds * 100 + pence

    # 2. Whole pounds with trailing dash or slash (UK standard notation: '60 -', '60-', '60 - .', '60/-', '10 -', '5 -', '100 -')
    # In UK betting shops, '60 -' defines £60.00 (6000p). The trailing dash represents zero pence (.00).
    m_dash = re.search(r'£?\s*(\d{1,4})\s*[-–—/]+(?:\s*[-–—/.=\s]*)?(?:total|stake|\s)*$', raw)
    if m_dash:
        return int(m_dash.group(1)) * 100

    # 3. Pounds with explicit £ symbol or 'total' prefix (e.g. '£7', 'total £10', 'total 7', 'total 60')
    m2 = re.search(r'(?:total|tot|stake|stk|t)?\s*[:=]?\s*£\s*(\d{1,4})\b', raw)
    if m2:
        return int(m2.group(1)) * 100

    m3 = re.search(r'(?:total|tot|stake|stk)\s*[:=]?\s*(\d{1,4})\b', raw)
    if m3:
        return int(m3.group(1)) * 100

    # 4. Pence with explicit 'p' (e.g. '50p', '50 p', '75p')
    m4 = re.search(r'\b(\d{1,3})\s*p\b', raw)
    if m4:
        return int(m4.group(1))

    return None


TOTAL_WORDS_PAT = r'\b(?:total|tot|stake|stk)\b'


def is_total_line(text: str) -> bool:
    """
    A line that can only be the customer's total: an amount, optionally with total/stake words ('£7', '60 -', '7 - 50',
    'Total £10', '50p'). Anything else on it (selection numbers like '2-9' with a stake, 'S/F/C', 'e/w', a runner,
    '1 x 50p doubles') makes it a bet line.
    """
    rest = re.sub(TOTAL_WORDS_PAT + r'|^\s*t\b', ' ', text.lower())
    rest = re.sub(r'£|(?<=\d)\s*p\b', ' ', rest)
    return bool(re.fullmatch(r'[\s\d.,:=\-–—/]*', rest)) and 1 <= len(re.findall(r'\d+', rest)) <= 2


def extract_written_total_pence(line_transcription: list[dict], gemini_pence: int | None = None, gemini_raw: str | None = None) -> tuple[int | None, str | None]:
    """
    Extracts the customer's written total stake in pence.
    Combines Gemini's parsed value with validation against raw text (handling UK '60 -' = £60.00 notation).
    """
    total_keywords_pat = TOTAL_WORDS_PAT

    # The Lucky 15/31/63 coupon's Total Stake box, pounds : pence with the colon printed ('6 : 20'), is the slip's last
    # line and its total. The reader took the unit stake above it ('10p') on every Lucky 31 on 27 Oct, so the
    # log said "Customer wrote £0.10". Spaces round the colon set it apart from a race time ('6:20').
    if line_transcription:
        last = str(line_transcription[-1].get('raw_text', '')).strip()
        if re.fullmatch(r'£?\s*\d{1,4}\s+:\s*\d{2}|£?\s*\d{1,4}\s*:\s+\d{2}', last):
            pence = parse_currency_string_to_pence(last)
            if pence:
                return pence, last

    # The reader's total must say 'total'/'stake' or be nothing but an amount: a bet line is never the total
    if gemini_raw and not re.search(total_keywords_pat, gemini_raw, re.I) and not is_total_line(gemini_raw):
        gemini_raw = None
        gemini_pence = None

    # Customer written total must appear in the last 2 lines of the slip or contain explicit 'total'/'stake'
    if gemini_raw and line_transcription:
        bottom_lines_text = " ".join(item.get('raw_text', '') for item in line_transcription[-2:])
        if not re.search(total_keywords_pat, gemini_raw, re.I) and (gemini_raw not in bottom_lines_text):
            gemini_raw = None
            gemini_pence = None

    # 1. First priority: Check if raw string contains explicit trailing dash notation (e.g. '60 -' = £60 = 6000p)
    if gemini_raw:
        parsed_from_raw = parse_currency_string_to_pence(gemini_raw)
        if parsed_from_raw is not None:
            # If raw string explicitly indicates whole pounds with dash (e.g. '60 -' = 6000p)
            # but Gemini mistakenly returned 60 pence, override with 6000p!
            if re.search(r'\b\d{1,4}\s*[-–—/]', gemini_raw) and parsed_from_raw >= 100:
                return parsed_from_raw, gemini_raw
            if gemini_pence is None or gemini_pence == 0:
                return parsed_from_raw, gemini_raw

    # 2. Check line transcription for explicit trailing dash notation (e.g. '60 -', '60 - TOTAL STAKE')
    # If customer wrote '60 -' at the bottom, but Gemini returned written_total_pence: 60 and raw: '60'
    if line_transcription:
        for item in reversed(line_transcription[-4:]):
            text = item.get('raw_text', '').strip()
            if re.search(r'\b\d{1,2}[:.]\d{2}\b', text) or not is_total_line(text):
                continue
            lt_pence = parse_currency_string_to_pence(text)
            if lt_pence is not None and lt_pence >= 100 and re.search(r'\b\d{1,4}\s*[-–—/]', text):
                # If gemini returned pence < 100 or gemini dropped the 100x scale
                if gemini_pence is None or gemini_pence < 100 or (gemini_pence * 100 == lt_pence):
                    return lt_pence, text

    if gemini_pence is not None and isinstance(gemini_pence, int) and gemini_pence > 0:
        raw_display = gemini_raw or f"£{gemini_pence / 100:.2f}"
        return gemini_pence, raw_display

    # Fallback: scan lines from bottom to top (ONLY lines that are nothing but a total)
    if line_transcription:
        for item in reversed(line_transcription[-3:]):
            text = item.get('raw_text', '').strip()
            if re.search(r'\b\d{1,2}[:.]\d{2}\b', text) or not is_total_line(text):
                continue
            pence = parse_currency_string_to_pence(text)
            if pence is not None and pence > 0:
                return pence, text

    return None, None


def parse_scoping_qualifier(text: str) -> tuple[str | None, int]:
    """Detects 'last N', 'above N', 'ab N', 'top N', 'first N', 'all N' qualifiers in bet text."""
    if not text:
        return None, 0
    word_map = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8}

    # 1. Last N
    m_last = re.search(r'\b(?:last|lst)\s*(\d+|two|three|four|five|six|seven|eight)\b', text, re.IGNORECASE)
    if m_last:
        val = m_last.group(1).lower()
        return 'last', word_map.get(val, int(val) if val.isdigit() else 0)

    # 2. Above N (including cursive/OCR glitches like abab, abov, aboub, abalt, asalt)
    # Also handles range notation 'AB 1-5' meaning 'use selections 1 through 5' (= above 5).
    # Detect range notation first: 'AB N-M' => use M as the qualifier count.
    m_above_range = re.search(r'\b(?:above|ab|abv|abab|abov|abve|aboub|asalt|abalt|aslt)\s*(\d+)\s*[-–]\s*(\d+)\b', text, re.IGNORECASE)
    if m_above_range:
        # 'AB 1-5' means selections 1 to 5, so use the higher bound (5) as the qualifier
        end_val = int(m_above_range.group(2))
        return 'above', end_val

    m_above = re.search(r'\b(?:above|ab|abv|abab|abov|abve|aboub|asalt|abalt|aslt)\s*(\d+|two|three|four|five|six|seven|eight)?\b', text, re.IGNORECASE)
    if m_above:
        val = m_above.group(1)
        if val:
            val = val.lower()
            return 'above', word_map.get(val, int(val) if val.isdigit() else 0)
        # In cursive handwriting, 'asalt', 'abalt', or 'aslt' represents 'ABOVE 5'
        if re.search(r'\b(?:asalt|abalt|aslt)\b', text, re.IGNORECASE):
            return 'above', 5
        return 'above', 0

    # 3. All / All N
    m_all = re.search(r'\b(?:all)\s*(\d+|two|three|four|five|six|seven|eight)?\b', text, re.IGNORECASE)
    if m_all:
        val = m_all.group(1)
        n = word_map.get(val.lower(), int(val) if val.isdigit() else 0) if val else 0
        return 'all', n

    # 4. Top / First N
    m_top = re.search(r'\b(?:top|first)\s*(\d+|two|three|four|five|six|seven|eight)\b', text, re.IGNORECASE)
    if m_top:
        val = m_top.group(1).lower()
        return 'top', word_map.get(val, int(val) if val.isdigit() else 0)

    return None, 0


def infer_selection_count_from_multiplier(bet_type: str, multiplier: int) -> int | None:
    """
    Infers the expected number of selections N from combination multiplier K
    where K = nCr(N, R).
    Calculates dynamically for ANY combination multiplier using combinatorial math.
    """
    if multiplier <= 0:
        return None
    b_type_norm = normalize_bet_type(bet_type)
    if 'double' in b_type_norm:
        r = 2
    elif 'treble' in b_type_norm:
        r = 3
    else:
        m_f = re.search(r'(\d+)[- ]folds?', b_type_norm)
        if m_f:
            r = int(m_f.group(1))
        else:
            return None

    for n in range(r, 25):
        if math.comb(n, r) == multiplier:
            return n
    return None


FOLD_BET_TYPES = ('', 'double', 'treble', 'accumulator')  # the fold a multiplier may decide; any other type it can't


def written_bet_type(text: str, names=()) -> str:
    """
    The bet type the customer's own words name, '' when they name none: '3x 50p WIN SINGLES' -> 'single', '1x 50p WIN
    PATENT' -> 'patent'. 'win' alone names no type here (it is the win part of '1x £1 win'), so a single needs the word.
    """
    t = normalize_bet_type('', text, names)
    if t == 'single' and not re.search(r'\bsingl', _without_names(str(text).lower(), names)):
        return ''
    return t


def names_its_own_type(written_type: str) -> bool:
    """A written type no multiplier may change: anything but a plain fold (single, patent, lucky 31, forecast ...)."""
    return written_type not in FOLD_BET_TYPES and not written_type.startswith('perm ')


COMPOUND_PART_WORDS = re.compile(r'\b(?:(doub\w*|dousl\w*|dubs\w*)|(treb\w*)|(acc\w*)|(singl\w*))\b', re.I)
# Words after a number that make it a count of bets or a fold size ('2 doubles', '4 fold'), never the stake
BET_COUNT_WORDS = re.compile(r'\s*(?:doub\w*|dousl\w*|dubs\w*|dbls?|treb\w*|acc\w*|singl\w*|\w*folds?|bets?|lines?|'
                             r'patents?|yankees?|trixies?|lucky|canadians?|heinz|goliaths?)\b', re.I)


def stake_from_bet_text(text: str) -> int | None:
    """
    The unit stake in pence written in a bet line: after a multiplier ('3 x 50 win double' = 50, '1 x 5 doubles' = 500),
    else an amount with £ or p ('2 doubles 50p' = 50, '£1 singles' = 100), else the first number that is neither a
    multiplier nor a count of bets ('5 ew treb' = 500). Whole pounds up to 10, pence above. None when none is written.
    Before (review B7, 28 Oct) the first number was the stake ('2 doubles 50p' = 2p) and a 'p' anywhere in the line
    made it pence.
    """
    t = str(text or '')
    after_x = re.search(r'\b\d+\s*x\s*(£)?\s*(\d{1,4})\s*(p|pence)?\b', t, re.I)
    candidates = [after_x] if after_x else []
    for m in re.finditer(r'(£)?\s*\b(\d{1,4})\s*(p|pence)?\b', t, re.I):
        rest = t[m.end():]
        if re.match(r'\s*x\b', rest, re.I) or (not (m.group(1) or m.group(3)) and BET_COUNT_WORDS.match(rest)):
            continue  # a multiplier ('3 x') or a count ('2 doubles'), not the stake
        candidates.append(m)
    marked = next((m for m in candidates if m.group(1) or m.group(3)), None)
    m = (after_x or marked or next(iter(candidates), None))
    if not m:
        return None
    digits = int(m.group(2))
    if m.group(1):  # pounds, with any pence written after them ('£2.50')
        pence = re.match(r'[.:]\s*(\d{2})\b', t[m.end():])
        return digits * 100 + (int(pence.group(1)) if pence else 0)
    if m.group(3):
        return digits
    return digits * 100 if digits <= 10 else digits


def compound_part_bet_type(part: str) -> str:
    """The bet type one part of an 'X & Y' bet line names: its own wording first ('r/f doubles', '4 fold acca'), else
    the word that let it be split (Doubles, Trebles, Acc, Singles). Before, every part that wasn't doubles was typed
    a treble, so '£1 singles & 50p double' entered a treble."""
    canonical = normalize_bet_type('', part)
    if canonical:
        return canonical
    m = COMPOUND_PART_WORDS.search(part)
    return ('double', 'treble', 'accumulator', 'single')[m.lastindex - 1] if m else 'single'


def split_compound_bet_entries(bets_list: list[dict]) -> list[dict]:
    """
    Splits compound bet entries where the VLM merged two distinct bet instructions into a single
    object using '&', 'and', or 'plus' (e.g. '3 x 50 win double & 1 x 50 ew treb').
    """
    if not bets_list:
        return bets_list
    expanded = []
    for bet in bets_list:
        desc = str(bet.get('description', '')).strip()
        m_split = re.search(r'^(.*?)\s*(?:&|\band\b|\bplus\b|\+)\s*(.*)$', desc, re.I)
        if m_split:
            part_a, part_b = m_split.group(1).strip(), m_split.group(2).strip()
            has_bet_a = bool(re.search(r'\b(?:doub\w*|dousl\w*|dubs\w*|treb\w*|acc\w*|singl\w*)\b', part_a, re.I))
            has_bet_b = bool(re.search(r'\b(?:doub\w*|dousl\w*|dubs\w*|treb\w*|acc\w*|singl\w*)\b', part_b, re.I))
            if has_bet_a and has_bet_b:
                print(f"[+] Compound Bet Splitter: Splitting merged bet '{desc}' into two distinct bets:")
                bet_a = dict(bet)
                bet_a['description'] = part_a
                bet_a['bet_type'] = compound_part_bet_type(part_a)
                stake_a = stake_from_bet_text(part_a)
                if stake_a is not None:
                    bet_a['stake_pence'] = stake_a
                bet_a['each_way'] = bool(re.search(r'\b(?:ew|e/w|each\s*way)\b', part_a, re.I))
                bet_a['cost_pence'] = calculate_bet_cost_pence(bet_a)

                bet_b = dict(bet)
                bet_b['description'] = part_b
                bet_b['bet_type'] = compound_part_bet_type(part_b)
                stake_b = stake_from_bet_text(part_b)
                if stake_b is not None:
                    bet_b['stake_pence'] = stake_b
                bet_b['each_way'] = bool(re.search(r'\b(?:ew|e/w|each\s*way)\b', part_b, re.I))
                bet_b['cost_pence'] = calculate_bet_cost_pence(bet_b)
                expanded.append(bet_a)
                expanded.append(bet_b)
                continue
        expanded.append(bet)
    return expanded


def recover_unemitted_interleaved_bets(
    bets_list: list[dict],
    selections: list[dict],
    line_transcription: list[dict]
) -> list[dict]:
    """
    Recovers intermediate bets that were transcribed in line_transcription but omitted
    by the VLM from the bets array (e.g. an intermediate '50p win double' placed between
    Selection 2 and Selection 3).
    """
    if not line_transcription or not selections:
        return bets_list

    # Backfill missing line numbers on selections if VLM omitted line_num
    for s_idx, s in enumerate(selections):
        if s.get('line_num') is None:
            s_name = str(s.get('name', '')).lower()
            s_time = str(s.get('time', '')).replace(':', '')
            for lt in line_transcription:
                lt_text = str(lt.get('raw_text', '')).lower()
                if (s_name and len(s_name) > 3 and s_name in lt_text) or (s_time and s_time in lt_text.replace(':', '').replace('.', '')):
                    s['line_num'] = lt.get('line_num')
                    break
            if s.get('line_num') is None:
                s['line_num'] = (s_idx + 1) * 2
                s['_line_guessed'] = True  # not read: the causality guard ignores the order (review R17)

    # Track existing lines and existing bet descriptions to prevent duplicate restoration
    existing_lines = set()
    existing_desc_tokens = []
    for b in bets_list:
        b_line = b.get('line_num')
        if b_line is not None:
            existing_lines.add(b_line)
        b_desc = str(b.get('description', '')).lower().strip()
        # Text matching is only for bets the VLM gave no line number: the same wording ('50 win double')
        # legitimately appears on several lines of one slip.
        if b_desc and b_line is None:
            existing_desc_tokens.append(b_desc)

    restored_bets = []
    for item in line_transcription:
        l_num = item.get('line_num')
        if l_num is None or l_num in existing_lines:
            continue
        text = str(item.get('raw_text', '')).strip()
        norm_text = text.lower()

        # If an existing bet already matches this text, it is NOT omitted!
        if any(norm_text in ex or ex in norm_text or SequenceMatcher(None, norm_text, ex).ratio() > 0.70 for ex in existing_desc_tokens):
            continue

        if not re.search(r'\b(?:doub\w*|dousl\w*|dubs\w*|treb\w*|acca\w*|accum\w*)\b', text, re.I):
            continue
        if re.search(r'cross(?:ed)?\s*out|struck|strike|scribbled|cancel', text, re.I):
            continue  # a crossed-out instruction is never a bet
        if re.search(r'\b\d{1,2}[:.]\d{2}\b', text) and not re.search(r'\b(?:win|ew|doub|treb)\b', text, re.I):
            continue

        preceding = [s for s in selections if (s.get('line_num') or 0) < l_num]
        if len(preceding) < 2:
            continue

        stake_p = stake_from_bet_text(text) or 50

        is_ew = bool(re.search(r'\b(?:ew|e/w|each\s*way)\b', text, re.I))
        b_type = 'double'
        if re.search(r'\b(?:treb\w*)\b', text, re.I):
            b_type = 'treble'
        elif re.search(r'\b(?:acc\w*)\b', text, re.I):
            b_type = 'accumulator'

        req_count = 2 if b_type == 'double' else (3 if b_type == 'treble' else len(preceding))
        if len(preceding) >= req_count:
            chosen_horses = preceding[-req_count:] if len(preceding) > req_count else list(preceding)
            chosen_names = set(h.get('name') for h in chosen_horses if h.get('name'))

            # Check if an existing bet already covers these exact horses or contains them in combination
            already_covered = False
            for ex in bets_list:
                # A bet holding runners written BELOW its own line is mis-scoped; it cannot vouch for this line
                ex_line = ex.get('line_num')
                if ex_line is not None and any((h.get('line_num') or 0) > ex_line for h in ex.get('horses', [])):
                    continue
                ex_type = normalize_bet_type(ex.get('bet_type', ''), ex.get('description', ''), selection_names(ex))
                ex_names = set(h.get('name') for h in ex.get('horses', []) if h.get('name'))
                if ex_type == b_type and chosen_names == ex_names:
                    already_covered = True
                    break
                if b_type == 'double' and ('double' in ex_type or 'doubles' in ex_type) and len(ex_names) > 2 and chosen_names.issubset(ex_names):
                    already_covered = True
                    break

            if already_covered:
                continue

            new_bet = {
                'line_num': l_num,
                'description': text,
                'bet_type': b_type,
                'each_way': is_ew,
                'stake_pence': stake_p,
                'horses': [dict(h) for h in chosen_horses]
            }
            new_bet['cost_pence'] = calculate_bet_cost_pence(new_bet)
            restored_bets.append(new_bet)
            print(f"[+] Interleaved Bet Restorer: Recovered omitted bet at Line {l_num} '{text}':")
            print(f"    - Type: {b_type} | Stake: {stake_p}p | EW: {is_ew} | Horses: {[h.get('name') for h in chosen_horses]}")

    if restored_bets:
        combined = bets_list + restored_bets
        combined.sort(key=lambda b: b.get('line_num') or 999)
        return combined
    return bets_list


def reconcile_bet_scoping_qualifiers(
    bets_list: list[dict],
    selections: list[dict],
    line_transcription: list[dict] | None = None
) -> list[dict]:
    """
    Enforces customer positional scoping qualifiers (e.g. 'LAST 2', 'LAST 3', 'ABOVE 2', 'AB 4', 'ALL 5')
    and combination multipliers (e.g. '6 x doubles' -> 4 selections, '3 x doubles' -> 3 selections).

    STRICT SEQUENTIAL CAUSALITY INVARIANT:
    - Bets are written from top to bottom.
    - A bet written at line L applies STRICTLY to selections written ABOVE line L (line_num < L).
    - It MUST NEVER pull or retain selections written BELOW line L.
    """
    if not bets_list or not selections:
        return bets_list

    bets_list = split_compound_bet_entries(bets_list)

    if line_transcription:
        bets_list = recover_unemitted_interleaved_bets(bets_list, selections, line_transcription)

    lines_map: dict[int, str] = {}
    if line_transcription:
        for lt in line_transcription:
            l_num = lt.get('line_num')
            l_text = str(lt.get('raw_text', '')).strip()
            if l_num is not None:
                lines_map[l_num] = l_text

    used_lines: set[int] = set()
    for b_idx, bet in enumerate(bets_list):
        desc = str(bet.get('description', '')).strip()
        raw = str(bet.get('raw_text', '')).strip()
        combined_text = f"{desc} {raw}".strip()
        b_line = bet.get('line_num')

        q_type, q_n = parse_scoping_qualifier(desc)
        if not q_type:
            q_type, q_n = parse_scoping_qualifier(raw)

        # If not found in bet description, check matching lines in line_transcription
        matched_line_num = b_line
        if not q_type and lines_map:
            if b_line in lines_map:
                lt_text = lines_map[b_line]
                lt_q_type, lt_q_n = parse_scoping_qualifier(lt_text)
                if lt_q_type and lt_q_n > 0:
                    q_type, q_n = lt_q_type, lt_q_n
                    matched_line_num = b_line
            else:
                b_type_keyword = str(bet.get('bet_type', '')).lower()
                b_ew = bool(bet.get('each_way', False))
                for l_num, l_text in lines_map.items():
                    if l_num in used_lines:
                        continue
                    l_lower = l_text.lower()
                    # whole words only: 'ew' inside Newmarket, Newcastle or Jewel is not each way
                    has_ew = bool(re.search(r'\b(?:ew|e/w|e\.w|each\s*way)\b', l_lower))
                    if has_ew != b_ew:
                        continue
                    # its own type's words only: a treble isn't paired with a line saying 'doub' (review R14)
                    own_words = BET_TYPE_WORDS.get(normalize_bet_type(b_type_keyword), ())
                    if b_type_keyword and (b_type_keyword in l_lower or any(w in l_lower for w in own_words)):
                        used_lines.add(l_num)
                        matched_line_num = l_num
                        lt_q_type, lt_q_n = parse_scoping_qualifier(l_text)
                        if lt_q_type and lt_q_n > 0:
                            q_type, q_n = lt_q_type, lt_q_n
                            if f"{q_type} {q_n}" not in desc.lower():
                                bet['description'] = f"{desc} {q_type.upper()} {q_n}".strip()
                        break

        # Candidate selections preceding or on this bet line
        effective_line = matched_line_num or b_line
        if effective_line is not None:
            preceding_selections = [s for s in selections if (s.get('line_num') or 0) <= effective_line]
        else:
            preceding_selections = []

        # If no preceding selections (e.g. bet is a header on Line 1 before any selections), candidate pool is all selections
        if not preceding_selections:
            preceding_selections = list(selections)

        # 1. STRICT CAUSALITY ENFORCEMENT:
        # A bet written after selections can NEVER contain selections written strictly below its instruction line!
        # GUARDS:
        # - Single-bet slip: If there is only 1 bet on the slip, all selections belong to that bet! Never truncate.
        # - Full cover / fixed count bets: If bet type requires N runners (e.g. Lucky 31=5, Canadian=5, Yankee=4, etc.)
        #   and bet already has N runners, do NOT strip below N.
        # - Only applies when multiple separate bets exist on the slip (e.g. interleaved bet entries).
        line_nums_read = not any(s.get('_line_guessed') for s in selections)
        if (len(bets_list) > 1 and effective_line is not None and line_nums_read and len(preceding_selections) > 0
                and len(preceding_selections) < len(selections)):
            norm_b = normalize_bet_type(str(bet.get('bet_type', '')), desc, selection_names(bet))
            req_selections_map = {
                'single': 1, 'double': 2, 'treble': 3,
                'trixie': 3, 'patent': 3,
                'yankee': 4, 'lucky 15': 4,
                'canadian': 5, 'super yankee': 5, 'lucky 31': 5,
                'heinz': 6, 'lucky 63': 6,
                'super heinz': 7,
                'goliath': 8
            }
            req_n = req_selections_map.get(norm_b)
            # Fewest selections the bet type can be: a cut below this is wrong, the runners below belong to the bet.
            # 9.2448236 (23 Oct): '£10 S/F/C' with 'TRAPS 4-5' on the line under it lost trap 5, the lone-selection
            # rule made the forecast a £10 win single, and the money still matched, so it was placed.
            min_n = req_n or {'straight forecast': 2, 'reversed forecast': 2, 'combination forecast': 2,
                              'tricast': 3, 'combination tricast': 3, 'accumulator': 2}.get(norm_b)

            preceding_names = {s.get('name') for s in preceding_selections if s.get('name')}
            preceding_line_nums = {s.get('line_num') for s in preceding_selections if s.get('line_num') is not None}
            filtered_horses = [
                h for h in bet.get('horses', [])
                if (h.get('line_num') in preceding_line_nums) or (h.get('name') in preceding_names)
            ]
            if min_n is not None and len(filtered_horses) < min_n:
                pass
            elif len(filtered_horses) < len(bet.get('horses', [])):
                removed_names = [h.get('name') for h in bet.get('horses', []) if h not in filtered_horses]
                print(f"[+] Causality Guard: Removed runner(s) {removed_names} from Bet #{b_idx + 1} '{desc}' because they were written BELOW line {effective_line}.")
                bet['horses'] = filtered_horses

        # 2. COMBINATION MULTIPLIER RESOLUTION (e.g. '6 x doubles' -> 4 selections, '3 x doubles' -> 3 selections)
        m_mult = re.search(r'\b(\d+)\s*x\b', combined_text)
        inferred_n = None
        mult_val = None
        if m_mult:
            mult_val = int(m_mult.group(1))
            inferred_n = infer_selection_count_from_multiplier(bet.get('bet_type', ''), mult_val)

        # A qualifier must agree with the bet it is attached to. Customers' margin notes ('LAST 2', 'ABV 4') often
        # sit half a line off; a note that contradicts the bet belongs to a neighbouring line.
        if q_type and q_n > 0:
            norm_q = normalize_bet_type(str(bet.get('bet_type', '')), combined_text, selection_names(bet))
            has_multiplier = bool(re.search(r'\b\d+\s*x\b|\b(?:x|cross)\s*doub', combined_text, re.I))
            single_line_size = {'double': 2, 'treble': 3}.get(norm_q) if not has_multiplier else None
            if single_line_size and q_n > single_line_size and len(bet.get('horses', [])) == single_line_size:
                print(f"[+] Scoping qualifier '{q_type.upper()} {q_n}' ignored for Bet #{b_idx + 1} '{desc}': a single {norm_q} "
                      f"has {single_line_size} selections (the note belongs to a neighbouring line).")
                q_type, q_n = None, 0
            elif inferred_n and q_n != inferred_n:
                print(f"[+] Scoping qualifier '{q_type.upper()} {q_n}' conflicts with the written {mult_val}x for Bet #{b_idx + 1}; "
                      f"using the multiplier ({inferred_n} selections).")
                q_type, q_n = None, 0
            elif norm_q in ('straight forecast double', 'reversed forecast double') and q_n < 4:
                q_n = 4  # a forecast double always covers two races x two runners

        if q_type and q_n > 0:
            if q_type == 'all':
                if 0 < q_n <= len(preceding_selections):
                    target_horses = preceding_selections[-q_n:]
                else:
                    target_horses = list(preceding_selections)
            elif q_n <= len(preceding_selections):
                if q_type in ['last', 'above']:
                    target_horses = preceding_selections[-q_n:]
                else:
                    target_horses = preceding_selections[:q_n]
            else:
                target_horses = list(preceding_selections)

            orig_names = [h.get('name') for h in bet.get('horses', [])]
            scoped_names = [h.get('name') for h in target_horses]
            if orig_names != scoped_names:
                print(f"[+] Positional Scoping Enforced: Bet #{b_idx + 1} '{bet.get('description')}' re-scoped using '{q_type.upper()} {q_n}':")
                print(f"    - Previous horses: {orig_names}")
                print(f"    - Scoped horses:   {scoped_names}")
                bet['horses'] = [dict(h) for h in target_horses]
                if q_n == 2 and 'double' in bet.get('bet_type', '').lower():
                    bet['bet_type'] = 'double'
                elif q_n == 3 and 'treble' in bet.get('bet_type', '').lower():
                    bet['bet_type'] = 'treble'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)

        elif inferred_n and inferred_n > 0 and len(preceding_selections) >= inferred_n:
            # If bet specifies a multiplier (e.g. '6 x doubles' requires 4 selections)
            orig_names = [h.get('name') for h in bet.get('horses', [])]
            if len(orig_names) != inferred_n or any(h not in [s.get('name') for s in preceding_selections] for h in orig_names):
                target_horses = preceding_selections[-inferred_n:]
                scoped_names = [h.get('name') for h in target_horses]
                mult_label = f"{mult_val}x" if mult_val is not None else "combination"
                print(f"[+] Multiplier Scoping Enforced: Bet #{b_idx + 1} '{desc}' auto-scoped to {inferred_n} preceding selections ({mult_label}):")
                print(f"    - Previous horses: {orig_names}")
                print(f"    - Scoped horses:   {scoped_names}")
                bet['horses'] = [dict(h) for h in target_horses]
                bet['cost_pence'] = calculate_bet_cost_pence(bet)

        else:
            # Accumulator Selection Minimum Invariant:
            # An accumulator MUST have at least 4 selections.
            # Strictly scoped within preceding_selections (NEVER pull selections below this bet line!)
            #
            # IMPORTANT: If the description explicitly mentions 'doub' or 'doubles', the VLM may have
            # assigned bet_type='accumulator' by mistake. Correct the bet_type to 'doubles' BEFORE
            # the accumulator auto-expansion guard runs, or 'N x doubles' will be incorrectly expanded
            # to all preceding selections.
            combined_text_check = f"{bet.get('description', '')} {bet.get('raw_text', '')}"
            if re.search(r'\b(?:doub\w*)\b', combined_text_check, re.I) and not re.search(r'\b(?:treb\w*|acc\w*|acca)\b', combined_text_check, re.I):
                if bet.get('bet_type', '').lower() in ('accumulator', 'single', ''):
                    print(f"[+] Pre-Expansion Type Correction: Bet #{b_idx + 1} '{bet.get('description')}' bet_type corrected from '{bet.get('bet_type')}' -> 'doubles' (explicit 'doub' keyword found).")
                    bet['bet_type'] = 'doubles'
                    bet['cost_pence'] = calculate_bet_cost_pence(bet)

            b_type_norm = normalize_bet_type(bet.get('bet_type', ''), bet.get('description', ''), selection_names(bet))
            if b_type_norm == 'accumulator' and len(bet.get('horses', [])) < 4:
                if len(preceding_selections) >= 4:
                    orig_names = [h.get('name') for h in bet.get('horses', [])]
                    scoped_names = [h.get('name') for h in preceding_selections]
                    if orig_names != scoped_names:
                        print(f"[+] Accumulator Scoping Enforced: Bet #{b_idx + 1} '{bet.get('description')}' expanded from {len(orig_names)} to all {len(scoped_names)} preceding selections:")
                        print(f"    - Previous horses: {orig_names}")
                        print(f"    - Scoped horses:   {scoped_names}")
                        bet['horses'] = [dict(h) for h in preceding_selections]
                        bet['cost_pence'] = calculate_bet_cost_pence(bet)

        # A single double / treble left short of runners (e.g. it named a selection that does not exist)
        # covers the selections written directly above it.
        norm_fill = normalize_bet_type(str(bet.get('bet_type', '')), combined_text, selection_names(bet))
        fill_n = {'double': 2, 'treble': 3}.get(norm_fill)
        if (fill_n and len(bet.get('horses', [])) < fill_n and len(preceding_selections) >= fill_n
                and not re.search(r'\b\d+\s*x\b', combined_text)):
            bet['horses'] = [dict(h) for h in preceding_selections[-fill_n:]]
            print(f"[+] Bet #{b_idx + 1} '{desc}' had fewer than {fill_n} valid selections; using the {fill_n} written above it.")
            bet['cost_pence'] = calculate_bet_cost_pence(bet)

        # Mathematical Combination & Fold Reconciliation:
        # Reconcile bet_type based on selection count and explicit multiplier
        n_horses = len(bet.get('horses', []))
        m_mult_raw = re.search(r'\b(\d+)\s*x\b', combined_text)
        mult_num = int(m_mult_raw.group(1)) if m_mult_raw else None

        # Forecasts / tricasts (incl. forecast doubles) have fixed line counts: never re-fold them.
        norm_now = normalize_bet_type(str(bet.get('bet_type', '')), combined_text, selection_names(bet))
        is_fc_or_tri = 'forecast' in norm_now or 'tricast' in norm_now
        # A type the customer named (singles, patent, lucky 31 ...) is the bet: the multiplier only counts its bets.
        # 9.2459179 (31 Oct): '3x 50p WIN SINGLES' + '1x 50p WIN PATENT' on 3 runners were re-folded from the
        # multipliers alone into 3 doubles + a treble (£2.00 against £5.00 paid), on all three scans.
        written_type = written_bet_type(combined_text, selection_names(bet))
        keeps_written_type = names_its_own_type(written_type)
        if keeps_written_type and normalize_bet_type(str(bet.get('bet_type', ''))) != written_type:
            print(f"[+] Bet #{b_idx + 1} '{desc}': the written '{written_type}' kept (read as '{bet.get('bet_type')}').")
            bet['bet_type'] = written_type
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        # The bet type the customer actually WROTE always outranks a fold guessed from the multiplier.
        # e.g. '4x 50 WIN x DOUBLES' on 2+2 same-race runners is 4 cross doubles, NOT 4C3 = 4 trebles.
        has_doub_word = bool(re.search(r'\b(?:doub\w*|dousl|dubs)\b', combined_text, re.I))
        has_treb_word = bool(re.search(r'\b(?:treb\w*|9reb|greb)\b', combined_text, re.I))
        has_acc_word = bool(re.search(r'\b(?:acc\w*|acca)\b', combined_text, re.I))
        written_fold = None
        if has_doub_word and not (has_treb_word or has_acc_word):
            written_fold = 2
        elif has_treb_word and not (has_doub_word or has_acc_word):
            written_fold = 3

        if is_fc_or_tri or keeps_written_type:
            pass
        elif n_horses == 3:
            # On 3 selections:
            # Explicit 3x multiplier or '3 doubles' -> 3 combination doubles (3C2 = 3 doubles)
            # 1x or 'treb' -> 'treble' (3C3 = 1 treble)
            # 'double' WITHOUT 3x (e.g. '50 EW Doub', '50p double') -> strictly 1 single double on the LAST 2 selections!
            # 'double' / 'treble(s)' written in full count too (review B5, 28 Oct: only 'doub' / 'treb' did, so a
            # '50p double' left on 3 runners cost 3 doubles). The plural 'doubles' stays out: on 3 runners it is 3 doubles.
            has_treb_hint = bool(re.search(r'\b(?:treb|trebl|trebles?|trebc|9reb|greb)\b', combined_text, re.I))
            has_doub_hint = bool(re.search(r'\b(?:doub|double|dousl|dubs)\b', combined_text, re.I))
            has_3x_mult = bool(mult_num == 3 or re.search(r'\b3\s*x\b', combined_text, re.I) or re.search(r'\b3\s*doubles\b', combined_text, re.I))

            # '1x' makes a treble only when no double is written: '1x 50p double' is one double, not a treble
            if (has_treb_hint or (mult_num == 1 and written_fold != 2)) and not (has_doub_hint and has_3x_mult):
                print(f"[+] Reconciled Bet #{b_idx + 1} '{desc}': 1x / Treble on 3 selections is a Treble.")
                bet['bet_type'] = 'treble'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif has_3x_mult:
                print(f"[+] Reconciled Bet #{b_idx + 1} '{desc}': 3x / Doubles on 3 selections is Doubles.")
                bet['bet_type'] = 'doubles'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif has_doub_hint:
                print(f"[+] Reconciled Bet #{b_idx + 1} '{desc}': Single double without 3x multiplier scoped to last 2 selections.")
                bet['horses'] = [dict(h) for h in bet['horses'][-2:]]
                bet['bet_type'] = 'double'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
        elif n_horses >= 4:
            # Dynamic Combinatorial Matching for N >= 4:
            matched_k = None
            if mult_num is not None:
                for k in range(2, n_horses + 1):
                    if math.comb(n_horses, k) == mult_num:
                        matched_k = k
                        break

            if written_fold is not None and matched_k is not None and matched_k != written_fold:
                print(f"[+] Fold Reconciliation: '{desc}' keeps its written fold ({'doubles' if written_fold == 2 else 'trebles'}); "
                      f"{mult_num}x on {n_horses} selections is not {n_horses}C{written_fold} (cross bet over same-race runners).")
                matched_k = None
                if written_fold == 2 and normalize_bet_type(str(bet.get('bet_type', ''))) != 'double':
                    bet['bet_type'] = 'doubles'
                    bet['cost_pence'] = calculate_bet_cost_pence(bet)

            if matched_k == 2:
                print(f"[+] Dynamic Fold Reconciliation: {mult_num}x on {n_horses} selections matched combination doubles.")
                bet['bet_type'] = 'doubles'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif matched_k == 3:
                print(f"[+] Dynamic Fold Reconciliation: {mult_num}x on {n_horses} selections matched combination trebles.")
                bet['bet_type'] = 'treble'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif matched_k and matched_k == n_horses:
                print(f"[+] Dynamic Fold Reconciliation: 1x on {n_horses} selections is an accumulator.")
                bet['bet_type'] = 'accumulator'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif matched_k and matched_k > 3:
                print(f"[+] Dynamic Fold Reconciliation: {mult_num}x on {n_horses} selections matched perm {matched_k}-folds.")
                bet['bet_type'] = f"perm {matched_k}-folds"
                bet['cost_pence'] = calculate_bet_cost_pence(bet)
            elif (mult_num == 1 or 'acc' in combined_text.lower()) and bet.get('bet_type', '').lower() in ['double', 'doubles', 'treble', '']:
                bet['bet_type'] = 'accumulator'
                bet['cost_pence'] = calculate_bet_cost_pence(bet)

        # EW Conflict Resolution with Line Transcription:
        if bet.get('each_way'):
            matching_text = ''
            if b_line is not None:
                matching_text = lines_map.get(b_line, '') or lines_map.get(b_line - 1, '')
            if matching_text and re.search(r'\bwin\b', matching_text, re.I) and not re.search(r'\b(?:ew|e/w|each\s*way)\b', matching_text, re.I):
                print(f"[+] EW Conflict Resolved: Bet #{b_idx + 1} '{desc}' corrected from each_way=True to each_way=False based on line transcription '{matching_text}'.")
                bet['each_way'] = False
                bet['cost_pence'] = calculate_bet_cost_pence(bet)

    # Deduplicate OCR phantom duplicates (e.g. '3x 50 EW DREB' transcribed alongside '1x 50 EW TREB')
    deduped_bets = []
    for b in bets_list:
        desc = b.get('description', '').lower()
        if 'dreb' in desc or 'grebl' in desc:
            has_valid_treb = any(  # the same bet read twice: same stake, terms and runners (review R16)
                'treb' in other.get('description', '').lower()
                and other.get('stake_pence') == b.get('stake_pence')
                and other.get('each_way') == b.get('each_way')
                and sorted(selection_names(other)) == sorted(selection_names(b))
                for other in bets_list if other is not b
            )
            if has_valid_treb:
                print(f"[+] Dropped phantom OCR duplicate bet: '{b.get('description')}' in favor of genuine Treble.")
                continue
        deduped_bets.append(b)
    bets_list = deduped_bets

    # Merge split-line doubles within the same section
    # (e.g. Gemini read '50 WIN DOUBLE' on line 5 and '3 x 50 EW DOUB' on line 6 because '3 x' was in left column)
    merged_section_bets = []
    skip_indices = set()
    for i in range(len(bets_list)):
        if i in skip_indices:
            continue
        b_curr = bets_list[i]
        b_curr_type = normalize_bet_type(b_curr.get('bet_type', ''), b_curr.get('description', ''), selection_names(b_curr))

        if b_curr_type == 'double' and i < len(bets_list) - 1:
            b_next = bets_list[i + 1]
            b_next_type = normalize_bet_type(b_next.get('bet_type', ''), b_next.get('description', ''), selection_names(b_next))

            if b_next_type == 'double':
                curr_names = sorted(h.get('name') for h in b_curr.get('horses', []))
                next_names = sorted(h.get('name') for h in b_next.get('horses', []))
                if curr_names == next_names:
                    # Only merge when IDENTICAL horse sets — the VLM split one bet across two lines (e.g. left-column '3 x').
                    # Do NOT merge when next_bet has more horses than curr_bet: that means they are two separate bets.
                    has_win = 'win' in b_curr.get('description', '').lower() or 'win' in b_next.get('description', '').lower()
                    # a written '3 x', not any '3' ('£3 win double'; review R16)
                    has_3x = bool(re.search(r'\b3\s*x\b', f"{b_curr.get('description', '')} {b_next.get('description', '')}", re.I))
                    if has_3x:
                        unit_sp = b_curr.get('stake_pence') or b_next.get('stake_pence') or 50
                        stake_lbl = f"{unit_sp}p" if unit_sp < 100 else (f"£{unit_sp // 100}" if unit_sp % 100 == 0 else f"£{unit_sp / 100:.2f}")
                        ew_label = "Win" if has_win else "EW"
                        print(f"[+] Merged split-line doubles '{b_curr.get('description')}' and '{b_next.get('description')}' into '3 x {stake_lbl} {ew_label} Doubles':")
                        b_next['horses'] = b_next.get('horses') if len(b_next.get('horses', [])) == 3 else b_curr.get('horses')
                        b_next['bet_type'] = 'doubles'
                        b_next['description'] = f"3 x {stake_lbl} {ew_label} Doubles"
                        b_next['each_way'] = not has_win
                        b_next['stake_pence'] = unit_sp
                        b_next['cost_pence'] = calculate_bet_cost_pence(b_next)
                        skip_indices.add(i)
                        continue

        merged_section_bets.append(b_curr)
    bets_list = merged_section_bets

    return bets_list


def _single_stake_pence(bet: dict) -> int | None:
    """A single's unit stake in pence (from 'unit_stake' when 'stake_pence' is null); None when neither was read."""
    sp = bet.get('stake_pence', 0)
    if sp is None and bet.get('unit_stake') is not None:
        try:
            sp = round(float(bet['unit_stake']) * 100)
        except (ValueError, TypeError):
            sp = 0
    return sp


BET_TYPE_WORDS = {'double': ('doub', 'dbl'), 'treble': ('treb', 'tbl'), 'accumulator': ('acc', 'fold')}


def _merge_singles(group: list[dict], how: str) -> list[dict]:
    """
    One F8 'Singles' bet for singles sharing a unit stake and each-way terms: Betty places one single per selection.
    A selection already in the merged bet stays a single of its own: two singles on one horse are two bets, not one
    (review R15); if the reader listed it twice by mistake, the money check sends the slip to staff.
    """
    if len(group) == 1:
        return list(group)
    base_bet = dict(group[0])
    all_horses, seen_keys, repeats = [], set(), []
    for b in group:
        for h in b.get('horses', []):
            h_name = str(h.get('name', '')).strip().lower()
            h_time = str(h.get('time', '')).strip().lower()
            h_key = (h_name, h_time) if h_name else id(h)
            if h_key in seen_keys:
                repeats.append({**b, 'horses': [h], 'description': f"Single on {h.get('name', '')}"})
            else:
                seen_keys.add(h_key)
                all_horses.append(h)
    base_bet['horses'] = all_horses
    n_count = len(all_horses)
    sp = _single_stake_pence(base_bet)  # never None: singles without a stake are not grouped
    is_ew = bool(base_bet.get('each_way', False))
    ew_str = " (Each-Way)" if is_ew else ""
    stake_str = f"£{sp / 100:.2f}" if sp >= 100 else f"{sp}p"
    base_bet['description'] = f"{n_count} x {stake_str}{ew_str} Singles"
    base_bet['bet_type'] = 'single'
    base_bet['stake_pence'] = sp
    base_bet['unit_stake'] = float(sp / 100.0)
    base_bet['each_way'] = is_ew
    kept = f"; {len(repeats)} repeated selection(s) kept as separate single(s)" if repeats else ""
    print(f"[+] Multi-Single Consolidation: {how} {len(group)} {stake_str}{ew_str} singles into 1 bet with {n_count} "
          f"runner(s) for F8 multi-selection entry{kept}.")
    return [base_bet] + repeats


def consolidate_identical_stake_singles(bets_list: list[dict]) -> list[dict]:
    """
    Consolidates multiple single bets that share identical unit stakes and each-way terms.
    In Betty, entering N selections into the slip and choosing 'Singles' (shortcut 's') on
    the F8 bet selection screen with unit stake X automatically places N single bets of stake X.
    This combines multiple single entries into a single F8 entry pass: every single on an all-singles slip, else
    consecutive singles between the other bets.
    """
    if not bets_list or len(bets_list) < 2:
        return bets_list

    def is_single(b: dict) -> bool:
        return normalize_bet_type(str(b.get('bet_type', '')), str(b.get('description', '')), selection_names(b)) == 'single'

    if all(is_single(b) for b in bets_list):
        grouped: dict[tuple, list[dict]] = {}
        for b in bets_list:
            sp = _single_stake_pence(b)
            key = (sp, bool(b.get('each_way', False))) if sp is not None else (None, id(b))  # no stake: never merged
            grouped.setdefault(key, []).append(b)
        return [m for group in grouped.values() for m in _merge_singles(group, "Grouped")]

    merged: list[dict] = []
    current_group: list[dict] = []
    for bet in bets_list:
        if not is_single(bet):
            merged.extend(_merge_singles(current_group, "Merged") if current_group else [])
            current_group = []
            merged.append(bet)
            continue
        if current_group:
            prev = current_group[-1]
            sp_curr = _single_stake_pence(bet)
            if not (sp_curr is not None and sp_curr == _single_stake_pence(prev)
                    and bool(bet.get('each_way', False)) == bool(prev.get('each_way', False))):
                merged.extend(_merge_singles(current_group, "Merged"))
                current_group = []
        current_group.append(bet)
    merged.extend(_merge_singles(current_group, "Merged") if current_group else [])
    return merged


# --- F8 SCREEN BET LIST OCR SCANNER & SELECTION ENGINE ---


def ocr_f8_row_text(row_index: int, list_img: Any = None) -> str:
    """
    OCRs the text of a single row in Betty's F8 bet list.
    Extracts text to verify the row label (e.g. 'Lucky 31', 'Singles', 'Doubles').
    """
    if row_index < 0 or row_index >= F8_NUM_ROWS:
        return ""
    # The 1366x768 layout, as _f8_rows crops it: the program runs at no other size, and taking the row height from
    # the live display read a saved 1366 screen at 1024 rows whenever this PC's display was smaller (23 Oct)
    list_region, row_h = F8_BET_LIST_REGION_1368, F8_ROW_HEIGHT_1368
    if list_img is None:
        try:
            list_img = pyautogui.screenshot(region=list_region)
        except Exception:
            return ""
    if list_img is None:
        return ""
    k_top = int(row_index * row_h)
    k_bot = int((row_index + 1) * row_h)
    row_crop = list_img.crop((0, k_top, list_region[2], k_bot))
    txt = pytesseract.image_to_string(row_crop, config='--psm 7').strip()
    if not txt:
        txt = pytesseract.image_to_string(row_crop, config='--psm 6').strip()
    return re.sub(r'[\n\r]+', ' ', txt).strip()


def is_virtual_selection(horse: dict) -> tuple[bool, str | None, str | None]:
    """
    Checks whether a selection represents a virtual racing event.
    Inspects meeting, raw_meeting_hint, time, raw_time, written_time, and name
    for virtual indicators: '(v)', 'v', 'virt', 'virtual', or registered virtual tracks.
    Returns: (is_virtual, canonical_name, virtual_type)
    """
    meeting = str(horse.get('meeting', '')).strip()
    raw_hint = str(horse.get('raw_meeting_hint', '')).strip()

    # 1. Direct meeting / hint lookup (test both raw_hint and meeting)
    for tok in [raw_hint, meeting]:
        if tok:
            is_v, can_name, v_type = meetings_manager.is_virtual_meeting(tok)
            if is_v:
                return True, can_name, v_type

    # 2. Check time fields for (v) indicator (e.g. '5.07(v)', '5.07 v', '17:07 (v)')
    for t_field in ['time', 'raw_time', 'written_time']:
        val = str(horse.get(t_field, '')).strip()
        if re.search(r'\([vV]\)|\b[vV]\b|\bvirt\b|\bvirtual\b', val):
            cleaned_val = re.sub(r'\s*\([vV]\)|\s*\b[vV]\b|\s*\bvirt\b|\s*\bvirtual\b', '', val).strip()
            if cleaned_val:
                horse[t_field] = cleaned_val
            return True, "Virtual", "virtual_generic"

    # 3. Check horse name for (v) indicator (e.g. 'Drop Zone (v)')
    h_name = str(horse.get('name', '')).strip()
    if re.search(r'\([vV]\)|\bvirt\b|\bvirtual\b', h_name):
        cleaned_name = re.sub(r'\s*\([vV]\)|\s*\bvirt\b|\s*\bvirtual\b', '', h_name).strip()
        if cleaned_name:
            horse['name'] = cleaned_name
        return True, "Virtual", "virtual_generic"

    return False, None, None


def is_international_selection(horse: dict) -> tuple[bool, str | None]:
    """Checks whether a selection represents an international horse racing meeting."""
    meeting = str(horse.get('meeting', '')).strip().lower()
    raw_hint = str(horse.get('raw_meeting_hint', '')).strip().lower()
    
    # Priority: If resolved to a domestic UK/Irish horse or greyhound course, it is NOT international!
    cat, c_name = meetings_manager.resolve_meeting(raw_hint or meeting)
    if cat in ("horse", "greyhound", "virtual"):
        return False, None
    if cat == "international" and c_name:
        return True, c_name

    clean_meet = re.sub(r'[^a-z0-9]', '', meeting)
    clean_hint = re.sub(r'[^a-z0-9]', '', raw_hint)
    intl = meetings_manager.get_international_meetings()
    if clean_meet in intl:
        return True, intl[clean_meet]
    if clean_hint in intl:
        return True, intl[clean_hint]
    return False, None


def is_bog_eligible_selection(horse: dict) -> tuple[bool, str]:
    """
    Checks whether a selection qualifies for Best Odds Guaranteed (BOG).
    Under retail betting shop rules, BOG ONLY applies to UK and Irish horse racing.
    Non-UK/Irish horse racing (international/US/French/etc.), greyhound racing,
    and virtual racing are strictly ineligible for guaranteed odds.
    """
    meeting = str(horse.get('meeting', '')).strip()
    raw_hint = str(horse.get('raw_meeting_hint', '')).strip()

    # 0. Runner verified on Betty's card: the feed's country code decides (UK/IE = domestic)
    card_category = horse.get('category')
    if card_category == 'domestic':
        return True, "Eligible UK/Irish horse racing (Betty racecard)."
    if card_category in ('international', 'virtual', 'greyhound'):
        return False, f"{card_category.title()} racing ({meeting}) is ineligible for BOG (Betty racecard)."

    # 1. Virtual check
    is_v, _, _ = is_virtual_selection(horse)
    if is_v:
        return False, "Virtual racing is ineligible for BOG."

    # 2. Greyhound check
    is_dog, _, _ = is_greyhound_or_trap_selection(horse)
    if is_dog:
        return False, "Greyhound racing is ineligible for BOG."

    # 3. International check
    is_intl, intl_name = is_international_selection(horse)
    if is_intl:
        return False, f"Non-UK/Irish racing ({intl_name or meeting}) is ineligible for BOG."

    cat, c_name = meetings_manager.resolve_meeting(raw_hint or meeting)
    if cat in ("international", "greyhound", "virtual"):
        return False, f"Non-UK/Irish / {cat} event ({c_name or meeting}) is ineligible for BOG."

    if cat == "horse":
        return True, "Eligible UK/Irish horse racing."

    # If unknown meeting, check if meeting matches any UK/Irish course alias or directory
    clean_m = re.sub(r'[^a-z0-9]', '', (raw_hint or meeting).lower())
    if clean_m in meetings_manager.course_alias_map:
        return True, "Eligible UK/Irish horse racing."

    # If meeting is specified but unknown, and doesn't match domestic courses:
    if clean_m and len(clean_m) >= 3:
        return False, f"Non-UK/Irish or unverified meeting '{meeting}' is ineligible for BOG."

    return True, "Default domestic horse racing."


def gemini_call(payload: dict, key: str, model: str, timeout: float, label: str) -> tuple[str, dict | None]:
    """
    One Gemini request, straight to Google with a key from .env, or through the relay when `key` is a relay slot
    ('relay:paid'). Returns (status, parsed JSON): status is 'ok', 'no_credit' (402), 'quota' (429, or the till's
    daily limit on the relay), 'refused' (the relay won't take this till's pass, or has no key in that slot), 'busy'
    (5xx, timeout, connection), 'unavailable' (other HTTP errors), 'blocked', 'bad_json' or 'aborted'.
    """
    if key.startswith(relay_link.RELAY_KEY_PREFIX):  # through the relay: this till's pass, the relay's key
        route = relay_link.relay_route()
        if not route:
            print(f"[-] {label}: this till isn't paired with the relay any more (pair it in the launcher).")
            return 'refused', None
        url = f"{route[0]}/gemini/{key[len(relay_link.RELAY_KEY_PREFIX):]}/v1beta/models/{model}:generateContent"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {route[1]}"}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    t0 = time.time()
    # The request runs on a daemon thread that is simply left behind on Esc. Inside `with ThreadPoolExecutor`, leaving
    # the block waited for the request to finish (up to `timeout`), so Esc didn't free the program until Google answered.
    outcome: dict = {}

    def _post():
        try:
            outcome['response'] = SESSION.post(url, headers=headers, json=payload, timeout=timeout)
        except Exception as e:  # raised again below, in the caller's thread
            outcome['error'] = e

    worker = threading.Thread(target=_post, name=f"gemini {label}", daemon=True)
    worker.start()
    while worker.is_alive():
        if abort_event.is_set():
            print(f"\n[!] {label}: request to {model} cancelled (abort).")
            return 'aborted', None
        worker.join(0.05)
    error = outcome.get('error')
    if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        print(f"[-] {label}: {model} timeout / connection error after {time.time() - t0:.0f}s: {error}")
        return 'busy', None
    if error is not None:
        raise error
    response = outcome['response']
    elapsed = time.time() - t0
    code = response.status_code
    if code != 200:
        try:
            msg = response.json().get('error', {}).get('message', '')
        except Exception:
            msg = ''
        # Refused by the relay itself, not by Gemini (direct reads never look)
        relay = key.startswith(relay_link.RELAY_KEY_PREFIX) and bool(response.headers.get('x-relay-error'))
        print(f"[-] {label}: {model} HTTP {code} in {elapsed:.1f}s {'(relay) ' if relay else ''}{msg[:120]}")
        if relay and code in (401, 404):  # till not paired / pass revoked, or no key in that slot on the relay
            return 'refused', None
        if relay and code == 403 and 'daily limit' in msg:
            return 'quota', None
        if code == 402:
            return 'no_credit', None
        if code == 429:
            return 'quota', None
        return ('busy' if code >= 500 else 'unavailable'), None
    try:
        data = response.json()
        block = data.get('promptFeedback', {}).get('blockReason')
        cand = (data.get('candidates') or [{}])[0]
        if block or cand.get('finishReason') in ('SAFETY', 'RECITATION', 'OTHER', 'BLOCKLIST', 'PROHIBITED_CONTENT'):
            print(f"[-] {label}: {model} blocked the request ({block or cand.get('finishReason')}).")
            return 'blocked', None
        text = cand['content']['parts'][0]['text'].strip()
        parsed = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', text))
    except Exception as e:
        print(f"[-] {label}: {model} returned no usable JSON ({e}).")
        return 'bad_json', None
    usage = data.get('usageMetadata', {})
    print(f"[+] {label}: {model} OK in {elapsed:.1f}s | Tokens: {usage.get('promptTokenCount', '?')} in / "
          f"{usage.get('candidatesTokenCount', '?')} out / {usage.get('thoughtsTokenCount', 0)} thinking / "
          f"{usage.get('cachedContentTokenCount', 0)} cached")  # cached: the part of 'in' Google bills at its cache discount
    return 'ok', parsed


_gemini_quota_until: dict[tuple[str, str], float] = {}  # (key, model) -> time its 429 quota block is assumed over
GEMINI_QUOTA_PAUSE_SECS = 600


def gemini_tier_request(payload: dict, keys: list[str], models: list[str], timeout: float, label: str) -> dict | None:
    """
    Try each key, each model in order. No credit (402) or refused by the relay -> next key; quota (429), blocked,
    bad JSON or unavailable -> next model; busy / timeout -> one retry of the same model, then the next. None when
    nothing answered.
    """
    for key_no, key in enumerate(keys, 1):
        for model in models:
            if _gemini_quota_until.get((key, model), 0) > time.time():
                continue
            for attempt in (1, 2):
                if abort_event.is_set():
                    return None
                status, data = gemini_call(payload, key, model, timeout, label)
                if status == 'ok':
                    return data
                if status == 'busy' and attempt == 1:
                    print(f"[*] {label}: {model} busy, retrying once...")
                    if not interruptible_sleep(2.0):
                        return None
                    continue
                break
            if status == 'aborted':
                return None
            if status == 'quota':
                _gemini_quota_until[(key, model)] = time.time() + GEMINI_QUOTA_PAUSE_SECS
            if status == 'no_credit':
                print(f"[!] {label}: Gemini key {key_no} of this step has no credit (HTTP 402).")
                break
            if status == 'refused':
                break
    return None


RELAY_FREE_SLOTS = ["relay:free1", "relay:free2"]  # the relay's free Gemini projects (GEMINI_KEY_FREE_1/2 on it)


def reader_route() -> str:
    """Where slip reads go: 'relay' (this till is paired; the relay holds the keys), 'keys' (.env) or 'none'."""
    if SLIP_READER != "gemini" and relay_link.relay_route():
        return "relay"
    return "keys" if GEMINI_API_KEY or GEMINI_FREE_KEYS else "none"


def reader_tiers() -> list[dict]:
    """
    The vision readers in the order they are tried. Default (SLIP_READER unset / 'waterfall'):
      1. paid Gemini (GEMINI_API_KEY, GEMINI_PAID_MODELS: Argon)
      2. free Gemini projects (GEMINI_API_KEY_2.., GEMINI_FREE_MODELS)   then: staff.
    A till paired with the relay uses the relay's keys in the same order, and never the keys in .env.
    SLIP_READER=gemini pins the given Gemini keys and models (paid evaluation runs never fall through to another key).
    """
    if SLIP_READER == "gemini":
        gemini_eval_keys = _env_list("GEMINI_API_KEYS") or _key_list("GEMINI_API_KEY", *[f"GEMINI_API_KEY_{i}" for i in range(2, 12)])
        return [{'label': 'Gemini', 'keys': gemini_eval_keys, 'models': VLM_WATERFALL_MODELS}] if gemini_eval_keys else []
    tiers: list[dict[str, Any]] = []
    if reader_route() == "relay":
        if GEMINI_PAID_MODELS:
            tiers.append({'label': f"{GEMINI_PAID_MODELS[0]} (paid, relay)", 'keys': ["relay:paid"], 'models': GEMINI_PAID_MODELS})
        if GEMINI_FREE_MODELS:
            tiers.append({'label': "free Gemini (relay)", 'keys': RELAY_FREE_SLOTS, 'models': GEMINI_FREE_MODELS})
        return tiers
    if GEMINI_API_KEY and GEMINI_PAID_MODELS:
        tiers.append({'label': f"{GEMINI_PAID_MODELS[0]} (paid)", 'keys': [GEMINI_API_KEY], 'models': GEMINI_PAID_MODELS})
    if GEMINI_FREE_KEYS and GEMINI_FREE_MODELS:
        tiers.append({'label': "free Gemini", 'keys': GEMINI_FREE_KEYS, 'models': GEMINI_FREE_MODELS})
    return tiers


_slip_reader_tier = 0  # the step that read the current slip; its re-checks start there


def read_vision_json(gemini_payload: dict, label: str, timeout: float,
                     start_tier: int = 0, remember_tier: bool = False) -> dict | None:
    """Ask each reader in the chain, from `start_tier`, until one returns JSON. None: no reader answered (staff)."""
    global _slip_reader_tier
    tiers = reader_tiers()
    for idx in range(min(start_tier, max(len(tiers) - 1, 0)), len(tiers)):
        if abort_event.is_set():
            return None
        tier = tiers[idx]
        STATUS_HUD.update(f"{label}: reading with {tier['label']} (step {idx + 1} of {len(tiers)})...")
        print(f"[*] {label}: step {idx + 1}/{len(tiers)} {tier['label']}")
        data = gemini_tier_request(gemini_payload, tier['keys'], tier['models'], timeout, label)
        if data is not None:
            print(f"[+] {label}: answered by step {idx + 1} ({tier['label']}).")
            if remember_tier:
                _slip_reader_tier = idx
            return data
        print(f"[!] {label}: {tier['label']} gave no answer; next reader.")
    print(f"[-] {label}: no reader answered ({len(tiers)} tried).")
    return None


def pre_process_slip_image(raw_img):
    """
    Pre-processes slip image with high stroke clarity for OCR / VLM.
    Maintains full pixel detail without downsampling native slip crops (365x505),
    applying balanced contrast and sharpness enhancement so fine pencil and biro strokes
    remain crisp and continuous without blocky saturation.
    """
    gray = raw_img.convert("L")
    w, h = gray.size
    max_dim = 1024
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = gray.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        scaled = gray

    # Balanced contrast enhancement so digit loops and handwriting strokes pop cleanly
    enhanced = ImageEnhance.Contrast(scaled).enhance(1.25)
    sharp = ImageEnhance.Sharpness(enhanced).enhance(1.20)
    return sharp


REFIT_MAX_COMBINATIONS = 729  # 3 readings on each of 6 bets: more and the money check sends the slip to staff


def bet_type_readings(bet: dict) -> list[str]:
    """The bet types one bet line can be read as: as reconciled, as the reader typed it, as its words name it (the
    fold its multiplier implies is already the reconciled one). Each is the type as costed and entered, words and all
    (normalize_bet_type over the description), so a type the customer wrote leaves one reading. Reconciled first."""
    text = f"{bet.get('description', '')} {bet.get('raw_text', '')}"
    names = selection_names(bet)
    out: list[str] = []
    for t in (bet.get('bet_type'), bet.get('_read_type'), written_bet_type(text, names)):
        norm = normalize_bet_type(str(t or ''), str(bet.get('description', '')), names) if t else ''
        if norm and norm not in out:
            out.append(norm)
    return out


def refit_bet_types_to_money(bets_list: list[dict], target_pence: int) -> bool:
    """
    When the bets don't cost the money: every combination of each bet's readings (bet_type_readings) is costed, and
    the bets are changed only when exactly ONE combination costs exactly `target_pence` (two that fit is a guess, and
    the money check then sends it to staff). True when the bets were changed.
    """
    options = [bet_type_readings(b) for b in bets_list]
    if not bets_list or all(len(o) <= 1 for o in options) or math.prod(len(o) for o in options) > REFIT_MAX_COMBINATIONS:
        return False
    costs = []
    for bet, types in zip(bets_list, options):
        by_type = {}
        for t in types:
            trial = dict(bet, bet_type=t)
            by_type[t] = calculate_bet_cost_pence(trial)
        costs.append(by_type)
    fits = [combo for combo in itertools.product(*options)
            if sum(c[t] for c, t in zip(costs, combo)) == target_pence]
    if len(fits) != 1:
        if len(fits) > 1:
            print(f"[-] Bet type readings: {len(fits)} different readings cost £{target_pence / 100:.2f}; none chosen.")
        return False
    for i, (bet, t) in enumerate(zip(bets_list, fits[0])):
        if normalize_bet_type(str(bet.get('bet_type', ''))) != t:
            print(f"[+] Bet type readings: Bet #{i + 1} '{bet.get('description')}' read as {t} "
                  f"(not {bet.get('bet_type')}): the only reading that costs £{target_pence / 100:.2f}.")
            bet['bet_type'] = t
        bet['cost_pence'] = calculate_bet_cost_pence(bet)
    return True


def process_slip_reading(bets_data: dict, img_str: str, payment_pence: int | None = None):
    """
    Shared post-processing for the vision model's slip reading: line backfill, phantom
    selections, hydration, scoping, singles consolidation, costing and the total healers. The healers fit the bets to
    the customer's written total, or to `payment_pence` (View Wagers' Payment) when no written total could be read.
    Returns (bets_list, raw_selections, img_str, written_total_pence, calc_total_pence).
    """
    # Display Chain-of-Thought raw line transcription in console
    lines_list = bets_data.get('line_transcription', [])
    if lines_list:
        print("\n--- Visual Slip Lines Transcribed ---")
        for lt in lines_list:
            print(f"  Line {lt.get('line_num')}: {lt.get('raw_text')}")

    raw_selections = bets_data.get('selections', [])
    lines_list = bets_data.get('line_transcription', [])
    # A line the reader marked struck carries the marker the bet restorer and total reader already skip
    for lt in lines_list:
        if lt.get('struck') and not re.search(r'cross(?:ed)?\s*out|struck', str(lt.get('raw_text', '')), re.I):
            lt['raw_text'] = f"[CROSSED OUT] {lt.get('raw_text', '')}"

    # A line saying dogs ("DOG'S", "dogs") that isn't a selection: the slip's numbers are traps where a meeting races
    # horses and dogs both (number_bet_is_dog; 9.2458296, 30 Oct)
    says_dogs = any(lt.get('kind') != 'selection' and not lt.get('struck')
                    and re.search(r"\bdog'?s?\b", str(lt.get('raw_text', '')), re.I) for lt in lines_list)
    # Readers sometimes fill 'UNKNOWN' / null into meeting fields; treat those as nothing written
    for s in raw_selections:
        if says_dogs:
            s['_slip_says_dogs'] = True
        for key in ('meeting', 'raw_meeting_hint'):
            if key in s:
                s[key] = _real_meeting(s[key], as_written=key == 'raw_meeting_hint')
        # A number has only its race to identify it: a time the reader marked unclear counts as not written, so an
        # unnamed runner with no readable time goes to staff, never to a guessed race (paul2, 26 Oct: a cut-off time
        # read as '3.17', a real Musselburgh race, locked No 8 there)
        if 'time' in (s.get('unclear') or []) and selection_number(s) is not None and s.get('raw_time'):
            print(f"[!] Selection #{s.get('selection_num')} '{s.get('name')}': the reader could not read its time "
                  f"('{s['raw_time']}'), so it counts as not written.")
            s['raw_time'] = s['time'] = ''
            s['time_unreadable'] = True
        # The reader copies the time as written; the 24-hour time is the program's ('6.30' -> 18:30), as pre-flight reads it
        if not s.get('time'):
            s['time'] = parse_race_time_to_minutes(str(s.get('raw_time') or ''))[1] or ''

    # Backfill missing line numbers on selections if omitted by VLM
    for s_idx, s in enumerate(raw_selections):
        if s.get('line_num') is None:
            s_name = str(s.get('name', '')).lower()
            s_time = str(s.get('time', '')).replace(':', '')
            for lt in lines_list:
                lt_text = str(lt.get('raw_text', '')).lower()
                if (s_name and len(s_name) > 3 and s_name in lt_text) or (s_time and s_time in lt_text.replace(':', '').replace('.', '')):
                    s['line_num'] = lt.get('line_num')
                    break
            if s.get('line_num') is None:
                s['line_num'] = (s_idx + 1) * 2
                s['_line_guessed'] = True  # not read: the causality guard ignores the order (review R17)

    bets_list = bets_data.get('bets', [])
    # Backfill missing line numbers on bets if omitted by VLM
    for b_idx, b in enumerate(bets_list):
        if b.get('line_num') is None:
            b_desc = str(b.get('description', '')).lower()
            for lt in lines_list:
                lt_text = str(lt.get('raw_text', '')).lower()
                if b_desc and (b_desc in lt_text or lt_text in b_desc):
                    b['line_num'] = lt.get('line_num')
                    break

    # Phantom selections: a "selection" placed on a bet-instruction line whose name does not appear
    # anywhere in that line's text was invented by the VLM (e.g. a 'LAST 2' scrawl read as a time).
    line_texts = {lt.get('line_num'): str(lt.get('raw_text', '')).lower() for lt in lines_list}
    line_kinds = {lt.get('line_num'): str(lt.get('kind') or '').lower() for lt in lines_list}
    bet_line_nums = {b.get('line_num') for b in bets_list if b.get('line_num') is not None}
    kept_selections = []
    for s in raw_selections:
        s_line = line_texts.get(s.get('line_num'), '')
        name_words = [w for w in clean_horse_name(s.get('name', '')).split() if len(w) >= 3]
        kind = line_kinds.get(s.get('line_num'))
        is_bet_line = (kind in ('bet', 'total') if kind else
                       s.get('line_num') in bet_line_nums and
                       re.search(r'\b(?:doub\w*|treb\w*|acc\w*|single|win|ew|f/?cast|forecast)\b', s_line))
        if is_bet_line and name_words and not any(w in s_line for w in name_words):
            print(f"[*] Dropped phantom selection #{s.get('selection_num')} '{s.get('name')}': line {s.get('line_num')} "
                  f"('{s_line}') is a bet instruction that does not contain this name.")
            continue
        kept_selections.append(s)
    raw_selections = kept_selections

    if raw_selections:
        print("\n--- Visual Slip Selections Extracted ---")
        for s in raw_selections:
            m_str = f" ({s.get('meeting') or s.get('raw_meeting_hint')})" if s.get('meeting') or s.get('raw_meeting_hint') else ""
            num_str = f" #{s.get('number')}" if s.get('number') else ""
            unclear_str = f" | unclear: {', '.join(s['unclear'])}" if s.get('unclear') else ""
            print(f"  Selection #{s.get('selection_num')} (Line {s.get('line_num')}): Price: {s.get('price')} | Selection: {s.get('name')}{num_str} | "
                  f"Time/Meeting: {s.get('raw_time') or s.get('time')}{m_str}{unclear_str}")

    # Hydrate bets.horses with full selection details (meeting, time, price, number, raw_time)
    # from raw_selections so Gemini does not waste 1000+ tokens re-generating duplicate runner objects.
    sel_by_num = {s.get('selection_num'): s for s in raw_selections if s.get('selection_num')}
    sel_by_name = {clean_horse_name(s.get('name', '')): s for s in raw_selections if s.get('name')}

    for bet in bets_list:
        hydrated = []
        for h in bet.get('horses', []):
            # A numbered reference resolves only by number (a dropped phantom must not fall back to a
            # same-named runner elsewhere on the slip); names are used only for unnumbered references.
            if h.get('selection_num') is not None:
                s_match = sel_by_num.get(h.get('selection_num'))
            else:
                s_match = sel_by_name.get(clean_horse_name(h.get('name', '')))
            if s_match:
                full_h = dict(s_match)
                if h.get('price') and str(h.get('price')).lower() not in ['sp', 'none', '']:
                    full_h['price'] = h['price']
                hydrated.append(full_h)
            elif h.get('selection_num') is None and str(h.get('name', '')).strip():
                hydrated.append(h)
            else:
                print(f"[*] Dropped reference to non-existent selection #{h.get('selection_num')} in bet '{bet.get('description')}'.")
        bet['horses'] = hydrated

    written_display = bets_data.get('written_total_raw')
    written_total_pence = bets_data.get('written_total_pence')

    # Reconcile written total with robust currency parser (handling UK '60 -' = £60.00 = 6000p)
    line_transcription = bets_data.get('line_transcription', [])
    verified_written_pence, verified_display = extract_written_total_pence(
        line_transcription, written_total_pence, written_display
    )
    if verified_written_pence is not None:
        written_total_pence = verified_written_pence
        written_display = verified_display or written_display

    for bet in bets_list:  # the reader's own type, before the reconcilers: one of the readings the money may pick
        bet['_read_type'] = bet.get('bet_type')

    # Positional Scoping Reconciler (enforces 'LAST 2', 'LAST 3', 'ABOVE N' qualifiers)
    bets_list = reconcile_bet_scoping_qualifiers(bets_list, raw_selections, line_transcription)

    # Multi-Single Consolidation: When multiple singles share the same unit stake & EW terms,
    # merge them into a single bet entry so Betty enters all selections at once and places 'Singles' via F8
    bets_list = consolidate_identical_stake_singles(bets_list)

    # Reconcile & compute total bet cost
    for bet in bets_list:
        calc_single_cost = calculate_bet_cost_pence(bet)
        bet['cost_pence'] = calc_single_cost

    calc_total_pence = sum(int(b.get('cost_pence') or 0) for b in bets_list)

    # Total Stake Reconciliation Healer: fits the bets to the customer's written total, or to Payment when no total
    # could be read from the slip
    target_pence, target_label = ((written_total_pence, "written") if written_total_pence is not None
                                  else (payment_pence, "paid"))
    # 1. Pounds vs. Pence Scaling Healer: If calc_total_pence * 100 == target_pence
    # (e.g. bet was transcribed as 60p win, but customer wrote '60 -' = £60.00 = 6000p)
    if target_pence is not None and calc_total_pence > 0 and (calc_total_pence * 100 == target_pence):
        print(f"[+] Total Stake Reconciliation Healer: Detected whole-pound stake mismatch (calc={calc_total_pence}p vs {target_label}={target_pence}p). Scaling bet stakes by 100x to whole pounds...")
        for bet in bets_list:
            if 'stake_pence' in bet and bet['stake_pence'] is not None:
                bet['stake_pence'] = int(bet['stake_pence'] * 100)
            if 'unit_stake' in bet and bet['unit_stake'] is not None:
                bet['unit_stake'] = float(bet['unit_stake'] * 100)
            if 'total_stake' in bet and bet['total_stake'] is not None:
                bet['total_stake'] = float(bet['total_stake'] * 100)
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        calc_total_pence = sum(int(b.get('cost_pence') or 0) for b in bets_list)
        print(f"[+] Reconciled bet stakes! New calculated total: {calc_total_pence}p (£{calc_total_pence/100:.2f}), matching {target_label} total {target_pence}p (£{target_pence/100:.2f}) exactly.")

    # 2. EW Auto-Correction Healer: Auto-correct misplaced EW markers
    # GUARD: Never flip a bet whose line_transcription explicitly says 'WIN' (not EW/each-way).
    # Flipping a WIN bet to EW is always wrong even if it makes totals match numerically.
    elif target_pence is not None and calc_total_pence != target_pence:
        lines_text_map = {lt.get('line_num'): str(lt.get('raw_text', '')).lower() for lt in line_transcription}
        flips = []  # bets whose each-way flip alone makes the total match
        for h_idx, bet in enumerate(bets_list):
            b_line = bet.get('line_num')
            b_line_text = lines_text_map.get(b_line, '')
            orig_ew = bool(bet.get('each_way', False))
            # If the line or description explicitly says 'win' (and NOT 'ew'/'each'), skip this bet
            line_is_explicit_win = bool(
                re.search(r'\bwin\b', b_line_text) and
                not re.search(r'\b(?:ew|e/w|each)\b', b_line_text)
            )
            desc_is_explicit_win = bool(
                re.search(r'\bwin\b', str(bet.get('description', '')).lower()) and
                not re.search(r'\b(?:ew|e/w|each)\b', str(bet.get('description', '')).lower())
            )
            line_is_explicit_ew = bool(re.search(r'\b(?:ew|e/w|each\s*way)\b', b_line_text))
            if line_is_explicit_win or desc_is_explicit_win or (orig_ew and line_is_explicit_ew):
                continue  # Never flip a bet whose written line explicitly says WIN or EW
            # Forecasts and tricasts have no each way: Betty ignores it, so the flip only hides the gap until the total
            # check after entry (9.2458262, 30 Oct: a £1 straight forecast "each way" to make £4 into £5)
            if not orig_ew and re.search(r'forecast|f/?cast|tricast', normalize_bet_type(str(bet.get('bet_type', '')))):
                continue
            bet['each_way'] = not orig_ew
            if calc_total_pence - int(bet.get('cost_pence') or 0) + calculate_bet_cost_pence(bet) == target_pence:
                flips.append(h_idx)
            bet['each_way'] = orig_ew
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        # Only an unambiguous flip: with two bets of the same cost, either flip fits the money, and the wrong one would
        # be placed each way with nothing left to catch it (review R1). Then the money check sends it to staff.
        if len(flips) == 1:
            bet = bets_list[flips[0]]
            bet['each_way'] = not bet.get('each_way', False)
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
            calc_total_pence = sum(int(b.get('cost_pence') or 0) for b in bets_list)
            ew_str = "Each-Way" if bet['each_way'] else "Win Only"
            print(f"[+] Total Stake Reconciliation Healer: Auto-corrected Bet #{flips[0] + 1} to {ew_str}! Calculated total now {calc_total_pence}p (£{calc_total_pence/100:.2f}), matching {target_label} total {target_pence}p (£{target_pence/100:.2f}) exactly.")
        elif flips:
            print(f"[-] Total Stake Reconciliation Healer: bets {', '.join(f'#{i + 1}' for i in flips)} could each be the "
                  f"misread each way; none changed.")

    # 3. Bet type readings: the money picks between the ways each bet line can be read, before any rescan (a rescan
    # reads the same words again; it can't fix how they were understood)
    if target_pence is not None and calc_total_pence != target_pence and refit_bet_types_to_money(bets_list, target_pence):
        calc_total_pence = sum(int(b.get('cost_pence') or 0) for b in bets_list)


    if written_total_pence is not None:
        print(f"[+] Customer Written Total Stake: {written_display} -> {written_total_pence}p (£{written_total_pence/100:.2f})")
    else:
        print("[*] No customer written total detected at the bottom of the slip.")
    print(f"[+] Total Calculated Bet Cost: {calc_total_pence}p (£{calc_total_pence/100:.2f}) across {len(bets_list)} bet(s).")

    return bets_list, raw_selections, img_str, written_total_pence, calc_total_pence


# The reader's fixed instructions. They open every slip scan unchanged, so Google can bill them at its cache discount
# (today's card and any rescan note follow them).
SLIP_READER_RULES = """You are reading a customer's handwritten betting slip from a UK betting shop. Copy what is written: the shop's
software works out costs, runners and house rules afterwards. A wrong guess is worse than a gap: if you cannot read
something, leave it empty and name it in "unclear". Today's card is given after these rules: use it only to choose
between readings the handwriting allows, never to change what is written.

HOW A SLIP IS LAID OUT
- Lines run top to bottom. A selection line names a runner; a bet line says how to bet; the last line is often the
  total stake.
- A selection line usually has a price in the left margin (15/2, 25-1, E or Evs = evens, SP), a horse name or a
  number, a race time, and sometimes a meeting, in full or as 1-2 letters after the time (4.28N).
- A bet line covers selections written ABOVE it, never below, and the most recent ones first. How many is set by the
  bet: a double takes the 2 just above, a treble the 3 just above, "N x doubles" the runners that make N doubles
  (3 x = 3 runners, 6 x = 4, 10 x = 5), "last N" / "above N" / "abv N" / "all N" the N just above, an accumulator
  with no number every selection above it. Several bet lines in a row can cover the same selections. A dividing line
  starts a new section. Only a bet line written before any selection covers the selections below it.
- A stake with no bet type ("£2 win", "50p ew") is a single on the selection on the same line, or just above it.
- A bet line can carry its own runners: "£1 SF/C 5.55 4-3" is a straight forecast on numbers 4 then 3 in the
  5.55. List such runners as selections on that line too.
- A multiplier ("3 x", "1x") belongs to the bet words on the same row.
- A line is struck out only by a deliberate scribble or line through it, not by the stroke of a letter.

SHOP SHORTHAND
- "No 6", "No.6", "#6" = saddle-cloth number 6 (never a meeting). "T3", "Tr 3", "Trap 3" = greyhound trap 3. A bare
  number with no T or Trap is a cloth number.
- "do", " or ditto = same as the line above. "fav" = the favourite.
- Stakes: "50" or "50p" = 50 pence; "£1", "1-" or "1.00" = one pound; a hasty £ can look like a Q, E, Z or 2.
- "ew", "e/w", "each way" = each-way; "w", "win" = win only.
- "doub"/"dbl" = double, "treb" = treble, "acc"/"acca" = accumulator, "x doubles" = cross doubles (every double
  between runners in different races), "s/f/cast", "sfc", "sf/c" = straight forecast, "r/f/cast", "rfc" = reversed
  forecast, "cfc" = combination forecast, "f/c doubles" = forecast double. Full covers: trixie, patent, yankee,
  canadian, heinz, super heinz, goliath, lucky 15 / 31 / 63. A printed coupon heading names the bet type.

WHAT TO RETURN
1. line_transcription: every line in order. raw_text exactly as written, keeping the customer's spelling. kind is
   selection, bet, total or other. struck is true only for a deliberately crossed-out line.
2. selections: one per runner written, in slip order, struck lines left out; a runner written twice is two
   selections. name is the letters as written, even when they are not a real word ("No 4" for a number).
   raw_time and raw_meeting_hint exactly as written ("4.28", "N"); empty when not written. number only when a number
   is written. price as written, empty when none. meeting only when a meeting is written in full, otherwise empty.
3. bets: one per bet line, struck lines left out. description is the line's words exactly. horses are the
   selection_nums it covers, in written order. bet_type is one of: single, double, treble, accumulator,
   straight forecast, reversed forecast, combination forecast, straight forecast double, reversed forecast double,
   tricast, combination tricast, trixie, patent, yankee, lucky 15, lucky 31, lucky 63, canadian, heinz,
   super heinz, goliath ("3 x doubles" and cross doubles are "double"). each_way true only for each-way.
   stake_pence is the stake per bet in pence as written (3 x 50p doubles = 50), never the total.
4. written_total_raw: the total line exactly as written, or empty when there is none. A bet line is never the total.
5. unclear (on a selection or bet): the fields you could not read with confidence (name, time, meeting, number,
   price, stake, bet). Leave the field empty rather than guess when it cannot be read at all."""
CARD_FROM_BEFORE_STRUCK_MINS = 30  # the reader's card starts this long before the bet was struck (a late bet stays on it)


def card_for_prompt(runners: list[dict], full: bool = False, from_mins: int | None = None) -> str:
    """
    Today's card in short form for the slip reader, with times as customers write them ('4.28'). UK & Irish horse and
    dog meetings get their race times; overseas meetings and the virtual tracks are named only, since most bets are
    UK & Irish and a digit costs a token. `full` (a rescan) gives every meeting but the virtual tracks its times.
    `from_mins` leaves out the races before it. No runner names: the race-list check sends one race's runners when a
    name does not match.
    """
    def timed(r: dict) -> bool:
        if r.get('category') == 'virtual':
            return False
        return full or r.get('category') == 'domestic' or (r.get('category') == 'greyhound'
                                                           and r.get('country') in DOMESTIC_COUNTRIES)
    races: dict[tuple[str, str], set[int]] = {}
    named: dict[str, set[str]] = {}
    for r in runners:
        if not r.get('meeting') or r.get('minutes') is None or (from_mins is not None and r['minutes'] < from_mins):
            continue
        category = r.get('category') or 'domestic'
        if timed(r):
            races.setdefault((category, r['meeting']), set()).add(r['minutes'])
        else:
            named.setdefault(category, set()).add(r['meeting'])
    shop = lambda mins: f"{(mins // 60) % 12 or 12}.{mins % 60:02d}"
    timed_titles = {'domestic': "UK & Irish horses", 'international': "International horses",
                    'greyhound': "Greyhounds" if full else "UK & Irish greyhounds"}
    named_titles = {'international': "International horses", 'greyhound': "Overseas greyhounds",
                    'virtual': "Virtual racing, a race every few minutes"}
    out = []
    for category in CATEGORY_ORDER:
        meetings = sorted((m, sorted(t)) for (c, m), t in races.items() if c == category)
        if meetings:
            out.append(f"{timed_titles[category]}:")
            out += [f"  {m}: {' '.join(shop(t) for t in times)}" for m, times in meetings]
    for category in CATEGORY_ORDER:
        if named.get(category):
            out.append(f"{named_titles.get(category, category)} (names only): {', '.join(sorted(named[category]))}")
    return "\n".join(out) or "(not available)"


def state_read_slip_via_api(api_key, retry_hint=None, payment_pence=None, struck_time=None):
    """STATE 1: Captures slip with in-memory enhancement, grounds handwriting against live racecards, and reconciles total stake.
    struck_time: when the bet was struck ('13:05'), if known. The card then starts CARD_FROM_BEFORE_STRUCK_MINS before
    it, rounded down to the hour, so the card stays the same (and cached) for a whole hour of scans."""
    print("[*] Taking screenshot of the slip...")
    slip_img = pyautogui.screenshot(region=SLIP_REGION)
    enhanced_img = pre_process_slip_image(slip_img)

    buffered = io.BytesIO()
    enhanced_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    struck_mins = parse_clock_minutes(struck_time)
    from_mins = None if struck_mins is None else max(0, struck_mins - CARD_FROM_BEFORE_STRUCK_MINS) // 60 * 60
    card_txt = card_for_prompt(racecard_manager.get_runners() + greyhound_card.get_runners(),
                               full=bool(retry_hint), from_mins=from_mins)
    retry_section = f"\nTHIS IS A RESCAN. {retry_hint}\n" if retry_hint else ""
    prompt_text = (f"{SLIP_READER_RULES}\n\nTODAY'S CARD (meeting: race times as customers write them, 12-hour):\n"
                   f"{card_txt}\n{retry_section}")

    line_item = {"type": "OBJECT",
                 "properties": {"line_num": {"type": "INTEGER"}, "raw_text": {"type": "STRING"},
                                "kind": {"type": "STRING", "enum": ["selection", "bet", "total", "other"]},
                                "struck": {"type": "BOOLEAN"}},
                 "required": ["line_num", "raw_text", "kind", "struck"],
                 "propertyOrdering": ["line_num", "raw_text", "kind", "struck"]}
    unclear = {"type": "ARRAY", "items": {"type": "STRING"}}
    selection_item = {"type": "OBJECT",
                      "properties": {"selection_num": {"type": "INTEGER"}, "line_num": {"type": "INTEGER"},
                                     "price": {"type": "STRING"}, "name": {"type": "STRING"},
                                     "number": {"type": "INTEGER"}, "raw_time": {"type": "STRING"},
                                     "raw_meeting_hint": {"type": "STRING"}, "meeting": {"type": "STRING"},
                                     "unclear": unclear},
                      "required": ["selection_num", "line_num", "price", "name", "raw_time", "raw_meeting_hint"],
                      "propertyOrdering": ["selection_num", "line_num", "price", "name", "number", "raw_time",
                                           "raw_meeting_hint", "meeting", "unclear"]}
    bet_item = {"type": "OBJECT",
                "properties": {"line_num": {"type": "INTEGER"}, "description": {"type": "STRING"},
                               "horses": {"type": "ARRAY", "items": {"type": "OBJECT",
                                                                     "properties": {"selection_num": {"type": "INTEGER"}},
                                                                     "required": ["selection_num"]}},
                               "bet_type": {"type": "STRING"}, "each_way": {"type": "BOOLEAN"},
                               "stake_pence": {"type": "INTEGER"}, "unclear": unclear},
                "required": ["line_num", "description", "horses", "bet_type", "each_way", "stake_pence"],
                "propertyOrdering": ["line_num", "description", "horses", "bet_type", "each_way", "stake_pence",
                                     "unclear"]}
    schema = {"type": "OBJECT",
              "properties": {"line_transcription": {"type": "ARRAY", "items": line_item},
                             "selections": {"type": "ARRAY", "items": selection_item},
                             "bets": {"type": "ARRAY", "items": bet_item},
                             "written_total_raw": {"type": "STRING"}},
              "required": ["line_transcription", "selections", "bets", "written_total_raw"],
              "propertyOrdering": ["line_transcription", "selections", "bets", "written_total_raw"]}

    instruction = "Now read the customer's slip in the image above and return the JSON."
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text},
                                                {"inline_data": {"mime_type": "image/png", "data": img_str}},
                                                {"text": instruction}]}],
        "generationConfig": {"response_mime_type": "application/json", "response_schema": schema}
    }
    bets_data = read_vision_json(payload, "Slip scan", timeout=SCAN_TIMEOUT_SECS, remember_tier=True)
    if bets_data is None:
        return None, None, None, None, None
    return process_slip_reading(bets_data, img_str, payment_pence)


def _ask_vision_json(prompt: str, img_str: str, api_key: str, schema: dict, label: str) -> dict | None:
    """One small vision request (slip image + question) through the reader chain, starting with the reader that read
    this slip; parsed JSON or None. (`api_key` is kept for the callers' signature; the chain holds the keys.)"""
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": img_str}}]}],
        "generationConfig": {"response_mime_type": "application/json", "response_schema": schema}
    }
    return read_vision_json(payload, label, timeout=RECHECK_TIMEOUT_SECS, start_tier=_slip_reader_tier)


RACE_LIST_MAX = 60  # most runners shown in one race-list check; whole races are added nearest the written time first


def race_list_for_selection(horse: dict, runners: list[dict]) -> list[dict]:
    """
    The runners a cashier scans for an unclear name: every runner in the race(s) within TIME_AGREE_MINS of the
    written time, narrowed to the written meeting letter when it fits a meeting racing then. UK/IRE races first
    (international / virtual only when no UK/IRE race is at that time). Ordered by race, then saddle cloth.
    """
    times = written_race_times(horse)
    if not times:
        return []
    hinted = _hinted_meeting(horse)
    near: list[dict] = []
    for category in CATEGORY_ORDER:
        near = [r for r in runners if r.get('category', 'domestic') == category and r.get('minutes') is not None
                and any(abs(r['minutes'] - m) <= TIME_AGREE_MINS for m in times)]
        if hinted:
            near = [r for r in near if _meeting_matches(r['meeting'], hinted)] or near
        if near:
            break
    races: dict[tuple[str, str], list[dict]] = {}
    for r in near:
        races.setdefault((r['meeting'], r['time_str']), []).append(r)
    by_gap = sorted(races.values(), key=lambda race: min(abs(race[0]['minutes'] - m) for m in times))
    chosen: list[dict] = []
    for race in by_gap:
        if chosen and len(chosen) + len(race) > RACE_LIST_MAX:
            break
        chosen.extend(sorted(race, key=lambda r: r.get('number') or 0))
    return sorted(chosen, key=lambda r: (r['minutes'], r['meeting'], r.get('number') or 0))


def reexamine_runner_with_ai(horse: dict, horse_idx: int, img_str: str, api_key: str, candidates: list[dict], runners: list[dict]) -> dict | None:
    """
    Race-list check for one selection the matcher could not confirm, done the way a cashier does it: the reader
    sees every runner in the race(s) at the written time (meeting letter respected) plus the matcher's best
    guesses, copies the letter shapes as written, then compares them with the real names. Price is never used.
    Accepted only with high confidence; a pick outside the races at the written time also needs a strong name
    fit, so a misread time cannot let a loosely similar name through.
    Returns the runner, or None (the caller then asks staff to confirm the selection).
    """
    if not img_str or not api_key:
        return None
    in_race = race_list_for_selection(horse, runners)
    elsewhere = [c for c in candidates if c not in in_race]
    options = in_race + elsewhere
    if not options:
        return None

    first_read = str(horse.get('name', '')).strip()
    written_time = str(horse.get('raw_time') or horse.get('time', '')).strip()
    hint = _hinted_meeting(horse)
    line_ref = f" on line {horse['line_num']}" if horse.get('line_num') else ""
    shown_time = written_time if (len(hint) > 2 or written_time.upper().endswith(hint.upper())) else written_time + hint
    time_ref = f"written with the race time '{shown_time}'" if written_time else "with no race time written"
    listing, last_race = [], None
    for i, r in enumerate(options, start=1):
        if i == len(in_race) + 1:
            listing.append("Other possible runners (similar names at other times on today's card):")
            last_race = None
        race = f"{r['meeting']} {r['time_str']}"
        if i <= len(in_race) and race != last_race:
            listing.append(f"{race}:")
            last_race = race
        listing.append(f"  {i}. {r['name']}" + (f" ({race})" if i > len(in_race) else ""))
    options_txt = "\n".join(listing)

    pick = _ask_vision_json(
        f"""You are an expert UK betting shop cashier identifying ONE selection on a handwritten slip.
Look at selection #{horse_idx}{line_ref}, {time_ref}. Its horse name could not be matched automatically.

These are the runners in the race(s) at that time on today's racecard:
{options_txt}

Work the way an experienced cashier does:
1. Copy the name exactly as the letters are shaped, even if that is not a real word. Do not turn the scrawl into an
   English word or a familiar name.
2. Compare those letter shapes with the runner names above: the first letter, letters that rise above or drop
   below the line, the length, and how the name ends. Names are often written as one run-together word.
3. Common handwriting confusions: 'op'/'w', 'ie'/'ke', 'i'/'r'/'e', 'a'/'o', 'n'/'h', 'rs'/'sh', 'lla'/'ck',
   and fast capitals F/G, R/L, M/N.
4. The odds written beside the name are the price taken, not the starting price. Never use them to choose a runner.
5. Never change what you read to make it fit a runner. If no runner fits the letter shapes, answer 0.
Answer "high" confidence only when the letter shapes clearly fit one runner and no other.
Return JSON: {{"letter_shapes": "...", "choice": <0-{len(options)}>, "confidence": "high" or "low"}}""",
        img_str, api_key,
        {"type": "OBJECT",
         "properties": {"letter_shapes": {"type": "STRING"}, "choice": {"type": "INTEGER"}, "confidence": {"type": "STRING"}},
         "required": ["letter_shapes", "choice", "confidence"],
         "propertyOrdering": ["letter_shapes", "choice", "confidence"]},
        f"Race-list check of '{first_read}' ({len(in_race)} in race, {len(elsewhere)} elsewhere)")
    if not pick:
        return None
    shapes = str(pick.get('letter_shapes', '')).strip()
    choice = int(pick.get('choice') or 0)
    confidence = str(pick.get('confidence', '')).lower()
    if not (1 <= choice <= len(options)) or confidence != "high":
        print(f"[!] Race-list check of '{first_read}': no confident pick (read '{shapes}', choice {choice}, {confidence}).")
        return None
    chosen = options[choice - 1]
    if choice <= len(in_race):
        print(f"[*] Race-list check: '{shapes}' -> '{chosen['name']}' ({chosen['meeting']} {chosen['time_str']}), in the race at the written time.")
        return chosen
    fit = max((name_similarity(clean_horse_name(n), clean_horse_name(chosen['name'])) for n in (shapes, first_read) if n), default=0.0)
    if fit >= NAME_ACCEPT_WITH_TIME:
        print(f"[*] Race-list check: '{shapes}' -> '{chosen['name']}' ({chosen['meeting']} {chosen['time_str']}), strong name fit {fit:.2f}.")
        return chosen
    print(f"[!] Race-list pick '{chosen['name']}' not accepted: it is not in a race at the written time and the name fit is only {fit:.2f}.")
    return None


def apply_manual_entry(horse: dict, entry: dict, runners: list[dict], struck_mins: float | None = None) -> str | None:
    """
    Staff's typed details for a selection the program could not read, put through the same card checks as a
    scanned selection (a name by the matcher, a number by the cloth-number lookup). On success the selection is
    updated in place and None is returned; otherwise the message to show staff.
    entry: {'name': name or number, 'time': race time as written, 'meeting': meeting, 'price': price taken ('' = SP)}
    """
    name = str(entry.get('name') or '').strip()
    time_txt = str(entry.get('time') or '').strip()
    meeting = str(entry.get('meeting') or '').strip()
    price = str(entry.get('price') or '').strip()
    if not name:
        return "Enter the horse name, or its number."
    typed = {'name': name, 'raw_time': time_txt, 'time': time_txt, 'raw_meeting_hint': meeting, 'meeting': ''}
    if is_unnamed_favourite(typed):  # 'fav': the SP favourite of the race the rules point to (Rule 1.8.4)
        if re.search(r'\b(?:2nd|second|jt|joint|co|cfav)\b', name.lower()):
            return "Only the favourite ('fav') can be entered here, not a second or joint favourite."
        dogs = is_greyhound_or_trap_selection(dict(typed))[2]
        pools = ([[r for r in runners if r.get('category') == 'greyhound']] if dogs
                 else [[r for r in runners if r.get('category') != 'greyhound'], runners])
        found, _ = unnamed_by_timing_rule(typed, pools, struck_mins, favourite=True)
        if len(found) != 1:
            return f"No single race found for the favourite at {time_txt or 'no time'} {meeting or 'no meeting'}."
        race = found[0]
        horse.update({'name': race['name'], 'meeting': race['meeting'], 'time': race['time_str'], 'number': None,
                      'category': race.get('category'), 'price': 'SP', 'favourite': True, 'feed': race.get('feed')})
        print(f"[+] Staff entry: the favourite of the {race['time_str']} at {race['meeting']} [SP]")
        return None
    number = selection_number(typed)
    if number is not None:
        if not time_txt:
            return f"Enter the race time for number {number}."
        # The same trap checks as a scanned selection: the dog card, and the selection marked as a dog. Before, a typed
        # trap was taken unchecked and with no category, so entry found a dog list for a 'horse' and left it for staff.
        dog_track = is_greyhound_or_trap_selection(dict(typed))[2]
        trap_written = bool(re.match(r'^(?:trap|tr|t)\.?\s*\d', name, re.IGNORECASE))
        if trap_written and not dog_track and meeting:
            dog_track = meeting  # 'T3 Newcastle': a trap, so the dogs at a venue that also races horses
        wm_letters = re.sub(r'[^a-z]', '', meeting.lower())
        if dog_track and not trap_written and any(r.get('category') != 'greyhound'
                                                  and re.sub(r'[^a-z]', '', r['meeting'].lower()) == wm_letters
                                                  for r in runners):
            dog_track = None  # 'No 8 Rome': a meeting on today's card, not a greyhound shorthand
        if dog_track:
            dog = match_trap_on_dog_card(dog_track, time_txt, number, struck_mins)
            if dog:
                horse.update({'name': dog['name'], 'meeting': dog['meeting'], 'time': dog['time_str'], 'number': number,
                              'category': 'greyhound', 'feed': dog.get('feed'), 'price': price})
                print(f"[+] Staff entry: trap {number} -> '{dog['name']}' at {dog['meeting']} {dog['time_str']} "
                      f"[{'Price: ' + price if price else 'SP'}]")
                return None
            if trap_written:
                return (f"Trap {number} at {dog_track} {time_txt}: no single race fits on Betty's greyhound card "
                        "(or the trap is vacant, or the race was off before the bet was struck).")
        ok, runner, near = match_number_to_racecard(typed, runners, struck_mins)
    else:
        ok, runner, near = match_runner_to_racecard(typed, runners)
    if not (ok and runner):
        closest = ", ".join(f"{r['name']} ({r['time_str']} {r['meeting']})" for r in near[:3])
        return (f"Not found on today's card: '{name}' {time_txt} {meeting}".rstrip() + "."
                + (f" Closest: {closest}." if closest else " Check the name, time and meeting."))
    horse.update({'name': runner['name'], 'meeting': runner['meeting'], 'time': runner['time_str'],
                  'number': runner.get('number'), 'category': runner.get('category'), 'price': price})
    print(f"[+] Staff entry matched: '{runner['name']}' #{runner.get('number')} at {runner['meeting']} {runner['time_str']}"
          f" [{'Price: ' + price if price else 'SP'}]")
    return None


def prompt_manual_horse_input(horse: dict, horse_idx: int, candidates: list[dict], runners: list[dict],
                              struck_mins: float | None = None, slip_img: str | None = None) -> bool:
    """
    Always-on-top dialog for a selection the program could not read: "Can't read 'xxxx'. Please enter manually".
    Staff fill in the name (or number), race time, meeting and any price taken, pre-filled with what was read;
    the closest runners are offered as one-click fills. The entry goes through the same card checks as a scanned
    selection, and the dialog stays open with the reason until it matches a runner (or staff cancel).
    A confirmed entry is recorded for training (journal_staff 'manual': what was read, what staff typed, the runner it
    matched, and `slip_img`, the slip as the reader saw it).
    Returns True when the selection was resolved (updated in place), False when cancelled.
    """
    slip_name = str(horse.get('name', '')).strip()
    read = {'name': slip_name,
            'time': str(horse.get('raw_time') or horse.get('time') or '').strip(),
            'meeting': _hinted_meeting(horse),
            'price': '' if str(horse.get('price') or '').strip().lower() in ('', 'sp', 'none') else str(horse.get('price')).strip()}
    result = {'confirmed': False}

    def _build_dialog():
        root = tk.Tk()
        root.title(f"{APP_NAME} - Selection #{horse_idx}")
        root.attributes('-topmost', True)
        root.resizable(False, False)
        root.configure(bg='#1E1E1E')
        fg, bg, panel = '#ECEFF1', '#1E1E1E', '#2A2A2A'

        header = ("No selection could be read. Please enter it (or 'fav' for the SP favourite)" if horse.get('_blank')
                  else f"Can't read \"{slip_name or '?'}\". Please enter manually")
        tk.Label(root, text=header,
                 font=('Segoe UI', 11, 'bold'), fg='#FFB74D', bg=bg).pack(padx=16, pady=(12, 2), anchor='w')
        tk.Label(root, text=f"Selection #{horse_idx} as read:  {slip_name or '?'}   |   time {read['time'] or 'not written'}"
                            f"   |   meeting {read['meeting'] or 'not written'}   |   price {read['price'] or 'SP'}",
                 font=('Segoe UI', 9), fg='#B0BEC5', bg=bg).pack(padx=16, anchor='w')

        form = tk.Frame(root, bg=panel, padx=12, pady=8)
        form.pack(fill='x', padx=16, pady=8)
        fields = {}
        for row, (key, label) in enumerate([('name', "Horse name or number"), ('time', "Race time"),
                                            ('meeting', "Meeting"), ('price', "Price taken (blank = SP)")]):
            tk.Label(form, text=label, font=('Segoe UI', 9), fg=fg, bg=panel, anchor='w').grid(row=row, column=0, sticky='w', pady=2)
            var = tk.StringVar(root, value=read[key])  # bound to this dialog, not the status HUD's Tk root
            ent = tk.Entry(form, textvariable=var, width=34, font=('Segoe UI', 10), fg='#FFFFFF', bg='#263238',
                           insertbackground='#FFFFFF', relief='solid', bd=1)
            ent.grid(row=row, column=1, sticky='we', padx=(10, 0), pady=2)
            fields[key] = (var, ent)

        def fill(r: dict):
            fields['name'][0].set(r['name'])
            fields['time'][0].set(r['time_str'])
            fields['meeting'][0].set(r['meeting'])
            fields['price'][1].focus_set()

        if candidates:
            tk.Label(root, text="Closest runners (click to fill):", font=('Segoe UI', 9, 'bold'), fg=fg, bg=bg).pack(padx=16, anchor='w')
            for c in candidates[:6]:
                tk.Button(root, text=f"#{c.get('number')} {c['name']}  ({c['time_str']} {c['meeting']})", font=('Segoe UI', 9),
                          fg=fg, bg='#37474F', activebackground='#455A64', activeforeground='#FFFFFF', relief='flat',
                          cursor='hand2', anchor='w', padx=8, pady=2, command=lambda r=c: fill(r)).pack(fill='x', padx=16, pady=1)

        error = tk.Label(root, text="", font=('Segoe UI', 9), fg='#EF5350', bg=bg, wraplength=480, justify='left')
        error.pack(padx=16, pady=(6, 0), anchor='w')

        def on_confirm():
            entry = {k: v[1].get() for k, v in fields.items()}
            problem = apply_manual_entry(horse, entry, runners, struck_mins)
            if problem:
                error.config(text=problem)
                return
            result['confirmed'] = True
            result['typed'] = entry
            root.destroy()

        def on_cancel():
            result['confirmed'] = False
            root.destroy()

        buttons = tk.Frame(root, bg=bg)
        buttons.pack(fill='x', padx=16, pady=(6, 12))
        tk.Button(buttons, text="Confirm (Enter)", font=('Segoe UI', 9, 'bold'), fg='#FFFFFF', bg='#2E7D32',
                  activebackground='#388E3C', relief='flat', cursor='hand2', padx=12, pady=6,
                  command=on_confirm).pack(side='left', fill='x', expand=True, padx=(0, 6))
        tk.Button(buttons, text="Cancel slip", font=('Segoe UI', 9), fg='#FFFFFF', bg='#C62828',
                  activebackground='#D32F2F', relief='flat', cursor='hand2', padx=12, pady=6,
                  command=on_cancel).pack(side='right', fill='x', expand=True, padx=(6, 0))

        root.bind('<Return>', lambda e: on_confirm())
        root.bind('<KP_Enter>', lambda e: on_confirm())
        root.bind('<Escape>', lambda e: (trigger_abort(), on_cancel()))
        root.protocol("WM_DELETE_WINDOW", on_cancel)
        root.update_idletasks()
        x = max(0, (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2)
        y = max(0, (root.winfo_screenheight() - root.winfo_reqheight()) // 2)
        root.geometry(f"+{x}+{y}")
        first_blank = next((v[1] for k, v in fields.items() if not v[0].get().strip()), fields['name'][1])
        first_blank.focus_set()
        first_blank.select_range(0, tk.END)
        root.mainloop()

    try:
        _build_dialog()
    except Exception as e:
        print(f"[-] Selection entry dialog error: {e}")
        result['confirmed'] = False

    if not result['confirmed']:
        print(f"[!] Staff cancelled the entry for selection #{horse_idx}.")
        return False
    journal_staff("manual", wager=_current_wager, selection=horse_idx, read=read, typed=result.get('typed'),
                  matched={k: horse.get(k) for k in ('name', 'number', 'meeting', 'time', 'price')},
                  image=save_slip_image(slip_img, _current_wager), test_mode=test_mode_on.is_set())
    return True


# NOTE: Discrepancy Settlement, Related Contingencies, and House Rules have been
# modularized into 'rules_engine.py' and externalized into 'bookmaker_rules.json'.
# All rules logic, BookmakerRulesManager, and resolution functions are imported above.


def split_bets_over_time_clashes(slip_data: list[dict]) -> list[dict]:
    """
    Rule 1.8.4: a selection whose written time fits races at several meetings equally (same rank) has the stake
    divided equally between them. Each bet holding such a selection becomes one bet per race at an equal share of
    its unit stake (several such selections: every combination). A stake that doesn't divide into whole pence goes
    to staff rather than being rounded.
    """
    out = []
    for bet in slip_data:
        options = [h.get('_alternatives') or [None] for h in bet.get('horses', [])]
        ways = 1
        for o in options:
            ways *= len(o)
        if ways == 1:
            out.append(bet)
            continue
        stake = int(bet.get('stake_pence') or 0)
        if stake % ways:
            raise WagerForStaff(f"Rule 1.8.4: {stake}p can't be divided equally over {ways} races that share the time written")
        for combo in itertools.product(*options):
            part = {**bet, 'stake_pence': stake // ways, 'horses': []}
            for horse, alt in zip(bet['horses'], combo):
                h = {k: v for k, v in horse.items() if k != '_alternatives'}
                if alt:
                    h.update(alt)
                part['horses'].append(h)
            part.pop('total_stake_pence', None)
            out.append(part)
        print(f"[+] Rule 1.8.4: '{bet.get('description') or bet.get('bet_type')}' divided over {ways} races at "
              f"{stake // ways}p each.")
    return out


DITTO_WORDS = re.compile(r'^\s*(?:do|ditto|dto)\s*\.?\s*$', re.IGNORECASE)  # a time written 'do' = the line above's


def state_pre_scan_and_match_slip(slip_data, raw_selections=None, img_str=None, api_key=None, written_total_pence=None,
                                  struck_time=None):
    """
    PRE-FLIGHT STAGE: Scans and cross-checks all runners across the ENTIRE slip against official racecards
    before any Betty automation begins. Resolves meetings, post times, and official saddle cloth numbers.
    If a horse cannot be matched automatically, prompts the operator to manually input/confirm it.
    struck_time: the 24-hour time the bet was struck ('13:05:30' or '13:05'), when known. Races already off by then
    (Betty's off slips, else the scheduled time: `still_to_run`) are never candidates for a number bet or staff's entry.
    """
    struck_mins = parse_clock_minutes(struck_time)
    print("\n" + "=" * 60)
    print(" [*] PRE-FLIGHT: Pre-scanning all slip selections against racecard data...")
    print("=" * 60)

    # Every horse and greyhound card Betty has, read fresh (not up to RECHECK_SECS old): a feed Betty added moments ago counts
    fresh = lambda card: card.refresh() if hasattr(card, 'refresh') else card.get_runners()  # tests' cards: get_runners
    runners = race_offs.mark(fresh(racecard_manager) + fresh(greyhound_card))  # with when each race went off
    _meeting_match_cache.clear()  # the cards and the meetings directory as they are now
    if not runners:
        print("[-] Betty racecard feed unavailable. Proceeding with UNVERIFIED slip data.")
        notify("Betty racecard feed not found: selections are NOT verified. Check each runner on screen.", is_error=True)
        return slip_data

    # 1. Collect unique selections across all bets and raw transcribed selections. Each written selection's key
    # (time with any ditto applied, name) is kept by its selection_num: a bet's runner is looked up by the selection
    # it came from, never by its own copy of the time, which has no ditto (review B1, 28 Oct: 'No 8' under
    # 'No 3 3.20 Don' was locked in the next Doncaster race by Rule 1.8.4, as untimed)
    unique_selections = {}
    key_by_num: dict = {}
    if raw_selections:
        last_valid_time = None
        last_valid_meeting = None
        for s in raw_selections:
            s_name = str(s.get('name', '')).strip()
            # Pick best time: prefer valid parseable time over raw strings with punctuation noise (e.g. '.')
            s_time = ''
            for k in ('raw_time', 'written_time', 'time'):
                val = str(s.get(k) or '').strip()
                if val and parse_race_time_to_minutes(val)[0] is not None:
                    s_time = val
                    break
            if not s_time:
                for k in ('raw_time', 'written_time', 'time'):
                    val = str(s.get(k) or '').strip()
                    if re.sub(r'[^a-zA-Z0-9]', '', val) and not DITTO_WORDS.match(val):  # '"' and 'do' are dittos
                        s_time = val
                        break
            if s_time and parse_race_time_to_minutes(s_time)[0] is not None:
                last_valid_time = s_time
            elif last_valid_time and not s_time and not s.get('time_unreadable'):  # an unreadable time is no ditto
                s_time = last_valid_time

            s_price = str(s.get('price', '')).strip()
            s_num = s.get('number')
            s_raw_hint = str(s.get('raw_meeting_hint', '')).strip()
            if not re.sub(r'[^a-zA-Z0-9]', '', s_raw_hint) or re.match(r'^\s*(?:ditto|dto)\b', s_raw_hint, re.I):
                s_raw_hint = ''  # '"' or 'ditto' = the meeting above ('do' stays: it can be Doncaster)
            s_meeting = str(s.get('meeting', '')).strip()
            if s_raw_hint or s_meeting:
                last_valid_meeting = s_raw_hint or s_meeting
            elif last_valid_meeting and not s_raw_hint:
                s_raw_hint = last_valid_meeting

            if not s_name and s_num is not None:
                s_name = str(s_num)  # a number with no name is a number bet ('5'), never dropped (review R13)
            if not s_name and s_num is None:
                # Nothing readable for this selection: kept for the staff pop-up, never dropped (user, 26 Oct)
                _, norm_time = parse_race_time_to_minutes(s_time)
                key = (norm_time or s_time.strip(), '')
                unique_selections.setdefault(key, {
                    'name': '', 'time': s_time, 'written_time': s_time, 'raw_time': s_time, 'raw_meeting_hint': s_raw_hint,
                    'meeting': s_meeting, 'line_num': s.get('line_num'), 'price': s_price, 'number': None, '_blank': True})
                if s.get('selection_num') is not None:
                    key_by_num[s['selection_num']] = key
            if s_name:
                _, norm_time = parse_race_time_to_minutes(s_time)
                clean_name = clean_horse_name(s_name)
                key = (norm_time or s_time.strip(), clean_name)
                if s.get('selection_num') is not None:
                    key_by_num[s['selection_num']] = key
                if key not in unique_selections:
                    unique_selections[key] = {
                        'name': s_name,
                        'time': s_time,
                        'written_time': s_time,
                        'raw_time': s.get('raw_time') if s.get('raw_time') and parse_race_time_to_minutes(str(s.get('raw_time')))[0] is not None else s_time,
                        'raw_meeting_hint': s_raw_hint,
                        'meeting': s_meeting or (s_raw_hint if s_raw_hint and len(s_raw_hint) > 2 else ''),
                        'line_num': s.get('line_num'),
                        'price': s_price,
                        'number': s_num,
                        '_slip_says_dogs': bool(s.get('_slip_says_dogs')),
                    }

    bet_kinds: dict[tuple, set] = {}  # selection -> the bet types it is in (single or not, for the dog rules)
    for bet in slip_data:
        for horse in bet.get('horses', []):
            h_name = str(horse.get('name', '')).strip()
            h_time = ''
            for k in ('raw_time', 'written_time', 'time'):
                val = str(horse.get(k) or '').strip()
                if val and parse_race_time_to_minutes(val)[0] is not None:
                    h_time = val
                    break
            if not h_time:
                h_time = str(horse.get('raw_time') or horse.get('written_time') or horse.get('time', '')).strip()
            h_price = str(horse.get('price', '')).strip()
            own_key = key_by_num.get(horse.get('selection_num'))  # the written selection's key, ditto applied
            if not h_name and horse.get('number') is not None:
                h_name = horse['name'] = str(horse['number'])  # a number bet, as above (review R13)
            if not h_name and horse.get('number') is None:
                _, norm_time = parse_race_time_to_minutes(h_time)
                h_key = own_key or (norm_time or h_time.strip(), '')
                unique_selections.setdefault(h_key, {**horse, 'name': '', '_blank': True})
                horse['_preflight_key'] = h_key
            if h_name:
                _, norm_time = parse_race_time_to_minutes(h_time)
                clean_name = clean_horse_name(h_name)
                h_key = own_key or (norm_time or h_time.strip(), clean_name)
                horse['_preflight_key'] = h_key  # step 3 copies the match back under the same key
                bet_kinds.setdefault(h_key, set()).add(str(bet.get("bet_type") or "").lower().strip())
                if h_key not in unique_selections:
                    unique_selections[h_key] = horse
                else:
                    if h_price and h_price.lower() not in ['sp', 'none', ''] and not unique_selections[h_key].get('price'):
                        unique_selections[h_key]['price'] = h_price
                    if horse.get('number') is not None and unique_selections[h_key].get('number') is None:
                        unique_selections[h_key]['number'] = horse.get('number')
                    if horse.get('raw_time') and not unique_selections[h_key].get('raw_time'):
                        unique_selections[h_key]['raw_time'] = horse.get('raw_time')
                    if horse.get('raw_meeting_hint') and not unique_selections[h_key].get('raw_meeting_hint'):
                        unique_selections[h_key]['raw_meeting_hint'] = horse.get('raw_meeting_hint')

    print(f"[*] Found {len(unique_selections)} unique selection(s) across {len(slip_data)} bet section(s).")

    # 2. Match each unique selection against Betty's card
    resolved_map = {}
    horse_idx = 0

    def _resolve(key, runner, price):
        resolved_map[key] = {
            'name': runner['name'],
            'meeting': runner['meeting'],
            'time': runner['time_str'],
            'price': price,
            'number': runner.get('number'),
            'category': runner.get('category'),
            'void': bool(runner.get('void')),
            'favourite': bool(runner.get('favourite')),
            'feed': runner.get('feed'),
            'dogs': bool(runner.get('dogs')),
        }

    for (h_time, h_name), sample_horse in unique_selections.items():
        if abort_event.is_set():
            return None

        horse_idx += 1
        orig_name = sample_horse.get('name', '')
        orig_time = sample_horse.get('time', '')
        price = sample_horse.get('price', '')
        p_disp = f" [Price: {price}]" if price else " [SP]"

        number = selection_number(sample_horse)
        written_meeting = _hinted_meeting(sample_horse)
        blank = bool(sample_horse.get('_blank'))
        if blank:
            where = f"{orig_time or 'no time'} {written_meeting or 'no meeting'}"
            print(f"[!] Selection #{horse_idx} ({where}): no selection could be read. Asking staff (pop-up)...")
            alert_staff(f"No selection could be read ({where}). Please enter it in the pop-up.")
        is_fav = not blank and is_unnamed_favourite(sample_horse)
        top3: list[dict] = []  # runners offered to staff (a favourite has none)
        if is_fav:
            # A favourite written ('fav', 'SP fav'): Betty's 'The Favourite' in the race the rules point to (Rule 1.8.4).
            # Only the absolute favourite has a row on Betty; a second or joint favourite goes to staff.
            if re.search(r'\b(?:2nd|second|jt|joint|co|cfav)\b', str(orig_name).lower()):
                print(f"[!] '{orig_name}': only the absolute favourite can be entered (Betty's 'The Favourite').")
            else:
                dog_track = is_greyhound_or_trap_selection(dict(sample_horse))[2]
                dogs_only = [r for r in runners if r.get('category') == 'greyhound']
                pools = [dogs_only] if dog_track else [[r for r in runners if r.get('category') != 'greyhound'], runners]
                ruled, how = unnamed_by_timing_rule(sample_horse, pools, struck_mins, favourite=True)
                if ruled:
                    for r in ruled:
                        print(f"[+] House rule ({how}): '{orig_name}' ({orig_time or 'no time'} {written_meeting or 'no meeting'}) -> "
                              f"The Favourite at {r['meeting']} ({r['time_str']}) [SP]")
                    _resolve((h_time, h_name), ruled[0], 'SP')
                    if len(ruled) > 1:
                        resolved_map[(h_time, h_name)]['alternatives'] = [
                            {'name': r['name'], 'meeting': r['meeting'], 'time': r['time_str'], 'price': 'SP', 'number': None,
                             'category': r.get('category'), 'favourite': True, 'feed': r.get('feed')} for r in ruled]
                    continue
                print(f"[!] '{orig_name}' ({orig_time or 'no time'} {written_meeting or 'no meeting'}): no race found for the favourite.")
        if is_fav or blank:
            pass  # not decided above: straight to staff, no name matching or paid re-check
        elif number is not None:
            # Number bets carry no name. What's written before the number decides horse or dog (number_bet_is_dog):
            # a dog is the trap at the written meeting and time on Betty's dog card, else the greyhound rules; a horse
            # is the cloth number at the written time and meeting, else Rule 1.8.4
            horses_only = [r for r in runners if r.get('category') != 'greyhound']
            dogs_only = [r for r in runners if r.get('category') == 'greyhound']
            if number_bet_is_dog(sample_horse, runners):
                dog_meeting = next((r['meeting'] for r in dogs_only if written_meeting
                                    and _meeting_matches(r['meeting'], written_meeting)), None)
                dog_meeting = dog_meeting or is_greyhound_or_trap_selection(dict(sample_horse))[2]
                dog = match_trap_on_dog_card(dog_meeting, orig_time, number, struck_mins) if dog_meeting and orig_time else None
                if dog:
                    print(f"[+] Trap {number} at {dog_meeting} {orig_time} -> '{dog['name']}' #{number} at {dog['meeting']} "
                          f"({dog['time_str']}) on Betty's greyhound card{p_disp}")
                    _resolve((h_time, h_name), dog, price)
                    continue
                ruled, how = trap_by_dog_rules(sample_horse, dogs_only, struck_mins,
                                               single=bool(bet_kinds.get((h_time, h_name))) and bet_kinds[(h_time, h_name)] <= SINGLE_BETS)
                if ruled:
                    print(f"[+] {how}: '{orig_name}' ({orig_time or 'no time'} {written_meeting or 'no meeting'}) -> "
                          f"'{ruled[0]['name']}' at {ruled[0]['meeting']} ({ruled[0]['time_str']}){p_disp}")
                    _resolve((h_time, h_name), ruled[0], price)
                    continue
                print(f"[!] Trap {number} ({orig_time or 'no time'} {written_meeting or 'no meeting'}): {how}.")
                top3 = sorted((r for r in dogs_only if r.get('number') == number and still_to_run(r, struck_mins)
                               and (not dog_meeting or _meeting_matches(r['meeting'], dog_meeting))),
                              key=lambda r: r['minutes'])[:6]
                pools = []
            else:
                # 'No.' or a bare number: a horse (user, 27 Oct). With no meeting written and no horse race at the time,
                # a dog race at that time is the last resort (user, 23 Oct)
                matched, runner_match, top3 = match_number_to_racecard(sample_horse, horses_only, struck_mins)
                if matched and runner_match:
                    print(f"[+] Confident Match by {sample_horse.get('_match_stage')}: '{orig_name}' ({orig_time} {written_meeting}) -> "
                          f"'{runner_match['name']}' #{runner_match.get('number')} at {runner_match['meeting']} ({runner_match['time_str']}){p_disp}")
                    _resolve((h_time, h_name), runner_match, price)
                    continue
                pools = [horses_only] if written_meeting else [horses_only, runners]
            # Untimed or incorrectly timed: the house rule decides (Rule 1.8.4), before staff are asked
            ruled, how = unnamed_by_timing_rule(sample_horse, pools, struck_mins) if pools else ([], '')
            if ruled:
                for r in ruled:
                    print(f"[+] House rule ({how}): '{orig_name}' ({orig_time or 'no time'} {written_meeting or 'no meeting'}) -> "
                          f"'{r['name']}'{' #' + str(r['number']) if r.get('number') else ''} at {r['meeting']} ({r['time_str']}){p_disp}")
                _resolve((h_time, h_name), ruled[0], price)
                if len(ruled) > 1:  # a time clash in the first rank: the bet is split over every race (Rule 1.8.4)
                    resolved_map[(h_time, h_name)]['alternatives'] = [
                        {'name': r['name'], 'meeting': r['meeting'], 'time': r['time_str'], 'price': price,
                         'number': r.get('number'), 'category': r.get('category')} for r in ruled]
                continue
            why = "no race time is written" if not orig_time else "no single race fits the written time and meeting"
            guesses = ", ".join(f"#{r.get('number')} {r['name']} ({r['time_str']} {r['meeting']})" for r in top3) or "none"
            print(f"[!] Number bet '{orig_name}' ({orig_time or 'no time'} {written_meeting or 'no meeting'}): {why}. Possible: {guesses}")
        else:
            print(f"\n[*] Crosschecking Selection #{horse_idx}: '{orig_name}' (Written Time: '{orig_time}', Meeting: '{written_meeting}')...")

            # Stages 1-2: name first, then the race at the written time
            matched, runner_match, top3 = match_runner_to_racecard(sample_horse, runners)
            if matched and runner_match:
                time_msg = f"({runner_match['time_str']})"
                if orig_time and orig_time != runner_match['time_str']:
                    time_msg = f"({runner_match['time_str']}) [Written '{orig_time}' -> racecard time '{runner_match['time_str']}']"
                print(f"[+] Confident Match by {sample_horse.get('_match_stage', 'name')}: '{orig_name}' -> '{runner_match['name']}' "
                      f"#{runner_match.get('number')} at {runner_match['meeting']} {time_msg}{p_disp}")
                _resolve((h_time, h_name), runner_match, price)
                continue

            guesses = ", ".join(f"{r['name']} ({r['time_str']} {r['meeting']})" for r in top3) or "none"
            print(f"[!] '{orig_name}' is not a confident match. Best 3 guesses: {guesses}")

        # Stage 3a: race-list check of the handwriting against every runner in the race(s) at the written time
        if number is None and not is_fav and not blank and img_str and api_key:
            choice = reexamine_runner_with_ai(sample_horse, horse_idx, img_str, api_key, top3, runners)
            if choice:
                print(f"[+] Re-check confirmed '{orig_name}' -> '{choice['name']}' #{choice.get('number')} at {choice['meeting']} ({choice['time_str']}){p_disp}")
                _resolve((h_time, h_name), choice, price)
                continue

        # Stage 3b: staff enter the selection; their details go through the same card checks as a scanned one
        print(f"[!] Unable to verify '{orig_name}' automatically. Asking staff to enter the selection...")
        user_ok = prompt_manual_horse_input(sample_horse, horse_idx, top3, runners, struck_mins, slip_img=img_str)
        if not user_ok or abort_event.is_set():
            print("[-] Slip pre-scan cancelled by operator during manual selection.")
            notify("Slip processing cancelled by operator.", is_error=True, title=f"{APP_NAME} - Cancelled")
            return None

        resolved_map[(h_time, h_name)] = {
            'name': sample_horse['name'],
            'meeting': sample_horse.get('meeting'),
            'time': sample_horse.get('time', orig_time),
            'price': sample_horse.get('price', price),
            'number': sample_horse.get('number'),
            'category': sample_horse.get('category'),
            'favourite': bool(sample_horse.get('favourite')),
            'feed': sample_horse.get('feed'),
            'dogs': bool(sample_horse.get('dogs')),
        }

    # 3. Synchronize all resolved runner details back into the slip data, under the key each runner was collected by
    for bet in slip_data:
        for horse in bet.get('horses', []):
            h_name = str(horse.get('name', '')).strip()
            clean_name = clean_horse_name(h_name)
            key = horse.get('_preflight_key')
            if key is None:  # not collected in step 1 (e.g. a number read with no name)
                h_time = str(horse.get('written_time') or horse.get('time', '')).strip()
                _, norm_time = parse_race_time_to_minutes(h_time)
                key = (norm_time or h_time.strip(), clean_name)
            res = resolved_map.get(key)
            if not res and clean_name and selection_number(horse) is None:
                # Fallback: the same name locked once, never a look-alike. 'No 3' and 'No 8' are 0.75 alike, and a
                # similarity fallback gave a double on No 3 / No 8 both runners as No 3 (review B2, 28 Oct)
                same = [r_data for (_, r_clean), r_data in resolved_map.items() if r_clean == clean_name]
                if len(same) == 1:
                    res = same[0]
            if res:
                horse['name'] = res['name']
                if res.get('meeting'):
                    horse['meeting'] = res['meeting']
                if res.get('time'):
                    horse['time'] = res['time']
                if res.get('number') is not None:
                    horse['number'] = res['number']
                if res.get('category'):
                    horse['category'] = res['category']
                if res.get('void'):
                    horse['void'], horse['number'] = True, None  # entered with 'v' on its race
                if res.get('favourite'):
                    horse['favourite'], horse['number'], horse['price'] = True, None, 'SP'  # through its folder
                if res.get('feed'):
                    horse['feed'] = res['feed']
                if res.get('dogs'):
                    horse['dogs'] = True
                if res.get('alternatives'):
                    horse['_alternatives'] = res['alternatives']
                res_p = str(res.get('price', '')).strip()
                if res_p and res_p.lower() not in ['sp', 'none', '']:
                    horse['price'] = res_p
                elif not horse.get('price') and res_p:
                    horse['price'] = res_p
    for bet in slip_data:  # after every bet: one runner can sit in two bets ('X & Y' lines share their runners)
        for horse in bet.get('horses', []):
            horse.pop('_preflight_key', None)

    # 3a. A selection whose time fits several races equally (Rule 1.8.4): the bet is split equally over them
    slip_data = split_bets_over_time_clashes(slip_data)

    # 3b. Apply Configured Bookmaker House Rules & Discrepancy Resolution Engine
    # Costs are re-measured now that every runner has a resolved meeting + time (same-race aware).
    pre_rules_total = sum(calculate_bet_cost_pence(b) for b in slip_data)
    slip_data = resolve_bookmaker_discrepancies(slip_data, runners=runners, rules_mgr=bookmaker_rules_mgr)
    post_rules_total = sum(calculate_bet_cost_pence(b) for b in slip_data)

    # Stake Integrity Guard: house-rule rewrites (clash splits, cross doubles, perms) must conserve the
    # customer's money. Rounding of divided stakes may move it by at most 1p per bet.
    if abs(post_rules_total - pre_rules_total) > len(slip_data):
        print(f"[!] STAKE INTEGRITY WARNING: Slip cost changed from {pre_rules_total}p to {post_rules_total}p while applying "
              f"{bookmaker_rules_mgr.get_firm_name()} rules. Check the bets below before placing.")
        notify(f"Check slip: house rules changed total from £{pre_rules_total / 100:.2f} to £{post_rules_total / 100:.2f}.",
               is_error=True)

    # 4. Display Confirmed Pre-Flight Summary Table
    print("\n" + "=" * 62)
    firm_hdr = f"({bookmaker_rules_mgr.get_firm_name().upper()} RULES)"
    print(f" {APP_NAME.upper()} - PRE-FLIGHT SELECTIONS LOCKED {firm_hdr}")
    print("=" * 62)
    for b_idx, bet in enumerate(slip_data, 1):
        b_type = bet.get('bet_type', 'Single').title()
        b_stake = bet.get('stake_pence', 0)
        ew_tag = " (Each-Way)" if bet.get('each_way') else ""
        b_cost = calculate_bet_cost_pence(bet)
        print(f" Bet {b_idx} [{b_type}{ew_tag} - {b_stake}p unit | {b_cost}p total]:")
        for h_idx, h in enumerate(bet.get('horses', []), 1):
            h_num = f" #{h.get('number')}" if h.get('number') else ""
            h_price = h.get('price', 'SP')
            p_tag = f" [TAKE PRICE: {h_price}]" if h_price and h_price.lower() not in ['sp', 'none', ''] else " [SP]"
            print(f"   {h_idx}. {h.get('name')}{h_num}  [{h.get('time')} {h.get('meeting')}]{p_tag}")
    print(f" SLIP TOTAL: {post_rules_total}p (£{post_rules_total / 100:.2f})")
    print("=" * 62 + "\n")

    notify(f"All {len(unique_selections)} runner(s) verified! Proceeding with Betty...", is_error=False, title=APP_NAME, bg_color="#1B5E20")
    return slip_data


# --- 4. THE EXECUTION ENGINE ---
MAX_SCAN_ATTEMPTS = 3


def bets_reading_signature(bets_list: list[dict]) -> tuple:
    """What decides the bets' cost, per bet: its words (letters and digits only: '3x 50p' and '3 x 50P' are one
    reading), stake, each way, type, runner count and cost. Two scans with the same signature read the same bets."""
    return tuple((_letters(f"{b.get('description', '')} {b.get('raw_text', '')}"), b.get('stake_pence'),
                  bool(b.get('each_way')), normalize_bet_type(str(b.get('bet_type', ''))), len(b.get('horses', [])),
                  b.get('cost_pence')) for b in bets_list or [])


def scan_and_reconcile(api_key, payment_pence: int | None = None, struck_time: str | None = None) -> dict:
    """
    Reads the slip on the race-entry screen and rescans (up to MAX_SCAN_ATTEMPTS, with a targeted hint) until the bets
    cost exactly what was paid. `payment_pence` is View Wagers' Payment, the money actually taken: when known it is the
    authority and must match to the penny. Without it (the test harness) the customer's written total must match instead.
    `struck_time` (View Wagers, '13:05') starts the reader's card shortly before the bet was struck.
    Returns {'ok', 'reason', 'slip_data', 'raw_selections', 'img_str', 'written_total_pence', 'calc_total_pence'}.
    """
    out: dict[str, Any] = {'ok': False, 'reason': '', 'slip_data': None, 'raw_selections': None, 'img_str': None,
                           'written_total_pence': None, 'calc_total_pence': None}
    hint, last_reading = None, None
    for attempt in range(1, MAX_SCAN_ATTEMPTS + 1):
        if abort_event.is_set():
            return out
        print(f"\n[*] --- SLIP SCAN ATTEMPT {attempt}/{MAX_SCAN_ATTEMPTS} ---")
        STATUS_HUD.update(f"Scanning slip ({' -> '.join(t['label'] for t in reader_tiers())})...")
        slip_data, raw_selections, img_str, written, calc = state_read_slip_via_api(
            api_key, retry_hint=hint, payment_pence=payment_pence, struck_time=struck_time)
        if abort_event.is_set():
            return out
        out.update(slip_data=slip_data, raw_selections=raw_selections, img_str=img_str,
                   written_total_pence=written, calc_total_pence=calc)
        if not slip_data:
            if img_str is None:  # every reader in the chain failed (credit, quota, timeouts): rescanning won't help
                out['reason'] = "Slip scan failed: no reader answered (credit / quota / connection). See the console."
                return out
            print(f"[-] Scan attempt {attempt} returned no bet data.")
            if attempt < MAX_SCAN_ATTEMPTS:
                if not interruptible_sleep(0.75):
                    return out
                continue
            out['reason'] = f"Slip scan failed: no bets could be read after {MAX_SCAN_ATTEMPTS} scans."
            return out

        calc = calc or 0
        if payment_pence is not None:
            target, what = payment_pence, "paid (View Wagers Payment)"
            if written and written != payment_pence:
                print(f"[!] Customer wrote £{written / 100:.2f} but paid £{payment_pence / 100:.2f}: Payment is the authority.")
        else:
            target, what = written, "written at the bottom of the slip"
        if not target:
            print(f"[*] Nothing to reconcile against; proceeding with parsed bets (£{calc / 100:.2f}).")
            out['ok'] = True
            return out
        diff = abs(calc - target)
        print(f"[*] Reconciling: bets £{calc / 100:.2f} vs {what} £{target / 100:.2f} [diff £{diff / 100:.2f}]")
        if diff == 0:
            out['ok'] = True
            return out
        # The same bets read again: the words are right and how they're costed isn't, which no rescan changes
        # (9.2459179, 31 Oct: three paid scans of identical lines)
        reading = bets_reading_signature(slip_data)
        if reading == last_reading:
            print("[!] The rescan read the same bets as the scan before it: rescanning again won't change the money.")
            out['reason'] = (f"Money mismatch: the bets cost £{calc / 100:.2f} but £{target / 100:.2f} was "
                             f"{what.split(' (')[0]}; two scans read the same bets.")
            return out
        last_reading = reading
        if attempt < MAX_SCAN_ATTEMPTS:
            hint = (f"ATTENTION: In the previous scan, the bets totaled £{calc / 100:.2f} ({calc}p), but the customer "
                    f"{'paid' if payment_pence is not None else 'wrote a total of'} £{target / 100:.2f} ({target}p) "
                    f"(difference of £{diff / 100:.2f}). Some bet instructions or selections were missed or misread "
                    f"(check every bet line under each group of selections, notes in the right-hand margin, and crossed-out "
                    f"lines). Please carefully re-examine every line of the slip from top to bottom so all selections "
                    f"and bets reconcile with £{target / 100:.2f}.")
            print(f"[*] Money mismatch: rescanning ({attempt + 1}/{MAX_SCAN_ATTEMPTS}) with a targeted hint...")
            STATUS_HUD.update(f"Bets £{calc / 100:.2f} vs {what.split(' (')[0]} £{target / 100:.2f}: rescanning...", bg='#E65100')
            if not interruptible_sleep(0.75):
                return out
            continue
        out['reason'] = (f"Money mismatch: the bets cost £{calc / 100:.2f} but £{target / 100:.2f} was "
                         f"{what.split(' (')[0]}, after {MAX_SCAN_ATTEMPTS} scans.")
        return out
    return out


# --- 5. BETTY SCREEN CLASSIFIER (1366x768 only) ---
# Each screen needs every colour signal (box, RGB, minimum share of matching pixels) AND its fixed label read by
# Tesseract. Measured on scratch/betty_screens/*.png: the right screen scores 0.8-1.0 on its signals, others ~0.
SCREEN_HOME = "HOME"
SCREEN_VIEW_WAGERS = "VIEW_WAGERS"
SCREEN_EVENT_MENU = "EVENT_MENU"
SCREEN_RACE_ENTRY = "RACE_ENTRY"              # race entry with the yellow time box hidden
SCREEN_RACE_ENTRY_READY = "RACE_ENTRY_READY"  # race entry with the yellow time box showing (the slip is scanned here)
SCREEN_RACE_ENTRY_EXHAUSTED = "RACE_ENTRY_EXHAUSTED"  # every meeting at the typed time dequeued: time shown in red
SCREEN_RACE_ENTRY_BROKEN = "RACE_ENTRY_BROKEN"  # Betty glitch: no slip image, "Special/Other Events Wager" drawn over it
SCREEN_RACE_LIST = "RACE_LIST"                # runners at the typed time ("Harl 11:04 | Trap 1. ..."), the cyan panel
SCREEN_REUSE_PANEL = "REUSE_PANEL"            # earlier selections (right-click on the slip). NEVER click a Master Index one
MODAL_LATE_SELECTION = "MODAL_LATE_SELECTION"  # red border: "Wager staked N mins after 'off'... 'Void Selection'?" (Yes)
MODAL_PRICE = "MODAL_PRICE"                    # blue border: "The price you entered was not correct..." (Price when struck, else Override)
MODAL_PAYMENT_MISMATCH = "MODAL_PAYMENT_MISMATCH"  # after F12, red: "Payment is not the same as on the original empty bet..."
MODAL_CONFIRM_STAKE = "MODAL_CONFIRM_STAKE"        # after No on the above, blue: "Please confirm this is the stake tendered"
SCREEN_BET_AND_STAKE = "BET_AND_STAKE"        # F8 "Choose Bet and Stake" (Place Bet / F12 lives here)
SCREEN_UNKNOWN = "UNKNOWN"

_BETTY_CYAN_HEADER = ((600, 30, 600, 25), (0, 255, 255), 0.7)  # "Your Betting Slip" header (S2-S4)
# Choose Bet and Stake is green until a selection is on the slip, then yellow (with a green Place Bet beside it)
_CHOOSE_BET_BUTTON = ((532, 636, 100, 108), [(0, 192, 0), (255, 255, 128)], 0.5)
_REUSE_PANEL_WHITE = ((8, 340, 390, 200), (255, 255, 255), 0.9)  # below the reuse rows: plain white
SCREEN_SIGNATURES = {
    SCREEN_HOME: {
        'colours': [((470, 205, 205, 75), (255, 255, 128), 0.7),    # View Wagers button
                    ((728, 615, 205, 75), (255, 255, 128), 0.7),    # End Program button
                    ((20, 150, 420, 550), (255, 255, 255), 0.9)],   # empty white left side
        'label': ((450, 12, 480, 55), ("managerterminal",)),
    },
    SCREEN_VIEW_WAGERS: {
        'colours': [((295, 278, 180, 255), (128, 255, 255), 0.5),   # cyan keypad
                    _BETTY_CYAN_HEADER],
        'label': ((290, 180, 265, 30), ("number",)),                # "View Wager Number:"
    },
    SCREEN_EVENT_MENU: {
        'colours': [((5, 115, 545, 630), (255, 255, 208), 0.5),     # grid of event-category buttons
                    ((568, 675, 145, 55), (255, 255, 128), 0.7),    # More Events button
                    _BETTY_CYAN_HEADER],
        'label': ((730, 680, 150, 45), ("searchindex",)),
    },
    SCREEN_RACE_ENTRY: {
        'colours': [((8, 110, 205, 35), (193, 0, 0), 0.5),          # red meeting-list header
                    _CHOOSE_BET_BUTTON,
                    ((940, 634, 80, 110), (0, 128, 0), 0.5)],       # dark green Cancel Bet
        'absent': [_REUSE_PANEL_WHITE],
        'label': ((5, 630, 80, 50), ("master", "index")),
    },
    SCREEN_REUSE_PANEL: {  # right-click on the slip image: earlier selections listed on the left, white rows
        'colours': [((8, 110, 205, 35), (193, 0, 0), 0.5),          # red meeting-list header
                    ((10, 292, 120, 24), (255, 255, 255), 0.7),     # white first selection row
                    _REUSE_PANEL_WHITE,
                    ((940, 634, 80, 110), (0, 128, 0), 0.5)],       # dark green Cancel Bet
        'label': ((5, 290, 128, 28), ()),                            # first row reads "Meet H:MM"
    },
    SCREEN_RACE_LIST: {  # runners listed after a time is typed (hatched when no prices are in yet)
        'colours': [_CHOOSE_BET_BUTTON,
                    ((940, 634, 80, 110), (0, 128, 0), 0.5),        # dark green Cancel Bet
                    ((5, 5, 128, 200), (64, 255, 255), 0.15, 70)],  # cyan / light-cyan / hatched runner list
        'absent': [((8, 110, 205, 35), (193, 0, 0), 0.2)],          # no red meeting-list header
        'label': ((5, 5, 128, 30), ()),                              # first row reads "Meet H:MM"
    },
    SCREEN_BET_AND_STAKE: {  # only parts present the moment F8 opens (Place Bet turns green, the bet list grows later)
        'colours': [((10, 78, 278, 45), (193, 0, 0), 0.6),          # red "Please Choose the Bet You Require Here"
                    ((322, 34, 204, 40), (193, 0, 0), 0.6),         # red "Please Choose the Unit Stake Here"
                    ((324, 84, 100, 410), (0, 255, 255), 0.8)],     # cyan £200 ... £1 stake column
        'label': ((314, 578, 72, 32), ("stake",)),                   # "Stake:"
    },
}
# Pop-ups sit on top of a screen whose own signals still match, so they are checked first.
MODAL_SIGNATURES = {
    MODAL_LATE_SELECTION: {
        'colours': [((350, 291, 665, 6), (255, 0, 0), 0.6),        # red top border
                    ((343, 300, 6, 230), (255, 0, 0), 0.8),        # red left border
                    ((360, 310, 640, 140), (255, 255, 255), 0.8)],  # white message area
        'label': ((380, 340, 620, 80), ("voidselection", "staked")),
    },
    MODAL_PAYMENT_MISMATCH: {  # same red box as the late-selection one; told apart by its message
        'colours': [((350, 291, 665, 6), (255, 0, 0), 0.6),
                    ((343, 300, 6, 230), (255, 0, 0), 0.8),
                    ((360, 310, 640, 140), (255, 255, 255), 0.8)],
        'label': ((380, 340, 620, 80), ("originalemptybet", "customeractuallygave")),
    },
    MODAL_CONFIRM_STAKE: {
        'colours': [((95, 177, 495, 6), (0, 0, 255), 0.4),         # blue top border
                    ((86, 190, 6, 350), (0, 0, 255), 0.8),         # blue left border
                    ((100, 360, 480, 170), (255, 255, 255), 0.8)],  # white lower half
        'label': ((100, 195, 380, 30), ("staketendered", "confirmthis")),
    },
    MODAL_PRICE: {
        'colours': [((405, 289, 610, 6), (0, 0, 255), 0.6),        # blue top border
                    ((401, 300, 6, 320), (0, 0, 255), 0.8),        # blue left border
                    ((415, 300, 430, 140), (255, 255, 255), 0.8)],  # white message area
        'label': ((415, 312, 430, 40), ("priceyouentered", "notcorrect")),
    },
}
RACE_ENTRY_TIME_BOX = ((400, 450, 80, 20), (255, 255, 128), 0.5)
# Betty's broken edit state (seen after alt-tabbing back to A-Bet and editing a new bet): the slip image is missing,
# its panel is plain cream, and "Special/Other Events Wager" is drawn over it. Back out and start again.
RACE_ENTRY_BROKEN_SLIP = ((500, 120, 350, 450), (255, 255, 208), 0.6, 20)
RACE_ENTRY_BROKEN_LABEL = ((445, 82, 260, 28), ("otherevents",))
# After `right` has dequeued every meeting at the typed time, Betty shows that time in red where the time box was
RACE_ENTRY_RED_TIME = ((410, 448, 65, 30), (255, 0, 0), 0.03)
# Top wager box under "Unedited (Exc.Fao)" on View Wagers: light blue = waiting, green = clicked/loaded, white = none
UNEDITED_QUEUE_BOX = (150, 157, 118, 28)
QUEUE_WAITING_RGB = (128, 255, 255)
QUEUE_SELECTED_RGB = (0, 255, 65)
# Some unedited wagers show yellow; they edit like any other (user, 23 Oct). Before, a yellow top box read as an
# empty list, so the watcher saw no work.
QUEUE_YELLOW_RGB = (255, 255, 128)
QUEUE_UNEDITED_RGBS = [QUEUE_WAITING_RGB, QUEUE_YELLOW_RGB]


def _colour_share(arr: Any, box: tuple, rgb: tuple | list, tol: int = 40) -> float:
    """Share of pixels in `box` within `tol` of `rgb` (per channel). `rgb` may be a list: any of those colours."""
    x, y, w, h = box
    region = arr[y:y + h, x:x + w, :3].astype(int)
    if region.size == 0:
        return 0.0
    hit = np.zeros(region.shape[:2], dtype=bool)
    for colour in (rgb if isinstance(rgb, list) else [rgb]):
        hit |= np.max(np.abs(region - np.array(colour)), axis=2) <= tol
    return float(np.mean(hit))


def _signals_pass(arr: Any, signals: Any) -> bool:
    """Every (box, rgb, min_share[, tolerance]) signal matches."""
    return all(_colour_share(arr, s[0], s[1], *s[3:]) >= s[2] for s in signals)


def _signals_absent(arr: Any, signals: Any) -> bool:
    """No (box, rgb, max_share[, tolerance]) signal reaches its share."""
    return all(_colour_share(arr, s[0], s[1], *s[3:]) < s[2] for s in signals)


def _label_reads(img: Any, box: tuple, keywords: tuple) -> bool:
    """Tesseract reads one of `keywords` (letters only, lower case) in the fixed label at `box`.
    With no keywords, the label must read as a meeting and clock time ("Harl 11:04")."""
    x, y, w, h = box
    crop = img.crop((x, y, x + w, y + h)).resize((w * 3, h * 3) if not keywords else (w * 2, h * 2))
    try:
        text = pytesseract.image_to_string(crop, config='--psm 7' if not keywords else '--psm 6')
    except Exception as e:
        print(f"[-] Screen label OCR failed: {e}")
        return False
    if not keywords:
        return re.search(r'[A-Za-z]{2,}\s*\d{1,2}[:.]\d{2}', text) is not None
    letters = re.sub(r'[^a-z]', '', text.lower())
    return any(k in letters for k in keywords)


def detect_screen(img: Any = None) -> str:
    """
    Which Betty screen is showing: one of the SCREEN_* names. `img` is a full 1366x768 screenshot (taken if omitted).
    A screen is named only when exactly one signature's colours all match AND its label reads; otherwise UNKNOWN.
    """
    if img is None:
        img = pyautogui.screenshot()
    img = img.convert('RGB')
    arr = np.array(img)
    for name, sig in MODAL_SIGNATURES.items():
        if _signals_pass(arr, sig['colours']) and _label_reads(img, *sig['label']):
            return name
    matches = [name for name, sig in SCREEN_SIGNATURES.items()
               if _signals_pass(arr, sig['colours']) and _signals_absent(arr, sig.get('absent', []))]
    if len(matches) != 1:
        return SCREEN_UNKNOWN
    name = matches[0]
    if not _label_reads(img, *SCREEN_SIGNATURES[name]['label']):
        return SCREEN_UNKNOWN
    if name == SCREEN_RACE_ENTRY:
        if _signals_pass(arr, [RACE_ENTRY_BROKEN_SLIP]) and _label_reads(img, *RACE_ENTRY_BROKEN_LABEL):
            return SCREEN_RACE_ENTRY_BROKEN
        if _signals_pass(arr, [RACE_ENTRY_TIME_BOX]):
            return SCREEN_RACE_ENTRY_READY
        if _signals_pass(arr, [RACE_ENTRY_RED_TIME]) and _red_time_reads(img):
            return SCREEN_RACE_ENTRY_EXHAUSTED
    return name


def _red_time_reads(img: Any) -> bool:
    """The red text where the time box was reads as a clock time (second signal for meetings exhausted)."""
    x, y, w, h = RACE_ENTRY_RED_TIME[0]
    crop = img.crop((x, y, x + w, y + h)).resize((w * 3, h * 3))
    try:
        text = pytesseract.image_to_string(crop, config='--psm 7 -c tessedit_char_whitelist=0123456789:.')
    except Exception:
        return False
    return re.search(r'\d{1,2}[:.]\d{2}', text) is not None


def view_wagers_queue_state(img: Any = None) -> str:
    """On View Wagers: 'waiting' (an unedited wager, not clicked: light blue or yellow), 'selected' (clicked/loaded)
    or 'empty'."""
    if img is None:
        img = pyautogui.screenshot()
    arr = np.array(img.convert('RGB'))
    if _colour_share(arr, UNEDITED_QUEUE_BOX, QUEUE_SELECTED_RGB) >= 0.5:
        return 'selected'
    if _colour_share(arr, UNEDITED_QUEUE_BOX, QUEUE_UNEDITED_RGBS) >= 0.5:
        return 'waiting'
    return 'empty'


# --- 6. ALWAYS-ON WATCHER ---
# ` toggles the watcher, Shift+` toggles test mode, Esc aborts the current action. A key press or click from a person
# (not injected by this program) switches the watcher off so it never fights staff; ` switches it back on, and it
# looks at the screen after WATCHER_RESUME_SETTLE_SECS to work out where Betty is.
REQUIRED_RESOLUTION = (1366, 768)
WATCHER_RESUME_SETTLE_SECS = 2.0


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    return default if not raw else raw in ("1", "true", "yes", "on")


watcher_on = threading.Event()
test_mode_on = threading.Event()
if _env_flag("BETTY_TEST_MODE", False):  # live by default (places bets); BETTY_TEST_MODE=1 starts in test mode
    test_mode_on.set()
_watcher_resume_at = 0.0
_watcher_screen = SCREEN_UNKNOWN
_staff_input_expected = 0  # >0 while the program is waiting for staff (staff dialog, test-mode review)
_watcher_stop_reason = ""  # why the current watcher action was stopped: "staff", "off" (both touch nothing) or "" (Esc)
# Held while the watcher starts or ends an action and while a key / ` / Esc changes its state, so a staff key can't
# land between the loop's "is it on?" and its reset of the stop flags (9.2452711, 26 Oct: lost, the next wager started)
_watcher_state_lock = threading.Lock()
_wager_opened = False  # the current wager's bet edit was opened (End): only then does Esc or a failure leave it for staff
_paused_for_staff = False  # the watcher went idle because staff used the till (not switched off with `)
_last_staff_activity = 0.0  # last key, click or mouse movement by a person
STAFF_IDLE_RESUME_SECS = 60  # paused for staff: switch back on after this long with no activity at all
_staff_input_lock = threading.Lock()


class staff_input_expected:
    """Context: staff are meant to use the keyboard/mouse now, so their input must not switch the watcher off."""
    def __enter__(self):
        global _staff_input_expected
        with _staff_input_lock:
            _staff_input_expected += 1

    def __exit__(self, *exc):
        global _staff_input_expected
        with _staff_input_lock:
            _staff_input_expected -= 1


def watcher_mode_text() -> str:
    parts = ["WATCHER ON" if watcher_on.is_set() else "WATCHER OFF"]
    parts.append("TEST MODE" if test_mode_on.is_set() else "LIVE: PLACES BETS")
    parts.append(f"Screen: {_watcher_screen}")
    return "  |  ".join(parts)


def watcher_hud_colour() -> str:
    if not watcher_on.is_set():
        return '#37474F'
    return '#4A148C' if test_mode_on.is_set() else '#E65100'  # purple = test, orange = live (places bets)


def watcher_state() -> dict:
    """What the launcher shows: watcher on/off (or paused for staff), test or live, Betty's screen, the wager in hand."""
    return {'watcher': watcher_on.is_set(), 'paused_for_staff': _paused_for_staff, 'test_mode': test_mode_on.is_set(),
            'screen': _watcher_screen, 'busy': watcher_busy, 'wager': _current_wager}


def refresh_watcher_hud(msg: str | None = None):
    STATUS_HUD.set_mode(watcher_mode_text())
    backend_event("state", **watcher_state())
    if msg is not None:
        STATUS_HUD.update(msg, bg=watcher_hud_colour(), badge=IDLE_BADGE)


def set_watcher(on: bool, why: str = "` pressed"):
    """
    Watcher on or off, from ` or the launcher's Start / Pause (`why` says which, for the console). Off stops at once
    and touches nothing: a wager in hand is tried again on resume. On puts the status panel back in its corner and looks at
    Betty after a short settle.
    """
    global _watcher_resume_at, _watcher_stop_reason, _paused_for_staff
    _paused_for_staff = False  # the switch decides: off stays off, on is on
    if not on:
        with _watcher_state_lock:
            watcher_on.clear()
            if watcher_busy:
                _watcher_stop_reason = "off"  # stop at once and touch nothing, like staff input; the wager is tried again on resume
                abort_event.set()
        print(f"[*] Watcher OFF ({why}).")
        refresh_watcher_hud("Watcher off. Press ` to switch it on.")
        return
    if watcher_on.is_set():
        refresh_watcher_hud()
        return
    STATUS_HUD.snap_home(timeout=0)  # dragged away: back to its corner, clear of what the watcher reads
    _watcher_resume_at = time.time() + WATCHER_RESUME_SETTLE_SECS
    watcher_on.set()
    print(f"[*] Watcher ON ({why}){' (TEST MODE)' if test_mode_on.is_set() else ''}. "
          f"Looking at Betty in {WATCHER_RESUME_SETTLE_SECS:.0f}s...")
    refresh_watcher_hud(f"Watcher on. Looking at Betty in {WATCHER_RESUME_SETTLE_SECS:.0f}s...")


def toggle_watcher():
    set_watcher(not watcher_on.is_set())


def set_test_mode(on: bool):
    """Test mode (stops just before placing) or live (places checked wagers), from Shift+` or the launcher."""
    if on:
        test_mode_on.set()
        print("[*] TEST MODE ON: wagers stop just before placing.")
    else:
        test_mode_on.clear()
        print("[!] TEST MODE OFF - LIVE: checked wagers will be PLACED (F12). Shift+` to go back to test mode.")
    refresh_watcher_hud("Test mode on: stops before placing." if on
                        else "LIVE: checked wagers will be PLACED (F12). Shift+` = back to test mode.")


def toggle_test_mode():
    set_test_mode(not test_mode_on.is_set())


def on_staff_input(kind: str):
    """
    A person used the till ("key", "click" or "move", never this program's own input). Every kind counts as activity
    for the auto-resume; a key or click also pauses the watcher, unless staff input is expected (a prompt is open).
    Called inside the input hooks, so it only sets flags: the message goes out on another thread. Windows silently
    removes a hook that is slow to return, and the watcher would then type while staff use the till (review R7).
    """
    global _watcher_stop_reason, _paused_for_staff, _last_staff_activity
    _last_staff_activity = time.time()
    if kind == "move":  # every mouse movement comes here: no lock for it
        return
    with _watcher_state_lock:
        if not watcher_on.is_set() or _staff_input_expected > 0:
            return
        watcher_on.clear()
        _paused_for_staff = True
        if watcher_busy:
            _watcher_stop_reason = "staff"  # stop at once and touch nothing: staff have the terminal
            abort_event.set()
    threading.Thread(target=_announce_staff_pause, args=(kind,), daemon=True).start()


def _announce_staff_pause(kind: str):
    print(f"[*] Staff used the till ({kind}): watcher paused. It resumes after {STAFF_IDLE_RESUME_SECS}s with no activity, or press `.")
    refresh_watcher_hud(f"Staff using the till: paused. Resumes after {STAFF_IDLE_RESUME_SECS}s with no activity (or press `).")


class HumanInputMonitor:
    """
    Low-level Windows keyboard and mouse hooks that report key presses and clicks made by a person. Input injected by
    this program (pyautogui, keyboard replays) carries the INJECTED flag and is ignored, as are the watcher's own keys
    (`, Shift, Esc) and clicks on the HUD.
    """
    WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
    KEY_DOWN_MSGS = {0x0100, 0x0104}                      # WM_KEYDOWN, WM_SYSKEYDOWN
    CLICK_MSGS = {0x0201, 0x0204, 0x0207, 0x020A, 0x020B}  # left/right/middle down, wheel, X button
    WM_MOUSEMOVE = 0x0200
    LLKHF_INJECTED, LLMHF_INJECTED = 0x10, 0x01
    OWN_SCAN_CODES = {0x29, 0x2A, 0x36, 0x01}               # backtick, left/right Shift, Esc
    VK_ESCAPE = 0x1B

    def __init__(self, callback):
        import ctypes.wintypes as wt
        self.callback = callback
        self._wt = wt

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                        ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        class MSLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("pt", wt.POINT), ("mouseData", wt.DWORD), ("flags", wt.DWORD),
                        ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        self.KBD, self.MS = KBDLLHOOKSTRUCT, MSLLHOOKSTRUCT
        self.HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)
        self.user32 = ctypes.windll.user32
        self.user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
        self.user32.CallNextHookEx.restype = ctypes.c_ssize_t
        self.user32.SetWindowsHookExW.argtypes = [ctypes.c_int, self.HOOKPROC, wt.HINSTANCE, wt.DWORD]
        self.user32.SetWindowsHookExW.restype = wt.HHOOK
        self._kbd_proc = self.HOOKPROC(self._on_key)
        self._mouse_proc = self.HOOKPROC(self._on_mouse)

    def _on_key(self, code, wparam, lparam):
        if code == 0 and wparam in self.KEY_DOWN_MSGS:
            k = ctypes.cast(lparam, ctypes.POINTER(self.KBD)).contents
            if not (k.flags & self.LLKHF_INJECTED):
                if k.vkCode == self.VK_ESCAPE:
                    trigger_abort()  # a person's Esc; the program's own Esc presses are injected and never get here
                elif k.scanCode not in self.OWN_SCAN_CODES:
                    self.callback("key")
        return self.user32.CallNextHookEx(None, code, wparam, lparam)

    def _on_mouse(self, code, wparam, lparam):
        if code == 0 and (wparam in self.CLICK_MSGS or wparam == self.WM_MOUSEMOVE):
            m = ctypes.cast(lparam, ctypes.POINTER(self.MS)).contents
            if not (m.flags & self.LLMHF_INJECTED):
                if wparam == self.WM_MOUSEMOVE:
                    self.callback("move")  # activity only: keeps the auto-resume waiting while someone is at the till
                elif not STATUS_HUD.contains(m.pt.x, m.pt.y):
                    self.callback("click")
        return self.user32.CallNextHookEx(None, code, wparam, lparam)

    def _run(self):
        hooks = (self.user32.SetWindowsHookExW(self.WH_KEYBOARD_LL, self._kbd_proc, None, 0),
                 self.user32.SetWindowsHookExW(self.WH_MOUSE_LL, self._mouse_proc, None, 0))
        if not all(hooks):  # without them staff key presses and clicks aren't seen (review R7)
            notify("Staff detector didn't start: the watcher can't tell when staff use the till. Don't use the till "
                   "while the watcher is on, and restart Betty Companion.", is_error=True, sound=True)
        msg = self._wt.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()


# --- 6a. VIEW WAGERS: READING A WAGER (1366x768) ---
VIEW_WAGERS_BTN = (574, 241)           # Home: View Wagers
VW_QUEUE_FIRST_BOX = (148, 156, 122, 30)  # "Unedited (Exc.Fao)": first wager number box; further boxes every 35px
VW_QUEUE_PITCH = 35
VW_QUEUE_MAX = 8
VW_WAGER_NUMBER_BOX = (292, 562, 120, 46)  # loaded wager number, white on blue
VW_TIMESTAMPS_BOX = (418, 546, 100, 76)    # upper = struck, lower = scanned/edited
VW_SLIP_SUMMARY_BOX = (904, 486, 452, 140)  # grey panel: "1) Singles... Payment: £7.50."
VW_MARK_FAO_BTN = (525, 709)               # Mark bet fao Manager (no confirmation box)
_DIGITS_CFG = '--psm 7 -c tessedit_char_whitelist=0123456789.'


def _ocr_box(img: Any, box: tuple, config: str, scale: int = 3, invert: bool = False) -> str:
    x, y, w, h = box
    crop = img.crop((x, y, x + w, y + h)).resize((w * scale, h * scale))
    if invert:
        crop = ImageOps.invert(crop.convert('RGB'))
    try:
        return pytesseract.image_to_string(crop, config=config).strip()
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return ""


def normalise_wager_number(text: str) -> str | None:
    """'009.2445201' or '9.2445201' -> '9.2445201'; None when it doesn't read as a wager number."""
    m = re.search(r'(\d{1,4})\.(\d{7})', text or '')
    return f"{int(m.group(1))}.{m.group(2)}" if m else None


def read_unedited_queue(img: Any) -> list[str]:
    """Wager numbers listed under "Unedited (Exc.Fao)", top first: light blue, yellow or green (clicked) boxes;
    white = no box = end of the list."""
    arr = np.array(img.convert('RGB'))
    numbers = []
    for i in range(VW_QUEUE_MAX):
        x, y, w, h = VW_QUEUE_FIRST_BOX
        box = (x, y + i * VW_QUEUE_PITCH, w, h)
        if _colour_share(arr, (box[0] + 2, box[1] + 1, w - 4, 26), QUEUE_UNEDITED_RGBS + [QUEUE_SELECTED_RGB]) < 0.3:
            break
        number = normalise_wager_number(_ocr_box(img, box, _DIGITS_CFG))
        if not number:
            break
        numbers.append(number)
    return numbers


def read_wager_details(img: Any) -> dict:
    """The loaded wager on View Wagers: number, struck time (upper timestamp) and Payment in pence (None if unread)."""
    number = normalise_wager_number(_ocr_box(img, VW_WAGER_NUMBER_BOX, _DIGITS_CFG, invert=True))
    stamps = re.findall(r'(\d{1,2}):(\d{2}):(\d{2})', _ocr_box(img, VW_TIMESTAMPS_BOX, '--psm 6'))
    struck = f"{int(stamps[0][0]):02d}:{stamps[0][1]}" if stamps else None
    summary = without_thousands_commas(_ocr_box(img, VW_SLIP_SUMMARY_BOX, '--psm 6', scale=2))
    pay = re.search(r'Payment:\s*\D{0,2}\s*(\d+)\.(\d{2})', summary)
    return {'number': number, 'struck_time': struck,
            'struck_clock': ":".join(stamps[0]) if stamps else None,
            'payment_pence': int(pay.group(1)) * 100 + int(pay.group(2)) if pay else None,
            'summary': summary}


# --- 6b. NAVIGATION: expect -> act -> wait_for, never blind ---
class WatcherStop(Exception):
    """The current watcher action must stop (Esc, watcher switched off, staff using the terminal)."""


class NavError(Exception):
    """Betty did not reach the screen expected: recover (back out to Home) and never carry on blind."""


NAV_TIMEOUT = 4.0     # longest wait for Betty to change screen after one key press or click
_nav_recovering = False  # backing out after a stop: keys are allowed although the watcher is stopping
_home_unreachable = False  # the last go_home() ended away from Home: the watcher stops instead of trying again
ESC_UNCHANGED_LIMIT = 2  # Esc presses in a row that leave Betty on the same screen before go_home gives up


class HomeUnreachable(Exception):
    """go_home() could not get Betty back to Home: staff must look, the watcher never presses on."""


def _check_stop():
    if abort_event.is_set() and not _nav_recovering:
        raise WatcherStop()


class PlacingRefused(Exception):
    """An attempt to place a bet outside commit_wager() or in test mode. Never caught as a normal failure."""


_placing = False  # True only while commit_wager() is pressing F12


# Navigation keys sent as real extended keys (pyautogui sends them without the flag, like their numpad twins)
EXTENDED_KEYS = {'end': (0x23, 0x4F), 'home': (0x24, 0x47), 'pageup': (0x21, 0x49), 'pagedown': (0x22, 0x51),
                 'left': (0x25, 0x4B), 'up': (0x26, 0x48), 'right': (0x27, 0x4D), 'down': (0x28, 0x50)}


def betty_press(key: str):
    """One key to Betty, from the watcher. Never F3-F7 (they jump out of the bet edit) and never '.'.
    F12 (Place Bet) only from inside commit_wager(), and never in test mode."""
    if key in ('f3', 'f4', 'f5', 'f6', 'f7', '.'):
        raise NavError(f"refused to press '{key}' (forbidden while editing)")
    if key == 'f12' and (not _placing or test_mode_on.is_set()):
        raise PlacingRefused("F12 (Place Bet) refused: only commit_wager() may place, and never in test mode")
    _check_stop()
    _send_key(key)


def _send_key(key: str):
    if key in EXTENDED_KEYS:
        vk, scan = EXTENDED_KEYS[key]
        ctypes.windll.user32.keybd_event(vk, scan, 0x1, 0)        # KEYEVENTF_EXTENDEDKEY
        ctypes.windll.user32.keybd_event(vk, scan, 0x1 | 0x2, 0)  # ... | KEYEVENTF_KEYUP
    else:
        pyautogui.press(key)


def betty_click(x: int, y: int):
    _check_stop()
    click_betty_cell(x, y)


def wait_for_screen(targets: set, timeout: float = NAV_TIMEOUT) -> str:
    """Poll the screen until it is one of `targets` (returned) or `timeout` passes (last screen seen returned)."""
    t0 = time.time()
    screen = SCREEN_UNKNOWN
    while True:
        _check_stop()
        screen = detect_screen()
        if screen in targets or time.time() - t0 >= timeout:
            return screen
        time.sleep(0.02)


def expect_screen(targets: set, timeout: float = NAV_TIMEOUT, doing: str = "") -> str:
    """
    Waits for one of `targets`. A screen the program can't recognise (UNKNOWN) no longer stops it (user's decision,
    21 Oct): it carries on and the read-backs (betslip lines, bet lines, total vs Payment) check the result. A screen
    it recognises as a DIFFERENT one still stops it: Betty really is somewhere else.
    """
    screen = wait_for_screen(targets, timeout)
    if screen == SCREEN_UNKNOWN:
        print(f"[!] {doing or 'waiting'}: screen not recognised (expected {'/'.join(sorted(targets))}); carrying on.")
        return screen
    if screen not in targets:
        raise NavError(f"{doing or 'waiting'}: expected {'/'.join(sorted(targets))}, Betty shows {screen}")
    return screen


BUTTON_YELLOW = (255, 255, 128)


def find_buttons(img: Any, region: tuple, min_w: int = 30, min_h: int = 20) -> list[tuple[str, tuple[int, int]]]:
    """
    Betty's yellow buttons inside `region`: each solid yellow rectangle is found by colour, then its own text is read.
    Returns [(letters lower-case, centre)], so a button is clicked by what it says, never by a fixed position.
    """
    x0, y0, w, h = region
    rgb = img.convert('RGB')
    arr = np.array(rgb)[y0:y0 + h, x0:x0 + w, :3].astype(int)
    mask = np.max(np.abs(arr - np.array(BUTTON_YELLOW)), axis=2) <= 40
    taken = np.zeros_like(mask)
    rects = []
    for y in range(mask.shape[0]):
        for x in np.flatnonzero(mask[y] & ~taken[y]):
            if taken[y, x]:
                continue
            xe = x
            while xe < mask.shape[1] and mask[y, xe]:
                xe += 1
            ye = y
            while ye < mask.shape[0] and mask[ye, x]:
                ye += 1
            cx, cy = x0 + (x + xe) // 2, y0 + (y + ye) // 2
            inside = any(rx <= cx < rx + rw and ry <= cy < ry + rh for rx, ry, rw, rh in rects)  # shaded edge
            if xe - x >= min_w and ye - y >= min_h and not inside:
                rects.append((x0 + int(x), y0 + y, int(xe - x), ye - y))
                taken[y:ye, x:xe] = True
            else:
                taken[y, x:xe] = True
    buttons = []
    gray = rgb.convert('L')
    for bx, by, bw, bh in rects:
        crop = gray.crop((bx + 2, by + 2, bx + bw - 2, by + bh - 2)).resize(((bw - 4) * 3, (bh - 4) * 3))
        crop = crop.point(lambda v: 0 if v < 140 else 255)
        try:
            text = pytesseract.image_to_string(crop, config='--psm 6')
        except Exception:
            text = ""
        buttons.append((re.sub(r'[^a-z]', '', text.lower()), (bx + bw // 2, by + bh // 2)))
    return buttons


def find_button(img: Any, label: str, region: tuple) -> tuple[int, int] | None:
    """Centre of the one yellow button in `region` whose text starts with `label`; None if none or ambiguous."""
    want = re.sub(r'[^a-z]', '', label.lower())
    hits = [centre for text, centre in find_buttons(img, region) if text.startswith(want)]
    return hits[0] if len(hits) == 1 else None


# Pop-ups met while backing out, and the button that leaves each one without committing anything
MODAL_BACK_OUT = {  # (button, the pop-up's box)
    MODAL_PAYMENT_MISMATCH: ("No", (345, 291, 675, 250)),
    MODAL_CONFIRM_STAKE: ("Cancel", (88, 177, 510, 370)),
    MODAL_PRICE: ("Cancel", (401, 289, 620, 340)),
    MODAL_LATE_SELECTION: ("No", (345, 291, 675, 250)),
}


def go_home(max_steps: int = 8) -> bool:
    """
    The safe reset: Esc (or the backing-out button of a pop-up) until Betty shows Home, checking after every step.
    Returns True on Home. Never clicks blind: a pop-up button is clicked only where its label was read. When Esc leaves
    Betty on the same screen ESC_UNCHANGED_LIMIT times, Betty is given the keyboard for one more; then it stops
    (30 Oct, 15:33: 24 Esc on the runner list changed nothing). Sets _home_unreachable.
    """
    global _nav_recovering, _home_unreachable
    _nav_recovering = True
    try:
        unchanged = 0  # Esc presses in a row that left Betty on the same (recognised) screen
        for _ in range(max_steps):
            screen = detect_screen()
            if screen == SCREEN_UNKNOWN:  # often Betty mid-redraw: let it settle before pressing anything
                screen = wait_for_screen(ALL_SCREENS - {SCREEN_UNKNOWN}, timeout=1.5)
            if screen == SCREEN_HOME:
                _home_unreachable = False
                return True
            if screen in MODAL_BACK_OUT:
                label, region = MODAL_BACK_OUT[screen]
                spot = find_button(pyautogui.screenshot(), label, region)
                if not spot:
                    print(f"[-] Backing out: '{label}' not found on {screen}; not clicking blind.")
                    _home_unreachable = True
                    return False
                print(f"[*] Backing out of {screen}: '{label}'")
                betty_click(*spot)
            else:
                if unchanged > ESC_UNCHANGED_LIMIT:
                    print(f"[-] Backing out: Esc does nothing on {screen}; stopping.")
                    break
                if unchanged == ESC_UNCHANGED_LIMIT:
                    print(f"[*] Esc did nothing on {screen} twice: giving Betty the keyboard before one more.")
                    focus_betty()
                print(f"[*] Backing out from {screen}: Esc")
                betty_press('esc')
            after = wait_for_screen({s for s in ALL_SCREENS if s != screen}, timeout=2.0)
            stuck = after == screen and screen != SCREEN_UNKNOWN and screen not in MODAL_BACK_OUT
            unchanged = unchanged + 1 if stuck else 0
        home = detect_screen() == SCREEN_HOME
        _home_unreachable = not home
        return home
    finally:
        _nav_recovering = False


def open_view_wagers() -> str:
    """From Home or View Wagers to View Wagers (the status panel back in its corner first)."""
    STATUS_HUD.snap_home()
    screen = detect_screen()
    if screen == SCREEN_VIEW_WAGERS:
        return screen
    if screen not in (SCREEN_HOME, SCREEN_UNKNOWN):
        raise NavError(f"open View Wagers: expected Home, Betty shows {screen}")
    betty_click(*VIEW_WAGERS_BTN)
    return expect_screen({SCREEN_VIEW_WAGERS}, doing="open View Wagers")


def load_wager(row: int, number: str) -> dict:
    """Click the wager at `row` of the unedited list and confirm Betty loaded it (its number in the blue box)."""
    STATUS_HUD.snap_home()  # dragged over the summary panel it hides Payment (9.2448382, 23 Oct)
    current_q = read_unedited_queue(pyautogui.screenshot())
    if number in current_q:
        row = current_q.index(number)
    elif current_q:  # the list was read and the wager has left it (staff took it): its old row is another wager
        raise NavError(f"wager {number} is no longer in the unedited list")
    x, y, w, h = VW_QUEUE_FIRST_BOX
    print(f"[*] Clicking wager {number} (row {row + 1} of the unedited list); waiting for it to load...")
    betty_click(x + w // 2, y + h // 2 + row * VW_QUEUE_PITCH)
    t0, last_read = time.time(), None
    while time.time() - t0 < NAV_TIMEOUT:
        _check_stop()
        img = pyautogui.screenshot()
        details = read_wager_details(img)
        print(f"    blue box reads {details['number']!r}, struck {details['struck_clock']!r}, "
              f"Payment {details['payment_pence']!r}")
        # Taken only when two reads in a row agree: Betty draws the number before the struck time and Payment, and
        # 9.2453984 (27 Oct) was read with the wager shown before it (12:49:13, £10.00 for 11:03:28, £6.20)
        read = (details['number'], details['struck_clock'], details['payment_pence'])
        if details['number'] == number and details['struck_time'] and details['payment_pence'] is not None:
            if read == last_read:
                return details
            time.sleep(0.15)
        else:
            time.sleep(0.05)
        last_read = read
    last = read_wager_details(pyautogui.screenshot())
    if last['number'] == number:
        if (last['number'], last['struck_clock'], last['payment_pence']) != last_read:
            # Not read the same twice in a row: the struck time and Payment may still be the wager shown before, so
            # they count as unread and the caller sends it to staff (review B4, 28 Oct: one read was taken here)
            print(f"[!] Wager {number}: struck time / Payment not read the same twice "
                  f"({last['struck_clock']!r}, {last['payment_pence']!r}); not taken.")
            last.update(struck_time=None, struck_clock=None, payment_pence=None)
        return last  # loaded, but struck time / Payment unread or unconfirmed: the caller sends it to staff
    raise NavError(f"wager {number} did not load (blue box shows {last['number']})")


class SlipNotShowing(NavError):
    """Betty opened the bet without showing the slip (a Betty bug): Esc and open the wager again."""


SLIP_PAGE_BOX = (500, 120, 330, 440)  # inside the slip panel: a white page when the slip shows, plain cream when not


def slip_showing(img: Any = None) -> bool:
    """Betty shows the customer's slip as a white page; when it fails to, the panel is plain cream (0.85-0.98 white
    on every race-entry screenshot with a slip, 0.0 without)."""
    if img is None:
        img = pyautogui.screenshot()
    return _colour_share(np.array(img.convert('RGB')), SLIP_PAGE_BOX, (255, 255, 255), 12) >= 0.5


def open_race_entry() -> str:
    """
    From the loaded wager on View Wagers: End (Edit Empty Bet), '1' past the events screen to race entry, then '/'
    for the time box. The same on every till (user, 28 Oct): the cashiers' tills don't take '/' on the events screen.
    '1' is pressed again only while Betty still shows the events screen (it can be missed while the screen draws).
    """
    print(f"[*] Pressing End (Edit Empty Bet) on {detect_screen()}...")
    betty_press('end')
    screen = expect_screen({SCREEN_EVENT_MENU, SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, SCREEN_RACE_ENTRY_BROKEN},
                           doing="Edit Empty Bet (End)")
    print(f"[*] After End: {screen}")
    if screen in (SCREEN_EVENT_MENU, SCREEN_UNKNOWN):  # End always opens the event menu
        entry = {SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, SCREEN_RACE_ENTRY_BROKEN}
        for attempt in range(1, 4):
            betty_press('1')
            screen = wait_for_screen(entry | {SCREEN_EVENT_MENU}, timeout=0.6)
            screen = wait_for_screen(entry, timeout=1.5) if screen == SCREEN_EVENT_MENU else screen
            print(f"[*] After '1' ({attempt}): {screen}")
            if screen != SCREEN_EVENT_MENU:  # pressed again only while Betty still shows the events screen
                break
        if screen == SCREEN_EVENT_MENU:
            raise NavError("race entry ('1'): Betty still shows the events screen after 3 presses")
    if screen == SCREEN_RACE_ENTRY_BROKEN:
        raise SlipNotShowing("Betty opened the bet in its broken state (no slip image)")
    if screen == SCREEN_RACE_ENTRY:
        betty_press('/')  # '/' toggles the time box: pressed once, then checked
        screen = expect_screen({SCREEN_RACE_ENTRY_READY}, doing="time box ('/')")
    return screen


VW_UNEDITED_HEADER = (148, 100, 130, 50)  # "Unedited (Exc.Fao)", or "Unedited Fao Only" when the FAO list is shown


def unedited_list_is_fao_only(img: Any) -> bool:
    """View Wagers is showing the 'Unedited Fao Only' list (every wager on it is already FAO), not '(Exc.Fao)'."""
    letters = re.sub(r'[^a-z]', '', _ocr_box(img, VW_UNEDITED_HEADER, '--psm 6').lower())
    return 'faoonly' in letters or ('only' in letters and 'exc' not in letters)


def wager_gone_from_list(number: str) -> bool:
    """The wager has left the unedited list, seen ON View Wagers: any other screen reads as an empty list, which said
    'gone' while Betty showed something else."""
    img = pyautogui.screenshot()
    return detect_screen(img) == SCREEN_VIEW_WAGERS and number not in read_unedited_queue(img)


VW_FAO_MANAGER_AREA = (905, 200, 455, 200)  # the wager's slip panel, where Betty writes FAO MANAGER (x ~1015-1250, y ~290-320)
FAO_MAGENTA = (255, 0, 255)                # its colour; a guaranteed price is purple (128, 0, 128), never this
FAO_CONFIRM_SECS = 3.0


def shows_fao_manager(img: Any) -> bool:
    """View Wagers shows the loaded wager marked FAO: the large magenta FAO MANAGER on its slip panel (user's
    screenshot, 28 Oct). Colour alone: the letters cover ~2% of the area, nothing else there is magenta."""
    return _colour_share(np.array(img.convert('RGB')), VW_FAO_MANAGER_AREA, FAO_MAGENTA, tol=60) >= 0.005


def mark_wager_fao(number: str) -> str:
    """
    Send a wager to the manager: Home -> View Wagers -> click it -> Mark bet fao Manager -> FAO MANAGER shows on it.
    'marked'; 'already' when View Wagers shows the 'Unedited Fao Only' list, whose wagers are FAO already (clicking
    again does nothing: 9.2448529, 23 Oct); '' when it could not be done.
    """
    if not go_home():
        return ''
    open_view_wagers()
    img = pyautogui.screenshot()
    if unedited_list_is_fao_only(img):
        print(f"[*] FAO: Betty is showing the 'Unedited Fao Only' list, so wager {number} is FAO already: nothing clicked.")
        return 'already'
    queue = read_unedited_queue(img)
    if number not in queue:
        print(f"[-] FAO: wager {number} is not in the unedited list.")
        return ''
    load_wager(queue.index(number), number)
    betty_click(*VW_MARK_FAO_BTN)
    # Betty writes FAO MANAGER on the wager's slip panel at once; the wager leaves the unedited list only some time
    # later. Waiting for that reported every FAO as failed (9.2455944 and every one before it, 28 Oct; user)
    t0 = time.time()
    while time.time() - t0 < FAO_CONFIRM_SECS:
        if shows_fao_manager(pyautogui.screenshot()):
            print(f"[+] FAO: wager {number} shows FAO MANAGER.")
            return 'marked'
        time.sleep(0.1)
    print(f"[-] FAO: Mark bet fao Manager clicked for wager {number}, but FAO MANAGER didn't show.")
    return ''


ALL_SCREENS = {SCREEN_HOME, SCREEN_VIEW_WAGERS, SCREEN_EVENT_MENU, SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY,
               SCREEN_RACE_ENTRY_EXHAUSTED, SCREEN_RACE_ENTRY_BROKEN, SCREEN_RACE_LIST, SCREEN_REUSE_PANEL,
               SCREEN_BET_AND_STAKE, SCREEN_UNKNOWN, *MODAL_SIGNATURES}


# --- 6c. ENTERING A LOCKED WAGER INTO BETTY (test mode stops before F12) ---
# Every selection is already resolved against Betty's own card (meeting, time, cloth number), so entry is:
# '/' time box -> type the time -> runner list -> 'right' until the meeting is on top -> cloth number -> numpad +
# (price taken) or Enter (SP) -> answer the price / late-selection box -> read the betslip back before going on.
BETSLIP_BETS_ROWS = (488, 152)        # grey panel below it: "1) Treble. 2 Bets Each Way: ... @ 50p." "Payment: £1.00."
BETSLIP_CREAM = (255, 255, 208)


def betslip_left(img: Any) -> int:
    """Left edge of Betty's betslip panel, which moves: x ~878 on the race-entry screens, ~904 on Choose Bet and
    Stake / View Wagers. Found as the first column from which the panel's cream runs on unbroken."""
    arr = np.array(img.convert('RGB'))
    lefts = []
    # Rows the selection lines never reach (a line at y=200 once hid the edge with 3 selections). y=78, not 74: on
    # race entry y=74 is still the cyan header, so a price box over y=472 left no edge and lines read from x=906 (0).
    for y in (78, 472):
        cream = np.max(np.abs(arr[y, :, :3].astype(int) - np.array(BETSLIP_CREAM)), axis=1) <= 12
        lefts += [x + 2 for x in range(868, 912) if cream[x:x + 20].all()][:1]
    return min(lefts) if lefts else 906


def _betslip_box(img: Any, rows: tuple) -> tuple:
    left = betslip_left(img)
    return (left, rows[0], 1356 - left, rows[1])
RACE_LIST_ROW = (3, 2, 397, 33)               # first row of the runner list ("Worc 1:10 | 6. Reinado | 12-1")
RACE_LIST_PITCH = 35
F8_EACH_WAY_BOX = (152, 649, 140, 30)
F8_ROW_GREEN = (0, 255, 64)
MAX_MEETING_STEPS = 12   # 'right' presses before giving up on a meeting at the typed time
MEETING_REREAD_SECS = 1.5  # an unread top meeting is read again for up to this long before 'right' is pressed

# Bet types the program can enter: canonical type -> (Betty shortcut or None, Betty's full bet-list label, letters
# and digits only). Shortcuts are the user's (s d b q l j y o f r c i); anything else is found in the list by its
# name (PgDn pages; page order changes with the selections). Labels are the whole names from the user's screenshots
# of every list page (scratch/betty_screens/26_bet_list_full_p1-8.png), so no type needs a 'starts with' match:
# that let Lucky 15 match 'Lucky 15 Sport'.
ENTRY_BET_TYPES = {
    'single': ('s', 'singles'), 'double': ('d', 'doubles'), 'treble': ('b', 'trebles'),
    'accumulator': ('q', 'acconallselns'), 'yankee': ('y', 'yankee'), 'patent': ('o', 'patentortwist'),
    'lucky 15': ('l', 'lucky15'), 'lucky 31': ('j', 'lucky31'), 'lucky 63': (None, 'lucky63'),
    'trixie': (None, 'trixie'), 'canadian': (None, 'canadian'), 'heinz': (None, 'heinz'),
    'super heinz': (None, 'superheinz'), 'goliath': (None, 'goliath'),
    'straight forecast': ('f', 'straightforecasts'), 'reversed forecast': ('r', 'reversedforecasts'),
    'combination forecast': ('c', 'combinationfcasts'), 'tricast': ('i', 'tricasts'),
    'combination tricast': (None, 'combinationtricasts'),  # no shortcut (user): clicked in the list by name
}
# How Betty names each type on the betslip read-back ("1) Treble. ..."): letters that must appear
READBACK_NAMES = {'single': 'single', 'double': 'double', 'treble': 'treble', 'accumulator': 'fold', 'yankee': 'yankee',
                  'patent': 'patent', 'lucky 15': 'lucky15', 'lucky 31': 'lucky31', 'lucky 63': 'lucky63',
                  'trixie': 'trixie', 'canadian': 'canadian', 'heinz': 'heinz', 'super heinz': 'superheinz',
                  'goliath': 'goliath', 'straight forecast': 'forecast', 'reversed forecast': 'forecast',
                  'combination forecast': 'forecast', 'tricast': 'tricast', 'combination tricast': 'tricast'}


RULE_ROW_DARK_SHARE = 0.35  # a row this dark across the crop is a ruled line or a box edge, never text (text < 0.2)


def _ocr_bw(img: Any, box: tuple, config: str = '--psm 6', scale: int = 2, drop_rules: bool = False) -> str:
    """Dark text on a light panel: grey, threshold, enlarge, read. drop_rules: rows dark across the crop (a ruled line,
    Betty's dotted focus box) are blanked first; on 9.2452710 (26 Oct) the box's top edge on the crop's first row
    turned '8-1' into '81', the line didn't read and the betslip showed 2 selections instead of 3."""
    x, y, w, h = box
    grey = img.convert('L').crop((x, y, x + w, y + h))
    if drop_rules:
        arr = np.array(grey)
        arr[(arr < 150).mean(axis=1) > RULE_ROW_DARK_SHARE] = 255
        grey = Image.fromarray(arr)
    crop = grey.resize((w * scale, h * scale)).point(lambda v: 0 if v < 150 else 255)
    try:
        return pytesseract.image_to_string(crop, config=config).strip()
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return ""


def betty_meeting_abbrev(meeting: str) -> str:
    """Betty's 4-letter meeting label ("Worcester" -> "worc")."""
    return re.sub(r'[^a-z]', '', (meeting or '').lower())[:4]


def clock_12h(hhmm: str) -> str:
    """'13:10' -> '1:10', the way Betty prints race times."""
    m = re.match(r'(\d{1,2}):(\d{2})', hhmm or '')
    if not m:
        return ''
    h = int(m.group(1)) % 12 or 12
    return f"{h}:{m.group(2)}"


def entry_bet_type(bet: dict) -> str | None:
    """The canonical bet type to enter, or None when the program can't enter it (staff)."""
    n = len(bet.get('horses', []))
    t = normalize_bet_type(str(bet.get('bet_type', 'single')).strip().lower(), str(bet.get('description', '')),
                           selection_names(bet))
    m = re.match(r'perm (\d+)-folds', t)
    if m and int(m.group(1)) == n:
        t = 'accumulator'
    if t == 'accumulator' and n in (2, 3):
        t = 'double' if n == 2 else 'treble'
    # A plain 'F/C' / 'forecast' (9.2448384, 23 Oct: refused): straight on two runners in the order written,
    # combination on three or more, the same as calculate_bet_cost_pence costs it
    t = resolve_plain_forecast(t, n)
    return t if t in ENTRY_BET_TYPES else None


BETSLIP_LINE_TOP, BETSLIP_LINE_PITCH, BETSLIP_LINE_H = 83, 45.33, 18  # 18px tall covers the 12px main text without bleeding into the Jockey subline at y+21
BETSLIP_MAX_LINES = 8
# The name is lazy and may be empty: '(.+?)?' tried one character first, so a dog line '1. Sund 4:59 11-10 BP' read
# name '1', price '1-10' (9.2453098, 26 Oct)
BETSLIP_SELECTION_LINE = re.compile(
    r'^\W*(\d+|\?)\.\s*([A-Za-z\s]{3,7}?)\s+(\d{1,2}:\d{2})\s*(?:(?:(?:Trap\s*)?(\d+)\.\s*)|(?:Trap\s*(\d+)\s*))?(.*?)\s*[\W_]*(SP|NR|WD|VS|Evens|Evs|\d+\s*[-/]\s*\d+)(?:\s*(?:BP|EP))?[\W_]*$',
    re.IGNORECASE
)
GUARANTEED_PURPLE = (128, 0, 128)  # a guaranteed (BOG) price is purple; an ordinary one red (255, 0, 0)
# Price 'VS' = void selection: a late selection after "Yes" on Betty's late-selection box, drawn in black (9.2448544)
VOID_SELECTION = 'VS'
# Prices that mean the runner won't run or count: never guaranteed, fine for an SP selection ('WD' = withdrawn,
# shown instead of the price, 9.2448529)
NOT_RUNNING = ('NR', 'WD', VOID_SELECTION)


def read_betslip_selections(img: Any) -> list[dict]:
    """
    Selection lines on Betty's betslip panel, read one line at a time (the focused line's dotted box confused a
    whole-panel read): [{'n', 'meeting', 'time', 'number', 'name', 'price', 'guaranteed', 'y'}]. 'guaranteed' = the
    price is purple; 'y' = the line's centre, for clicking it.
    """
    left = betslip_left(img)
    arr = np.array(img.convert('RGB'))
    out = []
    for i in range(BETSLIP_MAX_LINES):
        top = int(BETSLIP_LINE_TOP + i * BETSLIP_LINE_PITCH)
        m = BETSLIP_SELECTION_LINE.match(_ocr_bw(img, (left, top, 1356 - left - 70, BETSLIP_LINE_H), '--psm 7', 3,
                                                 drop_rules=True).strip())
        if not m:
            break
        n_val = int(m.group(1)) if m.group(1).isdigit() else i + 1
        num = int(m.group(4) or m.group(5)) if (m.group(4) or m.group(5)) else None
        name = (m.group(6) or '').strip()
        # For greyhound trap lines (e.g. '1. Towc 5:06 SP'), number is on the subline below (e.g. 'Trap 4')
        if num is None:
            sub = _ocr_bw(img, (left, top + 18, 180, 16), '--psm 7', 3, drop_rules=True)
            m_trap = re.search(r'Trap\s*(\d+)', sub, re.IGNORECASE)
            if m_trap:
                num = int(m_trap.group(1))
                if not name:
                    name = f"Trap {num}"
        out.append({'n': n_val, 'meeting': m.group(2).replace(' ', '').lower(), 'time': m.group(3),
                    'number': num, 'name': name,
                    'price': m.group(7).replace(' ', ''),
                    'guaranteed': _colour_share(arr, (left + 250, top, 160, BETSLIP_LINE_H), GUARANTEED_PURPLE, 30) >= 0.02,
                    'y': top + BETSLIP_LINE_H // 2})
    return out


def read_betslip_bets(img: Any) -> dict:
    """The grey panel: {'bets': [{'n', 'name', 'count', 'each_way', 'stake_pence'}], 'payment_pence', 'text'}."""
    text = _ocr_bw(img, _betslip_box(img, BETSLIP_BETS_ROWS))
    flat = without_thousands_commas(" ".join(text.split()))
    bets = []
    chunks = re.split(r'(?=\b\d+\))', flat)
    for c in chunks:
        c = c.strip()
        if not c or not re.match(r'^\d+\)', c):
            continue
        m_active = re.match(
            r'^(\d+)\)\s*([A-Za-z0-9 \'+\-]+?)\.\s*(\d+)\s*Bets?(?:\s*:\s*\d+\s*[A-Za-z\']+)?\s*(Win Only|Each Way)?[^@]*@\s*(\S+)',
            c, re.I
        )
        if m_active:
            num = int(m_active.group(1))
            name = m_active.group(2).strip()
            count = int(m_active.group(3))
            ew = (m_active.group(4) or '').lower() == 'each way'
            stake_txt = m_active.group(5)
            pounds = re.search(r'(\d+)\.(\d{2})', stake_txt)
            pence = re.search(r'(\d+)\s*p', stake_txt, re.I)
            stake = int(pounds.group(1)) * 100 + int(pounds.group(2)) if pounds else (int(pence.group(1)) if pence else None)
            bets.append({'n': num, 'name': name, 'count': count, 'each_way': ew, 'stake_pence': stake})
            continue

        m_summary = re.match(
            r'^(\d+)\)\s*(?:[^\d]*(\d+\.\d{2})|(\d+)\s*p)\s*(Each Way|Win Only)?\s*([A-Za-z0-9 \'+\-]+?)\s*=',
            c, re.I
        )
        if m_summary:
            num = int(m_summary.group(1))
            stake = int(round(float(m_summary.group(2)) * 100)) if m_summary.group(2) else int(m_summary.group(3))
            ew = (m_summary.group(4) or '').lower() == 'each way'
            name = m_summary.group(5).strip()
            bets.append({'n': num, 'name': name, 'count': 1, 'each_way': ew, 'stake_pence': stake})
            continue

    total = re.search(r'Total Payment(?: On All\s*Wagers)?:\s*\D{0,2}\s*(\d+)\.(\d{2})', flat, re.I)
    pay = total or re.search(r'Payment:\s*\D{0,2}\s*(\d+)\.(\d{2})', flat)
    paid = re.search(r'Paid\s*\D{0,2}\s*(\d+)\.(\d{2})', flat)
    grand = read_slip_grand_total(img)
    return {'bets': bets,
            'payment_pence': grand if grand is not None else (int(pay.group(1)) * 100 + int(pay.group(2)) if pay else None),
            'paid_pence': int(paid.group(1)) * 100 + int(paid.group(2)) if paid else None, 'text': text}


BETTY_RED = (255, 0, 0)  # Betty's red text (the grand total; selection lines above the grey panel are red too)


def read_slip_grand_total(img: Any) -> int | None:
    """
    Betty's large red figure in the grey panel: the total of every betting slip on the wager (equal to 'Payment' with
    one slip). With several slips (F10) it is drawn over "Total Payment On All Wagers: £..", which then OCRs as noise,
    so only 'Payment' (the current slip) was read: 9.2448524 (£3 + £4 + £3) read £3.00 against £10 paid and went to
    staff (23 Oct). The figure is found wherever it is in the panel, as its biggest block of red, and only its red
    pixels are read, so the blue text under it drops out. None when there is no red figure (e.g. before a bet type
    is chosen) or it doesn't read as an amount.
    """
    left = betslip_left(img)
    x0, y0 = left, BETSLIP_BETS_ROWS[0]
    a = np.array(img.convert('RGB').crop((x0, y0, 1356, y0 + BETSLIP_BETS_ROWS[1]))).astype(int)
    red = np.max(np.abs(a - np.array(BETTY_RED)), axis=2) <= 75
    # Columns holding red, split into blocks wherever 20+ empty columns separate them; the figure is the biggest block
    cols = red.sum(axis=0)
    blocks, start, gap = [], None, 0
    for i, n in enumerate(list(cols) + [0] * 20):
        if n:
            start, gap = (i if start is None else start), 0
        elif start is not None:
            gap += 1
            if gap >= 20:
                blocks.append((start, i - gap + 1))
                start, gap = None, 0
    if not blocks:
        return None
    c0, c1 = max(blocks, key=lambda b: cols[b[0]:b[1]].sum())
    rows = np.nonzero(red[:, c0:c1].any(axis=1))[0]
    block = red[max(0, rows[0] - 4):rows[-1] + 5, max(0, c0 - 4):c1 + 4]
    if block.sum() < 200:  # a few red pixels are not the large figure
        return None
    h, w = block.shape
    mask = Image.fromarray(np.where(block, 0, 255).astype('uint8')).resize((w * 3, h * 3))
    try:
        text = pytesseract.image_to_string(mask, config='--psm 7 -c tessedit_char_whitelist=£0123456789.').strip()
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return None
    m = re.fullmatch(r'£?(\d{1,4})\.(\d{2})', text)
    return int(m.group(1)) * 100 + int(m.group(2)) if m else None


RACE_LIST_NAME_COL = (138, 172)  # x, width of the runner column ('Trap 1. Hollywell Orchid' / '01. North End Lady')


def race_list_is_dogs(img: Any) -> bool | None:
    """True when the runner list heading the screen is a greyhound race (its rows read 'Trap 1. ..'), False for a
    horse race ('01. ..'), None when its first rows can't be read."""
    kinds = set()
    for i in range(2):
        x, w = RACE_LIST_NAME_COL
        text = _ocr_bw(img, (x, RACE_LIST_ROW[1] + i * RACE_LIST_PITCH, w, RACE_LIST_ROW[3]), '--psm 7', 3).strip()
        if re.match(r'\W*trap\s*\d', text, re.I):
            kinds.add(True)
        elif re.match(r'\W*\d{1,2}\s*[.,]', text):
            kinds.add(False)
    return kinds.pop() if len(kinds) == 1 else None


RACE_LIST_ROWS = 17               # rows the runner list shows before its down arrow (scratch/betty_screens/36)
RACE_LIST_LABEL_COL = (3, 130)    # x, width of the 'Newc 2:31' column
RACE_LIST_PRICE_COL = (312, 88)   # x, width of the price column ('11-8' / 'NR', scratch/betty_screens/41)
RACE_LIST_ROW_NAME = re.compile(r'^\W*(?:(trap)\s*(\d{1,2})|(\d{1,2}))\s*[.,]\s*(.*)$', re.IGNORECASE)


def _race_list_column(img: Any, col: tuple) -> dict[int, str]:
    """One column of the runner list read in a single pass, by row: {row: text}. One OCR per column, not per row:
    17 rows x 2 columns read one at a time took several seconds on every 'right'."""
    x, w = col
    h, scale = RACE_LIST_ROWS * RACE_LIST_PITCH, 3
    crop = img.convert('L').crop((x, RACE_LIST_ROW[1], x + w, RACE_LIST_ROW[1] + h)).resize((w * scale, h * scale))
    try:
        d = pytesseract.image_to_data(crop.point(lambda v: 0 if v < 150 else 255), config='--psm 6',
                                      output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return {}
    rows: dict[int, list[str]] = {}
    for word, top, height in zip(d['text'], d['top'], d['height']):
        if word.strip():
            rows.setdefault(int((top + height / 2) / scale // RACE_LIST_PITCH), []).append(word.strip())
    return {r: " ".join(words) for r, words in rows.items()}


def race_list_rows(img: Any) -> list[dict]:
    """The runner rows showing in Betty's runner list, top first: [{'row', 'label', 'time', 'trap', 'number', 'name',
    'y'}]. 'trap' = a dog row ('Trap 4. Newinn Carole'); a horse row reads '04. Sleedagh'. 'y' = the row's centre."""
    labels, names = _race_list_column(img, RACE_LIST_LABEL_COL), _race_list_column(img, RACE_LIST_NAME_COL)
    out = []
    for r in sorted(set(labels) & set(names)):
        m_time = re.search(r'(\d{1,2})[:.](\d{2})', labels[r])
        m_name = RACE_LIST_ROW_NAME.match(names[r])
        cap = re.search(r'[A-Z][A-Za-z]{2,3}', labels[r])
        if not (m_time and m_name and cap):
            continue
        out.append({'row': r, 'label': cap.group(0).lower(), 'time': f"{int(m_time.group(1))}:{m_time.group(2)}",
                    'trap': bool(m_name.group(1)), 'number': int(m_name.group(2) or m_name.group(3)),
                    'name': m_name.group(4).strip(), 'y': RACE_LIST_ROW[1] + r * RACE_LIST_PITCH + RACE_LIST_ROW[3] // 2,
                    'virtual': bool(re.search(r'\(\s*v\s*\)', labels[r], re.I))})  # 'Mill 12:50(v)'
    return out


def find_runner_row(img: Any, horse: dict, candidates: list[str]) -> dict | None:
    """
    The selection's own row anywhere in the runner list, for a click (a click adds it to the betslip, user 27 Oct).
    Used only when horses and dogs share a label at the time: the Newcastle horses under the Newcastle dogs at 1:26
    (screenshot 41), where 'right' took both Newcastle lists off at once and typing 1-6 picks a trap (9.2453975,
    27 Oct). Every other race is brought to the top with 'right'. A row counts only when its meeting, time, kind
    (horse / dog), number and name all fit; None otherwise.
    """
    meeting, number = horse.get('meeting', ''), horse.get('number')
    want_time, want_dog = clock_12h(str(horse.get('time', ''))), is_dog_race(horse)
    if not meeting or not number or not want_time:
        return None
    for row in race_list_rows(img):
        if (row['time'] != want_time or row['number'] != int(number) or row['trap'] != want_dog
                or nearest_meeting_label(row['label'], candidates, prefer=meeting) != meeting):
            continue
        # Betty cuts long names at the column's edge ('A Bit Of Trud'): the name is compared over what shows
        shown, wanted = _letters(row['name']), _letters(horse.get('name'))
        if len(shown) >= 3 and name_similarity(shown, wanted[:len(shown)]) >= 0.75:
            return row
    return None


def nearest_meeting_label(word: str, candidates: list[str], prefer: str | None = None) -> str | None:
    """
    The meeting whose Betty label (first 4 letters) a runner-list label is: the nearest of every meeting racing then,
    only when it shares at least 3 of the 4 letters AND is at least one letter nearer than any other meeting. Close
    labels race together (Speedwell / Steepledowns, Greenacres / Greyville on 23 Oct), so a label equally near two
    meetings is no answer; nor is a label near none ('Stee' was once taken for Sheffield, 'shef', 2 of 4).
    """
    labels: dict[str, set[str]] = {}
    for c in candidates:
        labels.setdefault(betty_meeting_abbrev(c), set()).add(c)
    if not word or not labels:
        return None
    # letters apart, label length 4: 0 = identical; a label shorter on the screen ('San ') counts its missing letters
    ranked = sorted((_letters_off(word, lab), lab) for lab in labels)
    best_off, best_lab = ranked[0]
    next_off = ranked[1][0] if len(ranked) > 1 else 99
    if best_off > 1 or next_off - best_off < 1:
        return None
    group = labels[best_lab]
    if len(group) > 1:  # two meetings share the label (Doncaster horses and dogs): only the one wanted, checked by its rows
        return prefer if prefer in group else None
    return next(iter(group))


def top_meeting_in_race_list(img: Any, candidates: list[str], prefer: str | None = None) -> str | None:
    """Which of `candidates` (meetings racing at the typed time) heads the runner list, read from its first rows.
    None when the label isn't clearly one of them (`nearest_meeting_label`); a label two meetings share is `prefer`,
    the meeting wanted, whose rows the caller checks (horses or dogs)."""
    votes: dict[str, int] = {}
    for i in range(3):
        x, y, w, h = RACE_LIST_ROW
        text = _ocr_bw(img, (x, y + i * RACE_LIST_PITCH, 130, h), '--psm 7', scale=3)
        # Betty's label starts with a capital ('Shef 6:58'); the list's left border can read as a stray 'i' before it
        cap = re.search(r'[A-Z][A-Za-z]{2,3}', text)
        word = (cap.group(0) if cap else re.sub(r'[^A-Za-z]', '', text)).lower()[:4]
        if len(word) < 3:
            continue
        best = nearest_meeting_label(word, candidates, prefer)
        if best:
            votes[best] = votes.get(best, 0) + 1
    return max(votes, key=lambda k: votes[k]) if votes else None


# --- The runner list read by its contents: which race heads it, from the whole label column, the runners' cloth
# numbers and names, horses or dogs, and the '(v)' of a virtual race. The label alone wasn't enough on 31 Oct: the
# top label read 'wa' / 'bait' row by row where the column read 'mill' on all 9 rows (9.2459256, Millbank Bridge
# 12:50 virtuals), and 'East' read perfectly but was on no card (9.2459257, the virtual dogs' feed wasn't read).

def _feed_races_at(hhmm: str) -> dict[tuple, dict[int, str]]:
    """Every race on Betty's cards at this time and 12 hours from it: {(meeting, time, dogs): {cloth number: name}}."""
    times = _times_12h_apart(hhmm)
    races: dict[tuple, dict[int, str]] = {}
    for r in racecard_manager.get_runners() + greyhound_card.get_runners():
        if r.get('time_str') in times and r.get('number'):
            races.setdefault((r['meeting'], r['time_str'], is_dog_race(r)), {})[int(r['number'])] = r['name']
    return races


def _runners_of_race(rows: list[dict], race: dict[int, str]) -> int:
    """How many runner-list rows are the race's runners: its cloth number, and its name as far as Betty shows it."""
    n = 0
    for row in rows:
        name, shown = race.get(row['number']), _letters(row['name'])
        if name and len(shown) >= 3 and name_similarity(shown, _letters(name)[:len(shown)]) >= 0.75:
            n += 1
    return n


def runner_list_races(rows: list[dict]) -> list[list[dict]]:
    """The runner list's rows cut into races, top first. A race starts where the cloth numbers start again, the label
    changes by 2+ letters or the rows turn from horses to dogs (one misread letter doesn't start a race)."""
    races: list[list[dict]] = []
    for row in rows:
        last = races[-1][-1] if races else None
        if (last and row['number'] > last['number'] and row['trap'] == last['trap']
                and _letters_off(row['label'], last['label']) <= 1):
            races[-1].append(row)
        else:
            races.append([row])
    return races


def _common(values: list):
    """The value most of a race's rows read, when 2+ rows read it; None otherwise."""
    if not values:
        return None
    best = max(set(values), key=values.count)
    return best if values.count(best) >= 2 else None


def _race_is_wanted(block: list[dict], meeting: str, candidates: list[str], races: dict, want_dogs: bool,
                    want_virtual: bool) -> tuple[bool | None, tuple | None]:
    """
    Whether one race of the runner list is the wanted one, and the card race its runners are (None if unknown).
    True needs positive evidence: its runners are the wanted race's, or its label is the wanted meeting's. False needs
    positive evidence too: its runners are another race's, its label is 2+ letters off, or it is the other kind
    (dogs / horses) or virtual when the wanted race isn't. The runners and the label disagreeing is None.
    """
    fits = sorted(((_runners_of_race(block, race), key) for key, race in races.items()), reverse=True)
    card_race = (fits[0][1] if fits and fits[0][0] >= 2 and (len(fits) == 1 or fits[0][0] > fits[1][0]) else None)
    by_runners = None if card_race is None else card_race[0] == meeting
    label = _common([r['label'] for r in block])
    by_label = None
    if label:
        if nearest_meeting_label(label, candidates, prefer=meeting) == meeting:
            by_label = True
        elif _letters_off(label, betty_meeting_abbrev(meeting)) >= 2:
            by_label = False
    if by_runners is not None and by_label is not None and by_runners != by_label:
        return None, card_race
    if by_runners or by_label:
        return True, card_race
    if by_runners is False or by_label is False:
        return False, card_race
    if _common([r['trap'] for r in block]) not in (None, want_dogs):
        return False, card_race
    if not want_virtual and _common([r['virtual'] for r in block]):
        return False, card_race
    return None, card_race


def runner_list_top_by_content(img: Any, meeting: str, hhmm: str, candidates: list[str], want_dogs: bool,
                               want_virtual: bool = False) -> str | None:
    """
    The race heading Betty's runner list, read by its contents: `meeting` when it is the wanted race (or '<meeting>
    dogs' / '<meeting> horses' when it is the wanted label but the other kind), another meeting's name or a label off
    the card when it positively isn't, None when the rows can't say. Any race lower down that is the wanted one also
    says the top isn't. Never guesses the wanted race is on top: 'right' past it is what 9.2458229 lost.
    """
    rows = [r for r in race_list_rows(img) if r['time'] == clock_12h(hhmm)]
    if not rows or rows[0]['row'] > 1:  # the first rows unread: the top race isn't known
        return None
    blocks = runner_list_races(rows)
    races = _feed_races_at(hhmm)
    top, card_race = _race_is_wanted(blocks[0], meeting, candidates, races, want_dogs, want_virtual)
    if top is None and any(_race_is_wanted(b, meeting, candidates, races, want_dogs, want_virtual)[0]
                           for b in blocks[1:]):
        top = False
    if top is None:
        return None
    kind = _common([r['trap'] for r in blocks[0]])
    if top:
        return meeting if kind in (None, want_dogs) else f"{meeting} {'dogs' if kind else 'horses'}"
    if card_race:
        return card_race[0]
    label = _common([r['label'] for r in blocks[0]])
    named = label and nearest_meeting_label(label, candidates)
    return named or (f"'{label.title()}' (not on Betty's card)" if label else "another race")


def _top_reads_agree(by_label: str | None, by_rows: str | None, meeting: str) -> str | None:
    """The two reads of the top race together: either alone, or both when they agree on whether it is `meeting`."""
    if by_label is None or by_rows is None:
        return by_rows or by_label
    if (by_label == meeting) != (by_rows in (meeting, f"{meeting} dogs", f"{meeting} horses")):
        return None  # one says it's the wanted race and the other that it isn't: read again
    return by_rows

def _times_12h_apart(time_hhmm: str) -> set[str]:
    """The time and the time 12 hours from it: Betty's runner list is on a 12-hour clock."""
    m = re.match(r'(\d{1,2}):(\d{2})$', time_hhmm or '')
    times = {time_hhmm}
    if m:
        other = (int(m.group(1)) * 60 + int(m.group(2)) + 720) % 1440
        times.add(f"{other // 60:02d}:{other % 60:02d}")
    return times


def _meetings_at(time_hhmm: str) -> list[str]:
    """Horse and greyhound meetings racing at this time on Betty's cards, and 12 hours either side: Betty's runner
    list is on a 12-hour clock, so typing 6:58 also lists the 06:58 virtual Steepledowns race beside 18:58."""
    times = _times_12h_apart(time_hhmm)
    runners = racecard_manager.get_runners() + greyhound_card.get_runners()
    return sorted({r['meeting'] for r in runners if r.get('time_str') in times})


def _label_has_horses_and_dogs(meeting: str, time_hhmm: str) -> bool:
    """Whether horses and dogs both race under this meeting's Betty label at this time (Doncaster horses and
    Doncaster dogs): then only the runner list's own rows say which list Betty is showing."""
    times, label = _times_12h_apart(time_hhmm), betty_meeting_abbrev(meeting)

    def races_there(card) -> bool:
        return any(r.get('time_str') in times and betty_meeting_abbrev(r.get('meeting', '')) == label
                   for r in card.get_runners())
    return races_there(racecard_manager) and races_there(greyhound_card)


def _type_text(text: str):
    for ch in text:
        betty_press(ch)


PRICE_BOX_CLOSE_SECS = 0.8  # Enter or Override: the price box has this long to close
PRICE_BOX_FOCUS_SECS = 0.5  # after a betslip line is clicked: how long its price box may take to open


def _price_box_shows(open_: bool, timeout: float) -> bool:
    """Colour only (no OCR): whether the price box is open (`open_`), or closed, within `timeout` seconds."""
    t0 = time.time()
    while True:
        _check_stop()
        shows = _signals_pass(np.array(pyautogui.screenshot().convert('RGB')), MODAL_SIGNATURES[MODAL_PRICE]['colours'])
        if shows == open_:
            return True
        if time.time() - t0 > timeout:
            return False
        time.sleep(0.04)


def answer_price_box():
    """
    Betty's price check box: Enter takes the price when struck. A box with no price history has no 'Price when
    struck' button (only SP Only, Cancel and 'Override with entered price') and ignores Enter (user's screenshot 42,
    30 Oct: the program backed out of it); then 'Override with entered price' is clicked, found by its text. Still
    open: staff.
    """
    print("[*] Price check box: taking the price when struck (Enter).")
    betty_press('enter')
    if _price_box_shows(False, PRICE_BOX_CLOSE_SECS):
        return
    spot = find_button(pyautogui.screenshot(), "Override", MODAL_BACK_OUT[MODAL_PRICE][1])
    if not spot:
        raise WagerForStaff("the price check box stayed open after Enter, and its 'Override with entered price' "
                            "button wasn't found")
    print("[*] Price check box: Enter didn't close it (no price when struck): 'Override with entered price'.")
    betty_click(*spot)
    if not _price_box_shows(False, PRICE_BOX_CLOSE_SECS):
        raise WagerForStaff("the price check box stayed open after 'Override with entered price'")


def answer_entry_popups(max_rounds: int = 3):
    """After adding a runner: the price box -> price when struck, else Override (answer_price_box); a late selection
    -> Yes (void processing)."""
    for _ in range(max_rounds):
        screen = wait_for_screen(set(MODAL_SIGNATURES), timeout=0.4)
        if screen == MODAL_PRICE:
            answer_price_box()
        elif screen == MODAL_LATE_SELECTION:
            spot = find_button(pyautogui.screenshot(), "Yes", MODAL_BACK_OUT[MODAL_LATE_SELECTION][1])
            if not spot:
                raise NavError("late-selection box: 'Yes' not found")
            print("[*] Late selection: Yes (void selection processing).")
            betty_click(*spot)
        elif screen in (MODAL_PAYMENT_MISMATCH, MODAL_CONFIRM_STAKE):
            raise WagerForStaff(f"Betty asked about the payment while entering ({screen})")
        else:
            return


# --- Betty's race folders (the left panel of race entry): the favourite is entered there (user, 23 Oct) ---
# Layout from the user's screenshots (scratch/betty_screens/04, 09, 12, 37): the open folder's title, 3 meeting
# rows and 5 time rows with arrows to scroll them, the selections panel ('The Favourite' on top), and the other
# folders as buttons along the bottom ("Friday's SIS Horse Racing", ...), paged with Prev / Next.
FOLDER_TITLE_BOX = (5, 110, 212, 40)               # "Friday's SIS Greyhound Racing:" (yellow on red)
FOLDER_MEETING_ROW, FOLDER_TIME_ROW = (8, 150, 205, 33), (318, 81, 78, 33)
FOLDER_ROW_PITCH, FOLDER_MEETING_ROWS, FOLDER_TIME_ROWS = 35, 3, 5
FOLDER_MEETING_UP, FOLDER_MEETING_DOWN = (237, 134), (237, 226)
FOLDER_TIME_UP, FOLDER_TIME_DOWN = (419, 65), (419, 225)
FOLDER_FAVOURITE_ROW = (8, 341, 300, 32)           # 'The Favourite' / '0.The Favourite'
FOLDER_BUTTONS = ((85, 632, 140, 58), (232, 632, 140, 58), (379, 632, 140, 58), (85, 699, 140, 58), (232, 699, 140, 58))
FOLDER_NEXT = (485, 727)
FOLDER_SELECTED_GREEN = (0, 255, 64)
FOLDER_PAGES = 4                                   # pages of folder buttons tried (Next) before staff
FOLDER_SCROLL_STEPS = 25                           # arrow clicks per direction before a list counts as fully seen
# Which folder a race is in follows the feed it came from; the folder name is "<Today>'s " + this
FEED_FOLDERS = {'HGB00': 'SIS Horse Racing', 'DGB00': 'SIS Greyhound Racing', 'BFTRP': 'TRP Horses',
                'BFTV5': 'TRP Dogs 5'}


def _letters(text: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(text or '').lower())


def _box_centre(box: tuple) -> tuple[int, int]:
    return box[0] + box[2] // 2, box[1] + box[3] // 2


def folder_title(img: Any) -> str:
    """The open folder's name, letters and digits only ("fridayssisgreyhoundracing")."""
    return _letters(_ocr_box(img, FOLDER_TITLE_BOX, '--psm 6', invert=True))


# Betty names its folders in English whatever language Windows is in ('%A' would follow Windows; review R28)
ENGLISH_DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def betty_day_name() -> str:
    return ENGLISH_DAYS[time.localtime().tm_wday]


def open_race_folder(feed: str | None):
    """Opens today's folder holding a feed's races ("Friday's SIS Horse Racing" for HGB00), from the buttons along
    the bottom (paged with Next), and confirms it by the folder title."""
    if feed not in FEED_FOLDERS:
        raise WagerForStaff(f"Betty's folder for this race isn't known (feed {feed or 'unknown'})")
    want = _letters(f"{betty_day_name()}'s {FEED_FOLDERS[feed]}")
    for _ in range(FOLDER_PAGES):
        _check_stop()
        img = pyautogui.screenshot()
        if folder_title(img) == want:
            return
        for box in FOLDER_BUTTONS:
            if _letters(_ocr_bw(img, box, '--psm 6', 2)) == want:
                betty_click(*_box_centre(box))
                t0 = time.time()
                while time.time() - t0 < NAV_TIMEOUT:
                    if folder_title(pyautogui.screenshot()) == want:
                        return
                    time.sleep(0.1)
                raise WagerForStaff(f"Betty's '{FEED_FOLDERS[feed]}' folder didn't open")
        betty_click(*FOLDER_NEXT)  # the next page of folder buttons
        time.sleep(0.2)
    raise WagerForStaff(f"Betty's folder '{betty_day_name()}'s {FEED_FOLDERS[feed]}' wasn't found")


def pick_in_folder_list(first_row: tuple, n_rows: int, up: tuple, down: tuple, wanted: str, what: str):
    """Finds the row reading `wanted` (letters) in a folder list, scrolling down then up with its arrows until the
    rows stop changing, clicks it and confirms it turned green (selected)."""
    x, y, w, h = first_row
    for arrow in (down, up):
        last = None
        for _ in range(FOLDER_SCROLL_STEPS):
            _check_stop()
            img = pyautogui.screenshot()
            rows = [_letters(_ocr_bw(img, (x, y + i * FOLDER_ROW_PITCH, w, h), '--psm 7', 3)) for i in range(n_rows)]
            if wanted in rows:
                box = (x, y + rows.index(wanted) * FOLDER_ROW_PITCH, w, h)
                betty_click(*_box_centre(box))
                t0 = time.time()
                while time.time() - t0 < NAV_TIMEOUT:
                    arr = np.array(pyautogui.screenshot().convert('RGB'))
                    if _colour_share(arr, (box[0], box[1] + 2, box[2], box[3] - 4), FOLDER_SELECTED_GREEN, 60) >= 0.5:
                        return
                    time.sleep(0.08)
                raise WagerForStaff(f"{what} didn't select in Betty's folder")
            if rows == last:
                break  # the end of the list this way
            last = rows
            betty_click(*arrow)
            time.sleep(0.15)
    raise WagerForStaff(f"{what} isn't in Betty's folder")


def enter_favourite(horse: dict, already_on_slip: int):
    """
    The SP favourite of a race (a 'fav' written; Rule 1.8.4): Betty has no '/' route to it, so it goes through the
    race's folder (user, 23 Oct): open the folder, the meeting, the time, then 'The Favourite' (the top row of the
    selections; typing 0 also works there). Confirmed on the betslip like any selection.
    """
    meeting, hhmm = horse.get('meeting', ''), str(horse.get('time', ''))
    label = f"The Favourite {clock_12h(hhmm)} {meeting}"
    refresh_watcher_hud(f"Entering selection {already_on_slip + 1}: {label} (through Betty's folder)...")
    if detect_screen() not in (SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, SCREEN_UNKNOWN):
        raise WagerForStaff(f"not on race entry to open Betty's folder for {label}")
    open_race_folder(horse.get('feed'))
    pick_in_folder_list(FOLDER_MEETING_ROW, FOLDER_MEETING_ROWS, FOLDER_MEETING_UP, FOLDER_MEETING_DOWN,
                        _letters(meeting), f"meeting {meeting}")
    pick_in_folder_list(FOLDER_TIME_ROW, FOLDER_TIME_ROWS, FOLDER_TIME_UP, FOLDER_TIME_DOWN,
                        _letters(clock_12h(hhmm)), f"the {clock_12h(hhmm)} at {meeting}")
    if 'favourite' not in _letters(_ocr_bw(pyautogui.screenshot(), FOLDER_FAVOURITE_ROW, '--psm 7', 3)):
        raise WagerForStaff(f"'The Favourite' isn't showing for {label}")
    betty_click(*_box_centre(FOLDER_FAVOURITE_ROW))
    print(f"[*] Added {label} through Betty's folder.")
    answer_entry_popups()
    lines = _read_new_betslip_line(already_on_slip)
    if len(lines) != already_on_slip + 1:
        raise WagerForStaff(f"after adding {label} the betslip shows {len(lines)} selection(s), expected {already_on_slip + 1}")
    problems = betslip_line_problems(lines[-1], horse)
    if problems:
        raise WagerForStaff(f"betslip shows {', '.join(problems)} for {label}")
    got = lines[-1]
    print(f"[+] Betslip line {got['n']}: {got['meeting']} {got['time']} {got['name']} {got['price']} (checked)")


def is_dog_race(horse: dict) -> bool:
    """A greyhound race on Betty's runner list (rows 'Trap 1. ..'): a real dog race, or virtual dogs (Eastgreen),
    whose category is 'virtual' like the virtual horses'."""
    return horse.get('category') == 'greyhound' or bool(horse.get('dogs'))


def same_race_time(a: dict, b: dict) -> bool:
    """Whether two selections are on one runner list of Betty's: the same time on its 12-hour clock (typing 6:58 lists
    the 06:58 virtuals beside the 18:58 races). The favourite goes through the folders, never the list."""
    if a.get('favourite') or b.get('favourite'):
        return False
    ta, tb = clock_12h(str(a.get('time') or '')), clock_12h(str(b.get('time') or ''))
    return bool(ta) and ta == tb


def same_race(a: dict, b: dict) -> bool:
    """Whether two selections are in one race of Betty's runner list (meeting, time, horses or dogs), so the second
    can be chosen from the list the first was entered from. The favourite goes through the folders, never the list."""
    if a.get('favourite') or b.get('favourite'):
        return False
    def race(h: dict) -> tuple:
        return str(h.get('meeting') or ''), str(h.get('time') or ''), is_dog_race(h)
    return race(a) == race(b)


def _runner_list_top(meeting: str, hhmm: str, candidates: list[str], want_dogs: bool, both_kinds: bool,
                     reread_secs: float = MEETING_REREAD_SECS, want_virtual: bool = False) -> str | None:
    """
    The meeting at the top of Betty's runner list: `meeting` only when the list is also the selection's kind (horses
    or dogs), otherwise what was read ('Doncaster dogs', another meeting, a label off the card, None = unread after
    `reread_secs`). Read twice over: its label row by row, and the whole list by its contents
    (runner_list_top_by_content); when both say, they must agree.
    """
    # An unread top meeting is read again before 'right': read once mid-redraw, it was pressed past Dundalk 19:15
    # to the end of the list (9.2448555, 23 Oct)
    t_read = time.time()
    while True:
        _check_stop()
        shot = pyautogui.screenshot()
        top = _top_reads_agree(top_meeting_in_race_list(shot, candidates, prefer=meeting),
                               runner_list_top_by_content(shot, meeting, hhmm, candidates, want_dogs, want_virtual),
                               meeting)
        if top or time.time() - t_read > reread_secs:
            break
        time.sleep(0.1)
    if top != meeting:
        return top
    # Horses and dogs can share a meeting's label (Doncaster): a dog list's rows read 'Trap 1. ..', a horse
    # list's '01. ..', so the kind of list must be the selection's kind too
    dogs = race_list_is_dogs(shot)
    t_kind = time.time()
    while dogs is None and both_kinds and time.time() - t_kind < MEETING_REREAD_SECS:
        time.sleep(0.1)  # horses and dogs share the label: an unread list is read again, never assumed
        shot = pyautogui.screenshot()
        dogs = race_list_is_dogs(shot)
    if dogs is None and both_kinds:
        raise WagerForStaff(f"can't read whether Betty's {meeting} {clock_12h(hhmm)} list is the horses or "
                            "the dogs (both race then)")
    if dogs is None or dogs == want_dogs:
        return meeting
    return f"{meeting} {'dogs' if dogs else 'horses'}"


def _next_runner_list(prev_top: str | None, meeting: str, candidates: list[str]) -> str:
    """
    After 'right': the next runner list (RACE_LIST) or the end of the list (EXHAUSTED). A list the screen check doesn't
    recognise counts once its top meeting reads and differs from the one 'right' was pressed on (9.2452785, 26 Oct: 4 s
    lost waiting on an unrecognised list). Otherwise as expect_screen after NAV_TIMEOUT.
    """
    targets = {SCREEN_RACE_LIST, SCREEN_RACE_ENTRY_EXHAUSTED}
    t0 = time.time()
    while True:
        _check_stop()
        shot = pyautogui.screenshot()
        screen = detect_screen(shot)
        if screen in targets:
            return screen
        if screen == SCREEN_UNKNOWN:
            top = top_meeting_in_race_list(shot, candidates, prefer=meeting)
            if top and top != prev_top:
                return SCREEN_RACE_LIST
        if time.time() - t0 >= NAV_TIMEOUT:
            return expect_screen(targets, timeout=0, doing="next meeting ('right')")
        time.sleep(0.02)


def _read_new_betslip_line(already_on_slip: int) -> list[dict]:
    """
    The betslip lines once one more selection than `already_on_slip` shows, or the last read after NAV_TIMEOUT. A box
    that opens late (after answer_entry_popups stopped looking) is answered here; the betslip under it isn't read.
    """
    t0 = time.time()
    while True:
        _check_stop()
        img = pyautogui.screenshot()
        arr = np.array(img.convert('RGB'))
        box_open = any(_signals_pass(arr, sig['colours']) for sig in MODAL_SIGNATURES.values())
        lines = [] if box_open else read_betslip_selections(img)
        if len(lines) > already_on_slip or time.time() - t0 > NAV_TIMEOUT:
            return lines
        if box_open:
            answer_entry_popups()
        else:
            time.sleep(0.1)


def enter_selection(horse: dict, already_on_slip: int, after_same_race: bool = False, after_same_time: bool = False):
    """
    Adds one locked selection to the current betting slip and confirms it on the betslip read-back. After a selection
    in the same race (`after_same_race`), it is chosen from the runner list still showing, with no time typed again
    (user, 26 Oct: '1:17 Romford 3-4 S/F/C' is the 1:17 once, then 3 + Enter, 4 + Enter). After one at the same time
    at another meeting (`after_same_time`), the list still showing is that time's: 'right' on from it to the meeting
    (to-do, 30 Oct: the time was typed again for every selection). A meeting the list has already passed ends it, and
    the time is typed after all.
    """
    if horse.get('favourite'):
        return enter_favourite(horse, already_on_slip)
    meeting, hhmm, number = horse.get('meeting', ''), str(horse.get('time', '')), horse.get('number')
    void = bool(horse.get('void'))
    if not meeting or not re.match(r'\d{1,2}:\d{2}$', hhmm) or not (number or void):
        raise WagerForStaff(f"selection '{horse.get('name')}' has no meeting / time / cloth number to enter")
    takes_price = not void and str(horse.get('price') or '').strip().lower() not in ('', 'sp', 'none', '0')
    label = f"{'Void Selection' if void else horse.get('name') + ' #' + str(number)} {clock_12h(hhmm)} {meeting}"
    refresh_watcher_hud(f"Entering selection {already_on_slip + 1}: {label}...")
    rivals = _meetings_at(hhmm) or [meeting]
    candidates = rivals if meeting in rivals else rivals + [meeting]
    want_dogs, want_virtual = is_dog_race(horse), horse.get('category') == 'virtual'
    both_kinds = _label_has_horses_and_dogs(meeting, hhmm)

    img = pyautogui.screenshot()
    screen = detect_screen(img)
    row, top = None, None  # the selection's row lower down the list, clicked instead of typing its number
    if (after_same_race and screen == SCREEN_RACE_LIST
            and _runner_list_top(meeting, hhmm, candidates, want_dogs, both_kinds, want_virtual=want_virtual) == meeting):
        print(f"[*] {meeting} {clock_12h(hhmm)} is still showing: no time typed.")
    else:
        reuse = after_same_time and screen == SCREEN_RACE_LIST
        if reuse:
            print(f"[*] The {clock_12h(hhmm)} runner list is still showing: no time typed.")
        else:
            screen = _type_race_time(img, screen, hhmm)
        for _ in range(MAX_MEETING_STEPS):
            if screen == SCREEN_RACE_ENTRY_EXHAUSTED and reuse:  # passed it: from the start of the list after all
                print(f"[*] {meeting} wasn't further along the {clock_12h(hhmm)} runner list: typing the time.")
                reuse = False
                img = pyautogui.screenshot()
                screen = _type_race_time(img, detect_screen(img), hhmm)
            if screen == SCREEN_RACE_ENTRY_EXHAUSTED:
                raise WagerForStaff(f"{meeting} {clock_12h(hhmm)} is not in Betty's runner list")
            top = _runner_list_top(meeting, hhmm, candidates, want_dogs, both_kinds, want_virtual=want_virtual)
            if top is None:
                # Never 'right' on a list whose top wasn't read (9.2458229, 30 Oct: Newcastle 5:45 was already at the
                # top, unread while Betty drew it; 'right' then swallowed the runner number and Enter). Nor is an unread
                # top taken as the only meeting on the card at the time: the card can be short of a feed (9.2459253,
                # 31 Oct: taken as Ascot 2:33 with the Eastgreen 2:33 virtual dogs off the card)
                top = _runner_list_top(meeting, hhmm, candidates, want_dogs, both_kinds, reread_secs=NAV_TIMEOUT,
                                       want_virtual=want_virtual)
                if top is None:
                    raise WagerForStaff(f"the meeting at the top of Betty's {clock_12h(hhmm)} runner list could not be read")
            if top == meeting:
                break
            # 'right' brings each meeting to the top in turn (user, 28 Oct: "this has always been the way"). Only
            # when horses and dogs share the label is the race under the other one clicked: 'right' takes both off
            # (Newcastle 1:26, 9.2453975). Any other runner showing lower down is never clicked: a click on its
            # name adds it at SP (9.2455486, 28 Oct: Chief Minister 3/1 under Harlow went in at SP)
            if both_kinds and top in (f"{meeting} dogs", f"{meeting} horses"):
                row = None if void else find_runner_row(pyautogui.screenshot(), horse, candidates)
                if not row:
                    raise WagerForStaff(f"{label} can't be found under {top} in Betty's runner list "
                                        "(horses and dogs share the label)")
                break
            print(f"[*] Runner list starts with {top or 'an unread meeting'}: 'right' to bring up {meeting}.")
            betty_press('right')
            screen = _next_runner_list(top, meeting, candidates)
        else:
            raise WagerForStaff(f"could not bring {meeting} to the top of Betty's runner list")
    if row:  # a click adds it to the betslip (user, 27 Oct); typing its number would take a trap above it
        # The price is taken by clicking the price, the name gives SP (user, 28 Oct)
        col = RACE_LIST_PRICE_COL if takes_price else RACE_LIST_NAME_COL
        betty_click(col[0] + col[1] // 2, row['y'])
        print(f"[*] Added {label} by clicking its {'price' if takes_price else 'name'} "
              f"(row {row['row'] + 1} of the runner list, under {top}).")
    elif void:  # a card number not in the race: Betty's void selection for this race (user, 23 Oct; Rule 1.8.4)
        betty_press('v')
        print(f"[*] Added {label} with 'v'.")
    else:
        _type_text(str(int(number)))
        betty_press('add' if takes_price else 'enter')
        print(f"[*] Added {label} with {'numpad + (price)' if takes_price else 'Enter (SP)'}.")
    answer_entry_popups()

    lines = _read_new_betslip_line(already_on_slip)
    if len(lines) != already_on_slip + 1:
        raise WagerForStaff(f"after adding {label} the betslip shows {len(lines)} selection(s), expected {already_on_slip + 1}")
    got = lines[-1]
    if takes_price and got['price'].upper() == 'SP':  # user's rule: a price taken but none on Betty yet -> staff
        raise WagerForStaff(f"the customer took {horse.get('price')} on {label} but Betty has no price for it yet")
    problems = betslip_line_problems(got, horse)
    if problems:
        raise WagerForStaff(f"betslip shows {', '.join(problems)} for {label}")
    print(f"[+] Betslip line {got['n']}: {got['meeting']} {got['time']} {got['number']}. {got['name']} {got['price']} (checked)")


def _type_race_time(img: Any, screen: str, hhmm: str) -> str:
    """'/' for the yellow time box when it isn't showing, the race time, and the runner list it brings up (or the end
    of the list when Betty has no race then)."""
    box_open = _signals_pass(np.array(img.convert('RGB')), [RACE_ENTRY_TIME_BOX])
    if screen != SCREEN_RACE_ENTRY_READY and not (screen == SCREEN_UNKNOWN and box_open):
        betty_press('/')  # '/' toggles: pressed only when the yellow time box is not already showing
    # The time follows '/' at once: Betty keeps keys pressed before it has drawn the box (user, 26 Oct)
    _type_text(format_time_for_betty(hhmm))
    return expect_screen({SCREEN_RACE_LIST, SCREEN_RACE_ENTRY_EXHAUSTED}, doing=f"runner list for {hhmm}")


def betslip_runner_by_name(name: str, horse: dict) -> dict | None:
    """
    The runner in `horse`'s race on Betty's cards that a betslip name belongs to, or None when no runner is clearly
    it. Betty cuts names short ('Mythical Gues'), so each runner is compared over the betslip name's length too. Clear
    = the best fit is a good one and every other runner in the race fits clearly worse (9.2448563: '9. River Trieux'
    was River Trieux #5, the 9 an OCR slip; #9 was Hastily).
    """
    key = re.sub(r'[^a-z ]', '', name.lower()).strip()
    if len(key) < 3:
        return None
    meeting, hhmm = betty_meeting_abbrev(horse.get('meeting', '')), str(horse.get('time', ''))
    race = [r for r in racecard_manager.get_runners() + greyhound_card.get_runners()
            if r.get('time_str') == hhmm and betty_meeting_abbrev(r.get('meeting', '')) == meeting]
    scored = []
    for r in race:
        full = re.sub(r'[^a-z ]', '', str(r.get('name', '')).lower()).strip()
        scored.append((max(name_similarity(key, full), name_similarity(key, full[:len(key)])), r))
    scored.sort(key=lambda s: -s[0])
    if not scored or scored[0][0] < 0.8 or (len(scored) > 1 and scored[0][0] - scored[1][0] < 0.25):
        return None
    return scored[0][1]


def _meeting_label_fits(label: str | None, horse: dict) -> bool:
    """
    Whether a betslip line's meeting label is the selection's meeting: Betty's 4 letters exactly, or one letter off
    (an OCR slip) when no other meeting racing then is as near. Newcastle, Newmarket and Newton Abbot are all 'new',
    and a dog line shows only 'Trap N', so 3 letters let a dog bet at the wrong track pass (review R3).
    """
    got = re.sub(r'[^a-z]', '', str(label or '').lower())[:4]
    meeting = horse.get('meeting', '')
    want = betty_meeting_abbrev(meeting)
    if got == want:
        return True
    if not got or _letters_off(got, want) > 1:
        return False
    racing = set(_meetings_at(str(horse.get('time', '')))) | {meeting}
    return nearest_meeting_label(got, sorted(racing), prefer=meeting) == meeting


def _betslip_race_problems(got: dict, horse: dict) -> list[str]:
    """Whether a betslip line is in the selection's race: meeting (Betty's 4 letters) and time (12- or 24-hour)."""
    problems = []
    if not _meeting_label_fits(got.get('meeting'), horse):
        problems.append(f"meeting {got['meeting']}")
    # Accept either 12-hour or 24-hour time (e.g. 3:34 or 15:34 for virtuals)
    h_time = str(horse.get('time', ''))
    h_mins = parse_race_time_to_minutes(h_time)[0]
    got_mins = parse_race_time_to_minutes(got.get('time', ''))[0]
    if not ((got['time'] == clock_12h(h_time)) or (h_mins is not None and got_mins == h_mins)):
        problems.append(f"time {got['time']}")
    return problems


def betslip_line_problems(got: dict, horse: dict) -> list[str]:
    """What a betslip line gets wrong for a locked selection (meeting, time, number, name, SP vs price); [] = right."""
    problems = []
    if horse.get('favourite'):  # the SP favourite: its race, 'The Favourite', at SP
        problems = _betslip_race_problems(got, horse)
        if 'favourite' not in _letters(got.get('name')):
            problems.append(f"name '{got.get('name')}' instead of The Favourite")
        if got['price'].upper() != 'SP':
            problems.append(f"a price ({got['price']}) for the SP favourite")
        return problems
    if horse.get('void'):  # a void selection: its race (meeting, time) and VS, nothing else to check
        problems = _betslip_race_problems(got, horse)
        if got['price'].upper() != VOID_SELECTION:
            problems.append(f"{got['price']} instead of a void selection")
        return problems
    problems = _betslip_race_problems(got, horse)
    # Horse or dog is the selection's own kind, never the line's: a horse entered in the dog list at a shared label
    # (Doncaster horses and dogs at one time) reads 'Trap 3' and would otherwise skip the name check and pass
    category = horse.get('category')
    line_name = str(got.get('name') or '').strip()
    trap_line = line_name.lower().startswith('trap')
    kind_known = category in ('greyhound', 'domestic', 'international')  # virtual: either kind, the line says which
    is_dog = category == 'greyhound' or (not kind_known and trap_line)
    if kind_known and not is_dog and trap_line:
        problems.append(f"a dog ('{line_name}') where a horse was wanted")
    if is_dog and line_name and not trap_line:
        problems.append(f"a horse ('{line_name}') where a dog was wanted")
    if got['number'] != int(horse.get('number') or 0):
        # The name decides between an OCR digit slip and a wrong runner: two runners in a race never share a name.
        # Dog lines show only 'Trap N', so for dogs the number stays the check.
        named = None if is_dog else betslip_runner_by_name(str(got.get('name') or ''), horse)
        if not (named and named.get('number') == int(horse.get('number') or 0)):
            problems.append(f"number {got['number']}")
    if not is_dog and name_similarity(got['name'], str(horse.get('name', ''))) < 0.6:
        problems.append(f"name '{got['name']}'")
    takes_price = str(horse.get('price') or '').strip().lower() not in ('', 'sp', 'none', '0')
    if takes_price and got['price'].upper() == 'SP':
        problems.append("SP instead of a price")
    if not takes_price and got['price'].upper() not in ('SP', *NOT_RUNNING):
        problems.append(f"a price ({got['price']}) for an SP selection")
    return problems


def _slip_fault(lines: list[dict], horses: list[dict], struck_clock: str | None) -> str | None:
    """Why the betslip isn't right before F8 (count, a line, a guarantee), or None when it is."""
    if len(lines) != len(horses):
        return f"before F8 the betslip shows {len(lines)} selection(s), expected {len(horses)}"
    for line, horse in zip(lines, horses):
        problems = betslip_line_problems(line, horse)
        not_running = line['price'].upper() in NOT_RUNNING  # non-runner, withdrawn, void: never guaranteed
        wanted = bog_wanted(horse, struck_clock) and not not_running
        if wanted and not line['guaranteed']:
            problems.append("not guaranteed")
        if line['guaranteed'] and not wanted:
            problems.append("guaranteed but should not be")
        if problems:
            return f"before F8, line {line['n']} ({horse.get('name')}) shows {', '.join(problems)}"
    return None


def _line_guaranteed(arr: Any, left: int, i: int) -> bool:
    """Colour only (no OCR): is betslip line i's price purple?"""
    top = int(BETSLIP_LINE_TOP + i * BETSLIP_LINE_PITCH)
    return _colour_share(arr, (left + 250, top, 160, BETSLIP_LINE_H), GUARANTEED_PURPLE, 30) >= 0.02


def apply_guarantees(horses: list[dict], struck_clock: str | None):
    """
    Best odds guaranteed: each selection that qualifies (bog_wanted) is clicked on the betslip - clicked, not reached
    with the down arrow, which loses focus at a non-runner or late selection - then 'g' once, and its price must turn
    purple. 'g' can't be undone, so it is never pressed twice: unconfirmed -> staff. Fast: the lines are read once;
    after each 'g' only that line's colour (and the price box's blue border) is looked at, every 40 ms.
    """
    wanted = [i for i, h in enumerate(horses) if bog_wanted(h, struck_clock)]
    if not wanted:
        why = "struck outside the BOG windows" if not bog_window_applies(struck_clock) else "no UK/IRE horse with a price"
        print(f"[*] Best odds guaranteed: none needed ({why}).")
        return
    img = pyautogui.screenshot()
    lines = read_betslip_selections(img)
    if len(lines) != len(horses):
        raise WagerForStaff(f"the betslip shows {len(lines)} selection(s) before guaranteeing, expected {len(horses)}")
    left = betslip_left(img)
    price_box = MODAL_SIGNATURES[MODAL_PRICE]['colours']
    refresh_watcher_hud(f"Best odds guaranteed: {len(wanted)} selection(s)...")
    for i in wanted:
        if lines[i]['guaranteed'] or lines[i]['price'].upper() in NOT_RUNNING:
            continue  # a non-runner, withdrawn or void selection is never guaranteed
        betty_click(left + 60, lines[i]['y'])  # focus this selection (its "1. Meet 1:32" text, far from Remove)
        # Focusing a selection opens its price box again (user, 30 Oct): answered before 'g', which the box swallows
        if _price_box_shows(True, PRICE_BOX_FOCUS_SECS):
            answer_price_box()
        betty_press('g')
        answered, t0 = False, time.time()
        while time.time() - t0 < 2.0:
            _check_stop()
            arr = np.array(pyautogui.screenshot().convert('RGB'))
            if not answered and _signals_pass(arr, price_box):  # before the purple check: both can show at once
                answer_price_box()
                answered = True
            elif _line_guaranteed(arr, left, i):
                print(f"[+] Best odds guaranteed: {horses[i].get('name')} ({time.time() - t0:.2f}s).")
                break
            time.sleep(0.02)
        else:
            answer_entry_popups()  # anything else in the way (e.g. late selection), answered by its label
            if not _line_guaranteed(np.array(pyautogui.screenshot().convert('RGB')), left, i):
                raise WagerForStaff(f"pressed g once on {horses[i].get('name')} but the guarantee can't be confirmed "
                                    "(not pressed again)")
        # Purple can show before a box opens (9.2446520, 22 Oct: a box left open after 'g' hid the betslip, which then
        # read as 0 selections): answer any box that opens now, before the next line is clicked
        answer_entry_popups()


def check_slip_before_f8(horses: list[dict], struck_clock: str | None):
    """
    Before F8: every selection on the betslip is right, in order, and guaranteed exactly when it should be. Read
    until it is (Betty may still be redrawing after 'g', or a box may be open over it), up to NAV_TIMEOUT; only the
    last read decides.
    """
    t0 = time.time()
    while True:
        _check_stop()
        img = pyautogui.screenshot()
        arr = np.array(img.convert('RGB'))
        if any(_signals_pass(arr, sig['colours']) for sig in MODAL_SIGNATURES.values()):
            answer_entry_popups()
            img = pyautogui.screenshot()
        lines = read_betslip_selections(img)
        fault = _slip_fault(lines, horses, struck_clock)
        if not fault:
            break
        if time.time() - t0 > NAV_TIMEOUT:
            raise WagerForStaff(fault)
        time.sleep(0.1)
    n_bog = sum(1 for line in lines if line['guaranteed'])
    print(f"[+] Before F8: {len(lines)} selection(s) checked, {n_bog} guaranteed.")


def _f8_selected(img: Any) -> list[bool]:
    """Which of the bet list's 11 rows are selected (green), by colour alone: no text read."""
    x, y, w, _ = F8_BET_LIST_REGION_1368
    arr = np.array(img.convert('RGB'))
    return [_colour_share(arr, (x + 2, int(y + i * F8_ROW_HEIGHT_1368) + 3, w - 4, int(F8_ROW_HEIGHT_1368) - 6),
                          F8_ROW_GREEN) >= 0.4 for i in range(F8_NUM_ROWS)]


def _f8_texts(img: Any) -> list[str]:
    """
    The bet list's 11 rows as letters and digits, in one OCR of the whole list put back into rows by height. A
    Tesseract run per row (and a second for a blank one) took ~2 s a read, and choosing a bet type read the list
    about 4 times: 11-15 s on every bet before F12 (9.2455887, 28 Oct). One pass: ~0.3 s, the same 113 named rows
    on every saved bet-list screen.
    """
    x, y, w, h = F8_BET_LIST_REGION_1368
    scale = 2
    crop = img.convert('L').crop((x, y, x + w, y + h)).resize((w * scale, h * scale))
    try:
        d = pytesseract.image_to_data(crop, config='--psm 6', output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return [''] * F8_NUM_ROWS
    rows: dict[int, list[str]] = {}
    for word, top, height in zip(d['text'], d['top'], d['height']):
        if word.strip():
            rows.setdefault(int((top + height / 2) / scale // F8_ROW_HEIGHT_1368), []).append(word.strip())
    return [re.sub(r'[^a-z0-9]', '', " ".join(rows.get(i, [])).lower()) for i in range(F8_NUM_ROWS)]


def _f8_rows(img: Any) -> list[tuple[str, bool]]:
    """The bet list on Choose Bet and Stake: [(letters, selected)] for the 11 rows."""
    return list(zip(_f8_texts(img), _f8_selected(img)))


F8_PAGE_MIN_ROWS = 6      # a page counts as read only when this many rows read as known bet names (a blank row
                          # mid-redraw reads as junk like 'ne')
F8_PAGE_READS = 4         # reads of one page at most before it goes to staff as unreadable
# Every row Betty's bet list can show (user's screenshots of all 8 pages, 23 Oct: scratch/betty_screens/
# 26_bet_list_full_p1-8.png). Which rows show, and on which page, depends on the selections entered.
BETTY_BET_LIST = (
    "Singles", "Doubles", "Trebles", "Acc On All Selns", "Doubles + Trebles", "Yankee", "Lucky 15", "Patent or Twist",
    "Lucky 31", "Lucky 63", "Flag", "Perm Patent", "5 Perm Patent", "Round Robin or Split", "Perm Round Robin",
    "5 Perm Round Robin", "Trixie", "Singles + Doubles", "Reversed Forecasts", "Combination F'casts",
    "Straight Forecasts", "Tricasts", "Combination Tricasts", "Super Flag", "Heinz", "Super Yankee", "Canadian",
    "Super Heinz", "Goliath", "Union Jack", "Union Jack Trixies", "Union Jack Patent", "Forecast Doubles",
    "Rev. F'cast Doubles", "Rev. F'cast Trebles", "Comb. F'cast Doubles", "Forecast Trebles", "Lucky 31 Sport",
    "Lucky 15 Sport", "Lucky 63 Sport", "FR Lucky 15", "FR Lucky 31", "FR Lucky 63", "Round The Clock", "Multi",
    "A.T.C./If Cash Singles", "A.T.C./If Cash Double", "Single Stakes About", "Double Stakes About", "Banko", "Mix",
    "Roundabout", "Rounder", "Yap", "Comedy", "Gyroscope", "Single Lap or Waterfall", "Stop at a Winner",
    "Dundee Shuffle", "Sitter", "Fivespot", "Pontoon or Black Jack", "Magnificent 7", "Forecast Patent",
    "Rev Forecast Patent", "Pluto", "Fido", "Perm 4-Folds", "Perm 5-Folds", "Perm 6-Folds", "Perm 7-Folds",
    "Perm 8-Folds", "Perm 9-Folds", "Perm 10-Folds", "5 Fold Acca Insurance", "6 Fold Acca Insurance",
    "7 Fold Acca Insurance", "8 Fold Acca Insurance", "9 Fold Acca Insurance", "10 Fold Acca Insurance",
    "Acca Insurance", "Alphabet", "Accumulator(s)", "Play Your Dogs", "Match Max")
BET_LIST_LETTERS = tuple(re.sub(r'[^a-z0-9]', '', label.lower()) for label in BETTY_BET_LIST)


def _letters_off(a: str, b: str) -> int:
    """Edit distance: letters added, dropped or changed to turn a into b."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def nearest_bet_label(text: str) -> tuple[str, int] | None:
    """
    The row of Betty's bet list an OCR'd row (letters and digits only) is: its nearest label of all 84, with how many
    letters it is off. None when no label is near enough (about one letter in three) or two are equally near.
    """
    if not text:
        return None
    ranked = sorted((_letters_off(text, lab), lab) for lab in BET_LIST_LETTERS)
    off, lab = ranked[0]
    if off > max(1, len(lab) // 3) or (len(ranked) > 1 and ranked[1][0] == off):
        return None
    return lab, off


def bet_label_score(text: str, canon: str) -> float:
    """
    How well a bet-list row names `canon`: 1.0 exact, less a tenth per letter off, and 0.0 unless `canon`'s label is
    the row's nearest of all 84 labels Betty can show. So a near miss is taken only when no other bet is as near:
    'trebies' is Trebles, but 'FR Lucky 15', 'Lucky 15 Sport' or 'Doubles + Trebles' are never Lucky 15 or Trebles,
    because each is a row of its own.
    """
    near = nearest_bet_label(text)
    if not near or near[0] != ENTRY_BET_TYPES[canon][1]:
        return 0.0
    return 1.0 - 0.1 * near[1]


_f8_trail: list[str] = []  # keys sent on Choose Bet and Stake for the bet in hand, each marked when Betty had left it


def _f8_key(key: str):
    """
    A key on Choose Bet and Stake, noting whether Betty still shows it just after (colours only, no OCR). Only for the
    log: 9.2458229 (30 Oct) and 9.2455944 (28 Oct) went to Home after F8 and nothing said which key did it.
    """
    betty_press(key)
    try:
        arr = np.array(pyautogui.screenshot().convert('RGB'))
        still = _signals_pass(arr, SCREEN_SIGNATURES[SCREEN_BET_AND_STAKE]['colours'])
    except Exception:  # a screenshot that can't be read changes nothing here
        still = True
    _f8_trail.append(key if still else f"{key} (screen gone)")


def _left_f8(screen: str, doing: str) -> Exception:
    """The staff reason for Betty leaving Choose Bet and Stake, with the keys sent there printed first."""
    print(f"[*] Keys on Choose Bet and Stake before it left: {', '.join(_f8_trail) or 'none'}")
    return WagerForStaff(f"Betty left Choose Bet and Stake (now on {screen}) {doing}")


def _find_bet_row(canon: str) -> tuple[int | None, list]:
    """
    Reads the bet-list page until it holds `canon` (row returned) or is settled without it (None): enough rows hold a
    name and two reads agree. Before (9.2448240, 23 Oct) one read taken while Betty redrew the list was enough to
    press PgDn, so Trebles on page 1 was never seen.
    """
    last = None
    for _ in range(F8_PAGE_READS):
        _check_stop()
        shot = pyautogui.screenshot()
        rows = _f8_rows(shot)
        scores = [bet_label_score(text, canon) for text, _ in rows]
        if max(scores, default=0.0) > 0:
            return scores.index(max(scores)), rows
        texts = [text for text, _ in rows]
        if sum(1 for t in texts if nearest_bet_label(t)) >= F8_PAGE_MIN_ROWS and texts == last:
            # Before the caller pages on, the old row-by-row read (~2 s) has its say: PgDn is pressed only when
            # both readers agree the type isn't here (9.2455944, 28 Oct: Lucky 63, Betty went Home while paging)
            x, y, w, h = F8_BET_LIST_REGION_1368
            listed = shot.crop((x, y, x + w, y + h))
            slow = [(re.sub(r'[^a-z0-9]', '', ocr_f8_row_text(r, listed).lower()), sel) for r, (_, sel) in enumerate(rows)]
            scores = [bet_label_score(text, canon) for text, _ in slow]
            if max(scores, default=0.0) > 0:
                print(f"[*] Bet list: '{canon}' found by the row-by-row read (the one-pass read had {texts}).")
                return scores.index(max(scores)), slow
            print(f"[*] Bet list page has no '{canon}': {[nearest_bet_label(t)[0] if nearest_bet_label(t) else t for t in texts]}")
            return None, rows
        last = texts
        time.sleep(0.08)
    # A blank list is often no list: Betty left the screen by itself just after F8 (9.2455944, 28 Oct: on Home twice)
    screen = detect_screen()
    if screen != SCREEN_BET_AND_STAKE:
        raise _left_f8(screen, f"while choosing '{canon}'")
    raise WagerForStaff(f"Betty's bet list could not be read while looking for '{canon}'")


def choose_bet_type(canon: str, extending: bool = False):
    """Selects the bet type on Choose Bet and Stake, by its name (shortcut first, else found in the list)."""
    key, label = ENTRY_BET_TYPES[canon]

    # Singles is selected by default on Betty when F8 opens: if already selected, nothing to do
    if canon == 'single':
        initial_rows = _f8_rows(pyautogui.screenshot())
        # unless another row is selected too and only Singles is wanted (review R18)
        if (initial_rows and initial_rows[0][1] and bet_label_score(initial_rows[0][0], canon) > 0
                and (extending or not any(sel for _, sel in initial_rows[1:]))):
            return

    if key:
        _f8_key(key)
        time.sleep(0.08)
    for page in range(5):
        i, rows = _find_bet_row(canon)
        if i is not None:
            break
        print(f"[*] '{canon}' isn't on this page of the bet list: PgDn.")
        _f8_key('pagedown')  # the list pages round; bet types depend on the selections entered
        time.sleep(0.08)
        screen = detect_screen()
        if screen != SCREEN_BET_AND_STAKE:
            raise _left_f8(screen, f"after PgDn while choosing '{canon}'")
    else:
        raise WagerForStaff(f"Betty's bet list has no '{canon}' for these selections")
    if rows[i][0] != label:
        print(f"[*] Bet list: '{rows[i][0]}' taken as {canon} ('{label}').")
    x, y, w, _ = F8_BET_LIST_REGION_1368
    if not rows[i][1]:
        betty_click(x + w // 2, int(y + (i + 0.5) * F8_ROW_HEIGHT_1368))
        time.sleep(0.05)

    # Selecting a row doesn't change the list, so the rows' names are known: from here only the green is read
    if not extending:
        for j, selected in enumerate(_f8_selected(pyautogui.screenshot())):
            if selected and j != i:
                print(f"[*] Deselecting '{rows[j][0]}' (only {canon} wanted).")
                betty_click(x + w // 2, int(y + (j + 0.5) * F8_ROW_HEIGHT_1368))
                time.sleep(0.05)
        chosen = [rows[j][0] for j, sel in enumerate(_f8_selected(pyautogui.screenshot())) if sel]
        if chosen != [rows[i][0]]:
            raise WagerForStaff(f"could not select only {canon} in Betty's bet list (selected: {chosen})")
    elif not _f8_selected(pyautogui.screenshot())[i]:
        raise WagerForStaff(f"could not select {canon} in Betty's bet list for extended bet")


STAKE_BOX_DIGITS = 8  # backspaces clearing the last stake (pence): up to £99,999.99 (5 cleared only £999.99; review R18)


def enter_bet_terms(bet: dict, canon: str, bets_before: int, bet_no: int | None = None):
    """On Choose Bet and Stake: stake, each way / win, bet type. `bet_no` = the bet's place in the wager, for the log."""
    stake = round(float(bet.get('stake_pence') or 0))
    if stake <= 0:
        raise WagerForStaff("a bet has no stake")
    if bets_before > 0:
        time.sleep(0.15)
        for _ in range(STAKE_BOX_DIGITS):
            betty_press('backspace')
            time.sleep(0.01)
    for ch in str(stake):
        _f8_key(ch)
    _f8_key('enter')
    time.sleep(0.1)  # the each-way button is drawn after Enter (review R18)
    arr = np.array(pyautogui.screenshot().convert('RGB'))
    ew_on = _colour_share(arr, F8_EACH_WAY_BOX, F8_ROW_GREEN) >= 0.4
    if bool(bet.get('each_way')) != ew_on:
        _f8_key('e' if bet.get('each_way') else 'w')
    choose_bet_type(canon, extending=bets_before > 0)
    time.sleep(0.15)
    ew_str = 'Each Way' if bet.get('each_way') else 'Win Only'
    print(f"[+] Bet {bet_no or bets_before + 1} entered: {canon}, {ew_str} @ {stake}p.")


# --- Best odds guaranteed (BOG): the shop guarantees prices on UK & Irish horse racing for bets STRUCK inside these
# windows, end minute included (11:00:00-14:00:59, 17:00:00-18:00:59). Override with BOG_WINDOWS="11:00-14:00,...".
BOG_WINDOWS = _env_list("BOG_WINDOWS", "11:00-14:00,17:00-18:00")


def bog_window_applies(struck_clock: str | None) -> bool:
    """True when the bet was struck inside a BOG window (inclusive of the end minute). Unknown time -> False."""
    m = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', struck_clock or '')
    if not m:
        return False
    t = int(m.group(1)) * 60 + int(m.group(2))
    for window in BOG_WINDOWS:
        w = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', window)
        if w and int(w.group(1)) * 60 + int(w.group(2)) <= t <= int(w.group(3)) * 60 + int(w.group(4)):
            return True
    return False


def bog_wanted(horse: dict, struck_clock: str | None) -> bool:
    """A selection gets 'g' only if: struck inside a BOG window, a price was taken (never SP), and it is UK / Irish
    horse racing on Betty's horse card (not greyhounds, international or virtual)."""
    took_price = str(horse.get('price') or '').strip().lower() not in ('', 'sp', 'none', '0')
    return (bog_window_applies(struck_clock) and took_price and horse.get('category', 'domestic') == 'domestic'
            and horse.get('category') != 'greyhound' and is_bog_eligible_selection(horse)[0])


ORDERED_BET_TYPES = ('straight forecast', 'tricast')  # entered in the finishing order written


def same_selections(a: dict, b: dict) -> bool:
    """
    Whether bet b can go on bet a's slip with F11: the same selections, and in the same order when either bet is a
    straight forecast or tricast (the slip's order is the finishing order, so 'SF 3-5' then 'SF 5-3' is two slips).
    """
    def key(bet: dict) -> list[tuple[str, ...]]:
        # strings throughout: a void selection or the favourite has no number, and None can't be sorted with ints
        return [(str(h.get('meeting') or ''), str(h.get('time') or ''), str(h.get('number') or ''),
                 'void' if h.get('void') else '', 'fav' if h.get('favourite') else '') for h in bet.get('horses', [])]
    if entry_bet_type(a) in ORDERED_BET_TYPES or entry_bet_type(b) in ORDERED_BET_TYPES:
        return key(a) == key(b)
    return sorted(key(a)) == sorted(key(b))


BETTY_EXE = os.environ.get("BETTY_EXE", "bets.exe").strip().lower()  # Betty's program (C:\Betty\Bets.exe)


def window_pid(hwnd) -> int:
    import ctypes.wintypes as wt
    pid = wt.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def window_exe(hwnd) -> str:
    """The program file that owns a window, lower case ('bets.exe'), or '' when Windows won't say."""
    import ctypes.wintypes as wt
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x1000, False, window_pid(hwnd))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    buf, size = ctypes.create_unicode_buffer(260), wt.DWORD(260)
    kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(handle)
    return os.path.basename(buf.value).lower()


def betty_top_window() -> int | None:
    """
    The window Betty is showing: the topmost visible, full-size window of Betty's program. Betty has several, all
    untitled or titled alike ('A-Bet System' behind, an untitled one for the bet edit), so the window is found by
    the program that owns it, never by its title or by what is at a screen position.
    """
    import ctypes.wintypes as wt
    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def visit(hwnd, _):
        rect = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if user32.IsWindowVisible(hwnd) and rect.right - rect.left > 200 and window_exe(hwnd) == BETTY_EXE:
            found.append(hwnd)
            return False  # windows are listed top first: the first one is what Betty shows
        return True

    user32.EnumWindows(visit, 0)
    return found[0] if found else None


def focus_betty():
    """
    Gives Betty the keyboard again, through Windows (nothing in Betty is clicked). After the staff selection dialog
    closed, focus went elsewhere, so '/' never reached Betty and the wager backed out and was scanned again
    (9.2448749, 23 Oct). Not in the free tests, which have no Betty on screen.
    """
    if os.environ.get("BETTY_HEADLESS") == "1":
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = betty_top_window()
        if not hwnd:
            print(f"[-] Betty's program ({BETTY_EXE}) has no window open to give the keyboard to.")
        elif hwnd != user32.GetForegroundWindow():
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.08)
            if user32.GetForegroundWindow() != hwnd:
                print("[-] Windows didn't let Betty take the keyboard; the next key may not reach it.")
    except Exception as e:
        print(f"[-] Could not give Betty the keyboard: {e}")


def betty_in_front() -> bool:
    """
    Betty's program has the keyboard, so the watcher's keys reach Betty and nothing else. The till has one screen: when
    the launcher window (this program's parent) is in front, it is asked to step aside (it minimises itself), and any
    other window gives way to Betty through focus_betty. False when Betty still isn't in front, or isn't open: the
    watcher then waits and presses nothing. Always True in the free tests.
    """
    if os.environ.get("BETTY_HEADLESS") == "1":
        return True
    try:
        user32 = ctypes.windll.user32
        front = user32.GetForegroundWindow()
        if front and window_exe(front) == BETTY_EXE:
            return True
        if front and window_pid(front) == os.getppid():
            backend_event("step_aside")
            time.sleep(0.6)  # the launcher minimises; Windows usually hands the keyboard to Betty behind it
        focus_betty()
        front = user32.GetForegroundWindow()
        return bool(front) and window_exe(front) == BETTY_EXE
    except Exception as e:
        print(f"[-] Could not tell which window is in front: {e}")
        return False


def enter_wager(slip: list[dict], payment_pence: int, struck_clock: str | None = None):
    """
    Enters every locked bet: selections, then Choose Bet and Stake (F8), F11 when the next bet uses the same
    selections, F10 for a new betting slip. Finishes on Choose Bet and Stake with the total checked against Payment.
    """
    plan = [(bet, entry_bet_type(bet)) for bet in slip]
    missing = [str(bet.get('bet_type')) for bet, canon in plan if canon is None]
    if missing:
        raise WagerForStaff(f"bet type(s) the program can't enter yet: {', '.join(missing)}")
    focus_betty()  # a staff dialog may just have closed: keys must reach Betty, not the console
    bets_on_slip = 0
    for idx, (bet, canon) in enumerate(plan):
        assert canon is not None
        if not (idx and same_selections(bet, plan[idx - 1][0])):
            horses = bet.get('horses', [])
            for k, horse in enumerate(horses):
                after_race = k > 0 and same_race(horse, horses[k - 1])
                enter_selection(horse, k, after_same_race=after_race,
                                after_same_time=k > 0 and not after_race and same_race_time(horse, horses[k - 1]))
            apply_guarantees(bet.get('horses', []), struck_clock)
            # No whole-betslip re-read here (user, 26 Oct): every line was read back as it was entered and every
            # guarantee confirmed by its colour; the re-read failed on good slips (9.2452710). Payment is checked at F12.
            answer_entry_popups()
            bets_on_slip = 0
            _f8_trail[:] = ['f8']
            betty_press('f8')
        expect_screen({SCREEN_BET_AND_STAKE}, doing="Choose Bet and Stake (F8)")
        refresh_watcher_hud(f"Bet {idx + 1}/{len(plan)}: {canon}, {bet.get('stake_pence')}p"
                            f"{' each way' if bet.get('each_way') else ''}...")
        enter_bet_terms(bet, canon, bets_on_slip, bet_no=idx + 1)
        bets_on_slip += 1
        if idx < len(plan) - 1:
            if same_selections(plan[idx + 1][0], bet):
                _f8_trail.clear()
                _f8_key('f11')  # extend: same selections, next bet type
                time.sleep(0.2)
            else:
                betty_press('f10')  # new betting slip
                expect_screen({SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY}, doing="new betting slip (F10)")
    total = read_betslip_bets(pyautogui.screenshot())['payment_pence']
    if total != payment_pence:
        raise WagerForStaff(f"Betty's slip totals {'£%.2f' % (total / 100) if total is not None else 'unread'} "
                            f"but £{payment_pence / 100:.2f} was paid")
    print(f"[+] Entered and checked: Betty's total £{total / 100:.2f} = Payment.")


def commit_wager(number: str, payment_pence: int) -> str:
    """
    Places the entered, checked wager: F12 on Choose Bet and Stake. The ONLY code that can press F12, and it refuses
    in test mode. Placed = Betty back on View Wagers with the wager gone from the unedited list (so a restart can never
    place it twice). If Betty questions the payment after F12, nothing is answered: the wager goes to staff (FAO).
    """
    global _placing
    if test_mode_on.is_set():
        raise PlacingRefused(f"commit_wager({number}) called in test mode")
    screen = detect_screen()
    if screen not in (SCREEN_BET_AND_STAKE, SCREEN_UNKNOWN):  # the total below is read before F12 either way
        raise NavError(f"not on Choose Bet and Stake to place wager {number} (Betty shows {screen})")
    total = read_betslip_bets(pyautogui.screenshot())['payment_pence']
    if total != payment_pence:  # last look, immediately before the key
        raise WagerForStaff(f"Betty's slip totals {'£%.2f' % (total / 100) if total is not None else 'unread'} "
                            f"but £{payment_pence / 100:.2f} was paid")
    refresh_watcher_hud(f"Placing wager {number} (F12)...")
    print(f"[*] Placing wager {number}: F12.")
    _placing = True
    try:
        betty_press('f12')
    finally:
        _placing = False
    screen = expect_screen({SCREEN_VIEW_WAGERS, SCREEN_HOME, MODAL_PAYMENT_MISMATCH, MODAL_CONFIRM_STAKE},
                           timeout=8.0, doing="Place Bet (F12)")
    if screen in (MODAL_PAYMENT_MISMATCH, MODAL_CONFIRM_STAKE):
        raise WagerForStaff("Betty questioned the payment after F12 (nothing answered)")
    if screen == SCREEN_HOME:
        open_view_wagers()
    t0 = time.time()
    while time.time() - t0 < NAV_TIMEOUT:
        if wager_gone_from_list(number):
            print(f"[+] Wager {number} placed: it has left the unedited list.")
            return 'placed'
        time.sleep(0.3)
    raise WagerForStaff(f"after F12, wager {number} is still in the unedited list - please check it on Betty")


def wait_for_staff_review(number: str) -> str:
    """
    Test mode: the wager is entered and checked; staff place it (F12) or cancel it. Returns 'placed' when it has left
    the unedited list (looked at on View Wagers, opened from Home if staff end there), else 'cancelled' (Betty is then
    taken back to Home).
    """
    alert_staff(f"Wager {number} entered and checked (test mode). Place it with F12, or cancel it.")
    refresh_watcher_hud(f"TEST MODE: wager {number} entered and checked. Place it (F12) or cancel it.")
    with staff_input_expected():
        while True:
            _check_stop()
            screen = detect_screen()
            if screen in (SCREEN_VIEW_WAGERS, SCREEN_HOME):
                break
            time.sleep(0.5)
    if screen == SCREEN_HOME:  # F12 can land on Home too: look at the list before calling it cancelled (review R9)
        try:
            screen = open_view_wagers()
        except NavError as e:
            print(f"[-] Wager {number}: couldn't open View Wagers to see whether staff placed it ({e}).")
    if screen == SCREEN_VIEW_WAGERS and number not in read_unedited_queue(pyautogui.screenshot()):
        return 'placed'
    go_home()
    return 'cancelled'


# --- 6d. THE WATCHER LOOP ---
WATCHER_POLL_SECS = 5.0       # queue empty: look again this often, sitting on View Wagers
WATCHER_UNKNOWN_LIMIT = 3     # back-out attempts that fail in a row before the watcher stops and alerts staff
_wagers_left_for_staff: set[str] = set()  # this session: wagers placed, or stopped by Esc or a failure; not opened again (a pause is retried)
_current_wager: str | None = None
_nav_failures: dict[str, int] = {}  # wager -> navigation problems this session (left for staff after 2)
_open_elsewhere_until: dict[str, float] = {}  # wager -> time to look at it again (another till had it open)


SLIP_OPEN_ATTEMPTS = 3


def open_wager_slip(number: str):
    """
    End -> '/' to the time box with the customer's slip actually showing. Betty sometimes opens a bet without the slip
    (blank or "Special/Other Events Wager" panel): then Esc back to View Wagers, click the wager again and reopen.
    """
    for attempt in range(1, SLIP_OPEN_ATTEMPTS + 1):
        try:
            open_race_entry()
            if slip_showing():
                return
            print("[!] The slip panel is plain cream: Betty didn't display the slip.")
        except SlipNotShowing as e:
            print(f"[!] {e}.")
        if attempt == SLIP_OPEN_ATTEMPTS:
            break
        refresh_watcher_hud(f"Wager {number}: slip not showing; reopening ({attempt + 1}/{SLIP_OPEN_ATTEMPTS})...")
        betty_press('esc')  # bet edit -> View Wagers
        expect_screen({SCREEN_VIEW_WAGERS}, doing="back to View Wagers to reopen the bet")
        queue = read_unedited_queue(pyautogui.screenshot())
        if number not in queue:
            raise NavError(f"wager {number} left the unedited list while reopening it")
        load_wager(queue.index(number), number)
    raise WagerForStaff(f"Betty did not show the slip after {SLIP_OPEN_ATTEMPTS} tries")


class WagerOpenElsewhere(Exception):
    """Another till is viewing this wager's image ("TERMINAL x IS VIEWING THIS WAGER'S IMAGE"): skip it for now."""


OPEN_ELSEWHERE_RETRY_SECS = 30
VW_SLIP_MESSAGE_BOX = (900, 320, 460, 150)  # View Wagers slip panel: where "TERMINAL x IS VIEWING..." shows, in green
VW_MESSAGE_GREEN = (0, 255, 65)


def wager_open_elsewhere(img: Any) -> str | None:
    """On View Wagers: 'TERMINAL x' when another till is viewing the loaded wager's image (green message read by its
    colour, then by OCR), else None."""
    x, y, w, h = VW_SLIP_MESSAGE_BOX
    arr = np.array(img.convert('RGB'))[y:y + h, x:x + w].astype(int)
    mask = np.max(np.abs(arr - np.array(VW_MESSAGE_GREEN)), axis=2) <= 60
    if mask.mean() < 0.02:
        return None
    text = pytesseract.image_to_string(Image.fromarray(np.where(mask, 0, 255).astype('uint8')).resize((w * 2, h * 2)),
                                       config='--psm 6')
    flat = " ".join(text.upper().split())
    if "VIEWING" not in flat:
        return None
    m = re.search(r'TERMINAL\s*(\w+)', flat)
    return f"terminal {m.group(1)}" if m else "another terminal"


class WagerForStaff(Exception):
    """This wager can't be done safely by the program: one sentence for staff, then it is left for a person."""


def alert_staff(message: str):
    """HUD message with a sound: something needs a person."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass
    notify(message, is_error=True, title=f"{APP_NAME} - Staff needed")


def lock_wager(number: str, details: dict) -> list[dict]:
    """
    On the race-entry screen: read the slip (reconciled to the Payment taken), then check every selection against
    Betty's card with the struck time, staff prompts included. Returns the locked bets, or raises WagerForStaff.
    """
    pay = details['payment_pence']
    if not racecard_manager.get_runners():
        raise WagerForStaff("Betty's racecard feed can't be read, so no selection can be checked")
    screen = detect_screen()
    if screen not in (SCREEN_RACE_ENTRY_READY, SCREEN_RACE_ENTRY, SCREEN_UNKNOWN):  # scanned in the bet edit only
        raise NavError(f"not at the race-entry time box before scanning (Betty shows {screen})")
    print(f"[*] Scanning wager {number} at the race-entry time box.")
    api_key = GEMINI_API_KEY or "reader-chain"
    refresh_watcher_hud(f"Wager {number}: reading slip (paid £{pay / 100:.2f})...")
    scan = scan_and_reconcile(api_key, payment_pence=pay, struck_time=details['struck_time'])
    _check_stop()
    if not scan['ok']:
        raise WagerForStaff(scan['reason'] or "the slip could not be read")
    refresh_watcher_hud(f"Wager {number}: checking selections against Betty's card (struck {details['struck_time']})...")
    with staff_input_expected():  # staff answering a selection prompt must not switch the watcher off
        slip = state_pre_scan_and_match_slip(scan['slip_data'], raw_selections=scan['raw_selections'],
                                             img_str=scan['img_str'], api_key=api_key,
                                             written_total_pence=scan['written_total_pence'],
                                             struck_time=details['struck_clock'] or details['struck_time'])
    _check_stop()
    if not slip:
        raise WagerForStaff("staff cancelled the slip at the selection check")
    final = sum(calculate_bet_cost_pence(b) for b in slip)
    if final != pay:
        raise WagerForStaff(f"after house rules the bets cost £{final / 100:.2f} but £{pay / 100:.2f} was paid")
    return slip


def watcher_process_wager(row: int, number: str):
    """
    One wager: load it, read its number / struck time / Payment, open race entry, lock it (scan, money, selection
    check), enter it into Betty with every step read back, then place it (F12) - or, in test mode, stop before F12
    for staff to place or cancel it.
    """
    global _current_wager, _wager_opened
    _current_wager, _wager_opened = number, False
    details = load_wager(row, number)
    elsewhere = wager_open_elsewhere(pyautogui.screenshot())
    if elsewhere:
        _current_wager = None  # not ours to touch: no clean-up, no staff alert
        raise WagerOpenElsewhere(f"{elsewhere} is viewing its image")
    pay = details['payment_pence']
    print(f"[*] Wager {number}: struck {details['struck_clock']}, Payment "
          f"{'£%.2f' % (pay / 100) if pay is not None else 'unread'}")
    if not details['struck_time'] or pay is None:
        print(f"[-] View Wagers summary as read: {details['summary']!r}")
        raise WagerForStaff(f"View Wagers could not be read (struck time {details['struck_clock'] or 'unread'}, "
                            f"Payment {'£%.2f' % (pay / 100) if pay is not None else 'unread'})")
    refresh_watcher_hud(f"Wager {number}: struck {details['struck_time']}, Payment £{pay / 100:.2f}. Opening race entry...")
    _wager_opened = True  # End is pressed next: from here Esc or a failure leaves the wager for staff (a pause doesn't)
    open_wager_slip(number)
    slip = lock_wager(number, details)
    n_sel = len({(h.get('name'), h.get('time')) for b in slip for h in b.get('horses', [])})
    summary = f"{number}: {n_sel} selection(s), {len(slip)} bet(s), £{pay / 100:.2f}"
    print(f"[+] {summary} locked. Entering into Betty...")
    enter_wager(slip, pay, details['struck_clock'])
    if test_mode_on.is_set():  # test mode: never placed by the program
        outcome = wait_for_staff_review(number)
        print(f"[+] Wager {number}: {outcome} by staff.")
        STATUS_HUD.set_outcome(f"{summary} entered, {outcome} by staff {time.strftime('%H:%M')}")
    else:
        commit_wager(number, pay)
        STATUS_HUD.set_outcome(f"{summary} PLACED {time.strftime('%H:%M')}")
    _wagers_left_for_staff.add(number)
    _current_wager = None


STAFF_SCREENSHOTS_KEPT = 20  # newest kept in logs/ (no image folder of their own)
STAFF_JOURNAL = "staff_journal.jsonl"  # logs/: every wager left for staff and every selection staff typed
STAFF_JOURNAL_DAYS = 30
SLIP_IMAGES_KEPT = 200  # logs/slip_*.png: the slip as read, for each selection staff had to type (training)


def journal_staff(kind: str, **data):
    """
    One line in logs/staff_journal.jsonl ('staff': a wager left for staff; 'manual': a selection staff typed), for the
    launcher's Staff entries tab, and the same as a status event. Kept STAFF_JOURNAL_DAYS days.
    """
    entry = {'kind': kind, 'date': time.strftime('%Y-%m-%d'), 'time': time.strftime('%H:%M:%S'),
             'version': __version__, **data}
    try:
        if os.environ.get("BETTY_HEADLESS") != "1":  # the free tests' made-up wagers stay out of logs/
            os.makedirs(app_paths.log_dir(), exist_ok=True)
            with open(os.path.join(app_paths.log_dir(), STAFF_JOURNAL), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        print(f"[-] Could not write the staff journal: {e}")
    # After the line is written: the launcher re-reads the journal when it hears of it
    backend_event(kind, **{k: v for k, v in entry.items() if k not in ('kind', 'time')})


def prune_staff_records():
    """At start-up: journal lines older than STAFF_JOURNAL_DAYS, and slip images beyond the newest SLIP_IMAGES_KEPT."""
    log_dir = app_paths.log_dir()
    path = os.path.join(log_dir, STAFF_JOURNAL)
    cutoff = time.strftime('%Y-%m-%d', time.localtime(time.time() - STAFF_JOURNAL_DAYS * 86400))
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        kept = [ln for ln in lines if ln.strip() and json.loads(ln).get('date', '') >= cutoff]
        if len(kept) != len(lines):
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(kept)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[-] Could not tidy the staff journal: {e}")
    try:
        slips = sorted(glob.glob(os.path.join(log_dir, "slip_*.png")), key=os.path.getmtime)
        for old in slips[:-SLIP_IMAGES_KEPT]:
            os.remove(old)
    except Exception:
        pass


def save_slip_image(img_str: str | None, number: str | None) -> str | None:
    """The slip as the reader saw it (the base64 PNG sent to Gemini), once per wager: logs/slip_<wager>_<date>.png."""
    if not img_str or os.environ.get("BETTY_HEADLESS") == "1":
        return None
    try:
        path = os.path.join(app_paths.log_dir(), f"slip_{number or 'unknown'}_{time.strftime('%Y%m%d')}.png")
        if not os.path.exists(path):
            os.makedirs(app_paths.log_dir(), exist_ok=True)
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_str))
        return path
    except Exception as e:
        print(f"[-] Could not save the slip image: {e}")
        return None


def save_staff_screenshot(number: str) -> str | None:
    """Betty's screen at the moment a wager goes to staff, before anything is backed out: logs/staff_<wager>_<time>.png,
    so a failure can be seen afterwards rather than guessed. Only the newest STAFF_SCREENSHOTS_KEPT are kept.
    Returns the file saved (None when it couldn't be)."""
    try:
        log_dir = app_paths.log_dir()  # next to the exe when packaged
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, f"staff_{number}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot().save(path)
        print(f"[*] Screen saved for staff: {path}")
        shots = sorted((f for f in os.listdir(log_dir) if f.startswith("staff_") and f.endswith(".png")),
                       key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
        for old in shots[:-STAFF_SCREENSHOTS_KEPT]:
            os.remove(os.path.join(log_dir, old))
        return path
    except Exception as e:
        print(f"[-] Could not save the staff screenshot: {e}")
        return None


def leave_wager_for_staff(number: str, reason: str):
    """
    A wager the program can't do. Test mode: back out and leave it unedited (staff are watching). Otherwise:
    Mark bet fao Manager, which moves it out of the unedited list. Either way: one sentence on the HUD, with a sound.
    """
    _wagers_left_for_staff.add(number)
    print(f"[!] Wager {number} needs staff: {reason}")
    shot = save_staff_screenshot(number)
    journal_staff("staff", wager=number, reason=reason, screenshot=shot, test_mode=test_mode_on.is_set())
    if test_mode_on.is_set():
        go_home()
        alert_staff(f"Wager {number} needs staff: {reason}. (Test mode: left unedited.)")
        STATUS_HUD.set_outcome(f"{number} -> staff: {reason} {time.strftime('%H:%M')}")
        return
    fao = mark_wager_fao(number)
    if fao == 'marked':
        alert_staff(f"Wager {number} sent to the manager (FAO): {reason}.")
    elif fao == 'already':
        alert_staff(f"Wager {number} needs staff: {reason}. (Already on the FAO list.)")
    else:
        alert_staff(f"Wager {number} needs staff: {reason}. Could NOT mark it FAO - please check Betty.")
    STATUS_HUD.set_outcome(f"{number} -> staff: {reason} {time.strftime('%H:%M')}")


_betty_hidden_reported = False  # "Betty isn't in front" printed once until she is again


def watcher_cycle():
    """One look: get to View Wagers, take the top wager not yet handled, or wait for the next poll."""
    global _betty_hidden_reported
    if not betty_in_front():  # a key now would land in whatever window is in front (the launcher, say)
        if not _betty_hidden_reported:
            print("[*] Betty isn't in front (or isn't open): the watcher waits and presses nothing.")
            _betty_hidden_reported = True
        refresh_watcher_hud(f"Betty isn't in front: waiting. Next look in {WATCHER_POLL_SECS:.0f}s.")
        t0 = time.time()
        while time.time() - t0 < WATCHER_POLL_SECS:
            _check_stop()
            time.sleep(0.1)
        return
    _betty_hidden_reported = False
    screen = detect_screen()
    if screen not in (SCREEN_HOME, SCREEN_VIEW_WAGERS):
        print(f"[*] Watcher found Betty on {screen}: backing out to Home first.")
        if not go_home():
            raise HomeUnreachable(f"could not get back to Home from {screen}")
    open_view_wagers()
    queue = read_unedited_queue(pyautogui.screenshot())
    now = time.time()
    todo = [(i, n) for i, n in enumerate(queue)
            if n not in _wagers_left_for_staff and _open_elsewhere_until.get(n, 0) <= now]
    if todo:
        print(f"[*] Unedited list: {queue} (done or left for staff this session, not opened again: {sorted(_wagers_left_for_staff) or 'none'})")
    for row, number in todo:
        try:
            watcher_process_wager(row, number)
            return
        except WagerOpenElsewhere as e:  # another till has it: leave it alone, next wager on the ladder
            _open_elsewhere_until[number] = time.time() + OPEN_ELSEWHERE_RETRY_SECS
            print(f"[*] Wager {number}: {e}. Moving on to the next wager; will look again in {OPEN_ELSEWHERE_RETRY_SECS}s.")
            STATUS_HUD.set_outcome(f"{number} open on {e} - skipped for now {time.strftime('%H:%M')}")
    busy = sum(1 for n in queue if _open_elsewhere_until.get(n, 0) > time.time())
    msg = "No unedited wagers. " if not queue else (
        f"No wager to do now ({busy} open on another till, {len([n for n in queue if n in _wagers_left_for_staff])} left for staff). ")
    refresh_watcher_hud(msg + f"Next look in {WATCHER_POLL_SECS:.0f}s.")
    t0 = time.time()
    while time.time() - t0 < WATCHER_POLL_SECS:
        _check_stop()
        time.sleep(0.1)


def resume_after_staff_idle() -> bool:
    """Paused because staff used the till (not switched off with `): back on once the till has been idle for
    STAFF_IDLE_RESUME_SECS (no key, click or mouse movement). Returns True when it switched the watcher back on."""
    global _paused_for_staff, _watcher_resume_at
    if (watcher_on.is_set() or not _paused_for_staff
            or time.time() - _last_staff_activity < STAFF_IDLE_RESUME_SECS):
        return False
    _paused_for_staff = False
    _watcher_resume_at = time.time()
    watcher_on.set()
    print(f"[*] No till activity for {STAFF_IDLE_RESUME_SECS}s: watcher back on, watching View Wagers.")
    refresh_watcher_hud(f"No activity for {STAFF_IDLE_RESUME_SECS}s: watcher back on.")
    return True


def _go_home_from_handler() -> bool:
    """go_home for watcher_loop's error handlers: an exception raised inside an `except` clause would leave the loop
    and end the watcher thread (the HUD still showing it on), so a failure here is only reported."""
    try:
        return go_home()
    except Exception as e:
        print(f"[-] Backing out to Home failed: {e}")
        return False


def watcher_loop():
    """While the watcher is on: work through unedited wagers (see watcher_cycle), recovering to Home on any trouble."""
    global watcher_busy, _watcher_stop_reason, _watcher_screen, _current_wager
    failures = 0
    while True:
        resume_after_staff_idle()
        wait = _watcher_resume_at - time.time()
        if wait > 0 and watcher_on.is_set():
            time.sleep(min(wait, 0.2))
            continue
        with _watcher_state_lock:  # "on?" and the reset are one step: a staff key now either stops it here or later
            starting = watcher_on.is_set()
            if starting:
                watcher_busy = True
                abort_event.clear()
                _watcher_stop_reason = ""
        if not starting:
            time.sleep(0.1)
            continue
        paused = False  # switched off (` / Pause) or staff used the till: the wager in hand is tried again on resume
        try:
            watcher_cycle()
            failures = 0
        except WatcherStop:
            reason = _watcher_stop_reason
            paused = reason in ("staff", "off")
            if reason in ("staff", "off"):  # ` is an instant pause that backs nothing out (user, 22 Oct)
                print(f"[*] Watcher stopped: {'staff have the terminal' if reason == 'staff' else 'switched off (`)'}. "
                      "Nothing touched.")
            else:
                print("[*] Watcher action stopped (Esc): backing out to Home.")
                abort_event.clear()
                if not _go_home_from_handler():
                    watcher_on.clear()
                    notify("Could not get Betty back to Home. Watcher off: please check Betty.", is_error=True)
            STATUS_HUD.set_outcome(f"stopped ({reason or 'Esc'}) {time.strftime('%H:%M')}")
        except PlacingRefused as e:
            print(f"[-] {e}")
            watcher_on.clear()
            notify(f"Watcher stopped: {e}", is_error=True)
        except WagerForStaff as e:
            failures = 0
            number, _current_wager = _current_wager, None
            abort_event.clear()
            if number:
                try:
                    leave_wager_for_staff(number, str(e))
                except WatcherStop:
                    print(f"[*] Wager {number} left for staff (watcher switched off).")
                except Exception as fao_error:  # e.g. NavError marking it FAO: the wager is already left for staff
                    print(f"[-] Wager {number}: could not finish leaving it for staff: {fao_error}")
                    _go_home_from_handler()
                    alert_staff(f"Wager {number} needs staff: {e}. Could NOT mark it FAO - please check Betty.")
                    STATUS_HUD.set_outcome(f"{number} -> staff: {e} {time.strftime('%H:%M')}")
            if _home_unreachable:  # backing out for the FAO failed: the next look would only press Esc again
                watcher_on.clear()
                notify("Could not get Betty back to Home. Watcher off: please check Betty.", is_error=True)
        except HomeUnreachable as e:
            print(f"[-] Watcher: {e}. Watcher off.")
            STATUS_HUD.set_outcome(f"problem: {e}")
            watcher_on.clear()
            notify(f"Watcher stopped: {e}. Please check Betty.", is_error=True)
        except NavError as e:
            if _current_wager:  # a navigation glitch is not the wager's fault: one more go before leaving it
                _nav_failures[_current_wager] = _nav_failures.get(_current_wager, 0) + 1
                if _nav_failures[_current_wager] < 2:
                    _current_wager = None
            failures += 1
            print(f"[-] Watcher{f' (wager {_current_wager})' if _current_wager else ''}: {e}")
            STATUS_HUD.set_outcome(f"problem: {e}")
            abort_event.clear()
            if failures >= WATCHER_UNKNOWN_LIMIT or not _go_home_from_handler():
                watcher_on.clear()
                notify(f"Watcher stopped: {e}. Please check Betty.", is_error=True)
            elif _current_wager:  # its second navigation failure: FAO in live mode, with a sound (review R8)
                number, _current_wager = _current_wager, None
                try:
                    leave_wager_for_staff(number, f"Betty's screens went wrong twice while entering it ({e})")
                except WatcherStop:
                    print(f"[*] Wager {number} left for staff (watcher switched off).")
                except Exception as fao_error:
                    print(f"[-] Wager {number}: could not finish leaving it for staff: {fao_error}")
                    _go_home_from_handler()
                    alert_staff(f"Wager {number} needs staff: {e}. Could NOT mark it FAO - please check Betty.")
        except Exception as e:
            print(f"[-] Watcher error{f' (wager {_current_wager})' if _current_wager else ''}: {e}")
            watcher_on.clear()
            notify(f"Watcher error: {e}. Watcher off.", is_error=True)
        finally:
            if _current_wager and paused:
                # A pause is not the wager's fault: it stays in the queue, and the watcher backs out to Home before
                # opening it again (user, 28 Oct: 9.2455510 / 512 / 514 were skipped for the session after `)
                print(f"[*] Wager {_current_wager}: paused part-way; it stays in the queue and is tried again on resume.")
            elif _current_wager and _wager_opened:
                _wagers_left_for_staff.add(_current_wager)  # stopped (Esc) or failed part-way: leave it for staff
                print(f"[!] Wager {_current_wager} left unedited for staff after the problem above (not marked FAO).")
                journal_staff("staff", wager=_current_wager, reason="stopped part-way: left unedited, not marked FAO",
                              screenshot=None, test_mode=test_mode_on.is_set())
                alert_staff(f"Wager {_current_wager} was left unedited part-way: please check it in Betty.")
            elif _current_wager:  # stopped before its bet edit was opened: nothing done to it, look again next time
                print(f"[*] Wager {_current_wager}: stopped before it was opened; it stays in the queue.")
            _current_wager = None
            with _watcher_state_lock:
                watcher_busy = False
                abort_event.clear()
        try:
            _watcher_screen = detect_screen()
        except Exception:
            _watcher_screen = SCREEN_UNKNOWN
        refresh_watcher_hud()


def check_screen_once(delay: float = 5.0):
    """Read-only diagnosis (python betty_companion.py --check-screen): one screenshot after `delay` seconds, then what
    the watcher would see. No key, no click."""
    print(f"[*] Screen check in {delay:.0f}s: bring Betty to the front...")
    time.sleep(delay)
    img = pyautogui.screenshot()
    screen = detect_screen(img)
    print(f"[*] Screen: {screen}")
    if screen == SCREEN_VIEW_WAGERS:
        print(f"[*] Unedited list: {read_unedited_queue(img)} (top box: {view_wagers_queue_state(img)})")
        d = read_wager_details(img)
        print(f"[*] Loaded wager: {d['number']!r} | struck {d['struck_clock']!r} -> {d['struck_time']!r} | "
              f"Payment {d['payment_pence']!r}p")
        print(f"[*] Summary as read: {d['summary']!r}")


# --- 7. LAUNCHER LINK (--backend) ---
# The launcher window runs this program with --backend and sends one command per line on stdin; this program answers
# with status events on stdout (backend_event): hello, ready, state, message, outcome, staff, error, fatal, bye.
BACKEND_QUIT_WAIT_SECS = 10  # Stop: how long a wager in hand gets to stop touching Betty before the program closes


def backend_quit(why: str = "Stop in the launcher"):
    """The launcher's Stop, or the launcher closed: the watcher off at once (nothing more is touched; a wager in hand
    is left for staff), a moment for it to let go of Betty, then the program ends."""
    set_watcher(False, why)
    t0 = time.time()
    while watcher_busy and time.time() - t0 < BACKEND_QUIT_WAIT_SECS:
        time.sleep(0.1)
    print(f"[*] Closing ({why}).")
    backend_event("bye", clean=not watcher_busy)
    sys.exit(0)


def handle_backend_command(line: str):
    """One command from the launcher: start, pause, test, live, status or quit."""
    cmd = line.strip().lower()
    if not cmd:
        return
    if cmd == "start":
        set_watcher(True, "Start in the launcher")
        focus_betty()  # the launcher has just stepped aside: Betty in front for the watcher
    elif cmd == "pause":
        set_watcher(False, "Pause in the launcher")
    elif cmd in ("test", "live"):
        set_test_mode(cmd == "test")
    elif cmd == "status":
        backend_event("state", **watcher_state())
    elif cmd == "quit":
        backend_quit()
    else:
        backend_event("error", text=f"unknown command: {cmd!r}")


def _open_command_stream():
    """stdin, where the launcher writes its commands (a windowed build starts without sys.stdin, so handle 0)."""
    if sys.stdin is not None:
        return sys.stdin
    try:
        return open(0, "r", encoding="utf-8", closefd=False)
    except OSError:
        return None


def backend_command_loop():
    """The launcher's commands until it closes the pipe (it quit or crashed), then shut down as for Stop."""
    stream = _open_command_stream()
    if stream is not None:
        for line in stream:
            try:
                handle_backend_command(line)
            except Exception as e:  # one bad command must not end the link (SystemExit, from quit, still does)
                print(f"[-] Launcher command {line.strip()!r} failed: {e}")
                backend_event("error", text=f"{line.strip()}: {e}")
    backend_quit("the launcher closed")


# --- 8. THE IDLE DAEMON ---
def main():
    """Start-up, run as a script (python betty_companion.py) or by the exe (BettyCompanion.exe --backend)."""
    if "--check-screen" in sys.argv:
        check_screen_once()
        sys.exit(0)
    sw, sh = get_screen_resolution()
    backend_event("hello", version=__version__, pid=os.getpid(), log=SESSION_LOG, screen=f"{sw}x{sh}")
    print("=======================================")
    print(f" {APP_NAME} - Active [{bookmaker_rules_mgr.get_firm_name()}]")
    print(f" Resolution: {sw}x{sh}")
    print("=======================================")
    if (sw, sh) != REQUIRED_RESOLUTION:
        msg = (f"Screen is {sw}x{sh}. Betty Companion only supports {REQUIRED_RESOLUTION[0]}x{REQUIRED_RESOLUTION[1]}; "
               "set the display to that size and restart.")
        print(f"[-] {msg}")
        notify(msg, is_error=True)
        backend_event("fatal", text=msg)
        time.sleep(8)
        sys.exit(1)
    print(" -> Press '`' (backtick) to switch the watcher on/off.")
    print(" -> Press 'Shift + `' to switch test mode on/off "
          f"(now {'ON: stops before placing' if test_mode_on.is_set() else 'OFF: places wagers'}).")
    print(" -> Press 'ESC' at any time to abort automation.\n")
    route = reader_route()
    link = relay_link.saved_link() if route == "relay" else None
    print("[*] Slip reader: " + (f"the relay at {link['url']} (this till: {link['name']})" if link
                                  else "Gemini keys in .env" if route == "keys"
                                  else "none set up: every slip goes to staff") + ".")
    prune_staff_records()
    print("[*] Idle Daemon Ready.\n")

    keyboard.add_hotkey('`', toggle_watcher, suppress=True)
    keyboard.add_hotkey('shift+`', toggle_test_mode, suppress=True)
    HumanInputMonitor(on_staff_input).start()
    threading.Thread(target=watcher_loop, daemon=True).start()
    refresh_watcher_hud()

    if BACKEND_MODE:
        backend_event("ready", test_mode=test_mode_on.is_set(), tesseract=TESSERACT_EXE,
                      readers=[t['label'] for t in reader_tiers()], route=route)
        backend_command_loop()
    else:
        keyboard.wait()


if __name__ == "__main__":
    main()
