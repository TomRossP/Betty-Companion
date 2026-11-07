__version__ = "1.3.7"
APP_NAME = f"Betty Companion v{__version__}"


import pyautogui  # type: ignore
import pytesseract
import keyboard  # type: ignore
import time
import os
import queue
import math
import itertools
from collections import Counter, deque
from dotenv import load_dotenv
import app_paths
import lessons
import relay_link

# Load variables from .env (next to the exe when packaged, else in the project folder) into os.environ
load_dotenv(app_paths.env_file())

import re
import base64
import calendar
import io
import json
import requests
import ctypes
import subprocess
import sys
import tkinter as tk
import threading
import atexit
import concurrent.futures
import glob
import shutil
import stat
import tempfile
from difflib import SequenceMatcher
from fractions import Fraction
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
    whole_bets,
)

# Betty local racecard feeds (C:\Events)
from betty_feed import BettyFeedCard, BettyOffTimes, DOMESTIC_COUNTRIES, DOG_SPORTS, SportsCard

# Centralized Meetings Directory Manager (Virtual, Greyhound, International & Aliases)
from meetings_manager import meetings_manager

# Betty's Master Index: how sports selections are entered
import master_index as mi
import sports_names

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


def _ask_tesseract_version_hidden():
    """
    pytesseract asks tesseract.exe its version once a run, on the first image_to_data, and that is its one run of
    tesseract.exe it doesn't hide. The console window took the keyboard from Betty 0.3 s after 'l' on Choose Bet and
    Stake, and Betty put Home in front of its bet edit 0.7 s later (recording of 9.2460715, 1 Nov; the forecasts that
    went Home on 1.2.1-1.2.11 the same way). 1.2.0's first image_to_data was on the runner list, where it did no harm;
    1.2.1's quicker reads left the bet list as the first. Asked here, hidden, before Betty is touched: pytesseract
    keeps the answer for the rest of the run.
    """
    check_output = subprocess.check_output
    subprocess.check_output = lambda *a, **k: check_output(*a, creationflags=subprocess.CREATE_NO_WINDOW, **k)
    try:
        pytesseract.get_tesseract_version()
    except (Exception, SystemExit) as e:  # pytesseract exits on a version it can't read
        print(f"[-] Tesseract's version could not be asked ({e}): its window may open over Betty once, on the first "
              "read of a list.")
    finally:
        subprocess.check_output = check_output


if TESSERACT_EXE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
    _ask_tesseract_version_hidden()
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
    _require_betty()
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
SCAN_TIMEOUT_SECS = app_paths.setting("SCAN_TIMEOUT_SECS", 90)     # timed-out requests are still billed: keep these generous
RECHECK_TIMEOUT_SECS = app_paths.setting("RECHECK_TIMEOUT_SECS", 45)


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
    key = (runner_meeting, hinted, lessons.version())  # a lesson taught since changes the answer
    if key not in _meeting_match_cache:
        _meeting_match_cache[key] = _meeting_matches_uncached(runner_meeting, hinted)
    return _meeting_match_cache[key]


def _meeting_matches_uncached(runner_meeting: str, hinted: str) -> bool:
    taught = lessons.meeting_for(hinted)  # this shop's own way of writing it ('N/M' = Newmarket): it decides
    if taught:
        return (lessons.letters(taught['means']) == lessons.letters(runner_meeting)
                or meetings_manager.are_meetings_equivalent(runner_meeting, taught['means']))
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
    borrowed = bool(horse.get('_time_borrowed'))  # no time written: the line above's says little about an unclear name

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
        if target_mins is not None and not race_at_time_seen and not borrowed:
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


NAMES_A_BET = re.compile(r"\b(?:doub\w*|dbl\w*|dousl|dubs|treb\w*|9reb|greb|acc\w*|fold\w*|\d+\s*-?\s*folds?|perm\w*|trix\w*|patent|yank\w*|"
                         r"lucky|heinz|goliath|canad\w*|forecasts?|tricasts?|cast|f/?c\w*|[srt]/?f\w*|cfc|rfc|sfc)\b", re.IGNORECASE)


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
        # With no bet line below this one, a runner below it has no other bet to belong to: it's this one's, written under its
        # stake (9.2468449, 6 Nov: '£1 c/fc 2 / 3 / 5' lost the 5 and the money was made up by making another bet each way)
        bet_line_below = effective_line is not None and any((other.get('line_num') or 0) > effective_line for other in bets_list)
        if (len(bets_list) > 1 and effective_line is not None and line_nums_read and len(preceding_selections) > 0
                and len(preceding_selections) < len(selections) and bet_line_below):
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
            min_n = req_n or {'straight forecast': 2, 'reversed forecast': 2, 'combination forecast': COMBINATION_FORECAST_MIN,
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
            # '6 x £1.50 E/W' on 6 selections, no bet type written: 6 singles (below), not the 4 runners that make 6 doubles
            if mult_val == len(bet.get('horses', [])) and mult_val != 3 and not NAMES_A_BET.search(combined_text):
                inferred_n = None

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

        # 'N x' on N selections with no bet type written is N singles (user, 6 Nov). 6 x also makes six 5-folds at the same money, so
        # nothing later would catch it (9.2468424: '6 x £1.50 E/W' taken for Perm 5-Folds). Not 3 x: a regular customer scrawls 'dbl'
        # after it, which the reader can miss, and his go in right as doubles (user, 6 Nov), so that stays as it is below.
        if mult_num == n_horses and n_horses >= 2 and n_horses != 3 and not is_fc_or_tri and not NAMES_A_BET.search(combined_text):
            print(f"[+] Reconciled Bet #{b_idx + 1} '{desc}': {mult_num}x on {n_horses} selections, no bet type written: {n_horses} singles.")
            bet['bet_type'] = 'single'
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        elif is_fc_or_tri or keeps_written_type:
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

        # A printed count of twice the bet's bets is each way, whatever the box says (printed_count_is_each_way)
        if printed_count_is_each_way(f"{desc} {lines_map.get(b_line, '') if b_line is not None else ''}", bet):
            if not bet.get('each_way'):
                print(f"[+] Printed count: Bet #{b_idx + 1} '{desc}' is each way, the box's count being twice the bet's bets.")
            bet['each_way'] = True
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        # EW Conflict Resolution with Line Transcription:
        elif bet.get('each_way'):
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
    (5xx, timeout, connection), 'bad_key' (Google: not a valid key), 'unavailable' (other HTTP errors), 'blocked',
    'bad_json' or 'aborted'.
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
        if code in (400, 403) and re.search(r'api key not valid|api_key_invalid', msg, re.I):
            return 'bad_key', None
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
GEMINI_QUOTA_PAUSE_SECS = app_paths.setting("GEMINI_QUOTA_PAUSE_SECS", 600)
_gemini_bad_keys: set[str] = set()  # keys Google called not valid: skipped for the rest of the run


def bad_key_advice(key: str, key_no: int) -> str:
    """What to replace when Google says a key isn't valid: the relay's secret for a relay slot, else the key in .env."""
    if key.startswith(relay_link.RELAY_KEY_PREFIX):
        slot = key[len(relay_link.RELAY_KEY_PREFIX):]
        secret = {'paid': 'GEMINI_KEY_PAID'}.get(slot) or f"GEMINI_KEY_FREE_{slot.removeprefix('free')}"
        return f"the relay's {secret} isn't a valid Gemini key: replace it in Cloudflare (relay\\RELAY_SETUP.md)"
    return f"Gemini key {key_no} of this step in .env isn't valid: replace it"


def gemini_tier_request(payload: dict, keys: list[str], models: list[str], timeout: float, label: str) -> dict | None:
    """
    Try each key, each model in order. No credit (402), not a valid key or refused by the relay -> next key; quota
    (429), blocked, bad JSON or unavailable -> next model; busy / timeout -> one retry of the same model, then the
    next. None when nothing answered.
    """
    for key_no, key in enumerate(keys, 1):
        if key in _gemini_bad_keys:
            continue
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
            if status == 'bad_key':  # the free key on the relay, 2 Nov: tried on every slip, never valid
                _gemini_bad_keys.add(key)
                print(f"[!] {label}: {bad_key_advice(key, key_no)}. Not tried again this run.")
                break
    return None


RELAY_FREE_SLOTS = ["relay:free1"]  # the relay's free Gemini project (GEMINI_KEY_FREE_1); the second went 3 Nov


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
    global _last_reading
    _last_reading = {'wager': _current_wager, 'img_str': img_str,
                     'lines': [str(lt.get('raw_text', '')) for lt in lines_list]}
    # This shop's taught bet wording ('YANKIE' = yankee): the lines and bets read as if the meaning was written
    taught_used: dict[str, dict] = {}
    for lt in lines_list:
        lt['raw_text'], used = lessons.apply_wording(str(lt.get('raw_text', '')))
        taught_used.update((x['id'], x) for x in used)
    for b in bets_data.get('bets', []):
        for key in ('description', 'raw_text', 'bet_type'):
            if b.get(key):
                b[key], used = lessons.apply_wording(str(b[key]))
                taught_used.update((x['id'], x) for x in used)
    for x in taught_used.values():
        print(f"[+] Taught wording: '{x['written']}' read as '{x['means']}'.")
        _lesson_used(x)
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
        # And only one the slip itself bears out: the money alone made '£4 3' each way, hiding a selection lost from another bet,
        # and it was placed wrong (9.2468449, 6 Nov). The line is read again on its own, not told what's wanted.
        wanted = ("win" if bets_list[flips[0]].get('each_way') else "each way") if len(flips) == 1 else None
        if wanted and stake_second_read(bets_list[flips[0]], img_str) != wanted:
            print(f"[-] Total Stake Reconciliation Healer: Bet #{flips[0] + 1} as {wanted} would fit the money, but a second read of "
                  "the line doesn't say so: not changed.")
        elif len(flips) == 1:
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
  between runners in different races), "s/f/cast", "sfc", "sf/c", "s/f" = straight forecast, "r/f/cast", "r/f cast", "rfc", "r/f", "rf" = reversed
  forecast ("50 r/f cast" is a reversed forecast on the 2 above, not a double; a hasty "cast" looks like "last", but "last" always has a
  number with it), "cfc", "c/fc", "c/f" = combination forecast, "f/c doubles" = forecast double. Full covers: trixie, patent, yankee,
  canadian, heinz, super heinz, goliath, lucky 15 / 31 / 63. A printed coupon heading names the bet type.
- The printed PATENT coupon has two stake boxes at its foot, "WIN 7 @" and "WIN 14 @". The second is a printing error for each way
  (14 bets is 7 each way): a stake in it has each_way true. raw_text keeps the printed words and the count.
- A regular customer writes a row of runner numbers ("3-4-1"), then the stake and "each way" run together as one fast scrawl with no
  clear letters: a 5, a squiggle, then a tall stroke looping up towards the numbers. It is "50p each way": each way singles on
  those numbers, never a combination forecast or tricast, whose letters are written separately.

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


READ_KEPT_SECS = 86400  # a saved read this old is gone at the next start, whatever became of its wager
SAVE_READS = os.environ.get("BETTY_HEADLESS") != "1"  # the free tests' made-up wagers aren't kept


def _read_file(number: str | None) -> str | None:
    return os.path.join(app_paths.log_dir(), "saved_reads", f"{number}.json") if number and SAVE_READS else None


def save_read(number: str | None, reading: dict):
    """A paid read of a wager's slip, kept until the wager is done with (user, 6 Nov): stopped or paused part-way, it's used again
    on the way back, with no new call. A slip doesn't change, and its wager number is its own."""
    path = _read_file(number)
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"wager": number, "saved": time.time(), "reading": reading}, f, ensure_ascii=False)
        os.replace(path + ".tmp", path)
    except OSError as e:
        print(f"[-] Could not save the read of wager {number}: {e}")


def load_saved_read(number: str | None) -> dict | None:
    """The read saved for this wager, or None. One that's too old, or won't read, isn't used."""
    path = _read_file(number)
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fresh = data.get("wager") == number and time.time() - float(data.get("saved", 0)) < READ_KEPT_SECS
        return data.get("reading") if fresh else None
    except (OSError, ValueError, TypeError):
        return None


def forget_read(number: str | None):
    """The wager is done with, placed or left for staff: its read goes."""
    path = _read_file(number)
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def prune_saved_reads():
    """At start-up: reads left behind, as when a wager was dealt with on another till."""
    if not SAVE_READS:
        return
    for path in glob.glob(os.path.join(app_paths.log_dir(), "saved_reads", "*.json*")):
        try:
            if time.time() - os.path.getmtime(path) > READ_KEPT_SECS:
                os.remove(path)
        except OSError:
            pass


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
    
    if not retry_hint:  # a rescan is asked for because the last read didn't add up: only then a new one
        saved = load_saved_read(_current_wager)
        if saved:
            print(f"[*] Slip scan: using the read saved for wager {_current_wager}, no new call (it was paused or stopped).")
            return process_slip_reading(saved, img_str, payment_pence)

    struck_mins = parse_clock_minutes(struck_time)
    from_mins = None if struck_mins is None else max(0, struck_mins - CARD_FROM_BEFORE_STRUCK_MINS) // 60 * 60
    card_txt = card_for_prompt(racecard_manager.get_runners() + greyhound_card.get_runners(),
                               full=bool(retry_hint), from_mins=from_mins)
    retry_section = f"\nTHIS IS A RESCAN. {retry_hint}\n" if retry_hint else ""
    taught_text, _ = lessons.prompt_section()
    examples = lessons.slip_examples()
    prompt_text = (f"{SLIP_READER_RULES}\n\nTODAY'S CARD (meeting: race times as customers write them, 12-hour):\n"
                   f"{card_txt}\n{taught_text}{retry_section}")
    example_parts = []
    for x in examples:  # worked examples: a slip from this shop and its lines exactly as staff read them
        try:
            with open(x['image'], "rb") as f:
                pic = base64.b64encode(f.read()).decode('utf-8')
        except OSError:
            continue
        example_parts += [{"text": "EXAMPLE: a slip from this shop, and its lines exactly as the shop's staff read it"
                                   + (f" ({x['note']})" if x.get('note') else "") + ":\n" + "\n".join(x['lines'])},
                          {"inline_data": {"mime_type": "image/png", "data": pic}}]
    if example_parts:
        example_parts.append({"text": "Now the customer's slip to read:"})
        try:  # shown, counted; not tied to this wager's outcome (they go with every slip)
            lessons.mark_used(x['id'] for x in examples)
        except Exception as e:
            print(f"[-] Could not count the example slips shown: {e}")
    # Meeting and wording lessons in the instructions count where they change a reading (pre-flight, apply_wording)

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
        "contents": [{"role": "user", "parts": [{"text": prompt_text}, *example_parts,
                                                {"inline_data": {"mime_type": "image/png", "data": img_str}},
                                                {"text": instruction}]}],
        "generationConfig": {"response_mime_type": "application/json", "response_schema": schema}
    }
    bets_data = read_vision_json(payload, "Slip scan", timeout=SCAN_TIMEOUT_SECS, remember_tier=True)
    if bets_data is None:
        return None, None, None, None, None
    save_read(_current_wager, bets_data)
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


WHOLE_CARD_FIT = 0.70       # how well the writing must fit a runner's name when the written price agrees too
WHOLE_CARD_FIT_ALONE = 0.88  # ... when there's no written price to agree
WHOLE_CARD_MARGIN = 0.12    # how far ahead of the next runner it must be
WHOLE_CARD_OFFER = 10       # runners from the whole card shown to the race-list check


def name_fit(written: str, runner: str) -> float:
    """How well writing fits a runner's name, as a whole or as its start: customers stop writing ('HARROW ON THE')."""
    a, b = clean_horse_name(written), clean_horse_name(runner)
    if not a or not b:
        return 0.0
    whole = name_similarity(a, b)
    return max(whole, name_similarity(a, b[:len(a)]) - 0.03) if len(a) >= 6 and len(a) < len(b) else whole


def written_price(horse: dict) -> Fraction | None:
    """The price written beside a selection, None for SP or nothing."""
    return _price_value(horse.get('price')) if str(horse.get('price') or '').strip().lower() not in ('', 'sp', 'none', '0') else None


def whole_card_ranking(horse: dict, runners: list[dict], struck_mins: float | None, taken: tuple = ()) -> list[dict]:
    """
    An unclear name against every runner still to run when the bet was struck, using all that's known about the
    selection (user, 6 Nov): how the name fits, Betty's price against the written one, the written time if there is one
    (a time borrowed from the line above counts for nothing) and the meeting. A runner already on the slip as another
    selection is left out. Best first: [{'runner', 'score', 'fit', 'agrees' (True / False / None: nothing to compare)}].
    """
    want = written_price(horse)
    hinted = _hinted_meeting(horse)
    times = set() if horse.get('_time_borrowed') else written_race_times(horse)
    ranked = []
    for r in runners:
        if r.get('category') == 'virtual' or not still_to_run(r, struck_mins):
            continue
        if (r['meeting'], r['time_str'], r.get('number')) in taken:
            continue
        fit = name_fit(str(horse.get('name') or ''), r['name'])
        betty = _price_value(r.get('price'))
        agrees = None if want is None or betty is None else want == betty
        score = fit + {True: 0.25, False: -0.05, None: 0.0}[agrees]
        if times:
            score += 0.10 if any(abs((r.get('minutes') or 0) - m) <= TIME_AGREE_MINS for m in times) else -0.10
        if hinted and _meeting_matches(r['meeting'], hinted):
            score += 0.05
        ranked.append({'runner': r, 'score': score, 'fit': fit, 'agrees': agrees})
    ranked.sort(key=lambda c: c['score'], reverse=True)
    return ranked


def whole_card_pick(ranked: list[dict]) -> dict | None:
    """The best of whole_card_ranking when it clearly stands out, on its name and the written price, or its name alone."""
    if not ranked:
        return None
    best = ranked[0]
    same_name = clean_horse_name(best['runner']['name'])
    next_score = next((c['score'] for c in ranked[1:] if clean_horse_name(c['runner']['name']) != same_name), 0.0)
    if best['score'] - next_score < WHOLE_CARD_MARGIN:
        return None
    if best['agrees'] is False:
        return None
    return best if best['fit'] >= (WHOLE_CARD_FIT if best['agrees'] else WHOLE_CARD_FIT_ALONE) else None


def pick_doubt(horse: dict, runner: dict) -> str | None:
    """
    Why a runner chosen for an unclear name can't stand. Written price: Betty's must be the same (9.2467175: 14-1 written,
    Mountain Of Light was 9-1; the four right picks that day all agreed). No price: a runner number written must be its
    number. A moved price sends a right pick to staff, which is the safe way to be wrong.
    """
    want = written_price(horse)
    if want is not None:
        betty = _price_value(runner.get('price'))
        if betty is None:
            return f"Betty has no price for {runner['name']} to compare with the {horse.get('price')} written"
        if betty != want:
            return f"{horse.get('price')} is written, but Betty has {runner['name']} at {runner.get('price')}"
        return None
    number = re.search(r'\d+', str(horse.get('name') or ''))
    if number and int(number.group(0)) == runner.get('number'):
        return None
    return f"no price is written to check {runner['name']} against"


def reexamine_runner_with_ai(horse: dict, horse_idx: int, img_str: str, api_key: str, candidates: list[dict], runners: list[dict]) -> dict | None:
    """
    Race-list check for one selection the matcher could not confirm, done the way a cashier does it: the reader
    sees every runner in the race(s) at the written time (meeting letter respected) plus the matcher's best
    guesses from the whole card, copies the letter shapes as written, then compares them with the real names. Betty's
    price is shown as support, never as the reason. A time borrowed from the line above isn't a written time.
    Accepted only with high confidence; a pick outside the races at the written time also needs a strong name
    fit, so a misread time cannot let a loosely similar name through.
    Returns the runner, or None (the caller then asks staff to confirm the selection).
    """
    if not img_str or not api_key:
        return None
    if horse.get('_time_borrowed'):
        horse = {**horse, 'raw_time': '', 'written_time': '', 'time': ''}
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
        listing.append(f"  {i}. {r['name']}" + (f" ({race})" if i > len(in_race) else "")
                       + (f" [Betty's price {r['price']}]" if r.get('price') else ""))
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
4. The odds written beside the name are the price taken. Betty's current price is shown beside each runner. A match
   supports a runner whose letter shapes fit, but never choose a runner because of its price alone.
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
    fit = max((name_fit(n, chosen['name']) for n in (shapes, first_read) if n), default=0.0)
    if fit >= NAME_ACCEPT_WITH_TIME or (fit >= 0.5 and not pick_doubt(horse, chosen)):
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


def taught_runner(horse: dict, runners: list[dict], written_time: str, written_meeting: str) -> tuple[dict, dict] | None:
    """
    A runner staff taught for this handwriting (lessons 'runner': the name as read -> the runner it was), when that
    runner is on today's card at the written time (and meeting, when one is written) and only one race fits.
    (runner, lesson) or None.
    """
    _, hhmm = parse_race_time_to_minutes(written_time) if written_time else (None, '')
    times = _times_12h_apart(hhmm) if hhmm else None
    for lesson in lessons.runner_lessons(horse.get('name')):
        fits = [r for r in runners if lessons.letters(r['name']) == lessons.letters(lesson['means'])
                and (times is None or r.get('time_str') in times)
                and (not written_meeting or _meeting_matches(r['meeting'], written_meeting))]
        if len(fits) == 1:
            return fits[0], lesson
    return None


def teach_from_manual_entry(read: dict, horse: dict, image: str | None) -> list[dict]:
    """
    Lessons from a selection staff typed in the can't-read box ('Remember this' ticked): the name as read is the
    runner it matched (unless they read the same), and a meeting written 2+ letters long that didn't match is the
    runner's meeting (a single letter is never a lesson: 'N' is Newmarket one race and Newcastle the next).
    """
    taught = []
    if os.environ.get("BETTY_HEADLESS") == "1":  # the free tests' made-up entries teach nothing
        return taught
    try:
        name = str(read.get('name') or '').strip()
        if name and not name.isdigit() and selection_number({'name': name}) is None and horse.get('name') \
                and not horse.get('favourite'):
            x = lessons.add('runner', name, horse['name'], {'meeting': horse.get('meeting'), 'time': horse.get('time')},
                            "typed in the can't-read box", image=image)
            taught += [x] if x else []
        meeting = str(read.get('meeting') or '').strip()
        if (len(lessons.letters(meeting)) >= 2 and horse.get('meeting')
                and not _meeting_matches(horse['meeting'], meeting)):
            x = lessons.add('meeting', meeting, horse['meeting'], source="typed in the can't-read box", image=image)
            taught += [x] if x else []
    except Exception as e:
        print(f"[-] Could not save what staff taught: {e}")
    for x in taught:
        print(f"[+] Learned: '{x['written']}' = {x['means']} ({lessons.KINDS[x['kind']].lower()}).")
    if taught:
        _lesson_sync_now.set()  # to the shop's other tills now
    return taught


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
        remember = tk.BooleanVar(root, value=True)
        tk.Checkbutton(root, text="Remember this for next time (shown on the System tab, Training)", variable=remember,
                       font=('Segoe UI', 9), fg=fg, bg=bg, selectcolor='#263238', activebackground=bg,
                       activeforeground=fg).pack(padx=16, pady=(4, 0), anchor='w')

        def on_confirm():
            entry = {k: v[1].get() for k, v in fields.items()}
            problem = apply_manual_entry(horse, entry, runners, struck_mins)
            if problem:
                error.config(text=problem)
                return
            result['confirmed'] = True
            result['typed'] = entry
            result['remember'] = remember.get()
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
    image = save_slip_image(slip_img, _current_wager)
    taught = teach_from_manual_entry(read, horse, image) if result.get('remember') else []
    journal_staff("manual", wager=_current_wager, selection=horse_idx, read=read, typed=result.get('typed'),
                  matched={k: horse.get(k) for k in ('name', 'number', 'meeting', 'time', 'price')},
                  image=image, test_mode=test_mode_on.is_set(), taught=[x['id'] for x in taught])
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


def race_list_pick_already_taken(resolved: dict, picks: set, borrowed: set = frozenset()) -> str | None:
    """
    The reason for staff when a runner chosen by the race-list check is also another selection on the slip. That check
    only knows the runners at the written time, so with a name it can't read and the time wrong or borrowed it can
    land on a runner already taken: "14-1 HARROW ON THE", no time, read 'MARROW ON THE' with 4:30 from the line above,
    was made Mountain Of Light, already on the slip at 9-1. The bets still cost what was paid (9.2467175, 5 Nov).
    `resolved`: {(time, written name): runner locked}. `picks`: the keys the race-list check chose. `borrowed`: those
    with no time written, taken from the line above: such a pick in the same race as another selection is no better
    (another runner in that 4:30 would have made the same false clash), though two runners in a race are often meant.
    """
    def runner(res: dict) -> tuple:
        return res.get('meeting'), res.get('time'), res.get('number')

    for key in picks:
        for other, res in resolved.items():
            if other[1] == key[1]:  # the same written name: one selection, even if it was collected under two times
                continue
            if runner(res) == runner(resolved[key]):
                r = resolved[key]
                return (f"the race-list check made '{key[1]}' {r.get('name')} #{r.get('number')} "
                        f"{clock_12h(str(r.get('time') or ''))} {r.get('meeting')}, already on the slip as '{other[1]}': "
                        "it's probably another runner, so check that selection on the slip")
            if key in borrowed and runner(res)[:2] == runner(resolved[key])[:2]:
                r = resolved[key]
                return (f"the race-list check made '{key[1]}' {r.get('name')} #{r.get('number')} "
                        f"{clock_12h(str(r.get('time') or ''))} {r.get('meeting')} with no time written beside it, in "
                        f"the same race as '{other[1]}': it's probably another runner, so check that selection on the slip")
    return None


FULL_COVERS = ('trixie', 'patent', 'yankee', 'canadian', 'heinz', 'super heinz', 'goliath', 'lucky 15', 'lucky 31', 'lucky 63')
PRINTED_COUNT = re.compile(r"\b(?:win|e\s*/?\s*w)\s*(\d{1,3})\b|\b(\d{1,3})\s*(?:@|bets?\b)", re.I)


def printed_count_is_each_way(text: str, bet: dict) -> bool:
    """
    A full cover whose stake line carries a count of twice its bets is each way. The printed Patent coupon's two stake
    boxes both say WIN, 'WIN 7 @' and 'WIN 14 @': the second is a printing error for each way, as 14 is 7 bets twice
    (user, 9.2468555, 6 Nov: £5 in it, £70 paid, read as £35 to win).
    """
    if normalize_bet_type(str(bet.get('bet_type', ''))) not in FULL_COVERS:
        return False
    bets = calculate_bet_cost_pence(dict(bet, stake_pence=1, each_way=False))
    return any(int(a or b) == 2 * bets for a, b in PRINTED_COUNT.findall(text))


def bet_type_second_read(bet: dict, img_str: str) -> dict | None:
    """What kind of bet one line is, read again on its own and not told the first reading's reason. {'bet_type', 'confidence'}."""
    line = f"on line {bet['line_num']} of the writing (counting from the top), " if bet.get('line_num') else ""
    return _ask_vision_json(
        f"""You are checking one bet line on a handwritten betting slip. Find the bet line {line}first read as
"{bet.get('description')}". Read only what kind of bet it says, letter by letter from the ink. "r/f", "rf", "r/fc", "r/f/cast", "r/f cast", "rfc" is
a reversed forecast. "s/f", "sf", "s/fc", "s/f/cast", "s/f cast", "sfc" is a straight forecast. A hasty "cast" looks like "last". "c/f", "c/fc", "cfc" is a combination forecast. "dbl",
"doub", "double" is a double. Don't work it out from the runners, the money or other lines.
Answer "high" confidence only if the letters are clear.
Return JSON: {{"letters": "...", "bet_type": "double", "reversed forecast", "straight forecast", "combination forecast" or "other", "confidence": "high" or "low"}}""",
        img_str, "reader-chain",
        {"type": "OBJECT", "properties": {"letters": {"type": "STRING"}, "bet_type": {"type": "STRING"}, "confidence": {"type": "STRING"}},
         "required": ["letters", "bet_type", "confidence"], "propertyOrdering": ["letters", "bet_type", "confidence"]},
        f"Second read of the bet type on '{bet.get('description')}'")


def check_same_race_doubles(slip: list[dict], img_str: str | None):
    """
    A double on exactly two runners in one race can't be a double as written: it's a forecast misread, or the customer's mistake, which
    the house rule splits (9.2468368, 6 Nov: '50 r/f cast' read '50 dbl last', split into two each way singles and placed wrong). Its
    line is read again on its own. A forecast: the bet is that. Surely a double: the house rule stands. Anything else: staff.
    """
    if not img_str:
        return
    for bet in slip:
        horses = bet.get('horses', [])
        if (normalize_bet_type(str(bet.get('bet_type', ''))) != 'double' or len(horses) != 2
                or (horses[0].get('meeting'), horses[0].get('time')) != (horses[1].get('meeting'), horses[1].get('time'))):
            continue
        answer = bet_type_second_read(bet, img_str) or {}
        kind = str(answer.get('bet_type') or '').lower()
        sure = str(answer.get('confidence') or '').lower() == 'high'
        if sure and kind in ('reversed forecast', 'straight forecast'):
            print(f"[+] '{bet.get('description')}': two runners in one race, and a second read says {kind} ('{answer.get('letters')}').")
            bet.update(bet_type=kind, each_way=False, description=f"{bet.get('stake_pence')}p {kind}")
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        elif not (sure and kind == 'double'):
            raise WagerForStaff(f"'{bet.get('description')}' reads as a double on two runners in one race, and a second read "
                                f"couldn't say what it is ('{answer.get('letters', '')}')")


def combination_second_read(bet: dict, img_str: str) -> dict | None:
    """A line read as a combination on 3 runners, read again on its own: is it one, or each way? {'bet', 'confidence'}."""
    line = f"on line {bet['line_num']} of the writing (counting from the top), " if bet.get('line_num') else ""
    return _ask_vision_json(
        f"""You are checking one bet line on a handwritten betting slip. Find the bet line {line}first read as
"{bet.get('description')}", under a row of runner numbers. It says one of two things. A combination forecast or tricast has its
letters written separately: "c/f", "c/fc", "cfc", "comb", "c/t", "tricast". Or it is each way on each number: "e/w", "each way", or,
from one regular customer, the stake and "each way" run together as one fast scrawl with no clear letters: a 5, a squiggle, then a
tall stroke looping up towards the numbers. That scrawl is "50p each way", never a combination. Read it from the ink. Don't work it
out from the runners, the money or other lines. Answer "high" confidence only if you are sure which of them it is.
Return JSON: {{"letters": "...", "bet": "combination", "each way" or "other", "confidence": "high" or "low"}}""",
        img_str, "reader-chain",
        {"type": "OBJECT", "properties": {"letters": {"type": "STRING"}, "bet": {"type": "STRING"}, "confidence": {"type": "STRING"}},
         "required": ["letters", "bet", "confidence"], "propertyOrdering": ["letters", "bet", "confidence"]},
        f"Second read of the bet on '{bet.get('description')}'")


def check_combination_lines(slip: list[dict], img_str: str | None):
    """
    A combination on 3 runners in one race costs the same as each way singles on them (6 stakes), so the money can't tell them
    apart. A regular customer's '50p each way' scrawl was read as a combination forecast or tricast (9.2468502, 9.2468536, 9.2468543,
    6 Nov: staff entered each as 3 each way singles). The line is read again on its own. Each way: singles. Surely a
    combination: it stands. Anything else: staff.
    """
    if not img_str:
        return
    for bet in slip:
        horses = bet.get('horses', [])
        if (normalize_bet_type(str(bet.get('bet_type', ''))) not in ('combination forecast', 'combination tricast') or len(horses) != 3
                or len({(h.get('meeting'), h.get('time')) for h in horses}) != 1):
            continue
        answer = combination_second_read(bet, img_str) or {}
        kind = str(answer.get('bet') or '').lower()
        sure = str(answer.get('confidence') or '').lower() == 'high'
        if sure and kind == 'each way':
            print(f"[+] '{bet.get('description')}': a second read says each way on each number ('{answer.get('letters')}').")
            bet.update(bet_type='single', each_way=True, description=f"{bet.get('stake_pence')}p each way")
            bet['cost_pence'] = calculate_bet_cost_pence(bet)
        elif not (sure and kind == 'combination'):
            raise WagerForStaff(f"'{bet.get('description')}' reads as a combination on 3 runners, which costs the same as each way "
                                f"singles, and a second read couldn't say which it is ('{answer.get('letters', '')}')")


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
                s['_time_borrowed'] = True

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
                        '_time_borrowed': bool(s.get('_time_borrowed')),
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
    race_list_picks, borrowed_picks = set(), set()  # chosen by the race-list check; of those, with a borrowed time
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
        taught_meeting = lessons.meeting_for(written_meeting)
        if taught_meeting:
            print(f"[+] Taught meeting: '{written_meeting}' is {taught_meeting['means']}.")
            _lesson_used(taught_meeting)
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
            learned = taught_runner(sample_horse, runners, orig_time, written_meeting)
            if learned:
                runner_match, lesson = learned
                print(f"[+] Taught: '{orig_name}' -> '{runner_match['name']}' #{runner_match.get('number')} at "
                      f"{runner_match['meeting']} ({runner_match['time_str']}) (staff taught '{lesson['written']}' = "
                      f"{lesson['means']}){p_disp}")
                _lesson_used(lesson)
                _resolve((h_time, h_name), runner_match, price)
                continue
            # Stage 2b: every runner on the card, with all that's known about the selection (user, 6 Nov)
            taken = tuple((r['meeting'], r['time'], r.get('number')) for r in resolved_map.values())
            ranked = whole_card_ranking(sample_horse, runners, struck_mins, taken)
            best = whole_card_pick(ranked)
            if best:
                r = best['runner']
                print(f"[+] Whole card: '{orig_name}' -> '{r['name']}' #{r.get('number')} at {r['meeting']} ({r['time_str']}), "
                      f"name fit {best['fit']:.2f}, Betty's price {r.get('price') or 'none'}{p_disp}")
                journal_staff('pick', wager=_current_wager, written=orig_name, price=price, chosen=r['name'],
                              race=f"{r['meeting']} {r['time_str']}", betty_price=r.get('price'), how="whole card")
                _resolve((h_time, h_name), r, price)
                race_list_picks.add((h_time, h_name))
                continue
            top3 = [c['runner'] for c in ranked[:WHOLE_CARD_OFFER]] or top3

        # Stage 3a: race-list check of the handwriting against every runner in the race(s) at the written time
        if number is None and not is_fav and not blank and img_str and api_key:
            choice = reexamine_runner_with_ai(sample_horse, horse_idx, img_str, api_key, top3, runners)
            doubt = pick_doubt(sample_horse, choice) if choice else None
            if doubt:
                print(f"[!] Race-list pick '{choice['name']}' for '{orig_name}' not accepted: {doubt}.")
            elif choice:
                print(f"[+] Re-check confirmed '{orig_name}' -> '{choice['name']}' #{choice.get('number')} at {choice['meeting']} ({choice['time_str']}){p_disp}")
                journal_staff('pick', wager=_current_wager, written=orig_name, price=price, chosen=choice['name'],
                              race=f"{choice['meeting']} {choice['time_str']}", betty_price=choice.get('price'), how="race-list check")
                _resolve((h_time, h_name), choice, price)
                race_list_picks.add((h_time, h_name))
                if sample_horse.get('_time_borrowed'):
                    borrowed_picks.add((h_time, h_name))
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

    taken = race_list_pick_already_taken(resolved_map, race_list_picks, borrowed_picks)
    if taken:
        raise WagerForStaff(taken)

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

    # 3a2. A double can't be on two runners in one race, so the line may be a forecast misread (9.2468368)
    check_same_race_doubles(slip_data, img_str)
    # A combination on 3 runners costs what each way singles on them do: the money can't tell (9.2468536)
    check_combination_lines(slip_data, img_str)

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


def _own_sums_note(written: int | None, paid: int) -> str:
    """For staff: the customer wrote the amount they paid, so the paid figure is right; the bets as read or the
    customer's sums are out (9.2459552 / 9.2459559, 31 Oct: bets of £8.00 and £7.50 under '10' and '8', paid as
    written). It said 'their own sums don't match' of line accumulators whose sums were exact (9.2466815, 5 Nov)."""
    return (f" The customer wrote £{written / 100:.2f} and paid it: check the bets as read against the slip."
            if written and written == paid else "")


LINE_ACC_MIN_LINES = 4  # fewer can be a misread stake, which a rescan may put right


def line_accumulator_reason(bets: list[dict], selections: list[dict] | None, paid: int) -> str | None:
    """
    The reason for staff when a slip is a line accumulator: one accumulator over groups of runners, one from each
    group making a line, so its cost is the groups' sizes multiplied (10p on 4, 4, 4, 2 and four singles = 128 lines,
    £12.80: 9.2466815 and 9.2466816, 5 Nov, costed 10p). A selection with no time written (football) is a group of its
    own. None unless the lines and the stake make exactly what was paid. The program can't enter these.
    """
    if len(bets) != 1 or not selections:
        return None
    groups: dict[Any, int] = {}
    for i, s in enumerate(selections):
        digits = re.sub(r'\D', '', str(s.get('raw_time') or s.get('time') or ''))
        key = digits or ('alone', i)
        groups[key] = groups.get(key, 0) + 1
    lines = math.prod(groups.values())
    stake = round(float(bets[0].get('stake_pence') or 0)) * (2 if bets[0].get('each_way') else 1)
    if lines < LINE_ACC_MIN_LINES or stake * lines != paid:
        return None
    sizes = ' x '.join(str(n) for n in sorted(groups.values(), reverse=True) if n > 1)
    return (f"a line accumulator: {sizes} = {lines} lines at {stake}p is £{paid / 100:.2f}, as paid. The slip's sums are "
            "right, but the program can't enter these")


def bets_reading_signature(bets_list: list[dict]) -> tuple:
    """What decides the bets' cost, per bet: its words (letters and digits only: '3x 50p' and '3 x 50P' are one
    reading), stake, each way, type, runner count and cost. Two scans with the same signature read the same bets."""
    return tuple((_letters(f"{b.get('description', '')} {b.get('raw_text', '')}"), b.get('stake_pence'),
                  bool(b.get('each_way')), normalize_bet_type(str(b.get('bet_type', ''))), len(b.get('horses', [])),
                  b.get('cost_pence')) for b in bets_list or [])


def stake_second_read(bet: dict, img_str: str | None) -> str | None:
    """How one bet line's stake is placed, read again on its own: 'win' or 'each way', None unless the reader is sure."""
    if not img_str:
        return None
    line = f"on line {bet['line_num']} of the writing (counting from the top), " if bet.get('line_num') else ""
    answer = _ask_vision_json(
        f"""You are checking one stake line on a handwritten betting slip. Find the bet line {line}first read as
"{bet.get('description')}". Read only how the stake is placed, letter by letter from the ink: to win ('WIN', 'W', or nothing
written, which means to win) or each way ('EW', 'E/W', 'E.W'). Don't work it out from the money or from other lines.
Answer "high" confidence only if the letters are clear.
Return JSON: {{"letters": "...", "stake": "win" or "each way", "confidence": "high" or "low"}}""",
        img_str, "reader-chain",
        {"type": "OBJECT", "properties": {"letters": {"type": "STRING"}, "stake": {"type": "STRING"},
                                          "confidence": {"type": "STRING"}},
         "required": ["letters", "stake", "confidence"], "propertyOrdering": ["letters", "stake", "confidence"]},
        f"Second read of the stake on '{bet.get('description')}'")
    if not answer or str(answer.get('confidence')).lower() != 'high':
        return None
    stake = str(answer.get('stake')).lower()
    return stake if stake in ('win', 'each way') else None


def each_way_second_read(slip_data: list[dict], img_str: str, short_by: int) -> bool:
    """
    The money is short, and two scans read the same bets. A bet read as win that would cost exactly the shortfall more if
    it were each way may be an 'EW' misread (9.2467051: '50 EW DOUB' read '50p WIN DOUB', 50p short). Each such line is read
    again on its own, not told what's expected. It's changed only if exactly one comes back each way, surely.
    """
    candidates = [b for b in slip_data if not b.get('each_way') and calculate_bet_cost_pence(b) == short_by]
    found = [bet for bet in candidates if stake_second_read(bet, img_str) == 'each way']
    if len(found) != 1:
        print(f"[*] Second read of {len(candidates)} line(s) that could be each way: {len(found)} read so; nothing changed.")
        return False
    found[0]['each_way'] = True
    print(f"[+] A second read says '{found[0].get('description')}' is each way: that accounts for the money.")
    return True


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
        line_acc = line_accumulator_reason(slip_data, raw_selections, target)
        if line_acc:  # a rescan would read the same, and cost another paid read
            print(f"[*] {line_acc[0].upper()}{line_acc[1:]}.")
            out['reason'] = line_acc
            return out
        # The same bets read again: the words are right and how they're costed isn't, which no rescan changes
        # (9.2459179, 31 Oct: three paid scans of identical lines)
        reading = bets_reading_signature(slip_data)
        if reading == last_reading:
            print("[!] The rescan read the same bets as the scan before it: rescanning again won't change the money.")
            if calc < target and img_str and each_way_second_read(slip_data, img_str, target - calc):
                calc = sum(calculate_bet_cost_pence(b) for b in slip_data)
                out.update(calc_total_pence=calc)
                if calc == target:
                    out['ok'] = True
                    return out
            out['reason'] = (f"Money mismatch: the bets cost £{calc / 100:.2f} but £{target / 100:.2f} was "
                             f"{what.split(' (')[0]}; two scans read the same bets.{_own_sums_note(written, target)}")
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
                         f"{what.split(' (')[0]}, after {MAX_SCAN_ATTEMPTS} scans.{_own_sums_note(written, target)}")
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
MODAL_PRICE = "MODAL_PRICE"                    # blue border: "The price you entered was not correct..." (answer_price_box)
MODAL_PAYMENT_MISMATCH = "MODAL_PAYMENT_MISMATCH"  # after F12, red: "Payment is not the same as on the original empty bet..."
MODAL_CONFIRM_STAKE = "MODAL_CONFIRM_STAKE"        # after No on the above, blue: "Please confirm this is the stake tendered"
MODAL_READ_FAILURE = "MODAL_READ_FAILURE"      # red: "Failure to Read Complete Data - End of File? ... \\Events\\5byBFTRP.dat" (Continue)
MODAL_EDITED_ELSEWHERE = "MODAL_EDITED_ELSEWHERE"  # after End, red: "Bet is marked as in the process of being edited on Manager Terminal!" (Continue)
SCREEN_MASTER_INDEX = "MASTER_INDEX"          # the search across every folder, with its cyan letter buttons: sports selections
SCREEN_BET_AND_STAKE = "BET_AND_STAKE"        # F8 "Choose Bet and Stake" (Place Bet / F12 lives here)
SCREEN_BET_EDIT_BLANK = "BET_EDIT_BLANK"      # the bet edit with no list on the left, in the moment between lists or
#                                               with Windows' taskbar over it (staff_9.2459953, user, 6 Nov)
SCREEN_UNKNOWN = "UNKNOWN"
SCREENS_NOT_SURE = (SCREEN_UNKNOWN, SCREEN_BET_EDIT_BLANK)  # nothing here says which step of the edit it is

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
        # A long runner list reaches down into where the keypad is (staff_9.2466825, 5 Nov), so the bet edit's Cancel Bet
        # rules View Wagers out: both matched, and the screen went unnamed
        'absent': [((940, 634, 80, 110), (0, 128, 0), 0.5)],
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
    SCREEN_REUSE_PANEL: {  # right-click on the slip image: earlier selections listed on the left. Its rows are white
        # or cyan, so detect_screen tells it by their shape (reuse_panel_open) on top of these, not by a colour
        'colours': [((8, 110, 205, 35), (193, 0, 0), 0.5),          # red meeting-list header
                    ((940, 634, 80, 110), (0, 128, 0), 0.5)],       # dark green Cancel Bet
    },
    SCREEN_RACE_LIST: {  # runners listed after a time is typed (hatched when no prices are in yet)
        'colours': [_CHOOSE_BET_BUTTON,
                    ((940, 634, 80, 110), (0, 128, 0), 0.5),        # dark green Cancel Bet
                    ((5, 5, 128, 200), (64, 255, 255), 0.15, 70)],  # cyan / light-cyan / hatched runner list
        'absent': [((8, 110, 205, 35), (193, 0, 0), 0.2)],          # no red meeting-list header
        'label': ((5, 5, 128, 30), ()),                              # first row reads "Meet H:MM"
    },
    SCREEN_MASTER_INDEX: {  # any state of it: empty, a list, "No selections found", or Betty's repeating list (mi_2-7, mi_11)
        'colours': [((405, 233, 80, 315), (128, 255, 255), 0.5),    # the cyan letter buttons
                    _CHOOSE_BET_BUTTON,
                    ((940, 634, 80, 110), (0, 128, 0), 0.5)],       # dark green Cancel Bet
        'absent': [((8, 110, 205, 35), (193, 0, 0), 0.2)],          # no red meeting-list header
        'label': ((405, 265, 80, 60), ("abc", "def")),              # the letter buttons' own letters
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
    MODAL_EDITED_ELSEWHERE: {  # the same red box again: another till has the bet open to edit (9.2462767, 2 Nov)
        'colours': [((350, 291, 665, 6), (255, 0, 0), 0.6),
                    ((343, 300, 6, 230), (255, 0, 0), 0.8),
                    ((360, 310, 640, 140), (255, 255, 255), 0.8)],
        'label': ((380, 340, 620, 80), ("beingedited", "processofbeing")),
    },
    MODAL_READ_FAILURE: {  # the same red box: Betty reading a feed file as it's rewritten, on a Master Index search (mi_16)
        'colours': [((350, 291, 665, 6), (255, 0, 0), 0.6),
                    ((343, 300, 6, 230), (255, 0, 0), 0.8),
                    ((360, 310, 640, 140), (255, 255, 255), 0.8)],
        'label': ((360, 350, 650, 60), ("failuretoread", "completedata", "endoffile")),
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
# The events page as pictures (screen 70, user, 6 Nov): what opens first on entering a bet to edit, as the plain grid of
# buttons does. It serves only to be passed: 1 goes to folder 1 and the bet edit, as on the grid
EVENT_MENU_PICTURES = [((875, 655, 78, 75), (255, 255, 128), 0.7),   # Cancel
                       ((755, 655, 78, 75), (255, 255, 128), 0.7),   # More Events
                       ((875, 562, 78, 72), (193, 0, 0), 0.7)]       # Pools Betting
EVENT_MENU_PICTURES_LABEL = ((95, 8, 395, 44), ("placeyourbets",))
# The bet edit, nothing else said: its header, Choose Bet, Cancel Bet and the betslip's cream panel, no list on the left
BET_EDIT_SIGNS = [_BETTY_CYAN_HEADER, _CHOOSE_BET_BUTTON, ((940, 634, 80, 110), (0, 128, 0), 0.5),
                  ((880, 140, 470, 300), (255, 255, 208), 0.6)]
BET_EDIT_NO_LIST = ((5, 5, 128, 200), (255, 255, 255), 0.9)
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


def _named_otherwise(img: Any, arr: Any) -> str:
    """No screen's signature fits: the events page as pictures, the bet edit with nothing on its left, or unknown."""
    if _signals_pass(arr, EVENT_MENU_PICTURES) and _label_reads(img, *EVENT_MENU_PICTURES_LABEL):
        return SCREEN_EVENT_MENU
    return SCREEN_BET_EDIT_BLANK if _signals_pass(arr, [*BET_EDIT_SIGNS, BET_EDIT_NO_LIST]) else SCREEN_UNKNOWN


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
    # The previous-selections panel by its rows' shape: they were taken as white, and 1.2.1-1.2.12 named the cyan
    # ones (selections not on the slip yet) RACE_ENTRY (screens 52-56)
    if _signals_pass(arr, SCREEN_SIGNATURES[SCREEN_REUSE_PANEL]['colours']) and reuse_panel_open(img):
        return SCREEN_REUSE_PANEL
    matches = [name for name, sig in SCREEN_SIGNATURES.items() if name != SCREEN_REUSE_PANEL
               and _signals_pass(arr, sig['colours']) and _signals_absent(arr, sig.get('absent', []))]
    if len(matches) != 1:
        return _named_otherwise(img, arr)
    name = matches[0]
    if not _label_reads(img, *SCREEN_SIGNATURES[name]['label']):
        return _named_otherwise(img, arr)
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
BETTY_TAKE_FRONT_SECS = app_paths.setting("BETTY_TAKE_FRONT_SECS", 300.0)  # nobody at the till this long: Betty is brought
#   forward and a screen staff left her on is backed out of. Sooner only by Start or `
BETTY_REQUIRE_QUIET_SECS = 2.0  # no person's input this long: a stray window in front may be made to give way
BETTY_REQUIRE_WAIT_SECS = 1.0   # how long Betty gets to have the keyboard before a key or click isn't sent
_switched_on_by_hand = False    # Start or `: the person wants it working now, so it may take the screen, once
_paused_for_staff = False  # the watcher went idle because staff used the till (not switched off with `)
_last_staff_activity = 0.0  # last key, click or mouse movement by a person
STAFF_IDLE_RESUME_SECS = app_paths.setting("STAFF_IDLE_RESUME_SECS", 60)  # paused for staff: switch back on after this long with no activity at all
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
    global _watcher_resume_at, _watcher_stop_reason, _paused_for_staff, _switched_on_by_hand
    _paused_for_staff = False  # the switch decides: off stays off, on is on
    _switched_on_by_hand = False
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
    _switched_on_by_hand = True
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


# A wager number is the shop, a dot, then the shop's wager count, with no fixed number of digits: shops differ, and
# Betty writes one wager two ways. The lists pad it ('010.0577805'); the blue box drops the zeros after the dot
# ('10.577805': HO Cashier, 7 Nov, where 7 digits after the dot were required and every wager "did not load"). A
# number run into more digits or another dot (a misread '010.0577.805') isn't taken.
_WAGER_NUMBER_RE = re.compile(r'(?<!\d)(?<!\d\.)(\d+)\.(\d+)(?!\d)(?!\.\d)')


def wager_number_parts(text: str | None) -> tuple[int, int] | None:
    """(shop, count), whatever the zeros: '010.0577805', '10.0577805' and '10.577805' are all (10, 577805)."""
    m = _WAGER_NUMBER_RE.search(text or '')
    return (int(m.group(1)), int(m.group(2))) if m else None


def same_wager(a: str | None, b: str | None) -> bool:
    """The same wager, however each was written ('10.577805' in the blue box, '10.0577805' from the list)."""
    parts = wager_number_parts(a)
    return parts is not None and parts == wager_number_parts(b)


def normalise_wager_number(text: str) -> str | None:
    """'009.2445201' -> '9.2445201': the shop's zeros dropped, the count as written. None when it isn't a number."""
    m = _WAGER_NUMBER_RE.search(text or '')
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


# The three boxes of a wager's details are read at once, each by its own Tesseract: one after another a read took
# 0.66 s, and a wager is read at least twice (two reads must agree) before it is taken (cashier till, 2 Nov)
_WAGER_OCR_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="wager ocr")


def read_wager_details(img: Any) -> dict:
    """The loaded wager on View Wagers: number, struck time (upper timestamp) and Payment in pence (None if unread)."""
    reads = [_WAGER_OCR_POOL.submit(_ocr_box, img, VW_WAGER_NUMBER_BOX, _DIGITS_CFG, invert=True),
             _WAGER_OCR_POOL.submit(_ocr_box, img, VW_TIMESTAMPS_BOX, '--psm 6'),
             _WAGER_OCR_POOL.submit(_ocr_box, img, VW_SLIP_SUMMARY_BOX, '--psm 6', scale=2)]
    number_text, stamps_text, summary_text = (r.result() for r in reads)
    number = normalise_wager_number(number_text)
    stamps = re.findall(r'(\d{1,2}):(\d{2}):(\d{2})', stamps_text)
    struck = f"{int(stamps[0][0]):02d}:{stamps[0][1]}" if stamps else None
    summary = without_thousands_commas(summary_text)
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
# '/' brought the time box up within a second whenever it did; from 2 Nov 17:14 Betty mostly ignores it and Tab brings
# it up instead. Waiting the whole NAV_TIMEOUT before Tab cost every wager 4 s on the cashier till (1.2.17, 52 of 52)
TIME_BOX_SLASH_SECS = 1.5
_nav_recovering = False  # backing out after a stop: keys are allowed although the watcher is stopping
_home_unreachable = False  # the last go_home() ended away from Home: the watcher tries again in HOME_RETRY_SECS
HOME_RETRY_SECS = app_paths.setting("HOME_RETRY_SECS", 60.0)  # between tries to get back to Home; staff are told once
UNKNOWN_READ_SECS = 600.0  # at most one paid look at a screen the program doesn't know, this often
SAFE_WAY_OUT = ("cancel", "close", "ok", "back", "continue", "no", "exit")  # the only buttons clicked on an unknown screen
ESC_UNCHANGED_LIMIT = 2  # Esc presses in a row that leave Betty on the same screen before go_home gives up
# Betty can stop drawing for 20 s at a time (cashier till, 6 Nov: once a minute, its link to Betty's files full; 9.2468149,
# 9.2468157, 9.2468160 went to staff and F12 on 9.2468158 went through unseen). Her clock, top right, ticks every second:
# within 1 s of the real time on 18 staff screens, 21 and 22 s behind on the two frozen ones
BETTY_FREEZE_SECS = app_paths.setting("BETTY_FREEZE_SECS", 45.0)  # longest wait for a frozen Betty to come back
BETTY_NO_CLOCK_WAIT_SECS = app_paths.setting("BETTY_NO_CLOCK_WAIT_SECS", 25.0)  # no clock showing: how long nothing moves before it's no freeze
BETTY_NO_CLOCK_QUIET_SECS = 30.0  # after such a wait found no freeze: not waited again for this long
BETTY_CLOCK_REGION = (1285, 34, 1362, 50)  # her red dot and clock; on most screens, and never on Home
BETTY_CLOCK_DOT_W, BETTY_CLOCK_DOT_MIN = 15, 30  # the dot: in the region's first 15 px, at least 30 red pixels
BETTY_CLOCK_TICK_SECS = 1.3  # longer than one tick


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
    _require_betty()
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


def _betty_clock(img: Any) -> bytes | None:
    """Betty's clock as pixels, None when it isn't showing."""
    arr = np.array(img.convert('RGB').crop(BETTY_CLOCK_REGION))
    dot = arr[:, :BETTY_CLOCK_DOT_W].astype(int)
    red = ((dot[:, :, 0] > 180) & (dot[:, :, 1] < 80) & (dot[:, :, 2] < 80)).sum()
    return arr.tobytes() if red >= BETTY_CLOCK_DOT_MIN else None


def _betty_picture(img: Any) -> bytes:
    """The screen, as pixels, without the corner where the status panel sits (it changes on its own)."""
    rgb = img.convert('RGB')
    return rgb.crop((0, 0, 1366, 625)).tobytes() + rgb.crop((0, 625, 1025, 768)).tobytes()


_no_clock_quiet_until = 0.0


def _wait_out_freeze_no_clock(shot: Any, doing: str) -> bool:
    """
    No clock on screen: Betty froze mid-draw, or she's alive on a screen without one, which can't be told yet. So when nothing
    moves for BETTY_NO_CLOCK_WAIT_SECS it was no freeze: False, and not waited for again for a while. True as soon as anything
    moves (9.2468289, 9.2468533, 6 Nov: both went to staff a moment before she came back).
    """
    global _no_clock_quiet_until
    if time.time() < _no_clock_quiet_until:
        return False
    still = _betty_picture(shot)
    t0, said = time.time(), False
    while time.time() - t0 < BETTY_NO_CLOCK_WAIT_SECS:
        _check_stop()
        time.sleep(0.25)
        if _betty_picture(pyautogui.screenshot()) != still:
            if said:
                print(f"[*] Betty moved after {time.time() - t0:.0f} s.")
            return True
        if not said and time.time() - t0 >= BETTY_CLOCK_TICK_SECS:
            said = True
            print(f"[*] Nothing has moved ({doing or 'waiting'}) and no clock is showing: Betty may have frozen. Waiting up to "
                  f"{BETTY_NO_CLOCK_WAIT_SECS:.0f} s.")
            refresh_watcher_hud("Betty may have frozen: waiting for her...")
    print(f"[*] Nothing moved in {BETTY_NO_CLOCK_WAIT_SECS:.0f} s: not a freeze.")
    _no_clock_quiet_until = time.time() + BETTY_NO_CLOCK_QUIET_SECS
    return False


def wait_out_freeze(doing: str = "") -> bool:
    """
    When Betty's clock has stopped, waits (up to BETTY_FREEZE_SECS) until it moves or goes. True when it had stopped:
    whatever was being waited for can have another look. Without a clock on screen: _wait_out_freeze_no_clock. For use
    when a wait has run out, as telling costs BETTY_CLOCK_TICK_SECS. Keys sent meanwhile aren't lost: Betty takes them after.
    """
    shot = pyautogui.screenshot()
    clock = _betty_clock(shot)
    if clock is None:
        return _wait_out_freeze_no_clock(shot, doing)
    time.sleep(BETTY_CLOCK_TICK_SECS)
    if _betty_clock(pyautogui.screenshot()) != clock:
        return False
    print(f"[*] Betty has frozen ({doing or 'waiting'}): her clock has stopped. Waiting for her, up to {BETTY_FREEZE_SECS:.0f} s.")
    refresh_watcher_hud("Betty has frozen: waiting for her...")
    t0 = time.time()
    while time.time() - t0 < BETTY_FREEZE_SECS:
        _check_stop()
        if _betty_clock(pyautogui.screenshot()) != clock:
            print(f"[*] Betty is back after {time.time() - t0 + BETTY_CLOCK_TICK_SECS:.0f} s.")
            return True
        time.sleep(0.25)
    print(f"[-] Betty is still frozen after {BETTY_FREEZE_SECS:.0f} s.")
    return True


def expect_screen(targets: set, timeout: float = NAV_TIMEOUT, doing: str = "") -> str:
    """
    Waits for one of `targets`, and through a freeze of Betty's (wait_out_freeze). A screen the program can't recognise
    (UNKNOWN) no longer stops it (user's decision, 21 Oct): it carries on and the read-backs (betslip lines, bet lines,
    total vs Payment) check the result. A screen it recognises as a DIFFERENT one still stops it: Betty really is
    somewhere else.
    """
    screen = wait_for_screen(targets, timeout)
    if screen not in targets:
        # A clock that moved while it was being told may have only just come back: a moment for her to draw, either way
        screen = wait_for_screen(targets, max(timeout, NAV_TIMEOUT) if wait_out_freeze(doing) else 1.0)
    if screen in SCREENS_NOT_SURE:
        print(f"[!] {doing or 'waiting'}: screen not recognised (expected {'/'.join(sorted(targets))}); carrying on.")
        return screen
    if screen not in targets:
        raise NavError(f"{doing or 'waiting'}: expected {'/'.join(sorted(targets))}, Betty shows {screen}")
    return screen


BUTTON_YELLOW = (255, 255, 128)


def read_buttons(img: Any, region: tuple, min_w: int = 30, min_h: int = 20) -> list[tuple[str, tuple[int, int]]]:
    """
    Betty's yellow buttons inside `region`: each solid yellow rectangle is found by colour, then its own text is read.
    Returns [(text as read, centre)], so a button is clicked by what it says, never by a fixed position.
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
        buttons.append((text, (bx + bw // 2, by + bh // 2)))
    return buttons


def find_buttons(img: Any, region: tuple, min_w: int = 30, min_h: int = 20) -> list[tuple[str, tuple[int, int]]]:
    """read_buttons with each text cut down to its letters, lower-case: [(letters, centre)]."""
    return [(re.sub(r'[^a-z]', '', text.lower()), centre) for text, centre in read_buttons(img, region, min_w, min_h)]


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
    MODAL_EDITED_ELSEWHERE: ("Continue", (345, 291, 675, 250)),
    MODAL_READ_FAILURE: ("Continue", (345, 291, 675, 250)),
}


_unknown_read_at = 0.0  # when an unknown screen was last read with the paid reader


def save_unknown_screen() -> str | None:
    """A picture of a screen the program doesn't know, in logs/ and so on the relay (a staff_ name), so it can be named.
    Never of another program's window: that would go up to the relay."""
    if _foreground_exe() != BETTY_EXE:
        return None
    try:
        path = os.path.join(app_paths.log_dir(), f"staff_UNKNOWN_{time.strftime('%Y%m%d_%H%M%S')}.png")
        os.makedirs(app_paths.log_dir(), exist_ok=True)
        pyautogui.screenshot().save(path)
        print(f"[*] Screen the program doesn't know, saved for naming: {path}")
        return path
    except Exception as e:
        print(f"[-] Could not save the unknown screen: {e}")
        return None


def click_way_out(img: Any, words: tuple[str, ...]) -> bool:
    """Clicks the first button on screen reading one of `words` exactly, in that order. Never any other button."""
    buttons = [(re.sub(r'[^a-z]', '', text.lower()), centre) for text, centre in read_buttons(img, (0, 0, 1366, 768))]
    for word in words:
        for text, centre in buttons:
            if text == word:
                print(f"[*] Unknown screen: clicking its '{word}' button.")
                betty_click(*centre)
                return True
    return False


def read_unknown_screen() -> bool:
    """
    Esc did nothing on a screen the program doesn't know (user, 6 Nov: it should read the screen and decide), with Betty
    in front. Any plainly safe button is clicked; failing that the screen is read by the slip reader, at
    most once per UNKNOWN_READ_SECS, for what it is and its way out, and only a safe button it names is clicked. Nothing
    that could place, confirm or close anything is ever pressed. True when something was tried.
    """
    global _unknown_read_at
    if _foreground_exe() != BETTY_EXE:  # it isn't Betty's screen that's showing: nothing to read, nothing to click
        return False
    img = pyautogui.screenshot()
    if click_way_out(img, SAFE_WAY_OUT):
        return True
    if time.time() - _unknown_read_at < UNKNOWN_READ_SECS:
        return False
    _unknown_read_at = time.time()
    buffered = io.BytesIO()
    img.convert('RGB').save(buffered, format="JPEG", quality=80)
    answer = _ask_vision_json(
        f"""This is a Windows till running a betting shop program called Betty. The program driving it doesn't recognise
this screen and wants to get back to Betty's home screen without changing anything.
Say briefly what is showing, and which on-screen button leaves it safely. Only these count: {', '.join(SAFE_WAY_OUT)}.
If none of them is on screen, or another program is covering Betty, leave "button" empty.
Return JSON: {{"what": "...", "button": "..."}}""",
        base64.b64encode(buffered.getvalue()).decode('utf-8'), "reader-chain",
        {"type": "OBJECT", "properties": {"what": {"type": "STRING"}, "button": {"type": "STRING"}},
         "required": ["what", "button"], "propertyOrdering": ["what", "button"]},
        "Reading an unknown screen")
    if not answer:
        return False
    word = re.sub(r'[^a-z]', '', str(answer.get('button') or '').lower())
    print(f"[*] Unknown screen, as read: {answer.get('what')} (way out: {word or 'none'})")
    return word in SAFE_WAY_OUT and click_way_out(pyautogui.screenshot(), (word,))


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
        unknown_steps, saved = 0, False
        for _ in range(max_steps):
            if abort_event.is_set() and _watcher_stop_reason in ("staff", "off"):
                print("[*] Backing out stopped: someone is using the till.")
                raise WatcherStop()
            screen = detect_screen()
            if screen == SCREEN_UNKNOWN:  # often Betty mid-redraw: let it settle before pressing anything
                screen = wait_for_screen(ALL_SCREENS - {SCREEN_UNKNOWN}, timeout=1.5)
            unknown_steps = unknown_steps + 1 if screen == SCREEN_UNKNOWN else 0
            if unknown_steps == 2 and not saved:  # not a redraw: Esc went by and it's still here
                saved = bool(save_unknown_screen())
            if unknown_steps >= 3 and read_unknown_screen():
                wait_for_screen(ALL_SCREENS - {SCREEN_UNKNOWN}, timeout=2.0)
                continue
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
                if screen == SCREEN_MASTER_INDEX:  # with the search area focused Esc does nothing (user, 5 Nov)
                    betty_click(*INDEX_ESC_SPOT)
                betty_press('esc')
            after = wait_for_screen({s for s in ALL_SCREENS if s != screen}, timeout=2.0)
            stuck = after == screen and screen != SCREEN_UNKNOWN and screen not in MODAL_BACK_OUT
            if stuck and wait_out_freeze(f"backing out from {screen}"):  # the Esc is still to come: not stuck yet
                stuck = wait_for_screen({s for s in ALL_SCREENS if s != screen}, timeout=2.0) == screen
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
    shown = pyautogui.screenshot()
    current_q = read_unedited_queue(shown)
    # What the blue box says now: seen again under the new number, Betty has drawn only the number so far, however many
    # reads agree (9.2468538, 6 Nov: frozen mid-draw, two reads gave 9.2468536's 16:39:41 and £3.00 for its 16:41:34 and £10.00)
    old = read_wager_details(shown)
    old_details = (old['struck_clock'], old['payment_pence']) if not same_wager(old['number'], number) else None
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
        if same_wager(details['number'], number) and details['struck_time'] and details['payment_pence'] is not None:
            if read == last_read and read[1:] != old_details:
                details['number'] = number  # as the list writes it, whatever zeros the blue box dropped
                corpus_save('wager_details', img, {'number': number},
                            {k: details[k] for k in ('number', 'struck_clock', 'payment_pence')})
                return details
            time.sleep(0.15)
        else:
            time.sleep(0.05)
        last_read = read
    last = read_wager_details(pyautogui.screenshot())
    if same_wager(last['number'], number):
        if (last['struck_clock'], last['payment_pence']) == old_details and wait_out_freeze(f"wager {number} loading"):
            # Otherwise Betty is alive and showing it: two wagers struck the same second for the same money
            time.sleep(0.3)
            last = read_wager_details(pyautogui.screenshot())
            last_read = (last['number'], last['struck_clock'], last['payment_pence'])
            last = read_wager_details(pyautogui.screenshot())
        if (last['number'], last['struck_clock'], last['payment_pence']) != last_read:
            # Not read the same twice in a row: the struck time and Payment may still be the wager shown before, so
            # they count as unread and the caller sends it to staff (review B4, 28 Oct: one read was taken here)
            print(f"[!] Wager {number}: struck time / Payment not read the same twice "
                  f"({last['struck_clock']!r}, {last['payment_pence']!r}); not taken.")
            last.update(struck_time=None, struck_clock=None, payment_pence=None)
        last['number'] = number  # as the list writes it, whatever zeros the blue box dropped
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
    screen = expect_screen({SCREEN_EVENT_MENU, SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, SCREEN_RACE_ENTRY_BROKEN,
                            MODAL_EDITED_ELSEWHERE}, doing="Edit Empty Bet (End)")
    print(f"[*] After End: {screen}")
    if screen == MODAL_EDITED_ELSEWHERE:
        # Another till is editing it. Before, End carried on under the pop-up and scanned a slip it half covered, then
        # sent the wager to staff (9.2462767, 2 Nov). Continue, and leave it for now like a wager viewed elsewhere
        label, region = MODAL_BACK_OUT[MODAL_EDITED_ELSEWHERE]
        spot = find_button(pyautogui.screenshot(), label, region)
        if not spot:  # the next wager would be clicked under the pop-up
            raise NavError(f"another terminal is editing the bet, and the pop-up's '{label}' wasn't found")
        betty_click(*spot)
        raise WagerOpenElsewhere("another terminal is editing it")
    if screen in (SCREEN_EVENT_MENU, *SCREENS_NOT_SURE):  # End always opens the event menu
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
        screen = wait_for_screen({SCREEN_RACE_ENTRY_READY}, timeout=TIME_BOX_SLASH_SECS)
        box_open = _signals_pass(np.array(pyautogui.screenshot().convert('RGB')), [RACE_ENTRY_TIME_BOX])
        if screen != SCREEN_RACE_ENTRY_READY and not (screen in SCREENS_NOT_SURE and box_open):
            # Betty now and then shows something else where the time box should be; Tab brings the box up (user, 2 Nov)
            print(f"[*] Time box ('/'): Betty shows {screen}, not the time box; pressing Tab and checking again.")
            betty_press('tab')
            screen = expect_screen({SCREEN_RACE_ENTRY_READY}, doing="time box ('/', then Tab)")
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
               SCREEN_MASTER_INDEX,
               SCREEN_BET_AND_STAKE, SCREEN_BET_EDIT_BLANK, SCREEN_UNKNOWN, *MODAL_SIGNATURES}


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
F8_EACH_WAY_BOX = (152, 649, 140, 30)  # Choose Bet and Stake's Each Way button: green when on
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
    # A forecast in each of two races, doubled ('4 x 40p R/F/CAST DOUBLES': 2 x 2 = 4 bets). Costed since October but
    # refused at entry, so the whole wager went to staff (9.2460746, 1 Nov). Betty's rows (screen 26 p3-p4), found by
    # name: no shortcut
    'straight forecast double': (None, 'forecastdoubles'), 'reversed forecast double': (None, 'revfcastdoubles'),
    # Every k-fold of the selections, found by name. The same-race rule turns a clashed accumulator over 4+ races into
    # these over all its selections at the stake divided (rules_engine CASE B), as Betty strikes only the lines whose
    # selections are all in different races: it charged 2 doubles, not 3, for Doubles over two runners in one race and
    # a third (9.2460884, 1 Nov). Refused at entry until 1.2.24, so the wager went to staff (9.2463985, 3 Nov)
    **{f'perm {k}-folds': (None, f'perm{k}folds') for k in range(4, 11)},
}
# How Betty names each type on the betslip read-back ("1) Treble. ..."): letters that must appear
READBACK_NAMES = {'single': 'single', 'double': 'double', 'treble': 'treble', 'accumulator': 'fold', 'yankee': 'yankee',
                  'patent': 'patent', 'lucky 15': 'lucky15', 'lucky 31': 'lucky31', 'lucky 63': 'lucky63',
                  'trixie': 'trixie', 'canadian': 'canadian', 'heinz': 'heinz', 'super heinz': 'superheinz',
                  'goliath': 'goliath', 'straight forecast': 'forecast', 'reversed forecast': 'forecast',
                  'combination forecast': 'forecast', 'tricast': 'tricast', 'combination tricast': 'tricast',
                  'straight forecast double': 'forecastdouble', 'reversed forecast double': 'fcastdouble',
                  **{f'perm {k}-folds': 'fold' for k in range(4, 11)}}


RULE_ROW_DARK_SHARE = 0.35  # a row this dark across the crop may be a ruled line or a box edge (text mostly < 0.3)
RULE_STANDS_OUT = 0.6       # ... when the rows either side are less than this share of it (rules ~0.5 beside 0.0)


def _rule_rows(grey: Any) -> list[int]:
    """
    The rows of a grey crop that are a ruled line or a box edge: dark across the crop AND standing out from the rows
    on either side (a rule is a thin line; text strokes come in a band of rows nearly as dark). On a long line the
    strokes alone passed the share: 'Phil 5:05 5. Honeysmakemon' lost a row through its letters and read 'Pri 59:05'
    (9.2462604, 2 Nov). Of the 152 betslip rows on the saved screens, only that row's blanking changed.
    """
    share = (grey < 150).mean(axis=1)
    beside = np.concatenate([[0.0], share, [0.0]])
    return [i for i, s in enumerate(share)
            if s > RULE_ROW_DARK_SHARE and beside[i] < RULE_STANDS_OUT * s and beside[i + 2] < RULE_STANDS_OUT * s]


def _bw_crop(img: Any, box: tuple, scale: int, drop_rules: bool) -> Any:
    """The crop _ocr_bw reads: grey, rules blanked when asked, enlarged, black and white."""
    x, y, w, h = box
    grey = img.convert('L').crop((x, y, x + w, y + h))
    if drop_rules:
        arr = np.array(grey)
        arr[_rule_rows(arr)] = 255
        grey = Image.fromarray(arr)
    return grey.resize((w * scale, h * scale)).point(lambda v: 0 if v < 150 else 255)


def _ocr_bw(img: Any, box: tuple, config: str = '--psm 6', scale: int = 2, drop_rules: bool = False) -> str:
    """Dark text on a light panel: grey, threshold, enlarge, read. drop_rules: rows dark across the crop (a ruled line,
    Betty's dotted focus box) are blanked first; on 9.2452710 (26 Oct) the box's top edge on the crop's first row
    turned '8-1' into '81', the line didn't read and the betslip showed 2 selections instead of 3."""
    try:
        return pytesseract.image_to_string(_bw_crop(img, box, scale, drop_rules), config=config).strip()
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return ""


def _grey_crop(img: Any, box: tuple, scale: int, drop_rules: bool = False) -> Any:
    """A crop for small text on a colour (the Master Index's rows): grey and smoothly enlarged, not black and white.
    Thresholded, the rows' cut-off letters read as other words ('Both Teams To Seo')."""
    x, y, w, h = box
    return img.convert('L').crop((x, y, x + w, y + h)).resize((w * scale, h * scale), Image.LANCZOS)


def _ocr_bw_many(img: Any, boxes: list, config: str = '--psm 6', scale: int = 2, drop_rules: bool = False,
                 crop: Any = _bw_crop) -> list[str]:
    """
    _ocr_bw on several boxes with one start of Tesseract: each crop a page of one run (a list of pictures). A start
    costs ~140 ms of the ~145 ms a small read takes (1 Nov), so the panel's 3 rows took 0.95 s as 6 reads. The text
    is the same as one read per box: 151 of 151 crops (panel rows, every betslip row on the saved screens). `crop`: how
    a box is made ready for reading.
    """
    if len(boxes) < 2 and crop is _bw_crop:
        return [_ocr_bw(img, b, config, scale, drop_rules) for b in boxes]
    if not boxes:
        return []
    folder = tempfile.mkdtemp(prefix="betty_ocr_")
    try:
        paths = []
        for i, box in enumerate(boxes):
            paths.append(os.path.join(folder, f"{i:03d}.png"))
            crop(img, box, scale, drop_rules).save(paths[-1])
        listing = os.path.join(folder, "pages.txt")
        with open(listing, "w", encoding="utf-8") as f:
            f.write("\n".join(paths) + "\n")
        pages = pytesseract.image_to_string(listing, config=config).split("\f")  # a form feed ends each page
        if len(pages) < len(boxes):
            raise ValueError(f"{len(pages)} pages read of {len(boxes)}")
        return [p.strip() for p in pages[:len(boxes)]]
    except Exception as e:
        print(f"[-] OCR of {len(boxes)} boxes in one go failed ({e}): read one by one.")
        return [_ocr_bw(img, b, config, scale, drop_rules) for b in boxes]
    finally:
        shutil.rmtree(folder, ignore_errors=True)


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


# Lines are 45 px apart (user's screenshots of 12 lines, 31 Oct: y = 91, 136 .. 451); 45.33 drifted ~3 px by the
# 9th line and clipped the tops of lines 11-12 ('SP' read 'oP'). 18px tall covers the 12px main text without bleeding
# into the Jockey subline at y+21
BETSLIP_LINE_TOP, BETSLIP_LINE_PITCH, BETSLIP_LINE_H = 83, 45, 18
# Lines the cream panel holds above the grey one: 9 (83 + 8 x 45.33 + 18 = 464 < 488). It was 8, so the 9th of 17
# selections was added but never read: "the betslip shows 8 selection(s), expected 9" (9.2459368, 31 Oct)
BETSLIP_MAX_LINES = int((BETSLIP_BETS_ROWS[0] - BETSLIP_LINE_TOP - BETSLIP_LINE_H) / BETSLIP_LINE_PITCH) + 1
# The name is lazy and may be empty: '(.+?)?' tried one character first, so a dog line '1. Sund 4:59 11-10 BP' read
# name '1', price '1-10' (9.2453098, 26 Oct)
# The dot after the line number can drop out of the read ('4 Keen 8:20 14. Puerto Rico SP', 9.2459454, 31 Oct): a
# space stands for it, the meeting's letters and the time that must follow keep the line unmistakable
# 'EP' (early price) can read 'EF': 3 of the 5 lines of 9.2460882 (1 Nov) never read on Choose Bet and Stake
BETSLIP_SELECTION_LINE = re.compile(
    r'^\W*(\d+|\?)(?:\s*\.\s*|\s+)([A-Za-z\s]{3,7}?)\s+(\d{1,2}:\d{2})\s*(?:(?:(?:Trap\s*)?(\d+)\.\s*)|(?:Trap\s*(\d+)\s*))?(.*?)\s*[\W_]*(SP|NR|WD|VS|Evens|Evs|\d+\s*[-/]\s*\d+)(?:\s*[BE][PF])?[\W_]*$',
    re.IGNORECASE
)
# A long name in bold runs into the SP beside it, and its S reads as something else: 'Wordfromhome&P' (9.2467112). What's
# left of the line can only be a price, and the name and SP are checked against the selection afterwards
BETSLIP_SP_JOINED = re.compile(r'([a-z])[&$58%]P$')
GUARANTEED_PURPLE = (128, 0, 128)  # a guaranteed (BOG) price is purple; an ordinary one red (255, 0, 0)
# Price 'VS' = void selection: a late selection after "Yes" on Betty's late-selection box, drawn in black (9.2448544)
VOID_SELECTION = 'VS'
# Prices that mean the runner won't run or count: never guaranteed, fine for an SP selection ('WD' = withdrawn,
# shown instead of the price, 9.2448529)
NOT_RUNNING = ('NR', 'WD', VOID_SELECTION)


def read_betslip_selections(img: Any) -> list[dict]:
    """
    Selection lines on Betty's betslip panel, read one line at a time (the focused line's dotted box confused a
    whole-panel read): [{'n', 'meeting', 'time', 'number', 'name', 'price', 'guaranteed', 'y', 'row'}]. 'guaranteed' =
    the price is purple; 'y' = the line's centre, for clicking it; 'row' = its place in the panel (0 = top). Rows are
    read down to the first blank one: a line that won't read is left out, never the lines under it (9.2459368, 31 Oct:
    the focus box round line 13 read '13.D0Wwn', so lines 14-17 weren't seen). Its number is then worked out from
    the others' (betslip_lines_by_number).
    """
    left = betslip_left(img)
    arr = np.array(img.convert('RGB'))
    out = []
    for i in range(BETSLIP_MAX_LINES):
        if _betslip_row_blank(arr, _betslip_row_box(left, i)):  # by colour first: reading a blank row 4 ways cost ~0.85 s
            break
        line = read_betslip_row(img, i, arr, left)
        if line is not None:
            out.append(line)
    # Whether the bottom row holds a line, read or not: only a full panel can hide lines above (_betslip_offset)
    full = not _betslip_row_blank(arr, _betslip_row_box(left, BETSLIP_MAX_LINES - 1))
    for line in out:
        line['panel_full'] = full
    hidden = _betslip_offset(out)
    for line in out:
        if line['n'] is None:  # '?.' read for its number: its row says it
            line['n'] = hidden + line['row'] + 1
    return out


def _betslip_row_box(left: int, row: int) -> tuple:
    return left, int(BETSLIP_LINE_TOP + row * BETSLIP_LINE_PITCH), 1356 - left - 70, BETSLIP_LINE_H


# Ways to read one betslip row, in turn: ruled rows blanked; as it is (blanking can take letters, the focus box's
# dots); the focus box's left and top edges cut off; larger. (rules blanked, cut left px, cut top px, scale)
BETSLIP_ROW_READS = ((True, 0, 0, 3), (False, 0, 0, 3), (False, 5, 2, 3), (False, 0, 0, 4))


def _betslip_first_read_box(left: int, row: int) -> tuple:
    """The box of a betslip row's first way of reading (BETSLIP_ROW_READS[0])."""
    x, y, w, h = _betslip_row_box(left, row)
    _, trim_x, trim_y, _ = BETSLIP_ROW_READS[0]
    return x + trim_x, y + trim_y, w - trim_x, h - trim_y


def read_betslip_row(img: Any, row: int, arr: Any = None, left: int | None = None,
                     first: str | None = None) -> dict | None:
    """One row of the betslip panel read as a selection line ('n' = the number printed on it, None when that didn't
    read), or None when the row doesn't read as one. `first`: the row's first way of reading, done already (several
    rows' in one start of Tesseract, read_betslip_tail)."""
    left = betslip_left(img) if left is None else left
    arr = np.array(img.convert('RGB')) if arr is None else arr
    box = _betslip_row_box(left, row)
    top = box[1]
    m = None
    for k, (drop, trim_x, trim_y, scale) in enumerate(BETSLIP_ROW_READS):  # the next way only when the last didn't read
        x, y, w, h = box
        text = first if k == 0 and first is not None else _ocr_bw(
            img, (x + trim_x, y + trim_y, w - trim_x, h - trim_y), '--psm 7', scale, drop_rules=drop)
        m = BETSLIP_SELECTION_LINE.match(BETSLIP_SP_JOINED.sub(r'\1 SP', text.strip()))
        if m:
            break
    if not m:
        return None
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
    return {'n': int(m.group(1)) if m.group(1).isdigit() else None, 'meeting': m.group(2).replace(' ', '').lower(),
            'time': m.group(3), 'number': num, 'name': name, 'price': m.group(7).replace(' ', ''),
            'guaranteed': _colour_share(arr, (left + 250, top, 160, BETSLIP_LINE_H), GUARANTEED_PURPLE, 30) >= 0.02,
            'y': top + BETSLIP_LINE_H // 2, 'row': row}


BETSLIP_TEXT_MIN_PX = 40  # dark or red pixels in a betslip row holding a line; a blank row of cream has none
BETSLIP_FOCUS_RED_MIN = 100  # red dashes of Betty's focus box along a row's top and bottom edges (~216 each)


def betslip_focus_row(img: Any) -> int | None:
    """The panel row Betty's dotted focus box is round (the line clicked or reached with Down), by colour alone: red
    dashes along the row's top edge and along the line before the next row (screen 48: y = 263 and 307, row 4)."""
    arr = np.array(img.convert('RGB')).astype(int)
    left = betslip_left(img)
    for r in range(BETSLIP_MAX_LINES):
        top = int(BETSLIP_LINE_TOP + r * BETSLIP_LINE_PITCH)
        edges = [arr[y, left:left + 430, :3] for y in (top, top + int(BETSLIP_LINE_PITCH) - 1)]
        if all(int((np.abs(e - np.array(BETTY_RED)).max(axis=1) <= 60).sum()) >= BETSLIP_FOCUS_RED_MIN for e in edges):
            return r
    return None


def _betslip_row_blank(arr: Any, box: tuple) -> bool:
    """No line in this row of the betslip panel: nearly all cream (text, red or blue, is far from it)."""
    x, y, w, h = box
    crop = arr[y:y + h, x:x + w, :3].astype(int)
    return int((np.abs(crop - np.array(BETSLIP_CREAM)).max(axis=2) > 80).sum()) < BETSLIP_TEXT_MIN_PX


# More selections than the panel holds: Betty scrolls it to the newest line and draws a yellow-on-red arrow at its top
# right (lines above); scrolled to the top, one at its bottom right (lines below). A selection must be on screen to be
# clicked and guaranteed (user's screenshots, 31 Oct: lines 4-12 under an up arrow, 1-9 over a down arrow).
BETSLIP_ARROW_ZONES = {'up': (1290, 75, 66, 40), 'down': (1290, 435, 66, 53)}  # x, y, w, h
BETSLIP_ARROW_MIN_PX = 40         # an arrow is ~125 yellow pixels; nothing else in those corners is yellow
BETSLIP_SCROLL_CLICKS = 30        # arrow clicks before a line counts as unreachable


def betslip_arrow(img: Any, which: str) -> tuple[int, int] | None:
    """Where Betty's betslip scroll arrow is ('up' / 'down'), its yellow arrow's centre, or None when it isn't drawn."""
    x, y, w, h = BETSLIP_ARROW_ZONES[which]
    a = np.array(img.convert('RGB').crop((x, y, x + w, y + h))).astype(int)
    yellow = (a[:, :, 0] > 200) & (a[:, :, 1] > 180) & (a[:, :, 2] < 80)
    if yellow.sum() < BETSLIP_ARROW_MIN_PX:
        return None
    ys, xs = np.nonzero(yellow)
    return x + int(xs.mean()), y + int(ys.mean())


def _betslip_offset(lines: list[dict]) -> int:
    """
    How many selections are scrolled away above the panel's top row. Each line read says so: its own number, less its
    row, less 1. It counts when most lines agree (2 at least, so a misread number is outvoted) and, above 0, only with
    a line on the panel's bottom row: only a full panel can hide lines (a lone line read '2.' hides nothing).
    """
    votes = Counter(line['n'] - _row(line, i) - 1 for i, line in enumerate(lines) if line.get('n'))
    ranked = votes.most_common(2)
    if not ranked or ranked[0][1] < 2 or (len(ranked) > 1 and ranked[1][1] == ranked[0][1]):
        return 0
    hidden = ranked[0][0]
    # Full: a line read on the bottom row, or the bottom row holding one that didn't read (the focus box on it)
    full = (max(_row(line, i) for i, line in enumerate(lines)) >= BETSLIP_MAX_LINES - 1
            or any(line.get('panel_full') for line in lines))
    if hidden <= 0 or not full:
        return 0
    return hidden


def _row(line: dict, i: int) -> int:
    """A line's row on the panel: as read, else its place in the list (lines built without one)."""
    return line.get('row', i)


def betslip_lines_by_number(lines: list[dict]) -> dict[int, dict]:
    """The lines showing, by selection number (1 = the first selection entered): the lines hidden above, plus their
    row. A row that didn't read is simply missing; the lines under it keep their numbers."""
    hidden = _betslip_offset(lines)
    return {hidden + _row(line, i) + 1: line for i, line in enumerate(lines)}


def betslip_rows_with_text(img: Any) -> list[int]:
    """The panel's rows holding a line, read or not, top first (colour only: down to the first blank row)."""
    arr, left = np.array(img.convert('RGB')), betslip_left(img)
    rows = []
    for r in range(BETSLIP_MAX_LINES):
        if _betslip_row_blank(arr, _betslip_row_box(left, r)):
            break
        rows.append(r)
    return rows


def betslip_count(lines: list[dict], img: Any = None) -> int:
    """How many selections the betslip holds: the number of its lowest line read, or with `img` (the screen the
    lines were read from) of its lowest row holding a line, read or not: a line whose text didn't read is still
    there (9.2459454, 31 Oct: '4 Keen' unread, so 'shows 3, expected 4' with line 4 in plain sight). Betty scrolls
    to the newest line as each one is added, so that is the last."""
    count = max(betslip_lines_by_number(lines), default=0)
    rows = betslip_rows_with_text(img) if img is not None else []
    return max(count, _betslip_offset(lines) + rows[-1] + 1) if rows else count


def _betslip_window(img: Any, lines: list[dict]) -> tuple[int, int]:
    """The selection numbers the panel's rows show, first and last: all 9 rows on a full panel (scrolled, or with lines
    below), else down to the lowest line read."""
    hidden = _betslip_offset(lines)
    if hidden or betslip_arrow(img, 'down'):
        return hidden + 1, hidden + BETSLIP_MAX_LINES
    return 1, max((_row(line, i) for i, line in enumerate(lines)), default=-1) + 1


def _click_betslip_arrow(img: Any, which: str, hidden: int) -> bool:
    """Clicks the betslip's `which` arrow and waits (up to NAV_TIMEOUT) for the panel to move: the lines hidden above
    it (`hidden` before the click) to change. False when the arrow isn't drawn."""
    spot = betslip_arrow(img, which)
    if not spot:
        return False
    betty_click(*spot)
    t0 = time.time()
    while time.time() - t0 < NAV_TIMEOUT:
        _check_stop()
        if _betslip_offset(read_betslip_selections(pyautogui.screenshot())) != hidden:
            break
        time.sleep(0.05)
    return True


BETSLIP_UNREAD_SECS = 1.0  # a line on the panel that doesn't read is read again this long


def betslip_row_of(n: int, lines: list[dict]) -> int:
    """The panel row selection `n` is on, from the lines showing (read or not, its row is its place under those
    hidden above)."""
    return n - _betslip_offset(lines) - 1


def _row_centre(row: int) -> int:
    return int(BETSLIP_LINE_TOP + row * BETSLIP_LINE_PITCH) + BETSLIP_LINE_H // 2


def show_betslip_line(n: int) -> list[dict]:
    """
    Scrolls Betty's betslip with its arrows until selection line `n` shows, and returns the lines then showing. Where
    it is comes from the lines' numbers after every click, so how far one click scrolls doesn't matter. A line on the
    panel that doesn't read (mid-redraw, a focus box) is read again for up to BETSLIP_UNREAD_SECS, never scrolled
    for; then the lines are returned without it, and its row is the lines hidden above plus its place
    (betslip_row_of).
    """
    clicks, unread_since = 0, None
    while True:
        _check_stop()
        img = pyautogui.screenshot()
        lines = read_betslip_selections(img)
        if n in betslip_lines_by_number(lines):
            return lines
        first, last = _betslip_window(img, lines)
        if first <= n <= last:
            unread_since = unread_since or time.time()
            if time.time() - unread_since > BETSLIP_UNREAD_SECS:
                return lines
            time.sleep(0.1)
            continue
        if clicks >= BETSLIP_SCROLL_CLICKS:
            raise WagerForStaff(f"betslip line {n} couldn't be brought into view with the betslip's arrows")
        which = 'up' if n < first else 'down'
        if not _click_betslip_arrow(img, which, first - 1):
            raise WagerForStaff(f"betslip line {n} isn't showing and Betty's {which} arrow on the betslip wasn't found")
        clicks, unread_since = clicks + 1, None


def scroll_betslip_to_end():
    """The betslip scrolled back down to its last line, as Betty leaves it after each selection is added."""
    for _ in range(BETSLIP_SCROLL_CLICKS):
        _check_stop()
        img = pyautogui.screenshot()
        if not _click_betslip_arrow(img, 'down', _betslip_offset(read_betslip_selections(img))):
            return


def read_whole_betslip() -> list[dict]:
    """
    Every selection line on the betslip, the first selection first. A panel with no scroll arrow shows them all;
    otherwise it is scrolled to the top, read on down with the down arrow and left at its last line. Each line's
    'row' is then its place in the whole slip (n - 1); its 'y' is where it showed when read. A line no page read is
    missing (_slip_fault says which).
    """
    img = pyautogui.screenshot()
    if not (betslip_arrow(img, 'up') or betslip_arrow(img, 'down')):
        return read_betslip_selections(img)
    show_betslip_line(1)
    seen: dict[int, dict] = {}
    for _ in range(BETSLIP_SCROLL_CLICKS):
        _check_stop()
        img = pyautogui.screenshot()
        lines = read_betslip_selections(img)
        seen.update(betslip_lines_by_number(lines))
        if not _click_betslip_arrow(img, 'down', _betslip_offset(lines)):
            break
    return [dict(seen[n], n=n, row=n - 1) for n in sorted(seen)]


_last_betslip_shot: Any = None  # the screen _read_new_betslip_line last read its lines from


def corpus_line(line: dict) -> dict:
    """A betslip line as the tests compare it: what the program checks of it."""
    return {k: line.get(k) for k in ('n', 'meeting', 'time', 'number', 'name', 'price', 'guaranteed')}


def check_new_betslip_line(lines: list[dict], already_on_slip: int, label: str) -> dict:
    """The betslip line of the selection just added, once the betslip holds exactly one more (counted by the lines'
    numbers when the panel scrolls). Betty scrolls to the new line; if the panel isn't showing it and has lines
    below, it is scrolled to."""
    want = already_on_slip + 1
    img = pyautogui.screenshot()
    if betslip_count(lines, img) < want and betslip_arrow(img, 'down'):
        lines = show_betslip_line(want)
        img = pyautogui.screenshot()
    on_slip = betslip_count(lines, img)
    if on_slip != want:
        raise WagerForStaff(f"after adding {label} the betslip shows {on_slip} selection(s), expected {want}")
    got = betslip_lines_by_number(lines).get(want)
    if got is None:  # not among the last lines read: the whole betslip read once before giving up
        lines = read_betslip_selections(img)
        got = betslip_lines_by_number(lines).get(want) if betslip_count(lines, img) == want else None
    if got is None:  # every way of reading it failed: what was added can't be checked
        raise WagerForStaff(f"after adding {label}, betslip line {want} is there but couldn't be read to check it")
    return got


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
RACE_LIST_TOP_ROWS = 4            # read to tell the race on top (its first runners): a quarter of the time of all 17
RACE_LIST_LABEL_COL = (3, 130)    # x, width of the 'Newc 2:31' column
RACE_LIST_PRICE_COL = (312, 88)   # x, width of the price column ('11-8' / 'NR', scratch/betty_screens/41)
RACE_LIST_ROW_NAME = re.compile(r'^\W*(?:(trap)\s*(\d{1,2})|(\d{1,2}))\s*[.,]\s*(.*)$', re.IGNORECASE)


def _race_list_column(img: Any, col: tuple, n_rows: int = RACE_LIST_ROWS) -> dict[int, str]:
    """One column of the runner list read in a single pass, by row: {row: text}. One OCR per column, not per row:
    17 rows x 2 columns read one at a time took several seconds on every 'right'. `n_rows`: only the top ones (the
    read takes time in proportion)."""
    x, w = col
    h, scale = n_rows * RACE_LIST_PITCH, 3
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


def race_list_rows(img: Any, n_rows: int = RACE_LIST_ROWS) -> list[dict]:
    """The runner rows showing in Betty's runner list, top first: [{'row', 'label', 'time', 'trap', 'number', 'name',
    'y'}]. 'trap' = a dog row ('Trap 4. Newinn Carole'); a horse row reads '04. Sleedagh'. 'y' = the row's centre.
    `n_rows`: only the top ones."""
    labels = _race_list_column(img, RACE_LIST_LABEL_COL, n_rows)
    names = _race_list_column(img, RACE_LIST_NAME_COL, n_rows)
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


# --- The previous-selections ("reuse") panel. Right-click on the slip image lists every selection already entered on
# this wager, all its slips, and stays open; a row's price takes the price, its name SP, as on the runner list (user,
# 31 Oct). Folder favourites can be reused; Master Index entries crash Betty, and the program never makes any.
# Rows ('Harl 10:32 | The Favourite | price') are 35 px apart from y = 286, in the runner list's columns. A row is
# white when that selection is on the slip being entered and cyan when it isn't (screens 15, 52-56).
REUSE_PANEL_X = (5, 400)      # the panel's width
REUSE_PANEL_COLS = (5, 137, 311, 399)  # its red column borders, top to bottom of the rows (screens 15, 52-56)
REUSE_ROW_PITCH = 35          # a row and its border: the rows' top and bottom lines are 36 / 71 / 106 px apart
REUSE_ROWS_MAX = 9            # rows above the folder buttons
SLIP_IMAGE_SPOT = (SLIP_REGION[0] + SLIP_REGION[2] // 2, SLIP_REGION[1] + SLIP_REGION[3] // 2)  # right-clicked
REUSE_SHOTS_KEPT = app_paths.setting("REUSE_SHOTS_KEPT", 10)         # pictures of the panel kept in logs/ when it couldn't be used


def _reuse_row_boxes(img: Any) -> list[tuple[int, int]]:
    """
    The panel's rows wherever it opens, by their shape: a red line right across the panel above the rows and one
    below (none between them), red column borders the whole way down, and a whole number of 35 px rows between.
    1.2.1-1.2.12 took a row as white between its own two red lines, from screen 15 alone (one row, on the slip), so
    the cyan rows of selections not yet on the slip, the ones to add, were never seen: the panel never worked live
    (9.2460806, 9.2460882, 1 Nov: 'didn't show', the selection typed). Found on screens 15 and 52-56 only, of 104.
    """
    a = np.array(img.convert('RGB').crop((0, 0, REUSE_PANEL_X[1] + 10, 630))).astype(np.int16)
    red = (a[:, :, 0] > 200) & (a[:, :, 1] < 70) & (a[:, :, 2] < 70)
    share = red[:, REUSE_PANEL_X[0]:REUSE_PANEL_X[1]].mean(axis=1)
    lines = [y for y in range(60, len(share) - 3) if share[y] >= 0.8 and share[y - 3] < 0.5 and share[y + 3] < 0.5]
    boxes = []
    for y0, y1 in zip(lines, lines[1:]):
        n = round((y1 - y0 - 1) / REUSE_ROW_PITCH)
        if not 1 <= n <= REUSE_ROWS_MAX or abs(y1 - y0 - 1 - n * REUSE_ROW_PITCH) > 3:
            continue
        if not all(red[y0 + 2:y1 - 1, x - 1:x + 2].any(axis=1).mean() >= 0.9 for x in REUSE_PANEL_COLS):
            continue
        h = (y1 - y0) / n
        boxes += [(round(y0 + k * h), round(y0 + (k + 1) * h)) for k in range(n)]
    return boxes


def reuse_panel_open(img: Any) -> bool:
    """Colour only: the panel is showing, at least one of its rows (_reuse_row_boxes)."""
    return bool(_reuse_row_boxes(img))


# Rows read 4x enlarged, in one start of Tesseract. At 3x 'Carl' read 'Can' (9.2460886), 'Towc' 'Towe' (9.2461093) and
# 'Harl' 'Har' (screen 15); at 4x all 62 rows on the saved panels read right, their names the same as at 3x (2 Nov)
REUSE_READ_SCALE = 4


def reuse_panel_rows(img: Any) -> list[dict]:
    """The panel's rows, top first: [{'row', 'label', 'time', 'name', 'y', 'unread', 'on_slip'}] ('name' without a
    cloth / trap number). A row whose meeting and time don't read is kept, marked 'unread': its place still counts.
    'on_slip': the row is white, the selection is on the slip being entered already."""
    rows = []
    arr = np.array(img.convert('RGB'))
    boxes = _reuse_row_boxes(img)
    texts = _ocr_bw_many(img, [box for y0, y1 in boxes for box in (
        (RACE_LIST_LABEL_COL[0] + 3, y0 + 3, RACE_LIST_LABEL_COL[1] - 6, y1 - y0 - 6),
        (RACE_LIST_NAME_COL[0] + 2, y0 + 3, RACE_LIST_NAME_COL[1] - 6, y1 - y0 - 6))], '--psm 7', REUSE_READ_SCALE)
    for k, (y0, y1) in enumerate(boxes):
        label, name = texts[2 * k], texts[2 * k + 1]
        m_time = re.search(r'(\d{1,2})[:.](\d{2})', label)
        cap = re.search(r'[A-Z][A-Za-z]{2,3}', label)
        on_slip = _colour_share(arr, (10, y0 + 3, 120, 4), (255, 255, 255), 20) >= 0.8  # above the text: its colour
        rows.append({'row': k, 'label': cap.group(0).lower() if cap else '',
                     'time': f"{int(m_time.group(1))}:{m_time.group(2)}" if m_time else '',
                     'name': re.sub(r'^\W*(?:trap\s*)?\d{1,2}\s*[.,]\s*', '', name, flags=re.I).strip(),
                     'y': (y0 + y1) // 2, 'unread': not (m_time and cap), 'on_slip': on_slip,
                     'text': f"{label} | {name}{' (on this slip)' if on_slip else ''}"})
    return rows


def save_reuse_picture(number: str | None) -> str | None:
    """Betty's screen when the previous-selections panel couldn't be used: logs/reuse_<wager>_<time>.png (the newest
    REUSE_SHOTS_KEPT kept), so the log can be followed by what Betty showed."""
    if os.environ.get("BETTY_HEADLESS") == "1":
        return None
    try:
        log_dir = app_paths.log_dir()
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, f"reuse_{number or 'unknown'}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot().save(path)
    except Exception as e:
        print(f"[-] Could not save the panel's picture: {e}")
        return None
    remove_oldest(glob.glob(os.path.join(log_dir, "reuse_*.png")), REUSE_SHOTS_KEPT)
    return path


def find_reuse_row(rows: list[dict], horse: dict, order: int | None = None, entered: int | None = None) -> dict | None:
    """
    The panel row that is this selection: its meeting's label (a letter out at most), time and name as far as Betty
    shows it ('The Favourite' for the favourite). When none reads as it but the panel lists exactly the selections
    entered (`entered` rows, in the order entered) and the row at its place (`order`) didn't read, that row: its place
    says it (the betslip check after the click still decides). None when no row fits. A white row is on the slip
    already and is never the one: a click would add it twice.
    """
    want_label, want_time = betty_meeting_abbrev(horse.get('meeting', '')), clock_12h(str(horse.get('time', '')))
    for row in rows:
        if row.get('unread') or row.get('on_slip'):
            continue
        if row['time'] != want_time or _letters_off(row['label'], want_label) > 1:
            continue
        shown = _letters(row['name'])
        if horse.get('favourite'):
            if 'favourite' in shown:
                return row
        elif re.fullmatch(r'trap\s*\d+', str(row['name']).strip().lower()):  # a dog's row names its trap, never the dog
            if int(re.sub(r'\D', '', row['name'])) == horse.get('number') and is_dog_race(horse):
                return row
        elif len(shown) >= 3 and name_similarity(shown, _letters(horse.get('name'))[:len(shown)]) >= 0.75:
            return row
    if order is not None and entered is not None and len(rows) == entered and 0 <= order < len(rows) \
            and rows[order].get('unread') and not rows[order].get('on_slip'):
        return dict(rows[order], by_place=True)
    return None


def betty_right_click(x: int, y: int):
    """A right-click on Betty, held like click_betty_cell's (Betty's controls miss a snap click)."""
    _check_stop()
    _require_betty()
    pyautogui.moveTo(x, y)
    interruptible_sleep(0.02)
    pyautogui.mouseDown(x, y, button='right')
    interruptible_sleep(0.035)
    pyautogui.mouseUp(x, y, button='right')
    interruptible_sleep(0.02)


def enter_from_reuse_panel(horse: dict, already_on_slip: int, order: int | None = None,
                           entered: int | None = None) -> dict | None:
    """
    A selection already entered on this wager, added again from the previous-selections panel: right-click on the slip
    image (unless the panel is open), its row read and clicked (price or name), and the betslip line checked as for
    any selection. The line, or None when it couldn't be done here and nothing was added (the panel didn't open, the
    row isn't in it, the click wasn't taken): the caller then enters it the usual way. A line added but wrong: staff.
    """
    label = (f"{'The Favourite' if horse.get('favourite') else horse.get('name') + ' #' + str(horse.get('number'))} "
             f"{clock_12h(str(horse.get('time', '')))} {horse.get('meeting', '')}")
    takes_price = (not horse.get('favourite')
                   and str(horse.get('price') or '').strip().lower() not in ('', 'sp', 'none', '0'))
    refresh_watcher_hud(f"Entering selection {already_on_slip + 1}: {label} (previously entered)...")
    if not reuse_panel_open(pyautogui.screenshot()):
        betty_right_click(*SLIP_IMAGE_SPOT)
        t0 = time.time()
        while not reuse_panel_open(pyautogui.screenshot()):
            _check_stop()
            if time.time() - t0 > NAV_TIMEOUT:
                shot = save_reuse_picture(_current_wager)
                print(f"[*] The previous-selections panel didn't show for {label} (no rows found on the left after "
                      f"the right-click{'; picture: ' + shot if shot else ''}): entering it the usual way.")
                return None
            time.sleep(0.05)
    rows = reuse_panel_rows(pyautogui.screenshot())
    row = find_reuse_row(rows, horse, order, entered)
    if not row:
        shot = save_reuse_picture(_current_wager)
        print(f"[*] {label} isn't among the previous selections as read: "
              f"{'; '.join(r.get('text') or f"{r.get('label')} {r.get('time')} | {r.get('name')}" for r in rows) or 'no rows read'}"
              f"{' (picture: ' + shot + ')' if shot else ''}. Entering it the usual way.")
        return None
    if row.get('by_place'):
        print(f"[*] Previous selections: row {row['row'] + 1} didn't read; it is {label} by its place in the order "
              "entered (checked on the betslip after the click).")
    col = RACE_LIST_PRICE_COL if takes_price else RACE_LIST_NAME_COL
    betty_click(col[0] + col[1] // 2, row['y'])
    print(f"[*] Added {label} from the previous selections (row {row['row'] + 1}, its "
          f"{'price' if takes_price else 'name: SP'}).")
    answer_entry_popups()
    lines = _read_new_betslip_line(already_on_slip)
    if betslip_count(lines, pyautogui.screenshot()) <= already_on_slip:
        shot = save_reuse_picture(_current_wager)
        print(f"[*] The click on {label} in the previous selections (row {row['row'] + 1}, y {row['y']}) wasn't taken"
              f"{' (picture: ' + shot + ')' if shot else ''}: entering it the usual way.")
        return None
    got = check_new_betslip_line(lines, already_on_slip, label)
    if takes_price and got['price'].upper() == 'SP':
        got = take_written_price(horse, got, label)
    problems = betslip_line_problems(got, horse)
    if problems:
        raise WagerForStaff(f"betslip shows {', '.join(problems)} for {label} (from the previous selections)")
    print(f"[+] Betslip line {got['n']}: {got['meeting']} {got['time']} {got['number']}. {got['name']} {got['price']} "
          "(checked)")
    return got


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
    x, y, w, h = RACE_LIST_ROW

    def one_by_one() -> list[str]:
        return [_ocr_bw(img, (x, y + i * RACE_LIST_PITCH, 130, h), '--psm 7', scale=3) for i in range(3)]

    def vote(texts: list[str]) -> str | None:
        votes: dict[str, int] = {}
        for text in texts[:3]:
            # Betty's label starts with a capital ('Shef 6:58'); the list's left border can read as a stray 'i' before it
            cap = re.search(r'[A-Z][A-Za-z]{2,3}', text)
            word = (cap.group(0) if cap else re.sub(r'[^A-Za-z]', '', text)).lower()[:4]
            if len(word) < 3:
                continue
            best = nearest_meeting_label(word, candidates, prefer)
            if best:
                votes[best] = votes.get(best, 0) + 1
        return max(votes, key=lambda k: votes[k]) if votes else None

    # The first three labels in one read (one read each took three times as long, on every runner list). It reads
    # most labels better, but can lose a label's first capital: 'Timb 2:42(v)' read 'imb 2:42(v)' and named no meeting,
    # where 1.2.0's read row by row named Timberwell (9.2460715 and 9.2460730, 1 Nov: both to staff). So when it names
    # none, the rows are read one at a time as in 1.2.0 before the label counts as unread.
    texts = [t for t in _ocr_bw(img, (x, y, 130, 3 * RACE_LIST_PITCH), '--psm 6', scale=3).splitlines() if t.strip()]
    top = vote(texts) if len(texts) >= 2 else None
    return top or vote(one_by_one())


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
    races = _feed_races_at(hhmm)
    for n_rows in (RACE_LIST_ROWS // 2, RACE_LIST_ROWS):  # the top half first; all of it only when that can't say
        rows = [r for r in race_list_rows(img, n_rows) if r['time'] == clock_12h(hhmm)]
        if not rows or rows[0]['row'] > 1:  # the first rows unread: the top race isn't known
            return None
        blocks = runner_list_races(rows)
        top, card_race = _race_is_wanted(blocks[0], meeting, candidates, races, want_dogs, want_virtual)
        if top is None and any(_race_is_wanted(b, meeting, candidates, races, want_dogs, want_virtual)[0]
                               for b in blocks[1:]):
            top = False
        if top is not None:
            break
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


def hhmm_on_card(meeting: str, time_hhmm: str) -> bool:
    """Whether Betty's cards have a race at this meeting at this time (or 12 hours from it)."""
    return meeting in _meetings_at(time_hhmm)


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
PRICE_BOX_BACK_MAX_SECS = 3  # a back price is taken only if it's this old or newer (user, 5 Nov)
PRICE_BOX_TOP_ROW_MAX_Y = 533  # the box's price buttons are centred above this, SP Only, Cancel and Override below it


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


def _back_price_age(text: str) -> int | None:
    """
    How many seconds old a Back button says its price is ('Back 1 Price 9-2 3 secs old'). None unless it reads as
    seconds and nothing else: an age with minutes in it, or a word read wrongly, counts as too old to be taken.
    """
    m = re.fullmatch(r'back \d price (?:\d{1,3} ?[-/] ?\d{1,3}|evs|evens) (?:0 mins? )?(\d{1,2}) secs? old',
                     ' '.join(text.lower().split()))
    return int(m.group(1)) if m else None


def _price_box_choice(img: Any) -> tuple[str, tuple[int, int]]:
    """
    Which button to click on a price box Enter didn't close, as (what it says, centre). The rule (user, 5 Nov):
    'Price when struck' if it's there, else the first Forward price, else Back 1 if it's 3 seconds old or less, else
    'Override with entered price'. Older back prices are never taken. Left to right the buttons run back in time to
    forward in time, so the first Forward is the leftmost and Back 1 the rightmost back. A price button that can't be
    read: staff, as the choice might be wrong without it.
    """
    buttons = read_buttons(img, MODAL_BACK_OUT[MODAL_PRICE][1])
    named = [(re.sub(r'[^a-z]', '', text.lower()), ' '.join(text.split()), centre) for text, centre in buttons]
    top = sorted((b for b in named if b[2][1] < PRICE_BOX_TOP_ROW_MAX_Y), key=lambda b: b[2][0])
    for letters, text, _ in top:
        if not letters.startswith(('pricewhenstruck', 'forward', 'back')):
            raise WagerForStaff(f"the price check box has a price button that couldn't be read ('{text}')")
    struck = [b for b in top if b[0].startswith('pricewhenstruck')]
    if struck:
        return struck[0][1], struck[0][2]
    forward = [b for b in top if b[0].startswith('forward')]
    if forward:
        return forward[0][1], forward[0][2]
    back = [b for b in top if b[0].startswith('back')]
    if back:
        _, text, (x, y) = back[-1]
        age = _back_price_age(text)
        # Read again, larger, before it's taken: 13 secs read as 3 would pay on an old price
        if (age is not None and age <= PRICE_BOX_BACK_MAX_SECS
                and _back_price_age(_ocr_bw(img, (x - 55, y - 36, 110, 72), '--psm 6', 5)) == age):
            return text, (x, y)
    override = [b for b in named if b[0].startswith('override')]
    if len(override) != 1:
        raise WagerForStaff("the price check box stayed open after Enter, and its 'Override with entered price' "
                            "button wasn't found")
    return "Override with entered price", override[0][2]


def answer_price_box():
    """
    Betty's price check box, for every line alike (user, 6 Nov), a typed price too: Enter takes the price when struck. A
    box with no 'Price when struck' button ignores Enter (user's screenshot 42, 30 Oct: the program backed out of it;
    9.2467105, 5 Nov); then the button is chosen by _price_box_choice and clicked, found by its text. Still open: staff.
    """
    print("[*] Price check box: taking the price when struck (Enter).")
    betty_press('enter')
    if _price_box_shows(False, PRICE_BOX_CLOSE_SECS):
        return
    label, spot = _price_box_choice(pyautogui.screenshot())
    print(f"[*] Price check box: Enter didn't close it (no price when struck): '{label}'.")
    betty_click(*spot)
    if not _price_box_shows(False, PRICE_BOX_CLOSE_SECS):
        raise WagerForStaff(f"the price check box stayed open after '{label}'")


F8_PRICE_BOX_TIMES = 3     # how many times one F8 may meet the price box before it's left to expect_screen
F8_AFTER_BOX_SECS = 1.0    # after the box is answered: how long Betty has to go on by herself before F8 is pressed again


def answer_price_box_after_f8():
    """
    F8 can open the price box again (9.2467105, 5 Nov: Far Too Fizzy, overridden at 9-2; backed out of it twice, so
    staff). It is answered like any other, and which line it's about isn't known here. Betty goes on to Choose Bet and
    Stake, or stays on the betslip, and then F8 is pressed again. Anything else is left to expect_screen.
    """
    targets = {SCREEN_BET_AND_STAKE, MODAL_PRICE}
    for _ in range(F8_PRICE_BOX_TIMES):
        if wait_for_screen(targets) != MODAL_PRICE:
            return
        print("[*] F8: Betty's price check box opened.")
        answer_price_box()
        if wait_for_screen(targets, F8_AFTER_BOX_SECS) in (SCREEN_RACE_LIST, SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY,
                                                           SCREEN_REUSE_PANEL):
            betty_press('f8')


POPUP_WAIT_SECS = 0.4        # how long a box is looked for after a step that can open one
POPUP_WAIT_AFTER_ADD = 0.1   # after adding a selection: the betslip read that follows answers a box opening later


LATE_HALF_DAY_MINS = 600  # a late-selection box this late is the race 12 hours ago at the same clock time (usually about 720)
LATE_BOX_TEXT = (380, 340, 620, 80)


def late_box_minutes(img: Any) -> int | None:
    """The minutes in the late-selection box ("Wager staked 62 mins, 38 secs after 'off'"), None when they don't read."""
    m = re.search(r"staked\s+([\d,]+)\s*min", _ocr_box(img, LATE_BOX_TEXT, '--psm 6'), re.I)
    return int(m.group(1).replace(',', '')) if m else None


def answer_entry_popups(max_rounds: int = 3, wait: float = POPUP_WAIT_SECS):
    """After adding a runner: the price box -> answer_price_box; a late selection -> Yes (void processing), or No when it's
    the race 12 hours ago (RaceHalfADayOld). `wait`: how long the first box is looked for."""
    for _ in range(max_rounds):
        screen = wait_for_screen(set(MODAL_SIGNATURES), timeout=wait)
        if screen == MODAL_PRICE:
            answer_price_box()
        elif screen == MODAL_LATE_SELECTION:
            shot = pyautogui.screenshot()
            mins = late_box_minutes(shot)
            if mins is not None and mins >= LATE_HALF_DAY_MINS:
                spot = find_button(shot, "No", MODAL_BACK_OUT[MODAL_LATE_SELECTION][1])
                if not spot:
                    raise NavError("late-selection box: 'No' not found")
                print(f"[*] Late selection, {mins} mins: the race 12 hours ago at this clock time. No.")
                betty_click(*spot)
                raise RaceHalfADayOld(f"only the race 12 hours earlier came up ({mins} mins late)")
            spot = find_button(shot, "Yes", MODAL_BACK_OUT[MODAL_LATE_SELECTION][1])
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
    if detect_screen() not in (SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, *SCREENS_NOT_SURE, SCREEN_REUSE_PANEL):
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
    got = check_new_betslip_line(_read_new_betslip_line(already_on_slip), already_on_slip, label)
    problems = betslip_line_problems(got, horse)
    if problems:
        raise WagerForStaff(f"betslip shows {', '.join(problems)} for {label}")
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
        # The label first (one read); the runners (a slower read) only when the label doesn't name a meeting on the
        # card (user, 31 Oct: speed). A label read as the wrong race is still caught: the betslip line after the
        # number is checked against the card.
        top = top_meeting_in_race_list(shot, candidates, prefer=meeting)
        if not top:
            top = runner_list_top_by_content(shot, meeting, hhmm, candidates, want_dogs, want_virtual)
        if top or time.time() - t_read > reread_secs:
            break
        time.sleep(0.1)

    def decided(result: str | None) -> str | None:
        if corpus_on():
            corpus_save('runner_top', shot, {'meeting': meeting, 'hhmm': hhmm, 'candidates': candidates,
                                             'want_dogs': want_dogs, 'both_kinds': both_kinds,
                                             'want_virtual': want_virtual, 'card': corpus_card(hhmm)}, result)
        return result

    if top != meeting:
        return decided(top)
    # Horses and dogs can share a meeting's label (Doncaster): a dog list's rows read 'Trap 1. ..', a horse
    # list's '01. ..', so the kind of list must be the selection's kind too
    dogs = race_list_is_dogs(shot)
    t_kind = time.time()
    while dogs is None and both_kinds and time.time() - t_kind < MEETING_REREAD_SECS:
        time.sleep(0.1)  # horses and dogs share the label: an unread list is read again, never assumed
        shot = pyautogui.screenshot()
        dogs = race_list_is_dogs(shot)
    if dogs is None and both_kinds:
        decided("staff: horses or dogs unread")
        raise WagerForStaff(f"can't read whether Betty's {meeting} {clock_12h(hhmm)} list is the horses or "
                            "the dogs (both race then)")
    if dogs is None or dogs == want_dogs:
        return decided(meeting)
    return decided(f"{meeting} {'dogs' if dogs else 'horses'}")


def corpus_card(hhmm: str) -> list[dict]:
    """The card's runners at this time (and 12 hours from it), for a decision kept by corpus_save: what the replay
    gives the program as Betty's card, as it was then (virtual races leave the feed once run)."""
    times = _times_12h_apart(hhmm)
    return [dict(r, dogs=dogs) for src, dogs in ((racecard_manager, False), (greyhound_card, True))
            for r in src.get_runners() if r.get('time_str') in times]


def runner_list_signature(img: Any) -> tuple:
    """What heads the runner list: its first rows as read (meeting, time, runner), letters only. It differs whenever
    another race comes to the top; () when the first rows don't read."""
    # One read across the meeting and runner columns of the first rows (both columns over all 17 rows took ~0.7 s, on
    # every 'right' and while waiting for it): what heads the list has changed when this text has
    x0, x1 = RACE_LIST_LABEL_COL[0], RACE_LIST_NAME_COL[0] + RACE_LIST_NAME_COL[1]
    text = _ocr_bw(img, (x0, RACE_LIST_ROW[1], x1 - x0, RACE_LIST_TOP_ROWS * RACE_LIST_PITCH), '--psm 6', 2)
    return tuple(t for t in (_letters(line)[:24] for line in text.splitlines()) if len(t) >= 6)


def _next_runner_list(prev_top: str | None, meeting: str, candidates: list[str], prev_sig: tuple = ()) -> str:
    """
    After 'right': the next runner list (RACE_LIST) or the end of the list (EXHAUSTED). A runner list counts only once
    the race on top has changed from the one 'right' was pressed on (`prev_sig`, runner_list_signature): the old list
    still showing is a runner list too, and read as the new one it had 'right' pressed again, past the meeting wanted
    (9.2459558, 31 Oct: Towcester read twice, Down Royal 2:38 skipped). A list the screen check doesn't recognise
    counts once its top meeting reads and differs (9.2452785, 26 Oct). Otherwise as expect_screen after NAV_TIMEOUT:
    the list unchanged that long means 'right' wasn't taken.
    """
    targets = {SCREEN_RACE_LIST, SCREEN_RACE_ENTRY_EXHAUSTED}
    t0 = time.time()
    while True:
        _check_stop()
        shot = pyautogui.screenshot()
        screen = detect_screen(shot)
        if screen == SCREEN_RACE_ENTRY_EXHAUSTED:
            return screen
        if screen in (SCREEN_RACE_LIST, *SCREENS_NOT_SURE):
            sig = runner_list_signature(shot)
            if sig and sig != prev_sig:
                return SCREEN_RACE_LIST
        if screen == SCREEN_RACE_LIST and not prev_sig and time.time() - t0 >= MEETING_REREAD_SECS:
            return screen  # nothing to compare with: as before, after a moment for Betty to redraw
        if screen in SCREENS_NOT_SURE:
            top = top_meeting_in_race_list(shot, candidates, prefer=meeting)
            if top and top != prev_top:
                return SCREEN_RACE_LIST
        if time.time() - t0 >= NAV_TIMEOUT:
            return expect_screen(targets, timeout=0, doing="next meeting ('right')")
        time.sleep(0.02)


def read_betslip_tail(img: Any, n: int = 2) -> list[dict]:
    """
    The betslip's last `n` lines read (the rows holding a line found by colour first, down to the first blank one):
    enough to check the line just added and how many there are (betslip_count with the screen). The whole betslip,
    read on every poll after each selection, cost 0.8-1.7 s (user, 31 Oct: speed).
    """
    arr, left = np.array(img.convert('RGB')), betslip_left(img)
    rows = betslip_rows_with_text(img)
    full = bool(rows) and rows[-1] == BETSLIP_MAX_LINES - 1
    drop, _, _, scale = BETSLIP_ROW_READS[0]
    firsts = _ocr_bw_many(img, [_betslip_first_read_box(left, r) for r in rows[-n:]], '--psm 7', scale, drop)
    out = [line for line in (read_betslip_row(img, r, arr, left, first) for r, first in zip(rows[-n:], firsts))
           if line]
    for line in out:
        line['panel_full'] = full
    hidden = _betslip_offset(out)
    for line in out:
        if line['n'] is None:
            line['n'] = hidden + line['row'] + 1
    return out


def _read_new_betslip_line(already_on_slip: int) -> list[dict]:
    """
    The betslip's last lines once one more selection than `already_on_slip` shows, or the last read after
    NAV_TIMEOUT. A box that opens late (after answer_entry_popups stopped looking) is answered here; the betslip
    under it isn't read. Only the last lines are read (read_betslip_tail): the new one, and one above it.
    """
    global _last_betslip_shot
    t0 = time.time()
    while True:
        _check_stop()
        img = pyautogui.screenshot()
        arr = np.array(img.convert('RGB'))
        box_open = any(_signals_pass(arr, sig['colours']) for sig in MODAL_SIGNATURES.values())
        lines = [] if box_open else read_betslip_tail(img)
        shown = betslip_count(lines, None if box_open else img) > already_on_slip
        if not shown and time.time() - t0 > NAV_TIMEOUT and wait_out_freeze(f"betslip line {already_on_slip + 1}"):
            t0 = time.time()
            continue
        if shown or time.time() - t0 > NAV_TIMEOUT:
            _last_betslip_shot = img  # the screen the lines were read from, for corpus_save
            return lines
        if box_open:
            answer_entry_popups()
        else:
            time.sleep(0.1)


# Betty adds a selection without a price now and then, usually when its feed has trouble: the runners in the race show
# prices, '+' puts this one on at SP and no price box opens (9.2466814, 9.2466824, 9.2466825, 5 Nov; another wager had
# 7/4 on Presley 40 minutes before). The written price is typed on the line then (user, 5 Nov). It went to staff before.
_typed_prices: dict[tuple, str] = {}  # this wager's selections whose price was typed: selection_key -> '7-2'
BETSLIP_PRICE_X, BETSLIP_PRICE_W = 285, 150  # the price on a betslip line, from the panel's left edge (names stop short)
PRICE_LINE_FOCUS_SECS = 1.5  # after the price is clicked: how long the line may take to show it has the focus
PRICE_TYPED_BOX_SECS = 1.0   # after Enter: how long the price box may take to open
EVENS_WORDS = ('ev', 'evs', 'evens', 'even')


def written_price_keys(price: Any) -> str | None:
    """A price as it is typed into Betty: 2/1 is 2.1, 7/2 is 7.2, 11/10 is 11.10, evens is 1.1 (user, 5 Nov). None
    when it isn't a plain price."""
    text = str(price or '').strip().lower()
    if text in EVENS_WORDS:
        return '1.1'
    m = re.fullmatch(r'(\d{1,3})\s*[-/.]\s*(\d{1,3})', text)
    return f"{int(m.group(1))}.{int(m.group(2))}" if m and int(m.group(1)) and int(m.group(2)) else None


def _price_value(price: Any) -> Fraction | None:
    """A written or betslip price as a number, so 5/1 and 5-1 are one price, and so are 1/1 and Evs."""
    keys = written_price_keys(price)
    return Fraction(*map(int, keys.split('.'))) if keys else None


def _betslip_price_x(arr: Any, left: int, row: int) -> int | None:
    """Where the price is on the betslip line at `row`: the middle of what's drawn there, by colour. None: nothing is."""
    top, x0 = int(BETSLIP_LINE_TOP + row * BETSLIP_LINE_PITCH), left + BETSLIP_PRICE_X
    crop = arr[top:top + BETSLIP_LINE_H, x0:x0 + BETSLIP_PRICE_W, :3].astype(int)
    cols = np.flatnonzero((np.abs(crop - np.array(BETSLIP_CREAM)).max(axis=2) > 80).any(axis=0))
    return x0 + int(cols.mean()) if cols.size else None


def second_price_read(horse: dict, img_str: str) -> dict | None:
    """
    The price beside one selection, read again on its own from the slip as read. It isn't told the first reading, so
    it can't just agree with it. {'price', 'cut_off', 'confidence'}, or None when no reader answered.
    """
    time_txt = str(horse.get('raw_time') or horse.get('written_time') or horse.get('time') or '').strip()
    hint = str(horse.get('raw_meeting_hint') or '').strip()
    line = f"on line {horse['line_num']} of the writing (counting from the top), " if horse.get('line_num') else ""
    answer = _ask_vision_json(
        f"""You are checking one price on a handwritten betting slip. The price is about to be keyed by hand, so a wrong
digit costs real money.
Find the selection {line}for the runner {horse.get('name')}{f", number {horse['number']}" if horse.get('number') else ''}{f", with the race time written '{time_txt}'" if time_txt else ''}{f" and the meeting written '{hint}'" if hint else ''}. The slip may show only its number, or spell its name differently.
Read only the price written beside it, usually to its left or right, like 5/1, 11/4, 7-2 or Evs. Read it digit by digit
from the ink. Do not work it out from what the horse might be, or from any other line.
Handwritten prices are often at the very edge of the picture, where digits can be cut off: 15/1 can look like 5/1 if the
1 is cut or touches the edge. Look at the edge closely. Set "cut_off" true if ink runs into the edge of the picture beside
this price, or if a digit could be missing for any other reason.
Answer "high" confidence only if every digit is clear. If you cannot find a price, leave "price" empty.
Return JSON: {{"price": "...", "cut_off": true or false, "confidence": "high" or "low"}}""",
        img_str, "reader-chain",
        {"type": "OBJECT",
         "properties": {"price": {"type": "STRING"}, "cut_off": {"type": "BOOLEAN"}, "confidence": {"type": "STRING"}},
         "required": ["price", "cut_off", "confidence"], "propertyOrdering": ["price", "cut_off", "confidence"]},
        f"Second read of the price of '{horse.get('name')}'")
    return answer or None


def take_written_price(horse: dict, got: dict, label: str) -> dict:
    """
    Betty has put a selection on at SP, but the customer took a price: the price on the betslip line is clicked, the
    written price typed and Enter pressed. Betty's box is answered in the usual order (answer_price_box, user, 6 Nov): the
    price when struck or a forward price if it offers one, otherwise 'Override with entered price', which keeps the price
    typed. Keys go only once Betty's focus box is on the line: anywhere else a digit picks a runner from the list. The line
    must then show a price. Returns the line. Anything else: staff, with nothing placed.
    A typed price is paid on as it stands, so it is read a second time first and typed only if that read agrees, is
    sure of every digit and sees nothing cut off: the first read took a 15/1 or 25/1 at the slip's edge for 5/1 and
    didn't mark it unclear (9.2466814, 5 Nov; the second read said cut off, the other 10 of 12 agreed and were sure).
    """
    price = horse.get('price')

    def stop(why: str) -> WagerForStaff:
        return WagerForStaff(f"the customer took {price} on {label}, Betty put it on at SP, and the price wasn't "
                             f"typed: {why}")

    keys = written_price_keys(price)
    if not keys:
        raise stop("it isn't a plain price")
    if 'price' in (horse.get('unclear') or []):
        raise stop("the slip reader wasn't sure of it")
    if selection_key(horse) not in _typed_prices:  # on a later slip of this wager it has been read twice already
        refresh_watcher_hud(f"Betty gave no price: reading {label}'s price again...")
        second = second_price_read(horse, _last_reading['img_str']) if _last_reading else None
        _check_stop()
        if not second:
            raise stop("it couldn't be read a second time to check it")
        again = str(second.get('price') or '').strip()
        if second.get('cut_off'):
            raise stop(f"a second read says it may be cut off at the edge of the slip (it read '{again}')")
        if _price_value(again) != _price_value(price):
            raise stop(f"a second read of the slip gave '{again}'")
        if str(second.get('confidence') or '').lower() != 'high':
            raise stop(f"a second read wasn't sure of it (it read '{again}')")
        print(f"[*] {label}: a second read of the slip agrees, {again}.")
    row, img = got['row'], pyautogui.screenshot()
    x = _betslip_price_x(np.array(img.convert('RGB')), betslip_left(img), row)
    if x is None:
        raise stop("the SP couldn't be found on the betslip")
    print(f"[!] Betty put {label} on at SP (no price from Betty): typing the customer's {price} as {keys}.")
    betty_click(x, got['y'])
    t0, cancelled = time.time(), False
    while True:
        _check_stop()
        shot = pyautogui.screenshot()
        if _signals_pass(np.array(shot.convert('RGB')), MODAL_SIGNATURES[MODAL_PRICE]['colours']):
            spot = None if cancelled else find_button(shot, "Cancel", MODAL_BACK_OUT[MODAL_PRICE][1])
            if not spot:
                raise stop("Betty's price box opened on the line before anything was typed")
            betty_click(*spot)  # nothing entered yet, so there is nothing for it to ask about
            cancelled = True
        elif betslip_focus_row(shot) == row:
            break
        elif time.time() - t0 > PRICE_LINE_FOCUS_SECS:
            raise stop("the line didn't take the focus when clicked, so nothing was typed")
        time.sleep(0.04)
    for ch in keys:  # not betty_press, which refuses '.': here it is the price's, on a line seen to have the focus
        _check_stop()
        _send_key(ch)
    if not _price_box_shows(True, 0.05):
        betty_press('enter')
    if _price_box_shows(True, PRICE_TYPED_BOX_SECS):
        answer_price_box()
    want, t0 = _price_value(price), time.time()
    while True:
        _check_stop()
        shot = pyautogui.screenshot()
        if _signals_pass(np.array(shot.convert('RGB')), MODAL_SIGNATURES[MODAL_PRICE]['colours']):
            answer_price_box()
            continue
        line = read_betslip_row(shot, row)
        shown = _price_value(line['price']) if line else None
        if shown is not None:
            if shown == want:
                print(f"[+] {label}: {line['price']} typed from the slip and showing on the betslip.")
            else:
                print(f"[+] {label}: Betty's price box gave {line['price']}, where {price} was written and typed.")
            _typed_prices[selection_key(horse)] = f"{want.numerator}-{want.denominator}"
            return dict(line, n=got.get('n') if line.get('n') is None else line['n'])
        if time.time() - t0 > NAV_TIMEOUT:
            raise stop(f"the betslip shows {line['price'] if line else 'nothing readable'} after typing {keys}")
        time.sleep(0.1)


def enter_selection(horse: dict, already_on_slip: int, after_same_race: bool = False, after_same_time: bool = False,
                    entered_before: bool = False, entered_order: tuple[int, int] | None = None,
                    next_horse: dict | None = None):
    """
    Adds one locked selection to the current betting slip and confirms it on the betslip read-back. After a selection
    in the same race (`after_same_race`), it is chosen from the runner list still showing, with no time typed again
    (user, 26 Oct: '1:17 Romford 3-4 S/F/C' is the 1:17 once, then 3 + Enter, 4 + Enter). After one at the same time
    at another meeting (`after_same_time`), the list still showing is that time's: 'right' on from it to the meeting
    (to-do, 30 Oct: the time was typed again for every selection). A meeting the list has already passed ends it, and
    the time is typed after all. A selection already entered on an earlier slip of this wager (`entered_before`) is
    taken from the previous-selections panel (enter_from_reuse_panel), else entered the usual way. A sports selection
    goes through the Master Index (`next_horse`: the one after it, for typing ahead).
    """
    if horse.get('sport'):
        return enter_sports_selection(horse, already_on_slip, next_horse)
    if _index_showing:  # a racing selection after a sports one
        index_leave()
    order, n_entered = entered_order or (None, None)
    if entered_before and not horse.get('void') and enter_from_reuse_panel(horse, already_on_slip, order, n_entered):
        return None
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
        walked, walked_again = 0, False  # 'right' presses this walk; whether the list was walked from its start again
        for _ in range(MAX_MEETING_STEPS * 2):
            if screen == SCREEN_RACE_ENTRY_EXHAUSTED and reuse:  # passed it: from the start of the list after all
                print(f"[*] {meeting} wasn't further along the {clock_12h(hhmm)} runner list: typing the time.")
                reuse, walked = False, 0
                img = pyautogui.screenshot()
                screen = _type_race_time(img, detect_screen(img), hhmm)
            if screen == SCREEN_RACE_ENTRY_EXHAUSTED and walked and not walked_again and hhmm_on_card(meeting, hhmm):
                # The end of the list after 'right' with the meeting on Betty's card: it was passed, not missing (a
                # read of the list before Betty redrew it). The list is walked once more from its start.
                print(f"[*] The end of the {clock_12h(hhmm)} runner list without {meeting}, which is on Betty's card: "
                      "passed it. Typing the time and walking the list again.")
                walked, walked_again = 0, True
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
                wait_out_freeze(f"runner list for {hhmm}")
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
            before = runner_list_signature(pyautogui.screenshot())
            betty_press('right')
            walked += 1
            screen = _next_runner_list(top, meeting, candidates, before)
        else:
            raise WagerForStaff(f"could not bring {meeting} to the top of Betty's runner list")
    lines = None
    # The race 12 hours ago shares this clock time: No, 'right', then 'left' and 'right', which shuffles the duplicate meeting
    # out and shows the second one, then staff (user, 6 Nov)
    for keys in ((), ('right',), ('left', 'right')):
        if keys:
            wait_for_screen({SCREEN_RACE_LIST})  # the box closing
            print(f"[*] {' then '.join(keys)} and {label} again: that was the race 12 hours ago.")
            for key in keys:
                before = runner_list_signature(pyautogui.screenshot())
                betty_press(key)
                screen = _next_runner_list(meeting, meeting, candidates, before)
            if screen == SCREEN_RACE_ENTRY_EXHAUSTED or _runner_list_top(meeting, hhmm, candidates, want_dogs, both_kinds,
                                                                         want_virtual=want_virtual) != meeting:
                continue
        try:
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
            answer_entry_popups(wait=POPUP_WAIT_AFTER_ADD)  # a box opening later is answered by the betslip read
            lines = _read_new_betslip_line(already_on_slip)
            break
        except RaceHalfADayOld:
            if row or void:  # no list to walk: 'right' would take another race away
                raise
    if lines is None:
        raise WagerForStaff(f"{label}: only the race 12 hours earlier came up, after 'right', then 'left' and 'right'")
    inputs = {'already_on_slip': already_on_slip, 'label': label, 'horse': horse}
    try:
        got = check_new_betslip_line(lines, already_on_slip, label)
    except WagerForStaff as e:
        corpus_save('betslip_line', _last_betslip_shot, inputs, {'error': str(e)})
        raise
    if takes_price and got['price'].upper() == 'SP':
        got = take_written_price(horse, got, label)
    problems = betslip_line_problems(got, horse)
    if corpus_on():
        corpus_save('betslip_line', _last_betslip_shot, dict(inputs, card=corpus_card(hhmm)),
                    {'line': corpus_line(got), 'problems': problems})
    if problems:
        raise WagerForStaff(f"betslip shows {', '.join(problems)} for {label}")
    print(f"[+] Betslip line {got['n']}: {got['meeting']} {got['time']} {got['number']}. {got['name']} {got['price']} (checked)")


def _type_race_time(img: Any, screen: str, hhmm: str) -> str:
    """'/' for the yellow time box when it isn't showing, the race time, and the runner list it brings up (or the end
    of the list when Betty has no race then)."""
    box_open = _signals_pass(np.array(img.convert('RGB')), [RACE_ENTRY_TIME_BOX])
    if screen != SCREEN_RACE_ENTRY_READY and not (screen in SCREENS_NOT_SURE and box_open):
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
    # A dog's line is 'Trap 3': 'trap' and its number, never the letters alone ('Trapper John', a horse, 7 Nov)
    trap_line = bool(re.match(r'\W*trap\s*\d', line_name, re.I))
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
    """Why the betslip isn't right before F8 (count, a line, a guarantee), or None when it is. `lines`: the whole
    betslip (read_whole_betslip), matched to the selections by number."""
    if betslip_count(lines) != len(horses):
        return f"before F8 the betslip shows {betslip_count(lines)} selection(s), expected {len(horses)}"
    by_number = betslip_lines_by_number(lines)
    unread = [n for n in range(1, len(horses) + 1) if n not in by_number]
    if unread:
        return f"before F8, betslip line(s) {', '.join(map(str, unread))} couldn't be read"
    for n, line in sorted(by_number.items()):
        horse = horses[n - 1]
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


def _line_guaranteed(arr: Any, left: int, row: int) -> bool:
    """Colour only (no OCR): is the price on the betslip panel's line at `row` (0 = top) purple?"""
    top = int(BETSLIP_LINE_TOP + row * BETSLIP_LINE_PITCH)
    return _colour_share(arr, (left + 250, top, 160, BETSLIP_LINE_H), GUARANTEED_PURPLE, 30) >= 0.02


def _focus_down_to(n: int, at: tuple, known: dict[int, dict]) -> tuple[dict, int] | None:
    """
    Down from the line just guaranteed (`at` = its number, its row, the lines hidden above) to selection `n`, the
    next. Which line has the focus is told by where Betty's focus box is, never by reading the line under it, which
    the box can garble (9.2459368, 31 Oct: line 4 under it didn't read, so staff). The box one row down: the panel
    didn't move. Anywhere else, the panel may have scrolled under it, by a line or a page: the lines showing are read
    and say how many are hidden above, so the box's row gives its line whatever Betty did (9.2459368, 15:10: Down
    from line 9 on the bottom row was taken only for one line's scroll, so ~12 s went in a wait and a click). The
    line's price and name come from `known`, read before the box was round it. Down is pressed only when the box is
    seen on the line just guaranteed. (line, lines hidden above) once confirmed; None (nothing pressed, or no move
    seen within NAV_TIMEOUT): the caller clicks the line instead, so 'g' never goes to a line that isn't confirmed.
    """
    _, row, hidden = at
    if betslip_focus_row(pyautogui.screenshot()) != row:
        return None
    betty_press('down')
    price_box = MODAL_SIGNATURES[MODAL_PRICE]['colours']
    bottom = BETSLIP_MAX_LINES - 1
    t0 = time.time()
    while time.time() - t0 < NAV_TIMEOUT:
        _check_stop()
        img = pyautogui.screenshot()
        arr = np.array(img.convert('RGB'))
        if _signals_pass(arr, price_box):  # focusing a line can open its price box (user, 30 Oct)
            answer_price_box()
            continue
        now, now_hidden = betslip_focus_row(img), hidden
        if now is None or (now == row and row != bottom):  # not moved yet (mid-panel the box can't stay put)
            time.sleep(0.03)
            continue
        if now != row + 1:  # not simply a row down: how far the panel scrolled is read, not assumed
            lines = read_betslip_selections(img)
            known.update(betslip_lines_by_number(lines))
            now_hidden = _betslip_offset(lines)
        if now_hidden + now + 1 != n:
            time.sleep(0.03)
            continue
        if now_hidden != hidden:  # for the log: what Betty did, so a change in it shows
            print(f"[*] Down to line {n}: Betty scrolled the betslip {now_hidden - hidden} line(s), "
                  f"line {n} is on its row {now + 1}.")
        base = known.get(n) or read_betslip_row(img, now, arr) or {'price': '', 'name': ''}
        return dict(base, n=n, row=now, y=_row_centre(now),
                    guaranteed=_line_guaranteed(arr, betslip_left(img), now)), now_hidden
    return None


def apply_guarantees(horses: list[dict], struck_clock: str | None):
    """
    Best odds guaranteed (user, 31 Oct): the first selection that qualifies (bog_wanted) is clicked and 'g' pressed,
    then Down to the next and 'g', and so on. Down is taken only to the line straight after one just guaranteed, and
    only once Betty's focus box is on that line; where the box goes after Down says which line it reached
    (_focus_down_to). Otherwise (the first, after a line skipped, a selection that doesn't qualify in between, a
    Down not seen) the line is scrolled into view and clicked by its row, read or not. A non-runner, withdrawn or
    void line is skipped and the next one clicked: Down loses focus there. Each 'g' must turn its price purple; 'g'
    can't be undone, so it is never pressed twice: unconfirmed -> staff. Every line read on the way is kept (`known`),
    so a line the focus box garbles is still known by what it showed before.
    """
    wanted = [i for i, h in enumerate(horses) if bog_wanted(h, struck_clock)]
    if not wanted:
        why = "struck outside the BOG windows" if not bog_window_applies(struck_clock) else "no UK/IRE horse with a price"
        print(f"[*] Best odds guaranteed: none needed ({why}).")
        return
    img = pyautogui.screenshot()
    lines = read_betslip_tail(img)
    if betslip_count(lines, img) != len(horses):
        raise WagerForStaff(f"the betslip shows {betslip_count(lines, img)} selection(s) before guaranteeing, "
                            f"expected {len(horses)}")
    left = betslip_left(img)
    known = dict(betslip_lines_by_number(lines))  # the rest are read as they're brought into view
    price_box = MODAL_SIGNATURES[MODAL_PRICE]['colours']
    boxes = [sig['colours'] for sig in MODAL_SIGNATURES.values()]
    refresh_watcher_hud(f"Best odds guaranteed: {len(wanted)} selection(s)...")
    t_all, at = time.time(), None  # at: (number, row, lines hidden above) of the line just guaranteed
    for i in wanted:
        n, name = i + 1, horses[i].get('name')
        reached = _focus_down_to(n, at, known) if at and at[0] == n - 1 else None
        if reached:
            (line, hidden), how = reached, 'Down'
        else:
            how = 'click'
            lines = show_betslip_line(n)
            known.update(betslip_lines_by_number(lines))
            hidden, row = _betslip_offset(lines), betslip_row_of(n, lines)
            arr = np.array(pyautogui.screenshot().convert('RGB'))
            line = dict(known.get(n) or {'price': '', 'name': ''}, n=n, row=row, y=_row_centre(row),
                        guaranteed=_line_guaranteed(arr, left, row))
            if not (line['guaranteed'] or line['price'].upper() in NOT_RUNNING):
                betty_click(left + 60, line['y'])  # focus it (its "1. Meet 1:32" text, far from Remove)
                # Focusing a selection opens its price box again (user, 30 Oct): answered before 'g', which it swallows
                if _price_box_shows(True, PRICE_BOX_FOCUS_SECS):
                    answer_price_box()
        if line['price'].upper() in NOT_RUNNING:
            print(f"[*] Best odds guaranteed: {name} shows {line['price']}: skipped, the next is clicked.")
            at = None
            continue
        at = (n, line['row'], hidden)
        if line['guaranteed']:
            continue
        betty_press('g')
        answered, t0 = False, time.time()
        while time.time() - t0 < 2.0:
            _check_stop()
            arr = np.array(pyautogui.screenshot().convert('RGB'))
            if not answered and _signals_pass(arr, price_box):  # before the purple check: both can show at once
                answer_price_box()
                answered = True
            elif _line_guaranteed(arr, left, line['row']):
                print(f"[+] Best odds guaranteed: {name} ({how}, {time.time() - t0:.2f}s).")
                break
            time.sleep(0.02)
        else:
            answer_entry_popups()  # anything else in the way (e.g. late selection), answered by its label
            if not _line_guaranteed(np.array(pyautogui.screenshot().convert('RGB')), left, line['row']):
                raise WagerForStaff(f"pressed g once on {name} but the guarantee can't be confirmed (not pressed again)")
        # Purple can show before a box opens (9.2446520, 22 Oct: a box left open after 'g' hid the betslip): a box
        # showing now is answered before the next line (one look, not a wait)
        if any(_signals_pass(np.array(pyautogui.screenshot().convert('RGB')), sig) for sig in boxes):
            answer_entry_popups()
    scroll_betslip_to_end()  # back down, as Betty left it (user, 31 Oct)
    print(f"[+] Best odds guaranteed: {len(wanted)} selection(s) in {time.time() - t_all:.1f}s.")


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
        lines = read_whole_betslip()
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


def _f8_row_turns(row: int, selected: bool, timeout: float = NAV_TIMEOUT) -> bool:
    """Colour only: whether the bet list's row shows `selected` (green, or not) within `timeout` seconds (0 = now)."""
    t0 = time.time()
    while True:
        _check_stop()
        if _f8_selected(pyautogui.screenshot())[row] == selected:
            return True
        if time.time() - t0 >= timeout:
            return False
        time.sleep(0.04)


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


# Choose Bet and Stake, from F8 to F10 / F11, is 1.2.0's code again (1.2.8): 1.2.1 took Betty as buffering the keys
# there and dropped the look after each key and the waits, and 9.2459992 (a two-dog reversed forecast) then went Home
# on that screen on every try of 1.2.1-1.2.7; 1.2.0 entered it, and so did the user by hand (31 Oct, 1 Nov). Putting
# back only some of the waits (1.2.3-1.2.5) didn't do it. 1.2.10: a second after the stake and after the bet type
# (F8_AFTER_STAKE_SECS, F8_AFTER_BET_TYPE_SECS). Keep this stretch as it is unless a change is tried live.
# 1.2.12: the cause wasn't the keys or their pace but a tesseract.exe console taking the keyboard from Betty just
# after the bet shortcut (_ask_tesseract_version_hidden). 1.2.14: the 1.2.10 waits out again, 1.2.12 proven live.
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
    print(f"[*] Betty's windows now, top first: {betty_windows_report()}")
    folder = F8_RECORDER.dump(_current_wager)
    if folder:
        print(f"[*] Choose Bet and Stake, 10 frames a second from F8: {folder}")
    return WagerForStaff(f"Betty left Choose Bet and Stake (now on {screen}) {doing}")


def _still_on_f8(doing: str):
    """Before the bet list's colours are blamed: a list read with nothing green was Betty on Home (9.2459992, 31 Oct:
    'selected: []', no keys printed). Raises the 'left' reason when Betty isn't on Choose Bet and Stake."""
    screen = detect_screen()
    if screen == SCREEN_UNKNOWN:  # often Betty mid-redraw: not taken as gone
        screen = wait_for_screen(ALL_SCREENS - {SCREEN_UNKNOWN}, timeout=1.5)
    if screen not in (SCREEN_BET_AND_STAKE, SCREEN_UNKNOWN):
        raise _left_f8(screen, doing)


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
            corpus_save('bet_row', shot, {'canon': canon}, scores.index(max(scores)))
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
            corpus_save('bet_row', shot, {'canon': canon}, None)
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

    x, y, w, _ = F8_BET_LIST_REGION_1368

    def row_centre(r: int) -> tuple[int, int]:
        return x + w // 2, int(y + (r + 0.5) * F8_ROW_HEIGHT_1368)

    def deselect(rows: list, keep: int | None, why: str):
        """Every row chosen on this page but `keep` clicked off, each seen to go off."""
        for j, selected in enumerate(_f8_selected(pyautogui.screenshot())):
            if selected and j != keep:
                print(f"[*] Deselecting '{rows[j][0]}' ({why}).")
                betty_click(*row_centre(j))
                if not _f8_row_turns(j, False):
                    raise WagerForStaff(f"'{rows[j][0]}' stayed chosen in Betty's bet list after a click "
                                        "(not clicked again)")

    if key:
        _f8_key(key)
        time.sleep(0.08)
    for page in range(5):
        i, rows = _find_bet_row(canon)
        if i is not None:
            break
        if not extending:
            # A row chosen here (Singles, from F8) can't be seen or turned off from the next page, and would go on
            # too: only the rows of the page holding the type were checked (1.2.14; no type had been paged to live)
            deselect(rows, None, f"{canon} is on another page")
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

    # A click on a row toggles it, so a row is clicked only once Betty has shown it isn't chosen. Its shortcut chooses
    # it, but Betty can be slow to show that (each way just pressed): the row has NAV_TIMEOUT to turn green first
    # (9.2459384, 31 Oct: Trebles read 0.08 s after 'b' as not chosen, clicked off, Singles off too: nothing chosen)
    if not _f8_row_turns(i, True, NAV_TIMEOUT if key else 0):
        _still_on_f8(f"before clicking '{canon}'")  # the row's place on another screen is something else
        betty_click(*row_centre(i))
        if not _f8_row_turns(i, True):
            raise WagerForStaff(f"clicked {canon} in Betty's bet list but it didn't turn green (not clicked again)")

    # Selecting a row doesn't change the list, so the rows' names are known: from here only the green is read
    if not extending:
        deselect(rows, i, f"only {canon} wanted")
        chosen = [rows[j][0] for j, sel in enumerate(_f8_selected(pyautogui.screenshot())) if sel]
        if chosen != [rows[i][0]]:
            _still_on_f8(f"after choosing '{canon}'")
            raise WagerForStaff(f"could not select only {canon} in Betty's bet list (selected: {chosen})")
    elif not _f8_selected(pyautogui.screenshot())[i]:
        _still_on_f8(f"after choosing '{canon}'")
        raise WagerForStaff(f"could not select {canon} in Betty's bet list for extended bet")


STAKE_BOX_DIGITS = 8  # backspaces clearing the last stake (pence): up to £99,999.99 (5 cleared only £999.99; review R18)
# 1.2.0's waits after the stake and after the bet type again (1.2.14). 1.2.10 made each 1 s, taking Betty's bet edit
# going behind Home as Betty being hurried; it was a tesseract.exe window taking the keyboard (1.2.12), and 1.2.12
# placed a Lucky 15 and a Lucky 31 with the 1 s waits still in (1 Nov). About 1.75 s a bet back.
F8_AFTER_STAKE_SECS = 0.1
F8_AFTER_BET_TYPE_SECS = 0.15


def enter_bet_terms(bet: dict, canon: str, bets_before: int, bet_no: int | None = None):
    """On Choose Bet and Stake: stake, each way / win, bet type. `bet_no` = the bet's place in the wager, for the log.
    Several whole bets of one type ('2 x 10p yankees') go in as one at the stake times that many: Betty takes one bet
    per type, and 1 yankee at 20p is 2 yankees at 10p (it was costed as 2 and entered as 1, so Betty's total fell
    short of the payment)."""
    stake = round(float(bet.get('stake_pence') or 0))
    if stake <= 0:
        raise WagerForStaff("a bet has no stake")
    n_bets = whole_bets(bet)
    if n_bets > 1:
        print(f"[*] {n_bets} x {canon} at {stake}p: entered as 1 {canon} at {stake * n_bets}p.")
        stake *= n_bets
    if bets_before > 0:
        time.sleep(0.15)
        for _ in range(STAKE_BOX_DIGITS):
            betty_press('backspace')
            time.sleep(0.01)
    for ch in str(stake):
        _f8_key(ch)
    _f8_key('enter')
    interruptible_sleep(F8_AFTER_STAKE_SECS)  # the each-way button is drawn after Enter too (review R18)
    arr = np.array(pyautogui.screenshot().convert('RGB'))
    ew_on = _colour_share(arr, F8_EACH_WAY_BOX, F8_ROW_GREEN) >= 0.4
    if bool(bet.get('each_way')) != ew_on:
        _f8_key('e' if bet.get('each_way') else 'w')
    choose_bet_type(canon, extending=bets_before > 0)
    interruptible_sleep(F8_AFTER_BET_TYPE_SECS)  # before F11, F10 or the total read and F12
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


ORDERED_BET_TYPES = ('straight forecast', 'tricast', 'straight forecast double')  # in the finishing order written


def selection_key(h: dict) -> tuple[str, ...]:
    """One selection, as Betty's betslip holds it: meeting, time, number, void, favourite (strings throughout)."""
    return (str(h.get('meeting') or ''), str(h.get('time') or ''), str(h.get('number') or ''),
            'void' if h.get('void') else '', 'fav' if h.get('favourite') else '')


def same_selections(a: dict, b: dict) -> bool:
    """
    Whether bet b can go on bet a's slip with F11: the same selections, and in the same order when either bet is a
    straight forecast or tricast (the slip's order is the finishing order, so 'SF 3-5' then 'SF 5-3' is two slips).
    """
    def key(bet: dict) -> list[tuple[str, ...]]:
        # strings throughout: a void selection or the favourite has no number, and None can't be sorted with ints
        return [selection_key(h) for h in bet.get('horses', [])]
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


def betty_windows_report() -> str:
    """
    Betty's visible full-size windows, top first, for the log: whether the bet edit (an untitled window in front of
    'A-Bet System') is still open when Betty shows Home. One window = the edit closed; two = it went behind. Bets.exe
    itself ran on (one process since the morning) both times Betty went Home on Choose Bet and Stake (user, 31 Oct).
    """
    if os.environ.get("BETTY_HEADLESS") == "1":
        return "not looked at (free test)"
    try:
        import ctypes.wintypes as wt
        user32 = ctypes.windll.user32
        front = user32.GetForegroundWindow()
        found: list[str] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
        def visit(hwnd, _):
            rect = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if user32.IsWindowVisible(hwnd) and rect.right - rect.left > 200 and window_exe(hwnd) == BETTY_EXE:
                title = ctypes.create_unicode_buffer(120)
                user32.GetWindowTextW(hwnd, title, 120)
                found.append(f"'{title.value or 'untitled'}' {rect.right - rect.left}x{rect.bottom - rect.top}"
                             f"{' (has the keyboard)' if hwnd == front else ''}")
            return True

        user32.EnumWindows(visit, 0)
        return "; ".join(found) or "none open"
    except Exception as e:
        return f"could not be listed ({e})"


class ForegroundLog:
    """
    Every window that takes the keyboard, from any program, with the time, for the log when a wager goes to staff.
    betty_windows_report lists only Betty's windows and the F8 recorder looked ten times a second, so neither showed
    the tesseract.exe console that had the keyboard for a moment before Betty went Home (1 Nov). Windows calls in as
    it happens (a WinEvent hook, out of context): looks only, nothing is pressed, clicked or polled.
    """
    SECS = 30  # looked back on a staff reason: the slowest reasons come ~5 s after what caused them

    def __init__(self):
        self._events: deque = deque(maxlen=200)
        self._proc = None  # Windows' callback, kept alive while the hook is
        self._started = False

    def start(self):
        if self._started or os.environ.get("BETTY_HEADLESS") == "1":
            return
        self._started = True
        threading.Thread(target=self._run, name="foreground log", daemon=True).start()

    def _run(self):
        import ctypes.wintypes as wt
        user32 = ctypes.windll.user32
        proc_type = ctypes.WINFUNCTYPE(None, wt.HANDLE, wt.DWORD, wt.HWND, wt.LONG, wt.LONG, wt.DWORD, wt.DWORD)
        user32.SetWinEventHook.restype = wt.HANDLE
        user32.SetWinEventHook.argtypes = [wt.DWORD, wt.DWORD, wt.HMODULE, proc_type, wt.DWORD, wt.DWORD, wt.DWORD]

        def on_foreground(_hook, _event, hwnd, *_):
            try:
                title = ctypes.create_unicode_buffer(120)
                user32.GetWindowTextW(hwnd, title, 120)
                self._events.append((time.time(), window_exe(hwnd), title.value, window_pid(hwnd)))
            except Exception:
                pass

        self._proc = proc_type(on_foreground)
        if not user32.SetWinEventHook(0x0003, 0x0003, None, self._proc, 0, 0, 0):  # EVENT_SYSTEM_FOREGROUND
            print("[-] Windows taking the keyboard won't be in the log (the hook was refused).")
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:  # the hook's calls come through here
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def others(self) -> str:
        """
        Other programs' windows that had the keyboard in the last SECS seconds, oldest first; 'none'. This program's
        own windows (the selection check staff type into) are left out: they take the keyboard on purpose, and
        counted as another program on 9.2462892 (2 Nov), which staff cancelled at the selection check.
        """
        now, own = time.time(), os.getpid()
        seen = [f"{exe or '?'} '{title or 'untitled'}' {now - t:.1f} s ago" for t, exe, title, pid in list(self._events)
                if now - t <= self.SECS and exe != BETTY_EXE and pid != own]
        return "; ".join(seen) or "none"


FOREGROUND_LOG = ForegroundLog()


class F8Recorder:
    """
    Betty's screen and windows ten times a second from F8 until the bet type is chosen, kept in memory and written to
    logs/f8_<wager>_<time>/ only when Betty leaves Choose Bet and Stake. 9.2459992 (31 Oct) went Home there five times
    on 1.2.1-1.2.5 with the same keys 1.2.0 sent and entered it with; one screenshot at the end showed only Home. The
    frames show what Betty did between the bet shortcut and Home (a box, a window behind, which had the keyboard).
    Looks only: nothing is pressed, clicked or moved.
    """
    FRAMES = 80        # 8 s at 0.1 s
    STEP = 0.1
    KEPT = 3           # recordings kept in logs

    def __init__(self):
        self._frames: list[tuple] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        # Off unless asked for (BETTY_F8_RECORD=1): 1.2.0 had nothing else running on Choose Bet and Stake (1.2.8)
        if os.environ.get("BETTY_HEADLESS") == "1" or os.environ.get("BETTY_F8_RECORD") != "1":
            return
        self.stop()
        self._frames, self._stop = [], threading.Event()
        self._thread = threading.Thread(target=self._run, name="f8 recorder", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _run(self):
        from PIL import ImageGrab
        t0 = time.time()
        while not self._stop.is_set():
            try:
                buf = io.BytesIO()
                ImageGrab.grab().convert('RGB').save(buf, 'JPEG', quality=70)
                self._frames.append((time.time() - t0, ','.join(_f8_trail), betty_windows_report(), buf.getvalue()))
                del self._frames[:-self.FRAMES]
            except Exception:
                pass
            self._stop.wait(self.STEP)

    def dump(self, number: str | None) -> str | None:
        """The frames so far, as logs/f8_<wager>_<time>/NN_<secs>s.jpg and index.txt; the folder, or None."""
        self.stop()
        if not self._frames:
            return None
        try:
            log_dir = app_paths.log_dir()
            folder = os.path.join(log_dir, f"f8_{number or 'unknown'}_{time.strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "index.txt"), "w", encoding="utf-8") as idx:
                for n, (t, keys, windows, jpg) in enumerate(self._frames):
                    name = f"{n:02d}_{t:05.2f}s.jpg"
                    with open(os.path.join(folder, name), "wb") as f:
                        f.write(jpg)
                    idx.write(f"{name}  keys so far: {keys}  |  windows: {windows}\n")
            old = sorted((d for d in os.listdir(log_dir) if d.startswith("f8_")),
                         key=lambda d: os.path.getmtime(os.path.join(log_dir, d)))
            for d in old[:-self.KEPT]:
                for f in os.listdir(os.path.join(log_dir, d)):
                    os.remove(os.path.join(log_dir, d, f))
                os.rmdir(os.path.join(log_dir, d))
            return folder
        except Exception as e:
            print(f"[-] Could not save the Choose Bet and Stake recording: {e}")
            return None


F8_RECORDER = F8Recorder()


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


_exe_by_window: dict[tuple, str] = {}  # (window, its process) -> program: asked before every key and click


def _foreground_exe() -> str:
    """The program that has the keyboard, '' when none or it can't be told. Betty's in the free tests."""
    if os.environ.get("BETTY_HEADLESS") == "1":
        return BETTY_EXE
    try:
        front = ctypes.windll.user32.GetForegroundWindow()
        if not front:
            return ""
        key = (front, window_pid(front))
        if key not in _exe_by_window:
            if len(_exe_by_window) > 64:
                _exe_by_window.clear()
            _exe_by_window[key] = window_exe(front)
        return _exe_by_window[key]
    except Exception:
        return ""


def _front_is_launcher() -> bool:
    try:
        front = ctypes.windll.user32.GetForegroundWindow()
        return bool(front) and window_pid(front) == os.getppid()
    except Exception:
        return False


def _someone_at_till() -> bool:
    """A key, click or mouse movement within BETTY_TAKE_FRONT_SECS: the till isn't the program's to take over."""
    return time.time() - _last_staff_activity < BETTY_TAKE_FRONT_SECS


def _require_betty():
    """
    Before every key and click (user, 6 Nov: Esc went to whatever was on top, 12:24 that day). With nobody at the till a
    stray window gives way; Betty gets a moment, as there's no window in front while hers change. Otherwise nothing is
    pressed and the watcher pauses as it does for staff, the wager in hand to be tried again.
    """
    global _watcher_stop_reason, _paused_for_staff
    if _foreground_exe() == BETTY_EXE:
        return
    if time.time() - _last_staff_activity >= BETTY_REQUIRE_QUIET_SECS:
        focus_betty()
    t0 = time.time()
    while time.time() - t0 < BETTY_REQUIRE_WAIT_SECS:
        if _foreground_exe() == BETTY_EXE:
            return
        time.sleep(0.02)
    with _watcher_state_lock:
        watcher_on.clear()
        _paused_for_staff = True
        _watcher_stop_reason = "staff"
        abort_event.set()
    print(f"[*] Betty hasn't got the keyboard ({_foreground_exe() or 'nothing'} has): nothing pressed, watcher paused.")
    raise WatcherStop()


def betty_in_front() -> bool:
    """
    Betty's program has the keyboard, so the watcher's keys reach Betty and nothing else. With someone at the till, or
    just having used it, whatever they have in front stays in front, the launcher included (user, 6 Nov: this took Betty
    back every 5 seconds). Otherwise, or just after the watcher was switched on by hand, the launcher steps aside and any
    other window gives way through focus_betty. False: the watcher waits and presses nothing.
    """
    if _foreground_exe() == BETTY_EXE:
        return True
    if _someone_at_till() and not _switched_on_by_hand:
        return False
    try:
        if _front_is_launcher():
            backend_event("step_aside")
            time.sleep(0.6)  # the launcher minimises; Windows usually hands the keyboard to Betty behind it
        focus_betty()
        return _foreground_exe() == BETTY_EXE
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
    _typed_prices.clear()
    bets_on_slip = 0
    entered: list[tuple] = []  # selections entered on this wager's earlier slips, in order (the previous-selections panel)
    # Clicking a Master Index row on the previous-selections panel crashes Betty: with one on the wager, it isn't used
    index_used = any(h.get('sport') for bet, _ in plan for h in bet.get('horses', []))
    index_forget()
    for idx, (bet, canon) in enumerate(plan):
        assert canon is not None
        if not (idx and same_selections(bet, plan[idx - 1][0])):
            horses = bet.get('horses', [])
            for k, horse in enumerate(horses):
                after_race = k > 0 and same_race(horse, horses[k - 1])
                key = selection_key(horse)
                enter_selection(horse, k, after_same_race=after_race,
                                after_same_time=k > 0 and not after_race and same_race_time(horse, horses[k - 1]),
                                entered_before=key in entered and not index_used,
                                entered_order=(entered.index(key), len(entered)) if key in entered else None,
                                **({'next_horse': horses[k + 1] if k + 1 < len(horses) else None}
                                   if horse.get('sport') else {}))
            entered += [selection_key(h) for h in horses if selection_key(h) not in entered]
            apply_guarantees(bet.get('horses', []), struck_clock)
            # No whole-betslip re-read here (user, 26 Oct): every line was read back as it was entered and every
            # guarantee confirmed by its colour; the re-read failed on good slips (9.2452710). Payment is checked at F12.
            answer_entry_popups()
            bets_on_slip = 0
            _f8_trail[:] = ['f8']
            F8_RECORDER.start()
            if index_used and detect_screen() == SCREEN_MASTER_INDEX:  # the index takes no shortcuts (user): its button
                betty_click(*INDEX_CHOOSE_BET_SPOT)
            else:
                betty_press('f8')
            answer_price_box_after_f8()
        expect_screen({SCREEN_BET_AND_STAKE}, doing="Choose Bet and Stake (F8)")
        refresh_watcher_hud(f"Bet {idx + 1}/{len(plan)}: {canon}, {bet.get('stake_pence')}p"
                            f"{' each way' if bet.get('each_way') else ''}...")
        try:
            enter_bet_terms(bet, canon, bets_on_slip, bet_no=idx + 1)
        finally:
            F8_RECORDER.stop()
        bets_on_slip += 1
        if idx < len(plan) - 1:
            if same_selections(plan[idx + 1][0], bet):
                _f8_trail.clear()
                F8_RECORDER.start()
                _f8_key('f11')  # extend: same selections, next bet type
                time.sleep(0.2)
            else:
                betty_press('f10')  # new betting slip
                expect_screen({SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY}, doing="new betting slip (F10)")
    if not test_mode_on.is_set():
        # Live: F12 next (commit_wager), with nothing read first. Betty checks its total against the Payment itself at
        # F12, and its question goes to staff (user, 1 Nov: ~1.5 s of reads before every F12, for the same check)
        print("[+] Entered: Betty checks its total against the Payment at F12.")
        return
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
    # Choose Bet and Stake told by its colours (~30 ms), then F12 at once. The screen's label and the total were read
    # here (~0.6 s, and the total once before in enter_wager): Betty checks the total against the Payment itself, and
    # its question after F12 goes to staff below (user, 1 Nov)
    t0 = time.time()
    while not _signals_pass(np.array(pyautogui.screenshot().convert('RGB')),
                            SCREEN_SIGNATURES[SCREEN_BET_AND_STAKE]['colours']):
        if time.time() - t0 > 1.0:
            raise NavError(f"not on Choose Bet and Stake to place wager {number} (Betty shows {detect_screen()})")
        time.sleep(0.05)
    refresh_watcher_hud(f"Placing wager {number} (F12)...")
    print(f"[*] Placing wager {number}: F12.")
    _placing = True
    try:
        betty_press('f12')
    finally:
        _placing = False
    try:
        screen = expect_screen({SCREEN_VIEW_WAGERS, SCREEN_HOME, MODAL_PAYMENT_MISMATCH, MODAL_CONFIRM_STAKE},
                               timeout=8.0, doing="Place Bet (F12)")
    except NavError as e:  # F12 has gone: never entered again, nor called unplaced (9.2468158, 6 Nov: placed 15 s later)
        raise WagerForStaff(f"F12 was pressed on wager {number} but Betty didn't move on: it may be placed, "
                            "please check it on Betty before entering it") from e
    if screen in (MODAL_PAYMENT_MISMATCH, MODAL_CONFIRM_STAKE):
        raise WagerForStaff("Betty questioned the payment after F12 (nothing answered)")
    if screen == SCREEN_HOME:
        open_view_wagers()
    t0 = time.time()
    while time.time() - t0 < NAV_TIMEOUT:
        if wager_gone_from_list(number):
            print(f"[+] Wager {number} placed: it has left the unedited list.")
            corpus_outcome(number, "placed")
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
WATCHER_POLL_SECS = app_paths.setting("WATCHER_POLL_SECS", 5.0)       # queue empty: look again this often, sitting on View Wagers
WATCHER_UNKNOWN_LIMIT = 3     # back-out attempts that fail in a row before the watcher stops and alerts staff
_wager_lessons: set[str] = set()  # lessons used on the current wager: counted placed / to staff when it ends
_last_reading: dict | None = None  # the current wager's slip as read: its lines and picture (Teach from this slip)


def _lesson_used(lesson: dict):
    """A taught lesson used on this wager: counted now, and its wager's outcome counted when it ends."""
    _wager_lessons.add(lesson['id'])
    try:
        lessons.mark_used([lesson['id']])
    except Exception as e:  # lessons.json busy or unwritable: the wager goes on, the count is lost
        print(f"[-] Could not count lesson {lesson['id']}: {e}")


LESSON_SYNC_SECS = app_paths.setting("LESSON_SYNC_SECS", 60)  # how often lessons are shared with the shop's other tills through the relay
_lesson_sync_now = threading.Event()  # set when something is taught: shared at once, not at the next round


def lesson_sync_loop():
    """
    Background: this till's lessons and its shop's kept the same through the relay (lessons.sync), every
    LESSON_SYNC_SECS and straight after a lesson is taught. What the shop shares is said once when it changes.
    """
    said = None
    while True:
        state = lessons.sync()
        news = (state.get('shared'), state.get('shop'), state.get('error'))
        if news != said:
            said = news
            if state.get('error'):
                print(f"[-] Lessons not shared: {state['error']}. The ones on this till still work.")
            elif state.get('shared'):
                print(f"[*] Lessons: shared with shop '{state['shop']}' on the relay." if state.get('shop') else
                      "[*] Lessons: kept on the relay for this till (it's in no shop on /admin).")
        _lesson_sync_now.wait(LESSON_SYNC_SECS)
        _lesson_sync_now.clear()


def _lessons_outcome(placed: bool):
    """The current wager ended: its lessons counted as placed or to staff (a lesson that keeps sending wagers to staff
    is turned off: said here)."""
    ids = set(_wager_lessons)
    _wager_lessons.clear()
    try:
        for x in lessons.record_outcome(ids, placed):
            print(f"[!] Lesson turned off: '{x['written']}' = {x['means']} ({x['staff']} wagers to staff, none placed).")
    except Exception as e:
        print(f"[-] Could not count the wager's lessons: {e}")


_wagers_left_for_staff: set[str] = set()  # this session: wagers placed, or stopped by Esc or a failure; not opened again (a pause is retried)
_current_wager: str | None = None
_nav_failures: dict[str, int] = {}  # wager -> navigation problems this session (left for staff after 2)
_first_nav_failure: tuple[str, Any] | None = None  # (wager, screen) of the latest first navigation problem, kept for its staff screenshot
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


OPEN_ELSEWHERE_RETRY_SECS = app_paths.setting("OPEN_ELSEWHERE_RETRY_SECS", 30)
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


class RaceHalfADayOld(WagerForStaff):
    """Betty's late-selection box said about 720 minutes: typing 16:40 also brings up the 04:40 at a virtual meeting. No was
    pressed; enter_selection tries the rest of the list (user, 6 Nov), and anywhere else it goes to staff."""


def alert_staff(message: str):
    """HUD message with a sound: something needs a person."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass
    notify(message, is_error=True, title=f"{APP_NAME} - Staff needed")


def sports_on() -> bool:
    """The Sports switch in the control window (System, Settings), read when asked: the switch changes it while running."""
    return bool(app_paths.setting("SPORTS_ON", app_paths.setting("RAB_SPORTS", 0)))


def sports_selection(horse: dict, slip_words: str, struck_at: float, records: list[dict], runners: list[dict]) -> dict | None:
    """
    A handwritten selection as a football match bet: a team in the table ('SPURS'), with no time, meeting or number written
    and no runner of that name today. Found in Betty's feed files, so it's typed into the Master Index as the till names it
    (Tottenham, never Spurs). None when it isn't one.
    """
    name = str(horse.get('name') or '').strip()
    if (not name or selection_number(horse) is not None or horse.get('raw_meeting_hint') or horse.get('meeting')
            or any(parse_race_time_to_minutes(str(horse.get(k) or ''))[0] is not None for k in ('raw_time', 'written_time', 'time'))):
        return None
    if any(clean_horse_name(r['name']) == clean_horse_name(name) for r in runners):
        return None  # a horse of that name is running today: the name, not the table, decides
    team = sports_names.team_for(name, slip_words)
    if not team:
        return None
    sel = sports_names.match_bet(team, records, struck_at, horse.get('price'))
    if not sel:
        raise WagerForStaff(f"'{name}' is {team['name']}, but Betty has no match of theirs to bet on")
    return sel


COMBINATION_FORECAST_MIN = 3  # on 2 Betty takes it as a reversed forecast, so it goes in and the money can still add up (9.2468449)


def bet_shape_fault(slip: list[dict]) -> str | None:
    """A bet that can't be what was read, whatever the money says: for staff rather than entered (user, 6 Nov)."""
    for bet in slip:
        if normalize_bet_type(str(bet.get('bet_type', ''))) == 'combination forecast':
            runners = len({selection_key(h) if h.get('time') else str(h.get('name')) for h in bet.get('horses', [])})
            if runners < COMBINATION_FORECAST_MIN:
                return (f"a combination forecast needs at least {COMBINATION_FORECAST_MIN} selections, and only {runners} were read "
                        f"for '{bet.get('description')}'")
    return None


def lock_sports_wager(scan: dict, details: dict) -> list[dict] | None:
    """
    A slip of football match bets, with the Sports switch on: each selection told from the team table and Betty's files,
    as a Request A Bet's are, ready for the Master Index. None when it holds no team. Only a plain match bet is entered:
    other markets, and a slip mixing racing with football, go to staff for now.
    """
    if not sports_on():
        return None
    reading = _last_reading or {}
    slip_words = " ".join(str(t) for t in reading.get('lines') or [])
    struck_at = calendar.timegm(time.strptime(f"{time.strftime('%Y-%m-%d')} {details['struck_time'][:5]}", "%Y-%m-%d %H:%M"))
    records, runners = sports_card.records(), racecard_manager.get_runners()
    locked: dict[int, dict] = {}
    for bet in scan['slip_data']:
        for horse in bet.get('horses', []):
            sel = sports_selection(horse, slip_words, struck_at, records, runners)
            if sel:
                locked[id(horse)] = sel
    total = sum(len(b.get('horses', [])) for b in scan['slip_data'])
    if not locked:
        return None
    if len(locked) != total:
        raise WagerForStaff("a slip mixing football with racing: the program enters all-football slips only, for now")
    other = sports_names.other_market_words(slip_words)
    if other:
        raise WagerForStaff(f"a football bet with '{other}' written: the program enters plain match bets only, for now")
    for bet in scan['slip_data']:
        bet['horses'] = [dict(sel := locked[id(h)], sport=True, written=h.get('name'), name=sel['text'], meeting=sel['event'],
                              time=sel['market'], number=sel['result'], category='sport', void=False, favourite=False,
                              price=h.get('price'), no_bog=True) for h in bet['horses']]
        for h in bet['horses']:
            print(f"[+] Football: '{h['written']}' @ {h['price'] or 'no price'} = {h['event']} | {h['market']} | {h['result']} "
                  f"(Betty's price {h.get('file_price') or 'none'}).")
    return scan['slip_data']


def lock_wager(number: str, details: dict) -> list[dict]:
    """
    On the race-entry screen: read the slip (reconciled to the Payment taken), then check every selection against
    Betty's card with the struck time, staff prompts included. Returns the locked bets, or raises WagerForStaff.
    """
    pay = details['payment_pence']
    if not racecard_manager.get_runners():
        raise WagerForStaff("Betty's racecard feed can't be read, so no selection can be checked")
    screen = detect_screen()
    if screen not in (SCREEN_RACE_ENTRY_READY, SCREEN_RACE_ENTRY, *SCREENS_NOT_SURE):  # scanned in the bet edit only
        raise NavError(f"not at the race-entry time box before scanning (Betty shows {screen})")
    print(f"[*] Scanning wager {number} at the race-entry time box.")
    api_key = GEMINI_API_KEY or "reader-chain"
    refresh_watcher_hud(f"Wager {number}: reading slip (paid £{pay / 100:.2f})...")
    scan = scan_and_reconcile(api_key, payment_pence=pay, struck_time=details['struck_time'])
    _check_stop()
    if not scan['ok']:
        raise WagerForStaff(scan['reason'] or "the slip could not be read")
    fault = bet_shape_fault(scan['slip_data'])
    if fault:
        raise WagerForStaff(fault)
    football = lock_sports_wager(scan, details)
    if football:
        final = sum(calculate_bet_cost_pence(b) for b in football)
        if final != pay:
            raise WagerForStaff(f"the football bets cost £{final / 100:.2f} but £{pay / 100:.2f} was paid")
        return football
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
    fault = bet_shape_fault(slip)
    if fault:
        raise WagerForStaff(fault)
    return slip


def watcher_process_wager(row: int, number: str):
    """
    One wager: load it, read its number / struck time / Payment, open race entry, lock it (scan, money, selection
    check), enter it into Betty with every step read back, then place it (F12) - or, in test mode, stop before F12
    for staff to place or cancel it.
    """
    global _current_wager, _wager_opened, _last_reading
    _current_wager, _wager_opened, _last_reading = number, False, None
    _wager_lessons.clear()
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
    try:
        open_wager_slip(number)
    except WagerOpenElsewhere:
        _current_wager, _wager_opened = None, False  # not ours to touch: no clean-up, no staff alert
        raise
    slip = lock_wager(number, details)
    n_sel = len({(h.get('name'), h.get('time')) for b in slip for h in b.get('horses', [])})
    summary = f"{number}: {n_sel} selection(s), {len(slip)} bet(s), £{pay / 100:.2f}"
    print(f"[+] {summary} locked. Entering into Betty...")
    enter_wager(slip, pay, details['struck_clock'])
    if test_mode_on.is_set():  # test mode: never placed by the program
        outcome = wait_for_staff_review(number)
        print(f"[+] Wager {number}: {outcome} by staff.")
        corpus_outcome(number, "entered (test mode)", outcome)
        STATUS_HUD.set_outcome(f"{summary} entered, {outcome} by staff {time.strftime('%H:%M')}")
    else:
        commit_wager(number, pay)
        STATUS_HUD.set_outcome(f"{summary} PLACED {time.strftime('%H:%M')}")
        _lessons_outcome(placed=True)
    _wagers_left_for_staff.add(number)
    forget_read(number)
    _current_wager = None


_removal_reported = False  # an old picture couldn't be removed: said once a session (the cashier till listed 30+ each)


def _mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _file_flags(path: str) -> str:
    """The Windows attributes that can stop a file being removed, for the log."""
    try:
        attrs = os.stat(path).st_file_attributes
    except (OSError, AttributeError):
        return "attributes unread"
    flags = [name for name, bit in (("read-only", stat.FILE_ATTRIBUTE_READONLY), ("hidden", stat.FILE_ATTRIBUTE_HIDDEN),
                                    ("system", stat.FILE_ATTRIBUTE_SYSTEM)) if attrs & bit]
    return ", ".join(flags) or "not read-only"


def remove_oldest(paths: list[str], keep: int):
    """
    Removes all but the newest `keep` of `paths`, each on its own: one that can't be removed is skipped (reported once)
    instead of stopping the rest, and a read-only one is made writable first. Never raises. On the cashier till one old
    picture couldn't be removed from 2 Nov 15:59; the removal shared the save's `try`, so every staff screen after it
    was reported unsaved, left out of the staff journal, and nothing older was tidied.
    """
    global _removal_reported
    paths = sorted(paths, key=_mtime)
    for path in paths[:max(0, len(paths) - keep)]:
        try:
            try:
                os.remove(path)
            except PermissionError:
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as e:
            if not _removal_reported:
                _removal_reported = True
                print(f"[-] Could not remove the old picture {os.path.basename(path)} ({_file_flags(path)}): {e}. "
                      "It and any others like it are skipped (said once a session); the saves aren't affected.")


STAFF_SCREENSHOTS_KEPT = app_paths.setting("STAFF_SCREENSHOTS_KEPT", 20)  # newest kept in logs/ (no image folder of their own)
STAFF_JOURNAL = "staff_journal.jsonl"  # logs/: every wager left for staff and every selection staff typed
STAFF_JOURNAL_DAYS = app_paths.setting("STAFF_JOURNAL_DAYS", 30)
SLIP_IMAGES_KEPT = app_paths.setting("SLIP_IMAGES_KEPT", 200)  # logs/slip_*.png: the slip as read, for each selection staff had to type (training)


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
    prune_saved_reads()
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
    remove_oldest(glob.glob(os.path.join(log_dir, "slip_*.png")), SLIP_IMAGES_KEPT)


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


def screen_now() -> Any:
    """Betty's screen now, or None when it can't be taken: for keeping the screen a fault happened on before backing
    out of it."""
    try:
        return pyautogui.screenshot()
    except Exception as e:
        print(f"[-] Could not take the screen: {e}")
        return None


def save_staff_screenshot(number: str, screen: Any = None, earlier: Any = None) -> str | None:
    """Betty's screen at the moment a wager goes to staff, before anything is backed out: logs/staff_<wager>_<time>.png,
    so a failure can be seen afterwards rather than guessed. `screen`: the one taken when it went wrong, when Betty
    has been backed out of since (else the screen now); `earlier`: the one from a failed first try, saved beside it as
    ..._first.png. Only the newest STAFF_SCREENSHOTS_KEPT are kept. Returns the file saved (None when it couldn't be)."""
    if screen is None and _foreground_exe() != BETTY_EXE:
        print("[*] No staff screen saved: Betty isn't in front, and another program's window would go up to the relay.")
        return None
    try:
        log_dir = app_paths.log_dir()  # next to the exe when packaged
        os.makedirs(log_dir, exist_ok=True)
        stem = os.path.join(log_dir, f"staff_{number}_{time.strftime('%Y%m%d_%H%M%S')}")
        path = stem + ".png"
        (screen if screen is not None else pyautogui.screenshot()).save(path)
        print(f"[*] Screen saved for staff: {path}")
        if earlier is not None:
            earlier.save(stem + "_first.png")
            print(f"[*] The first try's screen saved beside it: {stem}_first.png")
    except Exception as e:
        print(f"[-] Could not save the staff screenshot: {e}")
        return None
    remove_oldest(glob.glob(os.path.join(log_dir, "staff_*.png")), STAFF_SCREENSHOTS_KEPT)
    return path


# --- Live capture for the tests: each decision the program takes from Betty's screen (the race on top of the runner
# list, the betslip line after a selection, the bet list's row, a wager's View Wagers details), with the screen it was
# taken from, kept in logs\corpus. scratch/test_live_corpus.py runs today's code on every one and says where it would
# now decide differently, judged by how the wager ended (placed = the decision was right). The offline tests stood in
# for Betty and only had the screens already seen: they passed while the tills failed (user, 1 Nov). Looks only;
# written by a thread of its own, so nothing on the till waits for it. BETTY_CORPUS=0 turns it off.
CORPUS_KEPT = app_paths.setting("CORPUS_KEPT", 1500)             # pictures kept (~90 KB each)
_corpus_queue: queue.Queue = queue.Queue(maxsize=30)  # a full screen each: ~3 MB in memory until written
_corpus_writer_started = False
_corpus_lock = threading.Lock()


def corpus_dir() -> str:
    return os.path.join(app_paths.log_dir(), "corpus")


def corpus_on() -> bool:
    return os.environ.get("BETTY_HEADLESS") != "1" and os.environ.get("BETTY_CORPUS") != "0"


def corpus_save(kind: str, img: Any, inputs: dict, output: Any):
    """One decision for the tests (see above). Never raises, never waits: a full queue drops it."""
    if img is None or not corpus_on():
        return
    _corpus_put({'kind': kind, 'img': img, 'inputs': inputs, 'output': output})


def corpus_outcome(number: str | None, outcome: str, reason: str = ""):
    """How a wager ended (placed / entered in test mode / staff), which says whether its decisions were right."""
    if number and corpus_on():
        _corpus_put({'kind': 'outcome', 'img': None, 'inputs': {}, 'output': {'outcome': outcome, 'reason': reason},
                     'wager': number})


def _corpus_put(item: dict):
    global _corpus_writer_started
    try:
        item.setdefault('wager', _current_wager)
        item.update(version=__version__, time=time.strftime('%Y-%m-%d %H:%M:%S'))
        with _corpus_lock:
            if not _corpus_writer_started:
                threading.Thread(target=_corpus_writer, name="corpus", daemon=True).start()
                _corpus_writer_started = True
        _corpus_queue.put_nowait(item)
    except Exception:  # queue full, or anything else: the till never waits for the tests
        pass


def _corpus_writer():
    written = 0
    while True:
        item = _corpus_queue.get()
        try:
            folder = os.path.join(corpus_dir(), item['time'][:10].replace('-', ''))
            os.makedirs(folder, exist_ok=True)
            img = item.pop('img')
            if img is not None:
                name = f"{item['time'][11:].replace(':', '')}_{int(time.time() * 1000) % 1000:03d}_{item['kind']}_{item['wager'] or 'none'}.png"
                img.save(os.path.join(folder, name))
                item['file'] = os.path.relpath(os.path.join(folder, name), corpus_dir())
            with open(os.path.join(corpus_dir(), "index.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(item, default=str) + "\n")
            written += 1
            if written % 100 == 0:
                remove_oldest(glob.glob(os.path.join(corpus_dir(), "*", "*.png")), CORPUS_KEPT)
        except Exception:
            pass


def leave_wager_for_staff(number: str, reason: str, screen: Any = None, earlier: Any = None):
    """
    A wager the program can't do. Test mode: back out and leave it unedited (staff are watching). Otherwise:
    Mark bet fao Manager, which moves it out of the unedited list. Either way: one sentence on the HUD, with a sound.
    `screen` / `earlier`: the screens it went wrong on, when Betty has been backed out of since (see
    save_staff_screenshot).
    """
    _wagers_left_for_staff.add(number)
    print(f"[!] Wager {number} needs staff: {reason}")
    if os.environ.get("BETTY_HEADLESS") != "1":
        print(f"[*] Other programs' windows with the keyboard in the last {ForegroundLog.SECS} s: "
              f"{FOREGROUND_LOG.others()}")
    forget_read(number)
    corpus_outcome(number, "staff", reason)
    shot = save_staff_screenshot(number, screen, earlier)
    _lessons_outcome(placed=False)
    # The slip as read, for 'Teach from this slip' on the Staff entries tab (only when it was this wager's)
    reading = _last_reading if _last_reading and _last_reading.get('wager') == number else None
    journal_staff("staff", wager=number, reason=reason, screenshot=shot, test_mode=test_mode_on.is_set(),
                  reading=reading['lines'] if reading else None,
                  slip_image=save_slip_image(reading['img_str'], number) if reading else None)
    if test_mode_on.is_set():
        go_home()
        alert_staff(f"Wager {number} needs staff: {reason}. (Test mode: left unedited.)")
        STATUS_HUD.set_outcome(f"{number} -> staff: {reason} {time.strftime('%H:%M')}")
        return
    try:
        fao = mark_wager_fao(number)
    except NavError as e:
        print(f"[-] FAO: wager {number}: {e}")
        fao = ''
    if not fao:
        _fao_owed[number] = FAO_RETRIES
    if fao == 'marked':
        alert_staff(f"Wager {number} sent to the manager (FAO): {reason}.")
    elif fao == 'already':
        alert_staff(f"Wager {number} needs staff: {reason}. (Already on the FAO list.)")
    else:
        alert_staff(f"Wager {number} needs staff: {reason}. Could NOT mark it FAO - please check Betty.")
    STATUS_HUD.set_outcome(f"{number} -> staff: {reason} {time.strftime('%H:%M')}")


FAO_RETRIES = 3
_fao_owed: dict[str, int] = {}  # wagers left for staff that couldn't be marked FAO -> tries left (9.2468533, 6 Nov: never marked)


def retry_owed_fao(queue: list[str]) -> bool:
    """Betty is on View Wagers again: marks FAO a wager that couldn't be when it was left for staff. True when one was tried,
    as Betty has moved. A wager gone from the list has been taken by staff."""
    for number in list(_fao_owed):
        if number not in queue:
            del _fao_owed[number]
            continue
        _fao_owed[number] -= 1
        try:
            fao = mark_wager_fao(number)
        except NavError as e:
            print(f"[-] FAO: wager {number}: {e}")
            fao = ''
        if fao or not _fao_owed[number]:
            del _fao_owed[number]
            alert_staff(f"Wager {number} needs staff: sent to the manager (FAO)." if fao else
                        f"Wager {number} needs staff. Could NOT mark it FAO after {FAO_RETRIES} more tries - please check Betty.")
        return True
    return False


_betty_hidden_reported = False  # "Betty isn't in front" printed once until she is again
_left_screen_reported = False   # "left by staff" printed once until she's back on Home


_queue_seen: dict[str, float] = {}  # wagers waiting now -> when the watcher first saw each
_queue_said = ""


def report_queue(numbers: list[str]):
    """How many wagers are waiting and how long the oldest has been, for the control window."""
    global _queue_seen, _queue_said
    now = time.time()
    _queue_seen = {n: _queue_seen.get(n, now) for n in numbers}
    text = "None waiting"
    if numbers:
        oldest = min(_queue_seen.values())
        text = f"{len(numbers)} waiting, the oldest seen {time.strftime('%H:%M', time.localtime(oldest))}"
    if text != _queue_said:
        _queue_said = text
        backend_event("queue", text=text)


def watcher_cycle():
    """One look: get to View Wagers, take the top wager not yet handled, or wait for the next poll."""
    global _betty_hidden_reported, _home_lost_said, _switched_on_by_hand, _left_screen_reported
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
    if screen not in (SCREEN_HOME, SCREEN_VIEW_WAGERS) and _someone_at_till() and not _switched_on_by_hand:
        # Back on by itself with someone just gone from the till: what they left showing stays until the till is quiet
        if not _left_screen_reported:
            print(f"[*] Betty is on {screen}, left by staff: nothing pressed until the till has been quiet "
                  f"{BETTY_TAKE_FRONT_SECS:.0f}s (or press `).")
            _left_screen_reported = True
        refresh_watcher_hud(f"Betty is on {screen}: left alone until the till is quiet (or press `).")
        t0 = time.time()
        while time.time() - t0 < WATCHER_POLL_SECS:
            _check_stop()
            time.sleep(0.1)
        return
    _left_screen_reported = False
    if screen not in (SCREEN_HOME, SCREEN_VIEW_WAGERS):
        print(f"[*] Watcher found Betty on {screen}: backing out to Home first.")
        if not go_home():
            raise HomeUnreachable(f"could not get back to Home from {screen}")
    _home_lost_said = _switched_on_by_hand = False
    open_view_wagers()
    queue = read_unedited_queue(pyautogui.screenshot())
    if retry_owed_fao(queue):
        return
    now = time.time()
    todo = [(i, n) for i, n in enumerate(queue)
            if n not in _wagers_left_for_staff and _open_elsewhere_until.get(n, 0) <= now]
    report_queue([n for _, n in todo])
    if todo:
        print(f"[*] Unedited list: {queue} (done or left for staff this session, not opened again: {sorted(_wagers_left_for_staff) or 'none'})")
    for row, number in todo:
        try:
            watcher_process_wager(row, number)
            return
        except WagerOpenElsewhere as e:  # another till has it: leave it alone, next wager on the ladder
            _open_elsewhere_until[number] = time.time() + OPEN_ELSEWHERE_RETRY_SECS
            print(f"[*] Wager {number}: {e}. Moving on to the next wager; will look again in {OPEN_ELSEWHERE_RETRY_SECS}s.")
            STATUS_HUD.set_outcome(f"{number}: {e} - skipped for now {time.strftime('%H:%M')}")
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


_home_lost_said = False  # staff have been told Betty can't be got back to Home; cleared once she is


def home_lost(reason: str):
    """Home can't be reached (user, 6 Nov: the watcher never stops for this): staff told once, tried again in a minute."""
    global _home_lost_said
    print(f"[-] Watcher: {reason}. Trying again in {HOME_RETRY_SECS:.0f}s.")
    STATUS_HUD.set_outcome(f"problem: {reason}")
    if not _home_lost_said:
        _home_lost_said = True
        notify(f"{reason.capitalize()}. The program keeps trying; please check Betty.", is_error=True)
    interruptible_sleep(HOME_RETRY_SECS)


def watcher_loop():
    """While the watcher is on: work through unedited wagers (see watcher_cycle), recovering to Home on any trouble."""
    global watcher_busy, _watcher_stop_reason, _watcher_screen, _current_wager, _first_nav_failure
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
                    home_lost("could not get Betty back to Home")
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
                home_lost("could not get Betty back to Home")
        except HomeUnreachable as e:
            home_lost(str(e))
        except NavError as e:
            # The screen it went wrong on, before backing out: the staff screenshot was taken after the Esc presses,
            # so it showed Home (9.2462614 and five more, cashier till, 2 Nov)
            fault_screen = screen_now() if _current_wager else None
            if _current_wager:  # a navigation glitch is not the wager's fault: one more go before leaving it
                _nav_failures[_current_wager] = _nav_failures.get(_current_wager, 0) + 1
                if _nav_failures[_current_wager] < 2:
                    _first_nav_failure = (_current_wager, fault_screen)
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
                first = _first_nav_failure[1] if _first_nav_failure and _first_nav_failure[0] == number else None
                _first_nav_failure = None
                try:
                    leave_wager_for_staff(number, f"Betty's screens went wrong twice while entering it ({e})",
                                          screen=fault_screen, earlier=first)
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


# --- 6e. THE MASTER INDEX: SPORTS SELECTIONS ---
def _ocr_text_on(img: Any, box: tuple, background: tuple | None = None, scale: int = 2,
                 config: str = '--psm 6') -> str:
    """Text of any colour on a plain panel: every pixel far from the panel's colour black, the rest white. The panel's
    colour is `background`, else the commonest colour in the box."""
    x, y, w, h = box
    arr = np.array(img.convert('RGB').crop((x, y, x + w, y + h))).astype(int)
    if background is None:
        colours, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
        background = tuple(colours[counts.argmax()])
    far = np.max(np.abs(arr - np.array(background)), axis=2) > 60
    crop = Image.fromarray(np.where(far, 0, 255).astype('uint8')).resize((w * scale, h * scale))
    try:
        return pytesseract.image_to_string(crop, config=config).strip()
    except Exception as e:
        print(f"[-] OCR failed: {e}")
        return ""


# Betty's search across every folder, and how sports are entered (user, 5 Nov; scratch/betty_screens/mi_*). It's the
# quickest way and the most finicky: a search can show nothing, "No selections found" for what exists, or one record
# over and over (mi_5), so nothing on it is believed until it reads right, and every list is read again until it does.
# Where the peach Master Index button is: a folder's screen (mi_1, mi_12); the picture menu a callover opens on
INDEX_BUTTON_ZONES = ((20, 620, 70, 70), (5, 125, 65, 65))
INDEX_BUTTON_PEACH = (255, 196, 136)
INDEX_BOX = (16, 63, 296, 18)             # inside the search box's border: read as a letter, it took 'bournemo' for 'lbournemo'
INDEX_CARET_MAX_PX = 25                   # dark pixels of the box's caret alone: a letter adds more
INDEX_BOX_SPOT = (300, 71)                # clicked past the text, so the caret is at its end. Left of the letter
#                                           buttons, so Esc stays harmless; works while Betty loads back, too (user)
INDEX_ESC_SPOT = (700, 560)               # the slip's grey foot: clicked before Esc to back out. Not the beige: Remove is there
INDEX_FOLDER_SPOT = (155, 660)            # the first folder button: leaves the index for that folder
INDEX_CHOOSE_BET_SPOT = (582, 690)        # Choose Bet and Stake
INDEX_NONE_BOX = (55, 192, 280, 28)       # "No selections found in search"
INDEX_GRID_TOP = (170, 200)               # where the red line above the rows is (183 on mi_4-6)
INDEX_GRID_BOX = (0, 170, 440, 450)       # the list and its arrow: two pictures the same = Betty has stopped drawing
INDEX_ROW_PITCH = 35                      # 12 rows to a page, each with its border (the reuse panel's grid)
INDEX_ROWS_MAX = 12
INDEX_PRICE_SPOT_X = 355                  # a row is clicked on its price: its name would take SP
INDEX_MORE_ZONE = (405, 560, 30, 40)      # the red arrow: the next 12 rows (user)
INDEX_MORE_SPOT = (417, 579)
INDEX_ROW_COLOURS = {'cyan': [(0, 255, 255), (128, 255, 255)], 'green': (0, 255, 64), 'white': (255, 255, 255)}
INDEX_FILTERS = {  # a filter's button, what it should say, and what it says when left on another way (kept until Betty closes)
    'time': ((405, 90, 76, 23), "anytime", "today"), 'live': ((405, 122, 76, 23), "preevent", "inplay"),
    'kind': ((317, 154, 76, 23), "standard", "bdcms")}
INDEX_ICONS = [(x, y) for y in (105, 155) for x in (25, 88, 152, 216, 280)]  # sport filters; on: a pale blue aura (mi_10)
INDEX_ICON_HALF = (30, 24)
INDEX_AURA_MIN_PX = 150                   # an aura's pixels round an icon; none of them has that many of itself
INDEX_OPEN_SECS = app_paths.setting("INDEX_OPEN_SECS", 8.0)    # the index can take several seconds to load (user)
INDEX_LIST_SECS = app_paths.setting("INDEX_LIST_SECS", 8.0)    # a search gets this long to show before it is asked again:
#                                                                3 s for 'bournemo', 5 s with a ';' on the manager till (5 Nov)
INDEX_BOX_SECS = 6.0                      # a key to show in the box: Betty searches on each key, and is slow while she does
INDEX_PAGE_SECS = 3.0                     # the next page to replace the last
INDEX_PAGES_MAX = 20
INDEX_ADD_SECS = app_paths.setting("INDEX_ADD_SECS", 12.0)     # a click to its line on the slip: 2.2 s usually, 6.2 s seen
INDEX_REVISITS = 2                        # times the index is left and opened again for one selection
INDEX_TYPE_AHEAD = app_paths.setting("INDEX_TYPE_AHEAD", 0)    # 1: type the next search while Betty loads back (user: it buffers)
_index_typed = ""                         # what the program last typed in the box
_index_filters_checked = False            # since the index was opened
_index_showing = False                    # this program opened the index and hasn't left it
_index_no_row_clicks = False              # the probe: no row may be clicked at all
sports_card = SportsCard()


class IndexStuck(WagerForStaff):
    """The index wouldn't show a selection however it was asked, or the slip didn't take it. A shop's wager goes to
    staff; a Request A Bet is come back to, since the website only offers what's in Betty (user, 5 Nov)."""


def sports_records_by_key() -> dict:
    """Betty's sports records by what a line reads as. Files can hold one twice: the first is kept."""
    out: dict = {}
    for r in sports_card.records():
        out.setdefault(mi.record_key(r['event'], r['market'], r['result']), r)
    return out


def _index_cell_ink(arr: Any, box: tuple) -> bool:
    x, y, w, h = box
    return int((arr[y:y + h, x:x + w, :3].astype(int).sum(axis=2) < 200).sum()) >= 8


def _index_row_colour(arr: Any, box: tuple) -> str | None:
    for name, rgb in INDEX_ROW_COLOURS.items():
        if _colour_share(arr, box, rgb, 30) >= 0.5:
            return name
    # A racing row with no prices in yet is hatched, as on the runner list
    if _colour_share(arr, box, (64, 255, 255), 70) >= 0.2 and _colour_share(arr, box, (255, 255, 255), 30) >= 0.1:
        return 'hatched'
    return None


def _index_price_ink(arr: Any, box: tuple) -> list[str]:
    x, y, w, h = box
    dark = arr[y:y + h, x:x + w, :3].astype(int).sum(axis=2) < 200
    return ["".join('#' if v else '.' for v in row) for row in dark]


def _index_read_price(img: Any, arr: Any, box: tuple) -> tuple[str, bool]:
    """A price cell as (text, sure): by exact shape, else by Tesseract (not sure: Betty's green top row is bold, and
    its '-' can touch the next digit)."""
    shapes = mi.read_price_shapes(_index_price_ink(arr, box))
    if shapes:
        return shapes, True
    text = re.sub(r'\s', '', _ocr_box(img, box, '--psm 7')).replace('—', '-').replace('–', '-')
    return text, False


def read_search_box(img: Any) -> str:
    """The search box's text, '' when only its caret is there (read alone, the caret came back as letters)."""
    x, y, w, h = INDEX_BOX
    dark = int((np.array(img.convert('L').crop((x, y, x + w, y + h))) < 128).sum())
    if dark <= INDEX_CARET_MAX_PX:
        return ""
    return " ".join(_ocr_text_on(img, INDEX_BOX, (255, 255, 255), scale=3, config='--psm 7').split())


def read_index(img: Any = None) -> dict:
    """
    The index as it shows now. {'state': 'blank' (no list), 'none' ("No selections found"), 'drawing' (part of a list)
    or 'list'; 'search': the box as read; 'more': the red arrow shows; 'rows': [{'row', 'y', 'event', 'market', 'result',
    'price', 'price_sure', 'colour', 'usable'}]}. A row is usable unless it's white (Betty's repeating list), hatched or
    has no price, NO or NR: the wager takes the price when struck, so a misread price doesn't rule a row out.
    """
    img = (pyautogui.screenshot() if img is None else img).convert('RGB')
    arr = np.array(img)
    out = {'state': 'blank', 'search': read_search_box(img), 'rows': [],
           'more': _colour_share(arr, INDEX_MORE_ZONE, (220, 30, 30), 70) >= 0.08}
    red = (arr[:, :, 0] > 200) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
    share = red[:, REUSE_PANEL_COLS[0]:REUSE_PANEL_COLS[3]].mean(axis=1)
    lines = [y for y in range(INDEX_GRID_TOP[0], 620) if share[y] >= 0.6]
    tops = [y for y in lines if y <= INDEX_GRID_TOP[1]]
    if not tops:
        if _index_cell_ink(arr, INDEX_NONE_BOX) and 'noselections' in _letters(_ocr_box(img, INDEX_NONE_BOX, '--psm 7')):
            out['state'] = 'none'
        return out
    top = tops[0]
    below = [y for y in lines if y > top + 3]
    n = round((below[0] - top - 1) / INDEX_ROW_PITCH) if below else 0
    if not 1 <= n <= INDEX_ROWS_MAX:
        out['state'] = 'drawing'
        return out
    boxes = []
    for r in range(n):
        y = top + 1 + r * INDEX_ROW_PITCH
        cells = ((7, y, 128, 34), (139, y, 170, 34), (314, y + 2, 83, 31))
        colours = {_index_row_colour(arr, c) for c in cells}
        if len(colours) != 1 or None in colours or not all(_index_cell_ink(arr, c) for c in cells[:2]):
            out['state'] = 'drawing'  # a price cell can be empty: a racing row with no price yet
            return out
        boxes.append((r, y, cells, colours.pop()))
    lefts = _ocr_bw_many(img, [b[2][0] for b in boxes], '--psm 6', 4, crop=_grey_crop)
    results = _ocr_bw_many(img, [b[2][1] for b in boxes], '--psm 7', 3, crop=_grey_crop)
    for (r, y, cells, colour), left, result in zip(boxes, lefts, results):
        lines_left = [ln.strip() for ln in left.splitlines() if ln.strip()]
        price, sure = _index_read_price(img, arr, cells[2]) if _index_cell_ink(arr, cells[2]) else ('', True)
        out['rows'].append({'row': r, 'y': y + INDEX_ROW_PITCH // 2, 'event': lines_left[0] if lines_left else '',
                            'market': " ".join(lines_left[1:]), 'result': result.strip(), 'price': price,
                            'price_sure': sure, 'colour': colour,
                            'usable': colour not in ('white', 'hatched') and bool(price)
                            and _letters(price) not in ('no', 'nr')})
    out['state'] = 'list'
    return out


def index_filter_labels(img: Any) -> dict:
    """What each filter's button says, letters only ('' when it isn't showing: Standard isn't always there)."""
    arr = np.array(img.convert('RGB'))
    return {name: (_letters(_ocr_box(img, box, '--psm 7')) if _colour_share(arr, box, BETSLIP_CREAM, 30) >= 0.3 else '')
            for name, (box, _, _) in INDEX_FILTERS.items()}


def index_sport_filters_on(img: Any) -> list[tuple[int, int]]:
    """The sport icons with a pale blue aura: only that sport is being searched."""
    arr = np.array(img.convert('RGB')).astype(int)
    on = []
    for x, y in INDEX_ICONS:
        cut = arr[y - INDEX_ICON_HALF[1]:y + INDEX_ICON_HALF[1], x - INDEX_ICON_HALF[0]:x + INDEX_ICON_HALF[0]]
        pale = (cut[:, :, 0] > 120) & (cut[:, :, 0] < 235) & (cut[:, :, 1] > 240) & (cut[:, :, 2] > 240)
        if int(pale.sum()) >= INDEX_AURA_MIN_PX:
            on.append((x, y))
    return on


def index_check_filters():
    """
    A filter stays on until Betty closes (user, 5 Nov), and would hide a selection from every search, so each one left
    on is put back: Anytime, Pre-event, Standard, no sport. Read again after each click; one that won't go is said in
    the log and the search goes on.
    """
    img = pyautogui.screenshot()
    for spot in index_sport_filters_on(img):
        print(f"[*] Master Index: a sport filter is on at {spot}: clicking it off.")
        betty_click(*spot)
        time.sleep(0.3)
    labels = index_filter_labels(img)
    for name, (box, wanted, other) in INDEX_FILTERS.items():
        if other not in labels[name]:
            continue
        print(f"[*] Master Index: the {name} filter says '{labels[name]}': clicking it to '{wanted}'.")
        betty_click(box[0] + box[2] // 2, box[1] + box[3] // 2)
        time.sleep(0.3)
        if wanted not in index_filter_labels(pyautogui.screenshot())[name]:
            print(f"[!] Master Index: the {name} filter didn't go to '{wanted}'.")


def _find_index_button(img: Any) -> tuple[int, int] | None:
    """The centre of the peach Master Index button, by its colour."""
    for x, y, w, h in INDEX_BUTTON_ZONES:
        a = np.array(img.convert('RGB').crop((x, y, x + w, y + h))).astype(int)
        ys, xs = np.nonzero(np.max(np.abs(a - np.array(INDEX_BUTTON_PEACH)), axis=2) <= 40)
        if len(xs) >= 200:
            return x + int(xs.mean()), y + int(ys.mean())
    return None


def index_open():
    """To the Master Index from a folder's screen: its button (Betty has been seen ignoring keys, 2 Nov), else '#'."""
    global _index_typed, _index_filters_checked, _index_showing
    img = pyautogui.screenshot()
    screen = detect_screen(img)
    if screen == SCREEN_MASTER_INDEX:
        _index_showing = True
        return
    if screen not in (SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY, SCREEN_RACE_LIST, SCREEN_UNKNOWN):
        raise NavError(f"open the Master Index: Betty shows {screen}")
    spot = _find_index_button(img)
    if spot:
        betty_click(*spot)
    else:
        print("[*] The Master Index button wasn't found: pressing '#'.")
        betty_press('#')
    t0 = time.time()
    while True:
        screen = wait_for_screen({SCREEN_MASTER_INDEX, MODAL_READ_FAILURE}, timeout=max(0.5, INDEX_OPEN_SECS - (time.time() - t0)))
        if screen == SCREEN_MASTER_INDEX:
            break
        if not index_clear_read_failure() and time.time() - t0 >= INDEX_OPEN_SECS:
            raise IndexStuck("the Master Index didn't open")
    _index_typed, _index_filters_checked, _index_showing = "", False, True


def index_leave():
    """Out of the index by a folder button. '#' only opens it, and Esc from anywhere but the search area backs out of
    the wager (user, 5 Nov)."""
    global _index_showing
    _index_showing = False
    betty_click(*INDEX_FOLDER_SPOT)
    screen = wait_for_screen({SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY}, timeout=INDEX_OPEN_SECS)
    if screen not in (SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY):
        raise IndexStuck(f"a folder button didn't leave the Master Index (Betty shows {screen})")


def index_forget():
    """A new wager: the index isn't up, as far as the program knows."""
    global _index_showing
    _index_showing = False


def index_clear_read_failure(img: Any = None) -> bool:
    """Betty's red box when she reads a feed file as it's being rewritten ("Failure to Read Complete Data", mi_16): nothing
    goes on until its Continue is clicked. True when one was closed. Colours first: this is asked on every look at the list."""
    img = pyautogui.screenshot() if img is None else img
    if not _signals_pass(np.array(img.convert('RGB')), MODAL_SIGNATURES[MODAL_READ_FAILURE]['colours']):
        return False
    if detect_screen(img) != MODAL_READ_FAILURE:
        return False
    spot = find_button(img, "Continue", MODAL_BACK_OUT[MODAL_READ_FAILURE][1])
    if not spot:
        raise IndexStuck("Betty's 'Failure to Read Complete Data' box is up, and its Continue wasn't found")
    print("[*] Master Index: Betty's 'Failure to Read Complete Data' box: Continue.")
    betty_click(*spot)
    time.sleep(0.2)
    return True


def _index_key(key: str):
    """A key for the search box, '.' included ('over 2.5'): only ever after the box has been clicked. betty_press refuses
    '.' for the rest of the bet edit, where it does something else."""
    _check_stop()
    _send_key(key)


def index_type_search(wording: str, afresh: bool = False, pace: float = 0.0) -> bool:
    """
    `wording` in the box, keeping what's already right ('over 2.5; ' between selections, as the user does), and all in one
    go. Betty starts a search on a key: with a pause after the first letter (a search of everything holding 'b'), what
    exists came back "No selections found" (manager till, 5 Nov: 1 good of 9; typed in one go, 12 of 12). A letter away from
    the box can act on the bet edit (v adds a void selection), so first: Betty has the keyboard, the index is showing, the
    box is clicked. Read back after. False when it doesn't say what was typed.
    """
    global _index_typed
    if not betty_in_front():
        print("[!] Master Index: Betty hasn't got the keyboard: nothing typed.")
        return False
    betty_click(*INDEX_BOX_SPOT)
    shot = pyautogui.screenshot()
    if index_clear_read_failure(shot):
        betty_click(*INDEX_BOX_SPOT)
        shot = pyautogui.screenshot()
    if not _signals_pass(np.array(shot.convert('RGB')), SCREEN_SIGNATURES[SCREEN_MASTER_INDEX]['colours']):
        print("[!] Master Index: it isn't showing: nothing typed.")
        _index_typed = ""
        return False
    shown = read_search_box(shot)
    known = _index_typed if (_index_typed and not afresh and mi.search_box_reads(shown, _index_typed)) else None
    keep = mi.common_start(known, wording) if known is not None else 0
    erase = (len(known) - keep) if known is not None else len(shown) + 2 if shown else 0
    for key in ['backspace'] * erase + list(wording[keep:]):
        _index_key(key)
        if pace:
            time.sleep(pace)
    _index_typed = wording
    t0 = time.time()
    while True:
        shot = pyautogui.screenshot()
        if index_clear_read_failure(shot):
            _index_typed = ""
            return False if afresh else index_type_search(wording, afresh=True, pace=pace)
        if mi.search_box_reads(read_search_box(shot), wording):
            return True
        if time.time() - t0 > INDEX_BOX_SECS:
            print(f"[!] Master Index: the search box doesn't show '{wording}' after typing.")
            _index_typed = ""
            return False
        time.sleep(0.05)


def index_wait_list(wording: str, timeout: float | None = None) -> dict:
    """
    What the search shows once Betty has stopped drawing, up to `timeout`. 'verdict' on top of read_index: 'good' (the
    list holds what was typed, and the box says it), 'stale', 'ghost', 'none', 'blank', 'drawing', 'box' (the box says
    something else) or 'failure' (Betty's read-failure box, now closed). Returned at once when good; otherwise the last
    read, at the end of the wait.
    """
    timeout = INDEX_LIST_SECS if timeout is None else timeout
    t0, last, read = time.time(), None, None
    x, y, w, h = INDEX_GRID_BOX
    while True:
        _check_stop()
        img = pyautogui.screenshot()
        if index_clear_read_failure(img):
            return {'verdict': 'failure', 'rows': [], 'more': False}
        grid = np.array(img.convert('RGB').crop((x, y, x + w, y + h)))
        if last is not None and np.array_equal(grid, last):
            read = read_index(img)
            read['grid'] = grid
            read['verdict'] = mi.classify_list(read['rows'], wording) if read['state'] == 'list' else read['state']
            if not mi.search_box_reads(read['search'], wording):
                read['verdict'] = 'box'
            if read['verdict'] == 'good':
                corpus_save("index_list", img, {'search': wording}, {'rows': read['rows']})
                return read
        last = grid
        if time.time() - t0 >= timeout:
            if read is None:
                read = dict(read_index(img), grid=grid, verdict='drawing')
            return read
        time.sleep(0.08)


def index_search(wording: str, nudge: bool = True) -> dict:
    """The search asked, then again the ways the user does when Betty bugs out (5 Nov): wait, delete a letter and put it
    back, then delete it all and type it again. The read of the list; its 'verdict' says whether it can be believed."""
    if not index_type_search(wording):
        return {'verdict': 'box', 'rows': [], 'more': False}
    read = index_wait_list(wording)
    if read['verdict'] == 'good' or not nudge:
        return read
    print(f"[*] Master Index: '{wording}' shows {read['verdict']}: deleting a letter and putting it back.")
    betty_click(*INDEX_BOX_SPOT)
    _index_key('backspace')
    _index_key(wording[-1])
    read = index_wait_list(wording)
    if read['verdict'] == 'good':
        return read
    print(f"[*] Master Index: '{wording}' still shows {read['verdict']}: typing it all again.")
    if not index_type_search(wording, afresh=True):
        return {'verdict': 'box', 'rows': [], 'more': False}
    return index_wait_list(wording)


def _index_next_page(read: dict, wording: str) -> dict | None:
    """The red arrow, and the next page's read; None when no other page came."""
    betty_click(*INDEX_MORE_SPOT)
    t0 = time.time()
    x, y, w, h = INDEX_GRID_BOX
    while time.time() - t0 < INDEX_PAGE_SECS:
        _check_stop()
        grid = np.array(pyautogui.screenshot().convert('RGB').crop((x, y, x + w, y + h)))
        if not np.array_equal(grid, read['grid']):
            page = index_wait_list(wording)
            return page if page['verdict'] == 'good' else None
        time.sleep(0.05)
    return None


def _same_rows(a: list[dict], b: list[dict]) -> bool:
    key = lambda rows: [(r['event'], r['market'], r['result'], r['price']) for r in rows]
    return key(a) == key(b)


def index_page_to_row(read: dict, wording: str, sel: dict) -> tuple[dict | None, dict]:
    """
    The red arrow until the row shows: (the row or None, the page it's on, ready to click). A row that fits but whose
    market may be cut off, not at the requested price, could be the wrong one of two ('Both Teams To Scor'), so the pages
    after it are looked at too, and the search asked again to get back to it. Rows that can't be told apart go to staff.
    """
    seen_rows, fits, pages = [read['rows']], [], 1
    while True:
        choice = mi.choose_row(read['rows'], sel)
        if choice['fits'] and not choice['row']:
            raise WagerForStaff(f"the Master Index shows {choice['why']}: {sel.get('text')}")
        row = choice['row']
        if row and not fits and (mi.same_price(row['price'], sel.get('price')) or not mi.market_may_be_cut(row)):
            return row, read
        if row:
            fits.append((pages, row))
        if not read['more'] or pages >= INDEX_PAGES_MAX:
            break
        page = _index_next_page(read, wording)
        if page is None or any(_same_rows(page['rows'], rows) for rows in seen_rows):
            break
        read, pages = page, pages + 1
        seen_rows.append(read['rows'])
    if not fits:
        return None, read
    choice = mi.choose_row([r for _, r in fits], sel)
    if not choice['row']:
        raise WagerForStaff(f"the Master Index shows {choice['why']}: {sel.get('text')}")
    on_page = next(p for p, r in fits if r is choice['row'])
    if on_page == pages:
        return choice['row'], read
    read = index_search(wording)  # back to the first page, then on to its page
    for _ in range(on_page - 1):
        read = _index_next_page(read, wording) if read['verdict'] == 'good' else None
        if read is None:
            return None, {'rows': [], 'more': False}
    return mi.choose_row(read['rows'], sel)['row'], read


def index_find_row(sel: dict) -> tuple[dict, dict]:
    """
    The selection's row, however many ways it takes (user, 5 Nov): each wording in turn, the first asked again as
    index_search does, then out of the index by a folder button and in again. (row, the read it's on). IndexStuck when
    it never shows: for a Request A Bet, the program comes back to it a minute or two later.
    """
    global _index_filters_checked
    why = ""
    for visit in range(INDEX_REVISITS + 1):
        if visit:
            print(f"[*] Master Index: not found ({why}): leaving by a folder and coming back ({visit}/{INDEX_REVISITS}).")
            index_leave()
            index_open()
        if visit or not _index_filters_checked:
            index_check_filters()
            _index_filters_checked = True
        for k, wording in enumerate(mi.search_wordings(sel)):
            read = index_search(wording, nudge=k == 0)
            if read['verdict'] != 'good':
                why = f"'{wording}' shows {read['verdict']}"
                continue
            row, page = index_page_to_row(read, wording, sel)
            if row:
                return row, page
            why = f"no row fits on {'the list' if not read['more'] else 'any page'} for '{wording}'"
    raise IndexStuck(f"the Master Index didn't show {sel.get('text')}: {why}")


SPORT_LINE_FIRST = re.compile(r'^\W*(\d+)\s*[.,:]?\s*(.*)$')
SPORT_LINE_SECOND = re.compile(r'^(.*?)[\s\W]+(\d+\s*-\s*\d+|evens|evs|sp|nr)\W*(?:[BE][PF]|SP)?\W*$', re.IGNORECASE)


def read_sports_slip_line(img: Any) -> dict | None:
    """The betslip's last line as a sports one: {'n', 'first': event and market, 'result', 'price'}. Two rows of text in a
    line's place: '1. AGF Aarhus v Br  Goals Over Unde', 'Over 2.5     19-20 BP'. None while Betty is drawing it."""
    rows = betslip_rows_with_text(img)
    left = betslip_left(img)
    for row in rows[-1:-3:-1]:  # the one above when the last doesn't read as a line: Betty still drawing it
        x, y, w, h = _betslip_row_box(left, row)
        first, second = _ocr_bw_many(img, [(x, y, w, h), (x, y + h, w, h)], '--psm 7', 3, True)
        a, b = SPORT_LINE_FIRST.match(first.strip()), SPORT_LINE_SECOND.match(second.strip())
        if a and b:
            return {'n': int(a.group(1)), 'row': row, 'first': a.group(2), 'result': b.group(1).strip(),
                    'price': re.sub(r'\s', '', b.group(2))}
    return None


def index_confirm_line(already_on_slip: int, row: dict) -> dict:
    """
    After a row is clicked: Betty's boxes answered as for any selection (the price box takes the price when struck), then
    the slip's new line must be that row, and one more than before. Anything else stops the wager: a line added wrongly
    must never be placed.
    """
    t0, line = time.time(), None
    answer_entry_popups(wait=POPUP_WAIT_AFTER_ADD)
    while time.time() - t0 < INDEX_ADD_SECS:
        _check_stop()
        img = pyautogui.screenshot()
        arr = np.array(img.convert('RGB'))
        if any(_signals_pass(arr, sig['colours']) for sig in MODAL_SIGNATURES.values()):
            answer_entry_popups()
            continue
        line = read_sports_slip_line(img)
        if line and line['n'] == already_on_slip + 1 and mi.slip_line_fits(line, row):
            return line
        time.sleep(0.15)
    raise IndexStuck(f"after clicking {row['event']} {row['market']} {row['result']}, the slip's last line reads {line}, "
                     f"not selection {already_on_slip + 1}")


def enter_sports_selection(horse: dict, already_on_slip: int, next_horse: dict | None = None):
    """One locked sports selection: the index opened, its row found and clicked on the price, its line checked."""
    global _index_typed
    if _index_no_row_clicks:
        raise PlacingRefused("the probe doesn't click rows")
    refresh_watcher_hud(f"Master Index, selection {already_on_slip + 1}: {horse.get('text')}...")
    index_open()
    row, read = index_find_row(horse)
    x, y, w, h = INDEX_GRID_BOX
    if not np.array_equal(np.array(pyautogui.screenshot().convert('RGB').crop((x, y, x + w, y + h))), read['grid']):
        print("[*] Master Index: the list changed just before the click: reading it again.")
        row, read = index_find_row(horse)
    print(f"[*] Master Index: row {row['row'] + 1}: {row['event']} | {row['market']} | {row['result']} | {row['price']} "
          f"(wanted {horse.get('price')}).")
    betty_click(INDEX_PRICE_SPOT_X, row['y'])
    if (INDEX_TYPE_AHEAD and next_horse and next_horse.get('sport')
            and mi.same_price(row['price'], horse.get('rab_price') or horse.get('price'))):
        # Same price, so no price box to catch the letters. Typed into the place the box will be (user, 5 Nov: it buffers)
        ahead = mi.search_wordings(next_horse)[0]
        keep = mi.common_start(_index_typed, ahead)
        betty_click(*INDEX_BOX_SPOT)
        for key in ['backspace'] * (len(_index_typed) - keep) + list(ahead[keep:]):
            _index_key(key)
        _index_typed = ahead
    line = index_confirm_line(already_on_slip, row)
    print(f"[+] Selection {already_on_slip + 1} on the slip: {line['first']} | {line['result']} at {line['price']}.")


def _probe_betty_in_front() -> bool:
    """Betty has the keyboard, or the probe presses nothing. Windows only lets a program that has just had input bring a
    window forward, so Alt is tapped first (nothing else on Betty takes it). A key must never land on another window."""
    user32 = ctypes.windll.user32
    for _ in range(5):
        hwnd = betty_top_window()
        if hwnd and hwnd == user32.GetForegroundWindow():
            return True
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 0x2, 0)
        focus_betty()
        time.sleep(0.3)
    return False


def index_probe(items: list[str], adding: bool = False):
    """
    Testing only, with staff at the till, and never in the watcher: python betty_companion.py --index-probe "over 2.5;
    monaco" "yes; bournemout". From Home it opens an empty bet by Accept Cash Wager (a callover: finishing one places a
    real bet, user, 5 Nov), runs each search at three typing speeds and saves every frame to logs\\index_probe_<time>, then
    backs out. No row is clicked, and neither Choose Bet nor F12 is ever pressed. --index-try "<event market result @
    price>" also clicks each selection's row and checks its line, and backs out just the same. Touching the mouse or
    keyboard stops it.
    """
    global _index_no_row_clicks
    _index_no_row_clicks = not adding
    test_mode_on.set()
    folder = os.path.join(app_paths.log_dir(), f"index_probe_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(folder, exist_ok=True)
    print(f"[*] Master Index {'try' if adding else 'probe'} in 5 s, no bet is placed. Frames go to {folder}. Bring Betty to "
          "the front; touching the mouse or keyboard stops it.")
    time.sleep(5)
    if not _probe_betty_in_front():
        print("[-] Betty couldn't be brought to the front: nothing pressed.")
        return
    HumanInputMonitor(lambda kind: abort_event.set() if kind != "move" else None).start()

    def frame(tag: str):
        name = f"{time.strftime('%H%M%S')}_{int(time.time() * 1000) % 1000:03d}_{tag}.png"
        pyautogui.screenshot().save(os.path.join(folder, name))

    try:
        screen = detect_screen()
        print(f"[*] Betty shows {screen}.")
        if screen == SCREEN_VIEW_WAGERS and go_home():
            screen = SCREEN_HOME
        if screen == SCREEN_HOME:
            spot = find_button(pyautogui.screenshot(), "Accept", (450, 90, 240, 100))
            if not spot:
                print("[-] Accept Cash Wager wasn't found on Home: nothing done.")
                return
            betty_click(*spot)
            time.sleep(1.5)  # a picture menu no screen name covers (not the events screen a wager's bet edit opens on)
            betty_press('1')  # the first folder, as a wager's bet edit does, so the index opens from a folder's screen
            wait_for_screen({SCREEN_RACE_ENTRY, SCREEN_RACE_ENTRY_READY}, timeout=NAV_TIMEOUT)
        t0 = time.time()
        index_open()
        print(f"[+] Master Index open in {time.time() - t0:.1f}s; filters {index_filter_labels(pyautogui.screenshot())}.")
        frame("open")
        if adding:
            records = sports_records_by_key()
            for n, item in enumerate(items):
                text, _, price = item.partition('@')
                sel = dict(mi.split_line(text, records), price=price.strip(" )"), sport=True)
                print(f"[*] {n + 1}: {sel}")
                enter_sports_selection(sel, n)
                frame(f"added_{n + 1}")
        else:
            for wording in items:
                for pace in (0.0, 0.05, 0.15):
                    t0 = time.time()
                    ok = index_type_search(wording, afresh=True, pace=pace)
                    typed_in = time.time() - t0
                    read = index_wait_list(wording) if ok else {'verdict': 'box', 'rows': [], 'more': False}
                    print(f"[*] Typed in {typed_in:.1f}s, then {time.time() - t0 - typed_in:.1f}s for Betty to show it.")
                    print(f"[*] '{wording}' typed at {pace}s a key: {read['verdict']} after {time.time() - t0:.1f}s, "
                          f"{len(read['rows'])} rows, more below: {read['more']}")
                    for r in read['rows']:
                        print(f"[*]   {r['row'] + 1:2d} {r['event']!r} | {r['market']!r} | {r['result']!r} | {r['price']!r}"
                              f"{'' if r['price_sure'] else ' (unsure)'}")
                    frame(f"{re.sub(r'[^a-z0-9]', '_', wording)}_{pace}_{read['verdict']}")
    except WatcherStop:
        print("[*] Stopped by a key or click.")
    except (NavError, WagerForStaff, PlacingRefused) as e:
        print(f"[-] {type(e).__name__}: {e}")
        frame("problem")
    abort_event.clear()
    print("[*] Backing out: nothing placed.")
    print(f"[{'+' if go_home() else '-'}] Betty shows {detect_screen()}.")


def check_screen_once(delay: float = 5.0):
    """Read-only diagnosis (python betty_companion.py --check-screen): one screenshot after `delay` seconds, then what
    the watcher would see. No key, no click."""
    print(f"[*] Screen check in {delay:.0f}s: bring Betty to the front...")
    time.sleep(delay)
    img = pyautogui.screenshot()
    screen = detect_screen(img)
    print(f"[*] Screen: {screen}")
    if screen == SCREEN_MASTER_INDEX:
        read = read_index(img)
        print(f"[*] Master Index: search {read['search']!r}, {read['state']}, filters {index_filter_labels(img)}, "
              f"sport filters on {index_sport_filters_on(img)}, more below: {read['more']}")
        for r in read['rows']:
            print(f"[*]   {r['row'] + 1:2d} {r['colour']:5s} {r['event']!r} | {r['market']!r} | {r['result']!r} | "
                  f"{r['price']!r}{'' if r['price_sure'] else ' (unsure)'}")
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
    elif cmd in ("sports on", "sports off"):
        os.environ["SPORTS_ON"] = "1" if cmd == "sports on" else "0"
        print(f"[*] Sports {'on' if cmd == 'sports on' else 'off'} (the switch in the control window).")
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
    if "--index-probe" in sys.argv or "--index-try" in sys.argv:
        index_probe([a for a in sys.argv[1:] if not a.startswith("--")], adding="--index-try" in sys.argv)
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
    FOREGROUND_LOG.start()
    threading.Thread(target=watcher_loop, daemon=True).start()
    threading.Thread(target=lesson_sync_loop, name="lessons", daemon=True).start()
    refresh_watcher_hud()

    if BACKEND_MODE:
        backend_event("ready", test_mode=test_mode_on.is_set(), tesseract=TESSERACT_EXE,
                      readers=[t['label'] for t in reader_tiers()], route=route)
        backend_command_loop()
    else:
        keyboard.wait()


if __name__ == "__main__":
    main()
