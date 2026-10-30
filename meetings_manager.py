"""
Meetings Directory Manager for Betty Companion
==============================================
Centralized manager for covered race meetings, virtual tracks, greyhound courses,
and international tracks. Supports dynamic hot-reloading from meetings_directory.json
without requiring application restarts.
"""

import os
import json
import re
from difflib import get_close_matches
from typing import Any


# Core Irish & UK racecourses guaranteed fallback to prevent accidental greyhound misclassification
DEFAULT_DOMESTIC_HORSE_COURSES = {
    # Ireland
    "listowel": "Listowel",
    "curragh": "Curragh",
    "leopardstown": "Leopardstown",
    "punchestown": "Punchestown",
    "galway": "Galway",
    "fairyhouse": "Fairyhouse",
    "cork": "Cork",
    "navan": "Navan",
    "naas": "Naas",
    "gowran": "Gowran Park",
    "gowranpark": "Gowran Park",
    "tipperary": "Tipperary",
    "dundalk": "Dundalk",
    "downroyal": "Down Royal",
    "downpatrick": "Downpatrick",
    "limerick": "Limerick",
    "sligo": "Sligo",
    "clonmel": "Clonmel",
    "tramore": "Tramore",
    "ballinrobe": "Ballinrobe",
    "roscommon": "Roscommon",
    "killarney": "Killarney",
    "bellewstown": "Bellewstown",
    "laytown": "Laytown",
    "thurles": "Thurles",
    "wexford": "Wexford",
    # Common UK tracks prone to misclassification
    "ascot": "Ascot",
    "newbury": "Newbury",
    "newmarket": "Newmarket",
    "cheltenham": "Cheltenham",
    "aintree": "Aintree",
    "york": "York",
    "chester": "Chester",
    "haydock": "Haydock",
    "sandown": "Sandown",
    "kempton": "Kempton",
    "kemp": "Kempton",
    "lingfield": "Lingfield",
    "ling": "Lingfield",
    "southwell": "Southwell",
    "sout": "Southwell",
    "isout": "Southwell",
    "lsout": "Southwell",
    "wolverhampton": "Wolverhampton",
    "wolves": "Wolverhampton",
    "wolv": "Wolverhampton",
    "wow": "Wolverhampton",
    "woy": "Wolverhampton",
    "woly": "Wolverhampton",
    "wol": "Wolverhampton",
    "wov": "Wolverhampton",
    "wlv": "Wolverhampton",
    "wolver": "Wolverhampton",
    "wolverh": "Wolverhampton",
    "folv": "Wolverhampton",
    "olv": "Wolverhampton",
    "oly": "Wolverhampton",
    "jon": "Wolverhampton",
    "iwolv": "Wolverhampton",
    "lwolv": "Wolverhampton",
    "1wolv": "Wolverhampton",
    "iwow": "Wolverhampton",
    "lwow": "Wolverhampton",
    "1wow": "Wolverhampton",
    "iwoy": "Wolverhampton",
    "lwoy": "Wolverhampton",
    "1woy": "Wolverhampton",
    "woiv": "Wolverhampton",
    "wo1v": "Wolverhampton",
    "wo1": "Wolverhampton",
    "newcastle": "Newcastle",
    "newc": "Newcastle",
    "pontefract": "Pontefract",
    "pont": "Pontefract",
    "fontwell": "Fontwell",
    "font": "Fontwell",
    "beverley": "Beverley",
    "beve": "Beverley",
    "sedgefield": "Sedgefield",
    "sedg": "Sedgefield",
    "sedge": "Sedgefield",
    "ayr": "Ayr",
    "yr": "Ayr",
    "yt": "Ayr",
    "ay": "Ayr",
    "ayer": "Ayr",
    "ayre": "Ayr",
    "marketrasen": "Market Rasen",
    "market rasen": "Market Rasen",
    "mark": "Market Rasen",
    "markr": "Market Rasen",
    "mark r": "Market Rasen",
    "mktr": "Market Rasen",
    "mkt rasen": "Market Rasen",
    "mkt": "Market Rasen",
    "mr": "Market Rasen",
    "doncaster": "Doncaster",
    "donc": "Doncaster",
    "don": "Doncaster",
    "chepstow": "Chepstow",
    "chep": "Chepstow",
    "brighton": "Brighton",
    "brig": "Brighton",
    "carlisle": "Carlisle",
    "carl": "Carlisle",
    "cartmel": "Cartmel",
    "cart": "Cartmel",
    "catterick": "Catterick",
    "catt": "Catterick",
    "epsom": "Epsom",
    "eps": "Epsom",
    "ffoslas": "Ffos Las",
    "ffos las": "Ffos Las",
    "ffos": "Ffos Las",
    "goodwood": "Goodwood",
    "good": "Goodwood",
    "hamilton": "Hamilton",
    "ham": "Hamilton",
    "hereford": "Hereford",
    "here": "Hereford",
    "hexham": "Hexham",
    "hex": "Hexham",
    "huntingdon": "Huntingdon",
    "hunt": "Huntingdon",
    "kelso": "Kelso",
    "kel": "Kelso",
    "leicester": "Leicester",
    "leic": "Leicester",
    "ludlow": "Ludlow",
    "lud": "Ludlow",
    "musselburgh": "Musselburgh",
    "muss": "Musselburgh",
    "newtonabbot": "Newton Abbot",
    "newton abbot": "Newton Abbot",
    "newt": "Newton Abbot",
    "na": "Newton Abbot",  # 'N/A' or 'NA' as written (keys here are compared cleaned: letters and digits only)
    "newa": "Newton Abbot",  # 'New A'
    "nottingham": "Nottingham",
    "nott": "Nottingham",
    "perth": "Perth",
    "pert": "Perth",
    "per": "Perth",
    "plumpton": "Plumpton",
    "plum": "Plumpton",
    "redcar": "Redcar",
    "redc": "Redcar",
    "ripon": "Ripon",
    "rip": "Ripon",
    "salisbury": "Salisbury",
    "salis": "Salisbury",
    "stratford": "Stratford",
    "strat": "Stratford",
    "taunton": "Taunton",
    "taun": "Taunton",
    "thirsk": "Thirsk",
    "thir": "Thirsk",
    "uttoxeter": "Uttoxeter",
    "uttox": "Uttoxeter",
    "warwick": "Warwick",
    "warw": "Warwick",
    "wetherby": "Wetherby",
    "weth": "Wetherby",
    "wincanton": "Wincanton",
    "winc": "Wincanton",
    "windsor": "Windsor",
    "wind": "Windsor",
    "yarmouth": "Yarmouth",
    "yarm": "Yarmouth",
    "bath": "Bath",
    "kilbeggan": "Kilbeggan",
    "kilb": "Kilbeggan",
}


def _prefix_fits(written: str, key: str) -> bool:
    """A written meeting (letters and digits) is this alias: the same, the start of it, or running on from an alias of
    4+ letters. 4+ letters written either way."""
    if len(written) < 4:
        return False
    return written == key or key.startswith(written) or (len(key) >= 4 and written.startswith(key))


class MeetingsDirectoryManager:
    """
    Centralized directory manager for Betty Companion.
    Loads and hot-reloads virtual racing, greyhounds, international meetings,
    and domestic course aliases from meetings_directory.json.
    """

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "meetings_directory.json")
        self.config_path = config_path
        self._last_mtime: float = 0.0
        self.data: dict[str, Any] = {}

        # Cached index structures
        self.directory_greyhound_map: dict[str, str] = {}
        self.live_greyhound_source = None  # callable -> today's greyhound track names on Betty's own card
        self._live_greyhound: tuple = (None, {})
        self.virtual_map: dict[str, dict] = {}
        self.international_map: dict[str, str] = {}
        self.course_alias_map: dict[str, str] = {}

        self._load_config()

    def _check_and_reload(self):
        """Checks file modification timestamp and reloads if changed."""
        try:
            if os.path.exists(self.config_path):
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime > self._last_mtime:
                    self._load_config()
        except Exception:
            pass

    def _load_config(self):
        """Reads meetings_directory.json and indexes all aliases for O(1) matching."""
        # Initialize with baseline domestic horse racing directory
        new_aliases: dict[str, str] = {k: v for k, v in DEFAULT_DOMESTIC_HORSE_COURSES.items()}

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self._last_mtime = os.path.getmtime(self.config_path)

                # 1. Index Virtual Racing
                new_virtual: dict[str, dict] = {}
                for entry in self.data.get("virtual_racing", {}).values():
                    c_name = entry.get("canonical_name", "")
                    v_type = entry.get("type", "virtual_horse")
                    aliases = entry.get("aliases", [])
                    for a in aliases:
                        clean_a = re.sub(r'[^a-z0-9]', '', a.lower())
                        new_virtual[clean_a] = {"canonical_name": c_name, "type": v_type}
                    clean_c = re.sub(r'[^a-z0-9]', '', c_name.lower())
                    new_virtual[clean_c] = {"canonical_name": c_name, "type": v_type}
                self.virtual_map = new_virtual

                # 2. Index Greyhound Tracks
                new_greyhound: dict[str, str] = {}
                for entry in self.data.get("greyhound_tracks", {}).values():
                    c_name = entry.get("canonical_name", "")
                    aliases = entry.get("aliases", [])
                    for a in aliases:
                        clean_a = re.sub(r'[^a-z0-9]', '', a.lower())
                        new_greyhound[clean_a] = c_name
                    clean_c = re.sub(r'[^a-z0-9]', '', c_name.lower())
                    new_greyhound[clean_c] = c_name
                self.directory_greyhound_map = new_greyhound
                self._live_greyhound = (None, {})

                # 3. Index International Meetings
                new_intl: dict[str, str] = {}
                for entry in self.data.get("international_meetings", {}).values():
                    c_name = entry.get("canonical_name", "")
                    aliases = entry.get("aliases", [])
                    for a in aliases:
                        clean_a = re.sub(r'[^a-z0-9]', '', a.lower())
                        new_intl[clean_a] = c_name
                    clean_c = re.sub(r'[^a-z0-9]', '', c_name.lower())
                    new_intl[clean_c] = c_name
                self.international_map = new_intl

                # 4. Merge UK/Irish Course Aliases from JSON
                for k, v in self.data.get("uk_irish_course_aliases", {}).items():
                    clean_k = re.sub(r'[^a-z0-9]', '', k.lower())
                    new_aliases[clean_k] = v

            except Exception as e:
                print(f"[-] MeetingsDirectoryManager: Error loading {self.config_path}: {e}")
                try:  # not read again until the file changes; the last good directory stays in use (review R30)
                    self._last_mtime = os.path.getmtime(self.config_path)
                except OSError:
                    pass
                if getattr(self, "course_alias_map", None):
                    return

        self.course_alias_map = new_aliases

    @property
    def greyhound_map(self) -> dict[str, str]:
        """
        Greyhound tracks {clean alias: name}: the directory's tracks and their written shorthands, plus every real
        track on Betty's greyhound card today (live_greyhound_source), so new tracks (e.g. Australian) need no list.
        """
        if self.live_greyhound_source is None:
            return self.directory_greyhound_map
        try:
            names = tuple(self.live_greyhound_source())
        except Exception:
            return self.directory_greyhound_map
        if names != self._live_greyhound[0]:
            merged = dict(self.directory_greyhound_map)
            for name in names:
                merged.setdefault(re.sub(r'[^a-z0-9]', '', name.lower()), name)
            self._live_greyhound = (names, merged)
        return self._live_greyhound[1]

    def get_greyhound_tracks(self) -> dict[str, str]:
        """Returns a flat dictionary mapping {alias: canonical_name} for all greyhound tracks."""
        self._check_and_reload()
        return self.greyhound_map

    def get_international_meetings(self) -> dict[str, str]:
        """Returns flat dictionary mapping {clean_alias: canonical_name}."""
        self._check_and_reload()
        return self.international_map

    def is_virtual_meeting(self, meeting_name: str, prefixes: bool = True) -> tuple[bool, str | None, str | None]:
        """
        Checks whether meeting_name represents a virtual racing event.
        `prefixes`: also a name that starts, or is the start of, a virtual track's name (4+ letters both).
        Returns: (is_virtual, canonical_name, virtual_type)
        """
        self._check_and_reload()
        if not meeting_name:
            return False, None, None

        clean = re.sub(r'[^a-z0-9]', '', meeting_name.lower())
        clean_no_v = re.sub(r'v$', '', clean)

        # Explicit check for generic virtual indicators
        if clean in ['v', 'virt', 'virtual', 'virtuals'] or meeting_name.strip().lower() in ['(v)', '[v]', 'v.', '(v.)', 'v race', 'virtual race']:
            return True, "Virtual", "virtual_generic"

        if clean in self.virtual_map:
            info = self.virtual_map[clean]
            return True, info["canonical_name"], info["type"]
        if clean_no_v in self.virtual_map:
            info = self.virtual_map[clean_no_v]
            return True, info["canonical_name"], info["type"]

        # A prefix counts only between names of 4+ letters: the shorthands 'v', 'pp', 'sd', 'sv' started any meeting
        # ('Valley', 'Vaal'), and 3 letters written for a course ('San' for Sandown) started a virtual track's name
        # (Sandy Lanes), so the virtual card was searched first and a number bet locked there (review B3, 28 Oct)
        if prefixes and len(clean) >= 4:
            for k, info in self.virtual_map.items():
                if len(k) >= 4 and (k.startswith(clean) or clean.startswith(k)):
                    return True, info["canonical_name"], info["type"]

        return False, None, None

    def get_canonical_meeting_name(self, meeting_name: str) -> str | None:
        """
        Convenience method returning canonical name of any recognized meeting
        across horse racing, virtuals, greyhounds, and international tracks.
        """
        _, canonical = self.resolve_meeting(meeting_name)
        return canonical if canonical else None

    def resolve_meeting(self, raw_meeting: str) -> tuple[str, str]:
        """
        Resolves any meeting string to its category and canonical name.
        Returns: (category, canonical_name)
        Categories: 'virtual', 'horse', 'greyhound', 'international', 'unknown'
        """
        self._check_and_reload()
        if not raw_meeting:
            return "unknown", ""

        raw_no_aw = re.sub(r'\s*\((?:aw|a\.w\.|a/w)\)', '', raw_meeting, flags=re.IGNORECASE)
        raw_no_aw = re.sub(r'\b(?:aw|a\.w\.)\b', '', raw_no_aw, flags=re.IGNORECASE).strip()
        clean = re.sub(r'[^a-z0-9]', '', raw_no_aw.lower())
        if not clean:
            return "unknown", raw_meeting

        # 1. PRIORITY: Check exact match in UK/Irish Domestic Horse Courses & Aliases
        if clean in self.course_alias_map:
            return "horse", self.course_alias_map[clean]

        # 2. Check exact match in International Meetings (e.g. 'fontainebleau' must never be hijacked by 'font')
        if clean in self.international_map:
            return "international", self.international_map[clean]

        # 3. Check exact match in Virtual Racing (a virtual track's name or shorthand, or 'v' / 'virtual')
        is_virt, v_name, _ = self.is_virtual_meeting(raw_meeting, prefixes=False)
        if is_virt and v_name:
            return "virtual", v_name

        # 4. Check exact match in Greyhound Tracks
        if clean in self.greyhound_map:
            return "greyhound", self.greyhound_map[clean]

        # 5. Check prefix / substring matches for domestic horse courses. A written name begins a course name, or
        # runs on from a shorthand of 4+ letters: 'ham' must not make Hamburg Hamilton, nor 'don' Donegal Doncaster
        # (review R4)
        for k, v in self.course_alias_map.items():
            if _prefix_fits(clean, k):
                return "horse", v

        # 5. (cont.) A name the dog or international lists know in full ('Wollong' for Wollongong) before the loose
        # horse matching below can take it for a course ('Wolverhampton'; review R4)
        for kind, table in (("greyhound", self.greyhound_map), ("international", self.international_map)):
            for k, v in table.items():
                if len(clean) >= 5 and k.startswith(clean):
                    return kind, v

        # 5a. A virtual track's name begun or run on (4+ letters: 'Steeple', 'Sprintvalley2'), after the courses so
        # 'Sand' stays Sandown, not Sandy Lanes
        is_virt, v_name, _ = self.is_virtual_meeting(raw_meeting)
        if is_virt and v_name:
            return "virtual", v_name

        # Fuzzy match domestic horse courses before checking dogs
        close_horse = get_close_matches(clean, list(self.course_alias_map.keys()), n=1, cutoff=0.75)
        if close_horse:
            return "horse", self.course_alias_map[close_horse[0]]

        # 6. Check Greyhound Tracks prefix matches
        for k, v in self.greyhound_map.items():
            if _prefix_fits(clean, k):
                return "greyhound", v

        # Strict fuzzy match for greyhounds (0.85 threshold to avoid Listowel -> Towcester)
        close_dog = get_close_matches(clean, list(self.greyhound_map.keys()), n=1, cutoff=0.85)
        if close_dog:
            return "greyhound", self.greyhound_map[close_dog[0]]

        # 7. Check International Meetings prefix matches
        for k, v in self.international_map.items():
            if _prefix_fits(clean, k):
                return "international", v

        return "unknown", raw_meeting

    def are_meetings_equivalent(self, meet1: str, meet2: str) -> bool:
        """
        Determines whether two meeting strings represent the same race meeting / track.
        """
        if not meet1 or not meet2:
            return meet1 == meet2
        m1_clean = meet1.strip().lower()
        m2_clean = meet2.strip().lower()
        if m1_clean == m2_clean:
            return True
        c1 = self.get_canonical_meeting_name(meet1)
        c2 = self.get_canonical_meeting_name(meet2)
        if c1 and c2 and c1.lower() == c2.lower():
            return True
        return self.is_target_meeting_match(meet1, meet2) or self.is_target_meeting_match(meet2, meet1)

    def is_target_meeting_match(self, top_token: str, target_meeting: str) -> bool:
        """
        Unified meeting equivalence matcher for Betty's cyan panel header.
        """
        self._check_and_reload()
        if not top_token or not target_meeting:
            return False

        clean_top = re.sub(r'[^a-z0-9]', '', top_token.lower())
        raw_target_no_aw = re.sub(r'\s*\((?:aw|a\.w\.|a/w)\)', '', target_meeting, flags=re.IGNORECASE)
        raw_target_no_aw = re.sub(r'\b(?:aw|a\.w\.)\b', '', raw_target_no_aw, flags=re.IGNORECASE).strip()
        clean_target = re.sub(r'[^a-z0-9]', '', raw_target_no_aw.lower())

        if not clean_top or not clean_target:
            return False

        if clean_top == clean_target:
            return True

        clean_top_nov = re.sub(r'v$', '', clean_top)
        clean_target_nov = re.sub(r'v$', '', clean_target)
        if clean_top_nov and clean_top_nov == clean_target_nov:
            return True

        # 1. Check Domestic Horse Aliases first
        can_top = self.get_canonical_meeting_name(clean_top)
        can_target = self.get_canonical_meeting_name(clean_target)
        if can_top and can_target and can_top.lower() == can_target.lower():
            return True
        if clean_top in self.course_alias_map:
            can_alias = self.course_alias_map[clean_top]
            if re.sub(r'[^a-z0-9]', '', can_alias.lower()) == clean_target:
                return True

        # 2. Virtual matching
        is_v_target, v_can, _ = self.is_virtual_meeting(target_meeting)
        if is_v_target and v_can:
            clean_v_can = re.sub(r'[^a-z0-9]', '', v_can.lower())
            # If target is generic Virtual ('(v)', 'virtual', 'v'), ANY virtual track header matches!
            if v_can == "Virtual" or clean_target in ['v', 'virt', 'virtual', 'virtuals'] or target_meeting.strip().lower() in ['(v)', '[v]', 'v.', '(v.)']:
                if clean_top in self.virtual_map or clean_top_nov in self.virtual_map:
                    return True
                for k in self.virtual_map:
                    if len(clean_top) >= 3 and (clean_top.startswith(k) or k.startswith(clean_top)):
                        return True
            if clean_top_nov == clean_v_can or clean_v_can.startswith(clean_top_nov):
                return True
            if clean_top in self.virtual_map and self.virtual_map[clean_top]["canonical_name"] == v_can:
                return True
            if clean_top_nov in self.virtual_map and self.virtual_map[clean_top_nov]["canonical_name"] == v_can:
                return True

        # 3. Greyhound matching
        if clean_target in self.greyhound_map:
            can_target = self.greyhound_map[clean_target]
            if clean_top in self.greyhound_map and self.greyhound_map[clean_top] == can_target:
                return True
            if clean_top[:4] in self.greyhound_map and self.greyhound_map[clean_top[:4]] == can_target:
                return True

        # 4. International matching
        if clean_target in self.international_map:
            can_target = self.international_map[clean_target]
            if clean_top in self.international_map and self.international_map[clean_top] == can_target:
                return True
            if clean_top[:4] in self.international_map and self.international_map[clean_top[:4]] == can_target:
                return True
        if clean_top in self.international_map:
            can_alias = self.international_map[clean_top]
            if re.sub(r'[^a-z0-9]', '', can_alias.lower()) == clean_target:
                return True

        # 5. Prefix matching (>= 4 characters)
        target_prefix = clean_target[:4]
        if len(target_prefix) >= 4 and clean_top.startswith(target_prefix):
            return True

        # 5. Low-res OCR font quirks (c <-> e confusion: 'towc' <-> 'towe')
        norm_ce_target = re.sub(r'[ce]', 'c', target_prefix)
        norm_ce_top = re.sub(r'[ce]', 'c', clean_top[:len(target_prefix)])
        if len(target_prefix) >= 4 and norm_ce_top == norm_ce_target:
            return True

        # 6. Tolerant check for leading OCR delimiter artifact (e.g. 'isout'/'lsout' -> 'sout')
        if len(clean_top) >= 4:
            clean_top_strip1 = clean_top[1:]
            if clean_top_strip1 in self.course_alias_map:
                can_alias = self.course_alias_map[clean_top_strip1]
                if re.sub(r'[^a-z0-9]', '', can_alias.lower()) == clean_target:
                    return True
            if len(target_prefix) >= 4 and clean_top_strip1.startswith(target_prefix):
                return True

        # 7. Tolerant prefix check for leading OCR character drop / border artifact (e.g. 'owe' for 'towcester' / 'towe', 'ont' for 'fontwell')
        if len(clean_top) >= 3:
            norm_ce_top = re.sub(r'[ce]', 'c', clean_top)
            norm_ce_target = re.sub(r'[ce]', 'c', clean_target)
            if clean_target[1:].startswith(clean_top) or norm_ce_target[1:].startswith(norm_ce_top):
                return True
            if clean_target in self.greyhound_map:
                can_track = self.greyhound_map[clean_target]
                for a_k, a_v in self.greyhound_map.items():
                    if a_v == can_track and len(a_k) >= 4:
                        if a_k[1:] == clean_top or re.sub(r'[ce]', 'c', a_k[1:]) == norm_ce_top:
                            return True

        return False


# Singleton instance
meetings_manager = MeetingsDirectoryManager()