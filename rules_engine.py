"""
Rules Engine for Betty Companion (v1.11.0)
===========================================
Modular House Rules, Discrepancy Settlement, and Non-Normal State Dispatcher.
One set of house rules, BetAnsells, read from bookmaker_rules.json (re-read when the file is edited).
"""

import os
import json
import re
import itertools
import math
from collections import defaultdict
from typing import Callable
from difflib import get_close_matches


import app_paths
from meetings_manager import meetings_manager

# Standard UK Glossary Line Counts for full cover bets
UK_BETTING_GLOSSARY = {
    'single': 1,
    'double': 1,
    'treble': 1,
    'accumulator': 1,
    'acca': 1,
    'straight forecast': 1,
    'reversed forecast': 2,
    'tricast': 1,
    'trixie': 4,
    'patent': 7,
    'yankee': 11,
    'lucky 15': 15,
    'canadian': 26,
    'super yankee': 26,
    'lucky 31': 31,
    'heinz': 57,
    'lucky 63': 63,
    'super heinz': 120,
    'goliath': 247,
    # Exotic / speciality bets
    'alphabet': 26,
    'round robin': 10,
    'flag': 23,
    'super flag': 46,
    'rounder': 3,
    'roundabout': 3,
    'union jack': 8,
    'up-and-down': 2,
    # Forecast doubles: one forecast in each of 2 races, combined as a double
    'straight forecast double': 1,
    'reversed forecast double': 4,
}

# Customer forecast shorthand: 'f/c', 'fc', 'f/cast', 'fcast', 'forecast' (e.g. 'r/f/cast', 's/f/cast', 'rfc')
_FC = r'(?:f\s*\/?\s*c(?:ast)?|forecast)'
_RFC_RE = re.compile(rf'\b(?:rev(?:erse|ersed)?\s*{_FC}|r\s*\/\s*{_FC}|rfc)\b')
_CFC_RE = re.compile(rf'\b(?:comb(?:ination)?\s*{_FC}|c\s*\/\s*{_FC}|cfc)\b')
_SFC_RE = re.compile(rf'\b(?:str(?:aight)?\s*{_FC}|s\s*\/\s*{_FC}|sfc)\b')
_DOUBLE_WORD_RE = re.compile(r'\b(?:doubles?|doubs?|doubl\w*|dbls?)\b')


def match_forecast_bet_type(raw: str) -> str | None:
    """
    Recognises forecast bets in customer shorthand, including forecast doubles.
    'r/f/cast' -> 'reversed forecast'; '4x 50 r/f/cast doubles' -> 'reversed forecast double';
    's/f/cast doubles' -> 'straight forecast double'. Returns None when no forecast is written.
    """
    raw = raw.lower()
    if _RFC_RE.search(raw):
        base = "reversed forecast"
    elif _CFC_RE.search(raw):
        return "combination forecast"
    elif _SFC_RE.search(raw):
        base = "straight forecast"
    else:
        return None
    return f"{base} double" if _DOUBLE_WORD_RE.search(raw) else base


def resolve_plain_forecast(b_type: str, num_horses: int) -> str:
    """A forecast written without 'straight', 'reversed' or 'combination' (plain 'F/C', 'forecast'): a straight
    forecast on two runners (in the order written), a combination forecast on three or more (house default, user
    23 Oct). Any other bet type is returned unchanged."""
    if b_type != 'forecast':
        return b_type
    return 'combination forecast' if num_horses >= 3 else 'straight forecast'


def count_distinct_race_combos(horses: list[dict], k: int) -> int | None:
    """
    Counts the k-fold combinations whose selections all run in different races
    (BetAnsells Rule 1.8.1: same-race selections cannot be combined in a multiple).
    Returns None when any selection lacks a meeting or time, so callers fall back to nCr.
    """
    race_keys = []
    for h in horses:
        meeting, time_str = get_horse_event_key(h)
        if not meeting or not time_str:
            return None
        race_keys.append((meeting, time_str))
    if k <= 0 or k > len(race_keys):
        return 0
    return sum(1 for combo in itertools.combinations(race_keys, k) if len(set(combo)) == k)


def clean_horse_name(name: str) -> str:
    """Cleans punctuation, foreign suffixes like (IRE) or (FR), virtual (v) tags, and leading/trailing whitespace."""
    if not name:
        return ""
    n = re.sub(r'\s*\([A-Za-z]{2,3}\)', '', name)
    n = re.sub(r'\s*\([vV]\)', '', n)
    n = re.sub(r'[^a-zA-Z0-9\s]', ' ', n)
    return re.sub(r'\s+', ' ', n).strip().lower()


def parse_race_time_to_minutes(time_str: str) -> tuple[int | None, str | None]:
    """
    Parses various race time formats into total minutes from midnight and a normalized HH:MM string.
    Handles '14:15', '1415', '2.15', '2:15', '215', '1647', '6 00' (a faint dot read as a space), etc.
    A single minute digit is a dropped 0 before it ('17.9' = 17:09, '5.3' = 17:03): customers leave that 0 out, almost
    never the last one (user, 30 Oct).
    Converts UK afternoon racing (e.g. 2:15 -> 14:15).
    """
    if not time_str:
        return None, None
    s = time_str.strip()
    m = re.search(r'(\d{1,2})[:.\- ](\d{2})', s) or re.search(r'(?<!\d)(\d{1,2})[:.](\d)(?!\d)', s)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
    else:
        m_dig = re.search(r'\b(\d{3,4})\b', s)
        if m_dig:
            val = m_dig.group(1)
            h, mn = (int(val[:2]), int(val[2:])) if len(val) == 4 else (int(val[:1]), int(val[1:]))
        else:
            return None, None

    if 1 <= h <= 8:  # Afternoon racing (e.g. 2:15 -> 14:15, 4:50 -> 16:50); 9 and 10 are legitimate morning slots
        h += 12
    if 0 <= h < 24 and 0 <= mn < 60:
        return h * 60 + mn, f"{h:02d}:{mn:02d}"
    return None, None


WORD_TO_NUM = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}


def race_time_options(time_str: str) -> set[int]:
    """
    The minutes from midnight a written time can mean. 9, 10 and 11 o'clock can be morning or evening on a 12-hour
    slip ('No 4 9.40' for the 21:40 dogs), so both; 1-8 are afternoon (parse_race_time_to_minutes). Empty if unreadable.
    """
    mins, _ = parse_race_time_to_minutes(time_str)
    if mins is None:
        return set()
    return {mins, mins + 720} if 540 <= mins < 720 else {mins}


def selection_names(bet: dict) -> list[str]:
    """The names of a bet's selections, for normalize_bet_type to leave out of its description."""
    return [str(h.get('name') or '') for h in bet.get('horses', []) if isinstance(h, dict)]


def _without_names(text: str, names) -> str:
    """`text` with each selection name taken out (apostrophes ignored), so a name never decides the bet type."""
    text = re.sub(r"['’]", "", text)
    for name in names or ():
        words = re.findall(r"[a-z0-9]+", re.sub(r"['’]", "", str(name).lower()))
        if words and len("".join(words)) >= 3:
            text = re.sub(r"\b" + r"\W*".join(map(re.escape, words)) + r"\b", " ", text)
    return text


def normalize_bet_type(bet_type: str, desc: str = "", names=()) -> str:
    """
    Normalizes customer slang, abbreviations, and ligatures into canonical UK bet type strings.
    e.g. 'rfc', 'r/f/c', 'reversed f/c' -> 'reversed forecast'
         'sfc', 's/f/c', 'straight f/c' -> 'straight forecast'
         'cfc', 'c/f/c', 'comb f/c'      -> 'combination forecast'
         'l15', '4 l15'                 -> 'lucky 15'
         'l31', '5 l31'                 -> 'lucky 31'
    `names`: the bet's selection names (selection_names), taken out of `desc` first: 'Double on Pat's Pride & Beta'
    is a double, not a patent; '£1 win Union Jack Rose' a single, not a union jack (review R5).
    """
    raw = f"{bet_type} {_without_names(str(desc).lower(), names)}".lower().strip()

    # Forecasts (incl. forecast doubles and 'r/f/cast' / 's/f/cast' shorthand):
    fc_type = match_forecast_bet_type(raw)
    if fc_type:
        return fc_type
    if re.search(r'\b(?:combination\s*tricast|comb\s*tricast|ctc)\b', raw):
        return "combination tricast"
    if re.search(r'\b(?:tricast|stc)\b', raw):
        return "tricast"

    # Full cover bets (plurals too: '2 x 10p yankees'; a plural was returned unchanged and couldn't be entered):
    if re.search(r'\b(?:lucky\s*15|lucky15|l\s*15|l15)s?\b', raw):
        return "lucky 15"
    if re.search(r'\b(?:lucky\s*31|lucky31|l\s*31|l31)s?\b', raw):
        return "lucky 31"
    if re.search(r'\b(?:lucky\s*63|lucky63|l\s*63|l63)s?\b', raw):
        return "lucky 63"
    if re.search(r'\b(?:canadians?|super\s*yankees?)\b', raw):
        return "canadian"
    if re.search(r'\b(?:yankees?|yank)\b', raw):
        return "yankee"
    if re.search(r'\b(?:patents?|pat)\b', raw):
        return "patent"
    if re.search(r'\b(?:trixies?)\b', raw):
        return "trixie"
    if re.search(r'\b(?:super\s*heinz)\b', raw):
        return "super heinz"
    if re.search(r'\b(?:heinz)\b', raw):
        return "heinz"
    if re.search(r'\b(?:goliaths?)\b', raw):
        return "goliath"
    if re.search(r'\b(?:alphabet)\b', raw):
        return "alphabet"
    if re.search(r'\b(?:round\s*robin)\b', raw):
        return "round robin"
    if re.search(r'\b(?:super\s*flag)\b', raw):
        return "super flag"
    if re.search(r'\b(?:flag)\b', raw):
        return "flag"
    if re.search(r'\b(?:roundabout)\b', raw):
        return "roundabout"
    if re.search(r'\b(?:rounder)\b', raw):
        return "rounder"
    if re.search(r'\b(?:union\s*jack)\b', raw):
        return "union jack"
    if re.search(r'\b(?:up\s*and\s*down|cross\s*bet|ssa|dsa)\b', raw):
        return "up-and-down"

    # Permutation Folds vs. Straight Accumulators:
    # If the text explicitly mentions 'accumulator' or 'acca', or specifies a single line '1 x ... fold',
    # it is a straight Accumulator, NOT a multi-bet permutation.
    m_wfold = re.search(r'\b(?:perm\s*)?(two|three|four|five|six|seven|eight|nine|ten)[- ]?folds?\b', raw)
    if m_wfold:
        n_f = WORD_TO_NUM[m_wfold.group(1)]
        if n_f == 2:
            return "double"
        elif n_f == 3:
            return "treble"
        elif re.search(r'\b(?:accumulators?|accas?)\b', raw) or re.search(r'\b1\s*x\b', raw):
            return "accumulator"
        else:
            return f"perm {n_f}-folds"

    m_fold = re.search(r'\b(?:perm\s*)?(\d{1,2})[- ]folds?\b', raw)
    if m_fold:
        n_f = int(m_fold.group(1))
        if n_f == 2:
            return "double"
        elif n_f == 3:
            return "treble"
        elif re.search(r'\b(?:accumulators?|accas?)\b', raw) or re.search(r'\b1\s*x\b', raw):
            return "accumulator"
        else:
            return f"perm {n_f}-folds"

    # Standard multiples. 's?' takes the plural: '\bdouble\b' misses 'doubles' (no word boundary between e and s), and
    # 'trebles', 'singles', 'accas' were returned unchanged, so entry couldn't enter them (review B6, 28 Oct)
    if re.search(r'\b(?:accumulators?|accas?)\b', raw):
        return "accumulator"
    if re.search(r'\b(?:trebles?|treb)\b', raw):
        return "treble"
    if re.search(r'\b(?:doubles?|doub|dousl)\b', raw):
        return "double"
    if re.search(r'\b(?:singles?|win)\b', raw):
        return "single"

    return bet_type.lower().strip()


def is_greyhound_or_trap_selection(horse: dict) -> tuple[bool, int | None, str | None]:
    """
    Checks whether a selection represents a greyhound race or a trap bet.
    Returns: (is_greyhound, trap_number, resolved_meeting)
    """
    name = str(horse.get('name', '')).strip().lower()
    meeting = str(horse.get('meeting', '')).strip().lower()
    raw_hint = str(horse.get('raw_meeting_hint', '')).strip().lower()
    target_meeting = raw_hint or meeting

    # 1. Resolve meeting category first (prioritise horse racing and virtual racing protection)
    cat, c_name = meetings_manager.resolve_meeting(target_meeting)
    if cat in ["horse", "virtual"]:
        # Positively identified as horse racing or virtual racing -> exit immediately
        return False, None, None
    if meetings_manager.is_virtual_meeting(meeting)[0] or meetings_manager.is_virtual_meeting(raw_hint)[0]:
        return False, None, None

    resolved_track = c_name if cat == "greyhound" else None

    # 2. Greyhound fallback lookup only if not identified as horse racing
    if not resolved_track and target_meeting:
        tracks = meetings_manager.get_greyhound_tracks()
        resolved_track = tracks.get(meeting) or tracks.get(raw_hint)
        if not resolved_track:
            for tok in [raw_hint, meeting]:
                if tok and len(tok) >= 3:
                    # Stricter cutoff (0.8) to prevent cross-matching horse courses like Listowel -> Towcester
                    close = get_close_matches(tok, list(tracks.keys()), n=1, cutoff=0.8)
                    if close:
                        resolved_track = tracks[close[0]]
                        break

    # 3. Check if name is a trap pattern
    trap_num = None
    m_trap = re.match(r'^(?:trap|t|tr|no\.?|#)?\s*(\d{1,2})$', name, re.IGNORECASE)
    if m_trap:
        trap_num = int(m_trap.group(1))
    elif name.isdigit():
        trap_num = int(name)

    if resolved_track or trap_num is not None:
        return True, trap_num, resolved_track

    return False, None, None


LINES_PER_BET_TYPE: dict[str, int] = {
    'single': 1, 'double': 1, 'treble': 1, 'accumulator': 1, 'acca': 1,
    'straight forecast': 1, 'reversed forecast': 2, 'combination forecast': 2,
    'straight forecast double': 1, 'reversed forecast double': 4,
    'trixie': 4, 'patent': 7, 'yankee': 11, 'lucky 15': 15, 'lucky15': 15, 'l15': 15,
    'canadian': 26, 'super yankee': 26, 'lucky 31': 31, 'lucky31': 31, 'l31': 31,
    'heinz': 57, 'lucky 63': 63, 'lucky63': 63, 'super heinz': 120, 'goliath': 247,
    'alphabet': 26, 'round robin': 10, 'flag': 23, 'super flag': 46, 'rounder': 3,
    'roundabout': 3, 'union jack': 8
}


def whole_bets(bet: dict) -> int:
    """
    How many whole bets of a several-line type (patent 7, yankee 11 ...) its multiplier asks for: '2 x 10p yankees' =
    2 ('1x 50p patent' = 1, 9.2459179, 31 Oct). A multiplier that is already whole bets' lines ('7x patent',
    '22x yankee') is that many lines, so 1 bet per 7 / 11; any other type, or no multiplier: 1. Betty takes one bet of
    a type per line of the bet list, so entry enters the stake times this (2 yankees at 10p = 1 yankee at 20p).
    """
    names = selection_names(bet)
    b_type = resolve_plain_forecast(normalize_bet_type(str(bet.get('bet_type', 'single')), str(bet.get('description', '')),
                                                       names), len(bet.get('horses', [])))
    per_bet = UK_BETTING_GLOSSARY.get(b_type) or LINES_PER_BET_TYPE.get(b_type) or 1
    m = re.search(r'\b(\d+)\s*x\b', f"{bet.get('description', '')} {bet.get('raw_text', '')}".lower())
    if per_bet <= 1 or not m or 'forecast' in b_type or 'tricast' in b_type:  # their lines follow the runners
        return 1
    mult = int(m.group(1))
    return mult // per_bet if mult % per_bet == 0 else mult


def calculate_bet_cost_pence(bet: dict) -> int:
    """
    Calculates the total cost in pence for a single bet instruction.
    Correctly handles combination multipliers, forecasts, full cover bets, and each-way lines.
    """
    unit_stake = bet.get('stake_pence')
    if unit_stake is None and bet.get('unit_stake') is not None:
        try:
            unit_stake = round(float(bet['unit_stake']) * 100)
        except (ValueError, TypeError):
            unit_stake = 0
    if unit_stake is None:
        unit_stake = 0
    b_type = normalize_bet_type(str(bet.get('bet_type', 'single')), str(bet.get('description', '')), selection_names(bet))
    desc = str(bet.get('description', '')).lower()
    raw_text = str(bet.get('raw_text', '')).lower()
    combined_desc = f"{desc} {raw_text}"
    is_ew = bool(bet.get('each_way', False))
    ew_mult = 2 if is_ew else 1
    horses = bet.get('horses', [])
    num_horses = len(horses)
    b_type = resolve_plain_forecast(b_type, num_horses)  # costed exactly as entry_bet_type enters it

    cost = None
    # 1. Forecast bets (checked BEFORE the 'Nx' multiplier: a forecast double's lines are fixed by its type):
    if b_type in ('straight forecast double', 'reversed forecast double'):
        # SF double = 1 line (SF in race A x SF in race B); RF double = 2 x 2 = 4 lines
        cost = unit_stake * LINES_PER_BET_TYPE[b_type] * ew_mult
    elif b_type == 'straight forecast':
        cost = unit_stake * 1 * ew_mult
    elif b_type == 'reversed forecast':
        cost = unit_stake * 2 * ew_mult
    elif b_type == 'combination forecast':
        combo_lines = (num_horses * (num_horses - 1)) if num_horses >= 2 else 2
        cost = unit_stake * combo_lines * ew_mult
    elif b_type == 'tricast':
        cost = unit_stake * 1 * ew_mult
    elif b_type == 'combination tricast':
        combo_lines = (num_horses * (num_horses - 1) * (num_horses - 2)) if num_horses >= 3 else 6
        cost = unit_stake * combo_lines * ew_mult

    # 2. Explicit multiplier check in text (e.g. "3 x 50", "3x", "6 x")
    if cost is None:
        m_mult = re.search(r'\b(\d+)\s*x\b', combined_desc)
        if m_mult:
            per_bet = UK_BETTING_GLOSSARY.get(b_type) or LINES_PER_BET_TYPE.get(b_type) or 1
            # A bet of several lines: the multiplier counts whole bets ('1x 50p patent' = 7 lines, 9.2459179, 31 Oct,
            # costed 50p before), or is already whole bets' lines ('7x 50p patent'); whole_bets says which
            mult_lines = whole_bets(bet) * per_bet if per_bet > 1 else int(m_mult.group(1))
            cost = unit_stake * mult_lines * ew_mult

    # 3. Dynamic combination math based on number of horses.
    # Same-race pairs/folds are never struck (BetAnsells Rule 1.8.1), so once every selection has a
    # resolved meeting + time only different-race combinations are counted; otherwise plain nCr.
    def _combo_lines(k: int) -> int:
        valid = count_distinct_race_combos(horses, k)
        return valid if valid is not None else math.comb(num_horses, k)

    if cost is None:
        m_perm = re.search(r'perm\s*(\d+)[- ]folds?', b_type)
        if m_perm:
            k_fold = int(m_perm.group(1))
            if num_horses >= k_fold:
                cost = unit_stake * _combo_lines(k_fold) * ew_mult
            else:
                cost = unit_stake * 1 * ew_mult
        elif b_type == 'double':
            has_explicit_multi_double = bool(re.search(r'\b(?:\d+\s*x|(?:x|cross)\s*doub\w*|\d+\s*doubles?)\b', combined_desc))
            if (has_explicit_multi_double or num_horses > 2) and num_horses >= 2:
                cost = unit_stake * _combo_lines(2) * ew_mult
            else:
                # Singular double (e.g. '50 win double', '50 ew double'): strictly 1 line
                cost = unit_stake * 1 * ew_mult
        elif b_type == 'treble' and num_horses >= 3:
            cost = unit_stake * _combo_lines(3) * ew_mult
        elif b_type == 'single' and num_horses > 1:
            cost = unit_stake * num_horses * ew_mult

    # 4. System bets line count lookup from UK_BETTING_GLOSSARY:
    if cost is None:
        lines = UK_BETTING_GLOSSARY.get(b_type) or LINES_PER_BET_TYPE.get(b_type)
        if lines is None:  # the money check then decides; say why the cost may be wrong (review R26)
            print(f"[-] Bet type '{b_type}' isn't known: costed as 1 line.")
            lines = 1
        cost = unit_stake * lines * ew_mult

    bet['total_stake_pence'] = cost
    return cost


def get_horse_event_key(horse: dict) -> tuple[str, str]:
    """Returns a normalized (meeting, time) tuple representing the specific race event."""
    raw_meeting = str(horse.get('meeting', '')).strip()
    if raw_meeting:
        _, c_meeting = meetings_manager.resolve_meeting(raw_meeting)
        meeting = (c_meeting or raw_meeting).strip().lower()
    else:
        meeting = ""
    raw_time = str(horse.get('time', '')).strip()
    _, norm_time = parse_race_time_to_minutes(raw_time)
    time_str = norm_time or raw_time
    return (meeting, time_str)


def is_unnamed_favourite(horse: dict) -> bool:
    """Checks whether a selection represents an un-named favourite (Rule 1.7)."""
    name = str(horse.get('name', '')).strip().lower()
    fav_patterns = [
        'fav', 'favourite', 'favorite', '1st fav', 'first fav', 'first favourite',
        '2nd fav', 'second fav', 'second favourite', 'jt fav', 'co fav', 'cfav',
        'sp fav', 'unnamed fav', 'un-named fav'
    ]
    return any(name == p or name.startswith(p + ' ') or name.endswith(' ' + p) for p in fav_patterns)


# -----------------------------------------------------------------------------
# Module-level Notification System
# -----------------------------------------------------------------------------
def _default_notify(msg: str, is_error: bool = False, bg_color: str | None = None):
    prefix = "[-] [ALERT]" if is_error else "[+] [INFO]"
    print(f"{prefix} {msg}")

_GLOBAL_NOTIFY_CB: Callable[[str, bool, str | None], None] = _default_notify

def set_notification_callback(cb: Callable[[str, bool, str | None], None]):
    """Registers a global notification callback (e.g. Betty companion HUD banner)."""
    global _GLOBAL_NOTIFY_CB
    _GLOBAL_NOTIFY_CB = cb


# -----------------------------------------------------------------------------
# Bookmaker Rules Manager
# -----------------------------------------------------------------------------
RULES_FILE = "bookmaker_rules.json"  # shipped with the program; a shop's own copy next to the exe wins (app_paths.data_file)
# What the engine reads from the active profile. The values live only in bookmaker_rules.json.
REQUIRED_PARAMETERS = ("max_greyhound_traps",)
REQUIRED_STATES = (
    "STATE_FORECAST_NON_EXISTENT_RUNNER", "STATE_FORECAST_DIFFERENT_RACES", "STATE_FORECAST_REPEATED_RUNNER",
    "STATE_FORECAST_LONE_SELECTION", "STATE_FORECAST_UNNAMED_FAVOURITE", "STATE_TRICAST_ONE_NON_RUNNER",
    "STATE_TRICAST_TWO_NON_RUNNERS", "STATE_TRICAST_REPEATED_RUNNER", "STATE_TRICAST_UNNAMED_FAVOURITE",
    "STATE_FAVOURITE_EACH_WAY_REQUESTED", "STATE_MULTIPLE_SAME_RACE_CLASH", "STATE_SLIP_UNINSTRUCTED_SAME_RACE",
    "STATE_SLIP_UNINSTRUCTED_DIFFERENT_RACES", "STATE_UNNAMED_UNTIMED_OR_MISTIMED",
)


class RulesFileError(Exception):
    """bookmaker_rules.json is missing, unreadable, or lacks a rule the engine needs."""


class BookmakerRulesManager:
    """
    The house rules (BetAnsells) from bookmaker_rules.json, the only copy of the rules: nothing is built in, so a
    missing or incomplete file stops the program at start rather than settling on rules nobody can see. The file is
    re-read when edited; an edit that breaks it keeps the rules already loaded (and says so) instead of stopping mid-day.
    """

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or app_paths.data_file(RULES_FILE)
        self.rules: dict = {}
        self._last_mtime = 0.0
        self.load()

    def _read(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise RulesFileError(f"{self.config_path} is missing") from None
        except (OSError, ValueError) as e:
            raise RulesFileError(f"{self.config_path} can't be read ({e})") from None
        if not isinstance(data, dict):
            raise RulesFileError(f"{self.config_path} does not hold a set of rules")
        params = data.get('parameters', {})
        states = data.get('non_normal_states', {})
        missing = ([p for p in REQUIRED_PARAMETERS if p not in params]
                   + [s for s in REQUIRED_STATES if not (states.get(s) or {}).get('action')])
        if missing:
            raise RulesFileError(f"{self.config_path} is missing: {', '.join(missing)}")
        return data

    def load(self):
        """Loads the rules; raises RulesFileError when the file can't supply every rule."""
        mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0.0
        self.rules = self._read()
        self._last_mtime = mtime

    def _check_and_reload_if_modified(self):
        try:
            mtime = os.path.getmtime(self.config_path)
        except OSError:
            return  # file gone mid-day: keep the rules already loaded
        if mtime <= self._last_mtime:
            return
        self._last_mtime = mtime
        try:
            self.rules = self._read()
            print(f"[*] Bookmaker rules reloaded ({self.get_firm_name()}).")
        except RulesFileError as e:
            print(f"[-] {e}: keeping the rules loaded before the edit.")

    def get_rules(self) -> dict:
        """The house rules as loaded (re-read first if the file was edited)."""
        self._check_and_reload_if_modified()
        return self.rules

    def get_firm_name(self) -> str:
        """The firm the rules are for (BetAnsells)."""
        return self.get_rules().get('firm_name', 'BetAnsells')

    def get_parameter(self, param_key: str):
        """A rules parameter (every REQUIRED_PARAMETERS entry is checked at load)."""
        return self.get_rules()['parameters'][param_key]

    def get_state_action(self, state_name: str) -> tuple[str, str]:
        """Returns (action, citation) for a non-normal state (every REQUIRED_STATES entry is checked at load)."""
        cfg = self.get_rules()['non_normal_states'][state_name]
        return cfg['action'].upper(), cfg.get('citation', '')


# Singleton instance
rules_manager = BookmakerRulesManager()
bookmaker_rules_mgr = rules_manager  # Alias for backward compatibility


# -----------------------------------------------------------------------------
# Selection Existence & Legality Check
# -----------------------------------------------------------------------------
def is_selection_existent(horse: dict, runners: list[dict] | None = None, rules_mgr: BookmakerRulesManager | None = None) -> tuple[bool, str]:
    """
    Checks whether a selection represents a legally existent, declared runner or trap
    under the active bookmaker firm's rules.
    Returns: (is_existent: bool, reason: str)
    """
    mgr = rules_mgr or rules_manager
    max_traps = int(mgr.get_parameter("max_greyhound_traps"))
    firm = mgr.get_firm_name()

    name = str(horse.get('name', '')).strip().lower()
    num = horse.get('number')

    # 1. Explicit non-runner / void flag
    if horse.get('is_non_runner') or horse.get('is_void'):
        return False, "Marked as non-runner / void"

    # 2. Greyhound trap validation (max_greyhound_traps in bookmaker_rules.json: UK/IE races have 6, Australian 8)
    is_dog, trap_num, _ = is_greyhound_or_trap_selection(horse)
    effective_trap = trap_num if trap_num is not None else (num if isinstance(num, int) else None)
    # A selection written as a bare number is a trap only when it's a dog: horse number 12 is no 'Trap 12' (review R25)
    if is_dog or (effective_trap is not None and 'trap' in name):
        if effective_trap is not None and (effective_trap < 1 or effective_trap > max_traps):
            return False, f"Trap {effective_trap} does not exist ({firm}: greyhound races have at most {max_traps} traps)"

    # 3. Horse racecard cloth number validation (Rule 1.8.4)
    if runners and not is_dog:
        ev_key = get_horse_event_key(horse)
        race_runners = [
            r for r in runners
            if str(r.get('meeting', '')).strip().lower() == ev_key[0]
            and (str(r.get('time_str', '')).strip() == ev_key[1] or str(r.get('time', '')).strip() == ev_key[1])
        ]
        if race_runners:
            if num is not None and isinstance(num, int):
                declared_numbers = [r.get('number') for r in race_runners if r.get('number') is not None]
                if declared_numbers and num not in declared_numbers:
                    return False, f"Racecard #{num} does not appear in the {ev_key[1]} at {ev_key[0].title()} (non-runner)"

    return True, "Valid"


# -----------------------------------------------------------------------------
# Related Contingency Engine (Same-Race Multiples)
# -----------------------------------------------------------------------------
# Full covers: every single, double ... up to the accumulator, so a clash is split into whole bets of the same type
FULL_COVER_TYPES = {'trixie', 'patent', 'yankee', 'lucky 15', 'canadian', 'super yankee', 'lucky 31', 'heinz',
                    'lucky 63', 'super heinz', 'goliath'}
VOID_RACE_FEEDS = ('HGB00', 'BFTRP')  # SIS and TRP horses: a void selection's race comes from these when it can


def void_selections_for_split(runners: list[dict] | None, taken: set, k: int) -> list[dict]:
    """
    k void selections, each in its own UK/IRE horse race not in `taken` (the bet's races), for a full cover split by a
    same-race clash (user, 27 Oct: "any not already on the betslip"). The day's last races are used: they are still to
    run when the bet is entered, so Betty asks no late-selection question. [] when k such races aren't on the card.
    """
    races: dict[tuple, dict] = {}
    for r in runners or []:
        if r.get('category') != 'domestic' or not r.get('time_str') or not r.get('meeting'):
            continue
        key = get_horse_event_key({'meeting': r['meeting'], 'time': r['time_str']})
        if key not in taken:
            races.setdefault(key, r)
    ranked = sorted(races.values(), key=lambda r: (r.get('feed') not in VOID_RACE_FEEDS, -(r.get('minutes') or 0)))[:k]
    if len(ranked) < k:
        return []
    return [{'name': 'Void Selection', 'meeting': r['meeting'], 'time': r['time_str'], 'number': None, 'void': True,
             'category': 'domestic', 'feed': r.get('feed'), 'price': 'SP'} for r in ranked]


def split_clashed_full_cover(bet: dict, b_type: str, event_map: dict, runners: list[dict] | None) -> list[dict]:
    """
    A full cover (Lucky 31, Yankee, ...) with runners in the same race (user, 27 Oct, 9.2453976): one bet of the same
    type for each way of taking one runner per race, at the stake divided equally between them, the runners left out
    each replaced by a void selection in a race of its own. Lucky 31 10p e/w with Cayenne and Mon Missel both in the
    Newcastle 4.01 = two Lucky 31s 5p e/w, one with Cayenne and a void selection, the other with a void and Mon Missel.
    [] when no void races can be found (the bet is then left to the split below and staff).
    """
    horses, stake = bet.get('horses', []), int(bet.get('stake_pence') or 0)
    combos = list(itertools.product(*event_map.values()))
    left_out = len(horses) - len(event_map)
    voids = void_selections_for_split(runners, set(event_map), left_out)
    if not voids:
        return []
    out = []
    for kept in combos:
        spare = iter(voids)
        chosen = [h if any(h is k for k in kept) else next(spare) for h in horses]
        out.append({'bet_type': b_type,
                    # Never the clashed bet's own words: normalize_bet_type reads the description
                    'description': f"{b_type.title()} on {', '.join(str(h.get('name')) for h in chosen)} (same-race clash split)",
                    'horses': chosen, 'stake_pence': stake // len(combos), 'each_way': bool(bet.get('each_way')),
                    'clash_split_from': b_type})
    return out


def resolve_same_race_contingencies(
    slip_data: list[dict],
    notify_cb: Callable[[str, bool, str | None], None] | None = None,
    runners: list[dict] | None = None
) -> list[dict]:
    """
    UK Betting Shop Rule (Tattersalls Rules & BetAnsells Rule 1.8.1) for Same-Race Multiples:
    When two or more horses in the same race appear in a multiple bet (Doubles or higher),
    the bet cannot be struck as a related multiple. The bet is automatically split into
    lower accumulators / singles across the clashed runners at an equally divided unit stake.
    """
    notify = notify_cb or _GLOBAL_NOTIFY_CB
    resolved_bets: list[dict] = []

    for bet in slip_data:
        horses = bet.get('horses', [])
        stake = int(bet.get('stake_pence') or 0)
        each_way = bool(bet.get('each_way', False))
        desc = str(bet.get('description', ''))
        raw_text = str(bet.get('raw_text', ''))
        combined_desc = f"{desc} {raw_text}".lower()
        # Canonical type (e.g. 'doubles' + 'R/FORECAST ... X DOUBS' = reversed forecast double, which never clashes)
        b_type = normalize_bet_type(str(bet.get('bet_type', 'single')), combined_desc, selection_names(bet))

        # Singles, bets with <= 1 horse, or Forecast/Tricast bets cannot clash
        if len(horses) <= 1 or b_type == 'single' or 'forecast' in b_type or 'tricast' in b_type or 'fc' in b_type:
            resolved_bets.append(bet)
            continue

        # Group horses by their distinct race event (meeting, time)
        event_map: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for h in horses:
            ev_key = get_horse_event_key(h)
            event_map[ev_key].append(h)

        has_clash = any(len(h_list) > 1 for h_list in event_map.values())
        if not has_clash:
            # All horses run in distinct races - completely valid multiple
            resolved_bets.append(bet)
            continue

        # IDENTIFIED SAME-RACE CLASH!
        clashed_events = [ev for ev, h_list in event_map.items() if len(h_list) > 1]
        print(f"\n[!] Related Contingency Detected in {b_type.upper()} ({stake}p, EW={each_way}):")
        for ev in clashed_events:
            clashed_names = [h.get('name') for h in event_map[ev]]
            print(f"    - Same race at {ev[0].title()} ({ev[1]}): {clashed_names}")

        # CASE A0: Cross Doubles (e.g. '4x 50 WIN x DOUBLES' on 2 runners in each of 2 races).
        # 'x doubles' / 'cross doubles' means every double across DIFFERENT races, so same-race pairs
        # are never part of the bet. The same applies when the written multiplier equals the number of
        # valid different-race pairs. Kept as ONE Doubles bet over all selections (Betty only strikes
        # the valid pairs); no half-stake singles are created.
        valid_pairs = count_distinct_race_combos(horses, 2) or 0
        m_mult = re.search(r'\b(\d+)\s*x\b', combined_desc)
        is_cross_double = 'double' in b_type and len(horses) >= 3 and valid_pairs > 0 and (
            bool(re.search(r'\b(?:x|cross)\s*doub', combined_desc))
            or (m_mult is not None and int(m_mult.group(1)) == valid_pairs)
        )
        if is_cross_double:
            print(f"    -> Cross Doubles: {valid_pairs} valid different-race double(s) @ {stake}p; same-race pairs excluded (not split).")
            resolved_bets.append(bet)
            continue

        # CASE A: Combination Doubles (e.g. '3 x 50 WIN DOUB', '6 x DOUBLES')
        is_comb_double = ('double' in b_type and ('3 x' in combined_desc or '3x' in combined_desc or '6 x' in combined_desc or '6x' in combined_desc or len(horses) >= 3))
        if is_comb_double and len(horses) >= 3:
            pairs = list(itertools.combinations(horses, 2))
            clashed_pairs_count = 0
            for h1, h2 in pairs:
                ev1 = get_horse_event_key(h1)
                ev2 = get_horse_event_key(h2)
                if ev1 != ev2:
                    # Valid double across 2 distinct races
                    resolved_bets.append({
                        'bet_type': 'double',
                        'description': f"Double on {h1.get('name')} & {h2.get('name')}",
                        'horses': [h1, h2],
                        'stake_pence': stake,
                        'each_way': each_way
                    })
                    print(f"    -> Preserved valid Double: {h1.get('name')} & {h2.get('name')} @ {stake}p")
                else:
                    clashed_pairs_count += 1
                    # Clashed pair in same race -> split into two singles at half stake
                    split_stake = max(1, round(stake / 2))
                    resolved_bets.append({
                        'bet_type': 'single',
                        'description': f"Single on {h1.get('name')} (same-race pair split)",
                        'horses': [h1],
                        'stake_pence': split_stake,
                        'each_way': each_way
                    })
                    resolved_bets.append({
                        'bet_type': 'single',
                        'description': f"Single on {h2.get('name')} (same-race pair split)",
                        'horses': [h2],
                        'stake_pence': split_stake,
                        'each_way': each_way
                    })
                    print(f"    -> Split clashed Double into 2x Singles @ {split_stake}p: {h1.get('name')}, {h2.get('name')}")
            if notify and clashed_pairs_count > 0:
                notify(f"Same-race clash in Combination Doubles: {clashed_pairs_count} pair(s) split into {clashed_pairs_count * 2}x Singles @ {max(1, round(stake / 2))}p.", False, "#E65100")
            continue

        # CASE F: Full covers keep their type, one bet per clashed runner with void selections (user, 27 Oct). As a
        # plain multiple below, a Lucky 31 became Perm 4-Folds @ 5p: 620p paid, 20p of bets (9.2453976).
        if b_type in FULL_COVER_TYPES:
            split = split_clashed_full_cover(bet, b_type, event_map, runners)
            if split:
                n, unit = len(split), split[0]['stake_pence']
                if stake % n:
                    print(f"    [!] {stake}p does not divide equally into {n} bets: check the stake.")
                voids = sorted({f"{v.get('meeting')} {v.get('time')}" for b in split for v in b['horses'] if v.get('void')})
                print(f"    -> Split into {n} {b_type.title()}s @ {unit}p (EW={each_way}), one per runner in the same race; "
                      f"the others void selections ({', '.join(voids)}).")
                for b in split:
                    print(f"       {b_type.title()}: {', '.join(str(h.get('name')) for h in b['horses'])}")
                resolved_bets.extend(split)
                if notify:
                    notify(f"Same-race clash in {b_type.upper()}: {n} {b_type.title()}s @ {unit}p with void selections.",
                           False, "#E65100")
                continue
            print("    [!] No UK/IRE race free for the void selections: left for staff.")

        # CASE B: Standard Multiples (Single Double, Treble, Accumulator)
        distinct_events = list(event_map.keys())
        num_distinct_races = len(distinct_events)

        event_runner_lists = [event_map[ev] for ev in distinct_events]
        combinations = list(itertools.product(*event_runner_lists))
        num_comb = len(combinations)
        split_stake = max(1, round(stake / num_comb))

        if num_distinct_races == 1:
            target_btype = 'single'
        elif num_distinct_races == 2:
            target_btype = 'double'
        elif num_distinct_races == 3:
            target_btype = 'treble'
        else:
            target_btype = 'accumulator'

        # Preferred Betty entry: ONE permed bet over ALL selections at the divided stake
        # (e.g. clashed 6-fold @ 50p -> 'Perm 5-Folds' @ 25p; Betty strikes only the valid 5-folds,
        # 'Acc On All Selns' cannot be chosen). Only possible when the stake divides into whole pence.
        if num_distinct_races >= 2 and num_comb > 1 and stake % num_comb == 0:
            perm_btype = target_btype if num_distinct_races <= 3 else f"perm {num_distinct_races}-folds"
            perm_stake = stake // num_comb
            perm_bet = {
                'bet_type': perm_btype,
                # Description must not repeat the original type name: normalize_bet_type reads it.
                'description': f"{perm_btype.title()} on all {len(horses)} selections (same-race clash; {num_comb} valid lines)",
                'horses': list(horses),
                'stake_pence': perm_stake,
                'each_way': each_way,
                'clash_split_from': b_type,
            }
            resolved_bets.append(perm_bet)
            print(f"    -> Converted to {perm_btype.title()} @ {perm_stake}p over all {len(horses)} selections ({num_comb} valid lines, total {perm_stake * num_comb * (2 if each_way else 1)}p).")
            if notify:
                notify(f"Same-race clash in {b_type.upper()}: entered as {perm_btype.title()} @ {perm_stake}p ({num_comb} lines).", False, "#E65100")
            continue

        if stake % num_comb != 0:
            print(f"    [!] {stake}p does not divide equally into {num_comb} lines; splitting into separate bets @ {split_stake}p. Check stake manually.")

        for comb in combinations:
            comb_horses = list(comb)
            h_names = " & ".join([str(h.get('name', '')) for h in comb_horses])
            resolved_bets.append({
                'bet_type': target_btype,
                # Never the clashed bet's own type: normalize_bet_type reads the description ('split from clashed
                # double' turned these singles back into doubles at entry)
                'description': f"{target_btype.title()} on {h_names} (same-race clash split)",
                'horses': comb_horses,
                'stake_pence': split_stake,
                'each_way': each_way
            })
            print(f"    -> Created split {target_btype.title()} ({split_stake}p, EW={each_way}): {h_names}")

        if notify:
            notify(f"Same-race clash in {b_type.upper()}: auto-corrected to {num_comb}x {target_btype.title()} @ {split_stake}p.", False, "#E65100")

    return resolved_bets


# -----------------------------------------------------------------------------
# Discrepancy Settlement & Non-Normal State Dispatcher
# -----------------------------------------------------------------------------
def resolve_discrepancies(
    slip_data: list[dict],
    runners: list[dict] | None = None,
    rules_mgr: BookmakerRulesManager | None = None,
    notify_cb: Callable[[str, bool, str | None], None] | None = None
) -> list[dict]:
    """
    Discrepancy resolution: applies the house rules' settlement actions for non-normal states (BetAnsells).
    """
    mgr = rules_mgr or rules_manager
    firm = mgr.get_firm_name()
    notify = notify_cb or _GLOBAL_NOTIFY_CB
    first_pass_bets: list[dict] = []

    for bet in slip_data:
        horses = bet.get('horses', [])
        b_type = normalize_bet_type(str(bet.get('bet_type', 'single')), str(bet.get('description', '')),
                                    selection_names(bet))
        stake = int(bet.get('stake_pence') or 0)  # read as empty (null): no stake, not a crash (review R24)
        each_way = bool(bet.get('each_way', False))
        total_cost = calculate_bet_cost_pence(bet)

        # -------------------------------------------------------------
        # 1. STATE_FAVOURITE_EACH_WAY_REQUESTED
        # -------------------------------------------------------------
        if each_way and any(is_unnamed_favourite(h) for h in horses):
            act, cite = mgr.get_state_action("STATE_FAVOURITE_EACH_WAY_REQUESTED")
            cite_str = f" ({cite})" if cite else ""
            if act in ["VOID_PLACE_ELEMENT_SETTLE_WIN_ONLY", "VOID_PLACE_ELEMENT"]:
                fav_names = [h.get('name') for h in horses if is_unnamed_favourite(h)]
                # Entered each way as written and paid: Betty voids the place part and refunds it when it settles.
                # Made win only here, the bet no longer cost what was paid and always went to staff (review R11).
                print(f"\n[!] {firm} House Rules{cite_str}: Unnamed favourite ({fav_names}) is Win-Only.")
                print("    -> Entered each way as written; the place part is void and Betty refunds it at settlement.")
                notify(f"{firm} Rules{cite_str}: Favourites ({', '.join(fav_names)}) are Win-Only: the EW place part is "
                       "void at settlement.", False, "#E65100")

        # -------------------------------------------------------------
        # 2. UNINSTRUCTED SLIPS
        # -------------------------------------------------------------
        if b_type in ['', 'unknown', 'none', 'uninstructed'] and len(horses) >= 2:
            evs = [get_horse_event_key(h) for h in horses]

            # 2a. Same Race Uninstructed
            if len(horses) == 2 and evs[0] == evs[1]:
                act, cite = mgr.get_state_action("STATE_SLIP_UNINSTRUCTED_SAME_RACE")
                cite_str = f" ({cite})" if cite else ""
                if act in ["SETTLE_AS_STRAIGHT_FORECAST", "STRAIGHT_FORECAST"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: 2 selections in same race with no instructions -> Straight Forecast.")
                    bet['bet_type'] = 'straight forecast'
                    b_type = 'straight forecast'
                    first_pass_bets.append(bet)
                    continue
                elif act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Uninstructed slip in same race is void.")
                    notify(f"{firm} Rules{cite_str}: Uninstructed bet voided.", True, None)
                    continue

            # 2b. Different Races Uninstructed
            elif len(set(evs)) > 1:
                act, cite = mgr.get_state_action("STATE_SLIP_UNINSTRUCTED_DIFFERENT_RACES")
                cite_str = f" ({cite})" if cite else ""
                if act in ["SPLIT_INTO_EQUAL_WIN_SINGLES", "SPLIT_SINGLES"]:
                    split_unit = max(1, round(stake / len(horses)))
                    print(f"\n[!] {firm} House Rules{cite_str}: Uninstructed slip across multiple races -> Split into {len(horses)}x {split_unit}p Win Singles.")
                    for h in horses:
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {h.get('name')} ({firm} uninstructed split)",
                            'horses': [h],
                            'stake_pence': split_unit,
                            'each_way': each_way
                        })
                    continue
                elif act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Uninstructed slip across different races is void.")
                    notify(f"{firm} Rules{cite_str}: Uninstructed bet voided.", True, None)
                    continue

        # -------------------------------------------------------------
        # 3. FORECAST DISCREPANCIES
        # -------------------------------------------------------------
        is_fc = any(ft in b_type for ft in ['forecast', 'r/f', 'sfc', 'rfc', 'cfc']) or b_type == 'fc'
        if is_fc:
            # 3a. Unnamed favourites in forecast
            if any(is_unnamed_favourite(h) for h in horses):
                act, cite = mgr.get_state_action("STATE_FORECAST_UNNAMED_FAVOURITE")
                cite_str = f" ({cite})" if cite else ""
                if act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Unnamed favourite in Forecast. Forecast is void.")
                    notify(f"{firm} Rules{cite_str}: Forecast with unnamed favourite is void.", True, None)
                    continue

            # 3b. Selections in different races
            if len(horses) == 2:
                ev1 = get_horse_event_key(horses[0])
                ev2 = get_horse_event_key(horses[1])
                if ev1 != ev2:
                    act, cite = mgr.get_state_action("STATE_FORECAST_DIFFERENT_RACES")
                    cite_str = f" ({cite})" if cite else ""
                    if act in ["SPLIT_INTO_HALF_STAKE_SINGLES", "SPLIT_HALF_STAKE_SINGLES"]:
                        half_stake = max(1, round(total_cost / 2))
                        print(f"\n[!] {firm} House Rules{cite_str}: Forecast selections run in different races:")
                        print(f"    - {horses[0].get('name')} ({ev1[0].title()} {ev1[1]})")
                        print(f"    - {horses[1].get('name')} ({ev2[0].title()} {ev2[1]})")
                        print(f"    -> Split into 2x {half_stake}p Win Singles (total {total_cost}p conserved).")
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {horses[0].get('name')} ({firm} split from different-race forecast)",
                            'horses': [horses[0]],
                            'stake_pence': half_stake,
                            'each_way': False
                        })
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {horses[1].get('name')} ({firm} split from different-race forecast)",
                            'horses': [horses[1]],
                            'stake_pence': half_stake,
                            'each_way': False
                        })
                        notify(f"{firm} Rules{cite_str}: Forecast across different races split into 2x {half_stake}p Singles.", False, "#E65100")
                        continue
                    elif act in ["VOID_BET", "VOID"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Forecast across different races is void.")
                        notify(f"{firm} Rules{cite_str}: Different-race forecast voided.", True, None)
                        continue

            # 3c. Repeated selection in forecast
            if len(horses) >= 2:
                h_names = [clean_horse_name(str(h.get('name', ''))) for h in horses]
                h_nums = [h.get('number') for h in horses]
                all_same = (len(set(h_names)) == 1) or (h_nums[0] is not None and len(set(h_nums)) == 1)
                if all_same:
                    act, cite = mgr.get_state_action("STATE_FORECAST_REPEATED_RUNNER")
                    cite_str = f" ({cite})" if cite else ""
                    if act in ["CONVERT_TO_WIN_SINGLE_FULL_STAKE", "SINGLE_FULL_STAKE"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Repeated selection '{horses[0].get('name')}' in Forecast.")
                        print(f"    -> Settled as Win Single at full forecast stake ({total_cost}p).")
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {horses[0].get('name')} ({firm} repeated forecast)",
                            'horses': [horses[0]],
                            'stake_pence': total_cost,
                            'each_way': False
                        })
                        notify(f"{firm} Rules{cite_str}: Repeated forecast converted to {total_cost}p Single.", False, "#E65100")
                        continue
                    elif act in ["VOID_BET", "VOID"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Repeated forecast is void.")
                        notify(f"{firm} Rules{cite_str}: Repeated forecast voided.", True, None)
                        continue

            # 3d. Lone selection in forecast
            if len(horses) == 1:
                act, cite = mgr.get_state_action("STATE_FORECAST_LONE_SELECTION")
                cite_str = f" ({cite})" if cite else ""
                if act in ["CONVERT_TO_WIN_SINGLE_FULL_STAKE", "SINGLE_FULL_STAKE"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Lone selection '{horses[0].get('name')}' specified in Forecast.")
                    print(f"    -> Settled as Win Single at full forecast stake ({total_cost}p).")
                    first_pass_bets.append({
                        'bet_type': 'single',
                        'description': f"Single on {horses[0].get('name')} ({firm} lone forecast selection)",
                        'horses': [horses[0]],
                        'stake_pence': total_cost,
                        'each_way': False
                    })
                    notify(f"{firm} Rules{cite_str}: Lone forecast converted to {total_cost}p Single.", False, "#E65100")
                    continue
                elif act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Lone forecast selection is void.")
                    notify(f"{firm} Rules{cite_str}: Lone forecast voided.", True, None)
                    continue

            # 3e. Non-existent runner / non-runner / invalid number in forecast
            valid_horses = []
            invalid_info = []
            for h in horses:
                is_ex, reason = is_selection_existent(h, runners, rules_mgr=mgr)
                if is_ex:
                    valid_horses.append(h)
                else:
                    invalid_info.append((h.get('name', f"#{h.get('number')}"), reason))

            if invalid_info:
                act, cite = mgr.get_state_action("STATE_FORECAST_NON_EXISTENT_RUNNER")
                cite_str = f" ({cite})" if cite else ""
                if len(valid_horses) == 1:
                    rem_h = valid_horses[0]
                    inv_desc = ", ".join([f"{n} ({r})" for n, r in invalid_info])
                    if act in ["CONVERT_TO_WIN_SINGLE_FULL_STAKE", "SINGLE_FULL_STAKE"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Forecast contains non-existent selection(s): {inv_desc}.")
                        print(f"    -> Converted to Win Single on '{rem_h.get('name')}' at full forecast stake ({total_cost}p).")
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {rem_h.get('name')} ({firm} converted from forecast; non-existent {inv_desc})",
                            'horses': [rem_h],
                            'stake_pence': total_cost,
                            'each_way': False
                        })
                        notify(f"{firm} Rules{cite_str}: Invalid runner in Forecast. Converted to {total_cost}p Single on {rem_h.get('name')}.", False, "#E65100")
                        continue
                    elif act in ["CONVERT_TO_WIN_SINGLE_UNIT_STAKE", "SINGLE_UNIT_STAKE"]:
                        u_stake = int(bet.get('stake_pence') or 0)
                        print(f"\n[!] {firm} House Rules{cite_str}: Forecast contains non-existent selection(s): {inv_desc}.")
                        print(f"    -> Converted to Win Single on '{rem_h.get('name')}' at unit stake ({u_stake}p).")
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Single on {rem_h.get('name')} ({firm} converted at unit stake)",
                            'horses': [rem_h],
                            'stake_pence': u_stake,
                            'each_way': False
                        })
                        notify(f"{firm} Rules{cite_str}: Converted to {u_stake}p Single on {rem_h.get('name')}.", False, "#E65100")
                        continue
                    elif act in ["VOID_BET", "VOID"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Forecast with non-runner/non-existent selection is void.")
                        notify(f"{firm} Rules{cite_str}: Forecast voided.", True, None)
                        continue

                elif len(valid_horses) == 0:
                    if act != "ENTER_AS_WRITTEN_BETTY_SETTLES":
                        print(f"\n[!] {firm} House Rules{cite_str}: All selections in Forecast are non-existent. Bet is void.")
                        notify(f"{firm} Rules{cite_str}: All forecast selections non-existent. Bet void.", True, None)
                        continue
                    # As for one invalid selection: entered as written (void selections), Betty settles (review R10)
                    print(f"\n[!] {firm} House Rules{cite_str}: No selection in this Forecast is on the card. Entered as "
                          "written; Betty settles.")

            first_pass_bets.append(bet)
            continue

        # -------------------------------------------------------------
        # 4. TRICAST DISCREPANCIES
        # -------------------------------------------------------------
        is_tri = any(tt in b_type for tt in ['tricast', 'stc', 'ctc'])
        if is_tri:
            # 4a. Unnamed favourites in tricast
            if any(is_unnamed_favourite(h) for h in horses):
                act, cite = mgr.get_state_action("STATE_TRICAST_UNNAMED_FAVOURITE")
                cite_str = f" ({cite})" if cite else ""
                if act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Unnamed favourite in Tricast. Tricast is void.")
                    notify(f"{firm} Rules{cite_str}: Tricast with unnamed favourite is void.", True, None)
                    continue

            # 4b. Check for non-existent runners / non-runners
            valid_horses = []
            invalid_info = []
            for h in horses:
                is_ex, reason = is_selection_existent(h, runners, rules_mgr=mgr)
                if is_ex:
                    valid_horses.append(h)
                else:
                    invalid_info.append((h.get('name', f"#{h.get('number')}"), reason))

            if invalid_info:
                inv_desc = ", ".join([f"{n} ({r})" for n, r in invalid_info])
                if len(valid_horses) == 2:
                    act, cite = mgr.get_state_action("STATE_TRICAST_ONE_NON_RUNNER")
                    cite_str = f" ({cite})" if cite else ""
                    if act in ["CONVERT_TO_STRAIGHT_FORECAST_FULL_STAKE", "STRAIGHT_FORECAST_FULL_STAKE"]:
                        is_comb_tri = ('combination' in b_type or 'ctc' in b_type)
                        if is_comb_tri:
                            rf_stake = max(1, round(total_cost / 2))
                            print(f"\n[!] {firm} House Rules{cite_str}: 1 non-existent selection ({inv_desc}) in Combination Tricast.")
                            print(f"    -> Converted to Reversed Forecast on {[h.get('name') for h in valid_horses]} @ {rf_stake}p unit stake (total {total_cost}p).")
                            first_pass_bets.append({
                                'bet_type': 'reversed forecast',
                                'description': f"Reversed Forecast on {valid_horses[0].get('name')} & {valid_horses[1].get('name')} ({firm} from Comb Tricast)",
                                'horses': valid_horses,
                                'stake_pence': rf_stake,
                                'each_way': False
                            })
                            notify(f"{firm} Rules{cite_str}: Comb Tricast converted to Reversed Forecast on {[h.get('name') for h in valid_horses]}.", False, "#E65100")
                        else:
                            print(f"\n[!] {firm} House Rules{cite_str}: 1 non-existent selection ({inv_desc}) in Straight Tricast.")
                            print(f"    -> Converted to Straight Forecast on {valid_horses[0].get('name')} & {valid_horses[1].get('name')} @ full stake ({total_cost}p).")
                            first_pass_bets.append({
                                'bet_type': 'straight forecast',
                                'description': f"Straight Forecast on {valid_horses[0].get('name')} & {valid_horses[1].get('name')} ({firm} from Tricast)",
                                'horses': valid_horses,
                                'stake_pence': total_cost,
                                'each_way': False
                            })
                            notify(f"{firm} Rules{cite_str}: Tricast converted to Straight Forecast on {[h.get('name') for h in valid_horses]}.", False, "#E65100")
                        continue
                    elif act in ["VOID_BET", "VOID"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Tricast with non-runner is void.")
                        notify(f"{firm} Rules{cite_str}: Tricast voided.", True, None)
                        continue

                elif len(valid_horses) == 1:
                    act, cite = mgr.get_state_action("STATE_TRICAST_TWO_NON_RUNNERS")
                    cite_str = f" ({cite})" if cite else ""
                    if act in ["CONVERT_TO_SP_WIN_SINGLE_FULL_STAKE", "SINGLE_FULL_STAKE_SP"]:
                        rem_h = valid_horses[0]
                        rem_h['price'] = 'SP'
                        print(f"\n[!] {firm} House Rules{cite_str}: 2 non-existent selections ({inv_desc}) in Tricast.")
                        print(f"    -> Converted to Win Single at SP on '{rem_h.get('name')}' @ full stake ({total_cost}p).")
                        first_pass_bets.append({
                            'bet_type': 'single',
                            'description': f"Win Single at SP on {rem_h.get('name')} ({firm}: 2 non-runners)",
                            'horses': [rem_h],
                            'stake_pence': total_cost,
                            'each_way': False
                        })
                        notify(f"{firm} Rules{cite_str}: Tricast with 2 non-runners converted to {total_cost}p Single on {rem_h.get('name')}.", False, "#E65100")
                        continue
                    elif act in ["VOID_BET", "VOID"]:
                        print(f"\n[!] {firm} House Rules{cite_str}: Tricast with 2 non-runners is void.")
                        notify(f"{firm} Rules{cite_str}: Tricast voided.", True, None)
                        continue

                elif len(valid_horses) == 0:
                    act, cite = mgr.get_state_action("STATE_TRICAST_TWO_NON_RUNNERS")
                    cite_str = f" ({cite})" if cite else ""
                    if act != "ENTER_AS_WRITTEN_BETTY_SETTLES":
                        print(f"\n[!] {firm} House Rules{cite_str}: All selections in Tricast non-existent. Bet is void.")
                        notify(f"{firm} Rules{cite_str}: All tricast selections non-existent. Bet void.", True, None)
                        continue
                    # As for one or two invalid selections: entered as written, Betty settles (review R10)
                    print(f"\n[!] {firm} House Rules{cite_str}: No selection in this Tricast is on the card. Entered as "
                          "written; Betty settles.")

            # 4c. Repeated selection in tricast
            unique_h = []
            seen = set()
            for h in horses:
                c_name = clean_horse_name(str(h.get('name', '')))
                if c_name not in seen:
                    seen.add(c_name)
                    unique_h.append(h)
            if len(unique_h) == 2 and len(horses) == 3:
                act, cite = mgr.get_state_action("STATE_TRICAST_REPEATED_RUNNER")
                cite_str = f" ({cite})" if cite else ""
                if act in ["CONVERT_TO_STRAIGHT_FORECAST_FULL_STAKE", "STRAIGHT_FORECAST_FULL_STAKE"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Repeated selection in Tricast.")
                    print(f"    -> Converted to Straight Forecast on {unique_h[0].get('name')} & {unique_h[1].get('name')} @ full stake ({total_cost}p).")
                    first_pass_bets.append({
                        'bet_type': 'straight forecast',
                        'description': f"Straight Forecast on {unique_h[0].get('name')} & {unique_h[1].get('name')} ({firm} repeated tricast)",
                        'horses': unique_h,
                        'stake_pence': total_cost,
                        'each_way': False
                    })
                    notify(f"{firm} Rules{cite_str}: Repeated Tricast converted to Forecast on {[h.get('name') for h in unique_h]}.", False, "#E65100")
                    continue
                elif act in ["VOID_BET", "VOID"]:
                    print(f"\n[!] {firm} House Rules{cite_str}: Repeated tricast is void.")
                    notify(f"{firm} Rules{cite_str}: Repeated tricast voided.", True, None)
                    continue

            first_pass_bets.append(bet)
            continue

        first_pass_bets.append(bet)

    # -------------------------------------------------------------
    # 5. STATE_MULTIPLE_SAME_RACE_CLASH (RELATED CONTINGENCIES)
    # -------------------------------------------------------------
    act, cite = mgr.get_state_action("STATE_MULTIPLE_SAME_RACE_CLASH")
    if act in ["SPLIT_INTO_LOWER_ACCUMULATORS", "SPLIT_LOWER_ACCUMULATORS"]:
        final_bets = resolve_same_race_contingencies(first_pass_bets, notify_cb=notify, runners=runners)
    else:
        final_bets = first_pass_bets

    return final_bets


# -----------------------------------------------------------------------------
# Backward-compatibility Aliases
# -----------------------------------------------------------------------------
resolve_bookmaker_discrepancies = resolve_discrepancies
