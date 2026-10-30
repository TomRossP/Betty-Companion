"""
Betty Local Racecard Feed Reader
================================
Betty receives its race cards from SIS / TRP / Tote into C:\\Events as binary `.dat` files,
rewritten throughout the day. This module decodes them into the runner list pre-flight uses,
so selections are checked against exactly the card Betty itself shows (no internet needed).

File name: <day><month><year><FEED>.dat
  day   1-9 then a=10 ... v=31      month 1-9 then a=Oct, b=Nov, c=Dec      year v=2023, w=2024 ...
  e.g. kayHGB00.dat = 20 Oct 2026 SIS horse racing. Past days are kept in C:\\Events\\ARCHIVE.

.dat layout (little-endian, fixed-size blocks):
  header        145 bytes; uint16 meeting count at 111
  meeting       21976 bytes each: name @+11, midnight timestamp @+37, uint16 race count @+42,
                2-char country @+48 (UK/IE/FR/US..., VR = virtual)
  race          730 bytes each from meeting+88: timestamp @+46 (off time = ts - midnight), uint32 event id @+62,
                int32 runner indexes @+80 until -1, listed in saddle-cloth order
  runner table  97-byte records after the last meeting block; name @+12

When a race goes off Betty writes an off slip ("Clifton Park1 19:36 sent off automatically at ...", a View Wagers
number of its own) to C:\\DBF\\transact.DBF: TRANS_TYPE 87, DEALER_2 = the event id, DATE / TIME = when Betty marked
it off, normally seconds after the off. BettyOffTimes reads them.
"""
import datetime
import json
import os
import re
import struct
import time

import app_paths

HEADER_SIZE = 145
MEETING_COUNT_OFF = 111
MEETING_STRIDE = 21976
RACE_FIRST_OFF = 88
RACE_STRIDE = 730
RACE_EVENT_ID_OFF = 62  # Betty's event id: the off slips in transact.DBF and results.dbf name the race by it
RUNNER_STRIDE = 97
RUNNER_NAME_OFF = 12

# Horse racing is every feed Betty labels HORSE or AHorses (SIS, TRP, Australian, Tote, BTC virtual...). Read in
# priority order: SIS and TRP carry the meeting names Betty displays, the Tote feed fills any race they lack, then any
# other feed. Duplicate races across feeds are dropped.
HORSE_SPORTS = ("HORSE", "AHORSES")
DEFAULT_HORSE_FEEDS = ("HGB00", "BFTRP", "TTHR")
RECHECK_SECS = 10  # Betty rewrites today's feeds every few seconds: look at the files at most this often
DOMESTIC_COUNTRIES = {"UK", "IE"}

_DAY_CODES = "123456789abcdefghijklmnopqrstuv"
_MONTH_CODES = "123456789abc"


# Betty's files are on the manager till's C:\ (Betty 0). The cashier tills have no Events or DBF of their own: their
# Betty reads them from the manager till's C:\, shared as drvc and mapped as a network drive (F: at South Oxhey).
BETTY_SHARE = os.environ.get("BETTY_SHARE", r"\\PC\drvc")
BETTY_DRIVES = ["C:\\"] + [f"{d}:\\" for d in "DEFGHIJKLMNOPQRSTUVWXYZ"] + [BETTY_SHARE]
ROOT_RETRY_SECS = 30  # while no drive has Betty's folders, look again at most this often
_root = {"found": "", "tried_at": 0.0}


def _has_betty(root: str) -> bool:
    return all(os.path.isdir(os.path.join(root, sub)) for sub in ("Events", "DBF"))


def find_betty_root() -> str:
    """The first of BETTY_DRIVES holding both Events and DBF: C:\\ on the manager till, the mapped share (F:) on a
    cashier till, else the share itself (\\\\PC\\drvc, BETTY_SHARE) when no letter is mapped. '' when none has."""
    return next((d for d in BETTY_DRIVES if _has_betty(d)), "")


def saved_betty_root() -> str:
    """The drive saved for this build on this till ('' before the first save)."""
    try:
        with open(app_paths.betty_paths_file(), encoding="utf-8") as f:
            return json.load(f)["root"]
    except (OSError, ValueError, KeyError, TypeError):
        return ""


def save_betty_root() -> str:
    """
    Looks for Betty's drive and saves it for this build on this till: the launcher does it once, after the till is
    paired. The drive saved, or '' when no drive has Betty's folders (nothing saved).
    """
    root = find_betty_root()
    if root:
        _root.update(found=root)
        try:
            with open(app_paths.betty_paths_file(), "w", encoding="utf-8") as f:
                json.dump({"root": root, "found": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}, f, indent=2)
            print(f"[+] Betty's files: {root} (saved for this till)")
        except OSError as e:
            print(f"[-] Betty's files: {root}, but it couldn't be saved ({e}). Looked for again next run.")
    return root


def betty_root() -> str:
    """
    The drive holding Betty's Events and DBF folders: the one saved for this till, else found by find_betty_root
    (before the till is saved, or while its saved drive can't be reached, e.g. F: not reconnected yet; the saved
    one is kept). Found once a run; while none is found it's C:\\ (so messages name the usual place) and looked for
    again every ROOT_RETRY_SECS.
    """
    if not _root["found"] and time.time() - _root["tried_at"] >= ROOT_RETRY_SECS:
        _root["tried_at"] = time.time()
        saved = saved_betty_root()
        if saved and _has_betty(saved):
            _root["found"] = saved
        else:
            _root["found"] = find_betty_root()
            if saved:
                print(f"[-] Betty's files: the saved drive {saved} can't be reached; using {_root['found'] or 'none'}.")
            elif _root["found"]:
                print(f"[+] Betty's files: {_root['found']}")
    return _root["found"] or "C:\\"


def events_folder() -> str:
    """Betty's race card folder: BETTY_EVENTS_DIR, else Events on Betty's drive."""
    return os.environ.get("BETTY_EVENTS_DIR") or os.path.join(betty_root(), "Events")


def dbf_folder() -> str:
    """Betty's data folder (transact.DBF): BETTY_DBF_DIR, else DBF on Betty's drive."""
    return os.environ.get("BETTY_DBF_DIR") or os.path.join(betty_root(), "DBF")


def feed_prefix(day: datetime.date) -> str:
    return f"{_DAY_CODES[day.day - 1]}{_MONTH_CODES[day.month - 1]}{chr(ord('v') + day.year - 2023)}"


def _cstr(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("latin-1").strip()


SPORT_CODE_OFF = 44  # header: the feed's sport as Betty labels it ("HORSE", "DOG", "AFoot", "LOT", ...)


def feed_sport(path: str) -> str:
    """The sport code in a feed file's header, upper-cased ('' when unreadable)."""
    try:
        with open(path, "rb") as f:
            header = f.read(HEADER_SIZE)
    except OSError:
        return ""
    return _cstr(header[SPORT_CODE_OFF: SPORT_CODE_OFF + 10]).upper()


def decode_feed(data: bytes) -> list[dict]:
    """Decodes one feed file into race dicts: meeting, country, time_str, minutes, runners (cloth order)."""
    n_meetings = struct.unpack_from("<H", data, MEETING_COUNT_OFF)[0]
    runner_base = HEADER_SIZE + n_meetings * MEETING_STRIDE
    if n_meetings == 0 or runner_base > len(data):
        raise ValueError(f"unexpected layout ({n_meetings} meetings, {len(data)} bytes)")

    races = []
    for mi in range(n_meetings):
        mb = HEADER_SIZE + mi * MEETING_STRIDE
        meeting = _cstr(data[mb + 11: mb + 37])
        midnight = struct.unpack_from("<I", data, mb + 37)[0]
        n_races = struct.unpack_from("<H", data, mb + 42)[0]
        country = _cstr(data[mb + 48: mb + 50]).upper()
        for ri in range(n_races):
            rb = mb + RACE_FIRST_OFF + ri * RACE_STRIDE
            if rb + RACE_STRIDE > runner_base:
                break
            secs = struct.unpack_from("<I", data, rb + 46)[0] - midnight
            if not 0 <= secs < 86400:
                continue
            names = []
            for p in range(rb + 80, rb + RACE_STRIDE - 3, 4):
                idx = struct.unpack_from("<i", data, p)[0]
                if idx < 0:
                    break
                off = runner_base + idx * RUNNER_STRIDE + RUNNER_NAME_OFF
                names.append(_cstr(data[off: off + RUNNER_STRIDE - RUNNER_NAME_OFF]) if off < len(data) else "")
            if names:
                races.append({
                    "meeting": meeting, "country": country,
                    "time_str": f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}", "minutes": secs // 60,
                    "runners": names, "event_id": struct.unpack_from("<I", data, rb + RACE_EVENT_ID_OFF)[0],
                })
    return races


def _same_race(a: frozenset, b: frozenset) -> bool:
    """Two feeds' races at one time are the same race: the same runners, or all but one when one feed has dropped a
    non-runner (4+ runners, as virtual races reuse names; review R27: the race was listed twice)."""
    small = min(len(a), len(b))
    return a == b or (small >= 4 and len(a & b) >= small - 1 and abs(len(a) - len(b)) <= 1)


class BettyFeedCard:
    """Today's runners from Betty's local feeds, re-read whenever a feed file changes."""

    def __init__(self, events_dir: str | None = None, feeds: tuple[str, ...] | None = None,
                 day: datetime.date | None = None, category_resolver=None, sports: tuple[str, ...] | None = None,
                 greyhounds: bool = False):
        """
        Reads every feed of the day whose header carries one of the `sports` codes (default HORSE_SPORTS), found
        afresh as Betty adds feeds. Named `feeds` (or BETTY_HORSE_FEEDS) fix the list instead. `greyhounds`: every
        real race is category 'greyhound' (UK, Irish or Australian alike); virtual dogs stay 'virtual'.
        """
        self._events_dir = events_dir
        env_feeds = None if sports else os.environ.get("BETTY_HORSE_FEEDS")  # the horse override, not the dog card's
        self.feeds = feeds or (tuple(f.strip() for f in env_feeds.split(",")) if env_feeds else None)
        self.sports = None if self.feeds else tuple(s.upper() for s in (sports or HORSE_SPORTS))
        self.fixed_day = day
        self.category_resolver = category_resolver
        self.greyhounds = greyhounds
        self._signature: tuple = ()
        self._runners: list[dict] = []
        self._meetings: tuple[str, ...] = ()
        self._found: tuple = ((), ())  # (prefix, folder time) -> feed paths found by sport
        self._checked_at = 0.0
        self._reported: tuple = ()

    @property
    def events_dir(self) -> str:
        return self._events_dir or events_folder()  # found at each read: a cashier till's F: may connect after startup

    def _paths(self) -> list[str]:
        prefix = feed_prefix(self.fixed_day or datetime.date.today())
        if not self.sports:
            return [os.path.join(self.events_dir, f"{prefix}{feed}.dat") for feed in self.feeds]
        try:
            key = (prefix, os.path.getmtime(self.events_dir))  # the folder's time changes when Betty adds a feed
        except OSError:
            return []
        if self._found[0] != key:
            names = sorted(f for f in os.listdir(self.events_dir) if f.startswith(prefix) and f.lower().endswith(".dat"))
            paths = [os.path.join(self.events_dir, f) for f in names]
            rank = {feed: i for i, feed in enumerate(DEFAULT_HORSE_FEEDS)}
            paths.sort(key=lambda p: (rank.get(os.path.basename(p)[3:-4], len(rank)), p))
            self._found = (key, tuple(p for p in paths if feed_sport(p) in self.sports))
        return list(self._found[1])

    def _category(self, meeting: str, country: str) -> str:
        if country == "VR":
            return "virtual"
        if self.greyhounds:
            return "greyhound"
        if country in DOMESTIC_COUNTRIES:
            return "domestic"
        if country:
            return "international"
        # Tote feed carries no country code: fall back to the meetings directory
        if self.category_resolver:
            cat = self.category_resolver(meeting)
            return {"horse": "domestic", "virtual": "virtual"}.get(cat, "international")
        return "domestic"

    def refresh(self) -> list[dict]:
        """The runners as the feed files are now, skipping the RECHECK_SECS wait (a feed Betty added seconds ago)."""
        self._checked_at = 0.0
        return self.get_runners()

    def get_runners(self) -> list[dict]:
        if self._signature and time.monotonic() - self._checked_at < RECHECK_SECS:
            return self._runners
        self._checked_at = time.monotonic()
        paths = [p for p in self._paths() if os.path.exists(p)]
        signature = tuple((p, os.path.getmtime(p), os.path.getsize(p)) for p in paths)
        if signature == self._signature:
            return self._runners

        runners, seen_races = [], {}  # time -> runner-name sets of the races read at that time
        for path in paths:
            try:
                with open(path, "rb") as f:
                    races = decode_feed(f.read())
            except (OSError, ValueError, struct.error) as e:
                print(f"[-] Betty feed: could not read {os.path.basename(path)}: {e}")
                continue
            for race in races:
                names = frozenset(n.lower() for n in race["runners"] if n)
                if any(_same_race(names, seen) for seen in seen_races.get(race["time_str"], ())):
                    continue  # same race already read from a higher-priority feed (or a Tote pool alias)
                seen_races.setdefault(race["time_str"], []).append(names)
                category = self._category(race["meeting"], race["country"])
                meeting = re.sub(r"\d+$", "", race["meeting"]).strip() if category == "virtual" else race["meeting"]
                for cloth, name in enumerate(race["runners"], start=1):
                    if name:
                        runners.append({
                            "name": name, "meeting": meeting, "time_str": race["time_str"],
                            "minutes": race["minutes"], "number": cloth, "category": category,
                            "country": race["country"], "event_id": race["event_id"],
                            "feed": os.path.basename(path)[3:-4],  # e.g. 'HGB00': which Betty folder the race is in
                        })
        self._signature, self._runners = signature, runners
        self._meetings = tuple(sorted({r["meeting"] for r in runners if r["category"] != "virtual"}))
        n_races = len({(r["meeting"], r["time_str"]) for r in runners})
        report = (len(runners), n_races, tuple(paths))
        if runners and report != self._reported:  # say so only when the card itself changed, not on every rewrite
            self._reported = report
            print(f"[+] Betty feed: {len(runners)} runners in {n_races} races from {len(paths)} local feed file(s) "
                  f"({', '.join(os.path.basename(p)[3:-4] for p in paths)}).")
        elif not runners:
            print(f"[-] Betty feed: no runners found in {self.events_dir} for {feed_prefix(self.fixed_day or datetime.date.today())}*.")
        return runners

    def get_meetings(self) -> tuple[str, ...]:
        """Today's real (not virtual) meetings on this card, e.g. every greyhound track Betty has races for."""
        self.get_runners()
        return self._meetings


OFF_TRANS_TYPE = "87"  # transact.DBF: Betty's off slip, one per event sent off
OFF_READ_BACK = 20000  # records read back at a time to find the start of the day


class BettyOffTimes:
    """
    When Betty marked each of the day's races off, from its off slips in transact.DBF ({event id: seconds from
    midnight}, the earliest slip). The table is only ever appended to: the first read goes back to the start of the
    day, later reads take only the new records. Any problem reading it gives no off times (scheduled times decide).
    """

    def __init__(self, dbf_dir: str | None = None, day: datetime.date | None = None):
        self._dbf_dir = dbf_dir
        self.fixed_day = day
        self._day = ""
        self._read_to = 0  # records read so far
        self._offs: dict[int, int] = {}
        self._reported = ""

    @property
    def path(self) -> str:
        return os.path.join(self._dbf_dir or dbf_folder(), "transact.DBF")

    def refresh(self) -> dict[int, int]:
        day = (self.fixed_day or datetime.date.today()).strftime("%Y%m%d")
        if day != self._day:
            self._day, self._read_to, self._offs = day, 0, {}
        try:
            with open(self.path, "rb") as f:
                n, header_len, rec_len = struct.unpack_from("<IHH", f.read(12), 4)
                f.seek(32)
                fields, pos = {}, 1
                while (desc := f.read(32)) and desc[0] != 0x0D:
                    fields[desc[:11].split(b"\0")[0].decode("latin-1").upper()] = (pos, desc[16])
                    pos += desc[16]

                def get(rec: bytes, name: str) -> str:
                    at, size = fields[name]
                    return rec[at: at + size].decode("latin-1").strip()

                if n < self._read_to:  # the table was packed: read the day again
                    self._read_to, self._offs = 0, {}
                start = self._read_to
                if not start:  # back to the first record of the day
                    start = n
                    while start > 0:
                        start = max(0, start - OFF_READ_BACK)
                        f.seek(header_len + start * rec_len)
                        date = get(f.read(rec_len), "DATE")
                        if date and date < day:
                            break
                f.seek(header_len + start * rec_len)
                blob = f.read((n - start) * rec_len)
        except (OSError, KeyError, struct.error) as e:
            if self._reported != str(e):
                self._reported = str(e)
                print(f"[-] Betty off slips: could not read {self.path} ({e}). Scheduled times decide.")
            return {}
        for i in range(0, len(blob) - rec_len + 1, rec_len):
            rec = blob[i: i + rec_len]
            if rec[0:1] == b"*" or get(rec, "TRANS_TYPE") != OFF_TRANS_TYPE or get(rec, "DATE") != day:
                continue
            m = re.match(r"(\d{1,2}):(\d{2}):(\d{2})$", get(rec, "TIME"))
            event = get(rec, "DEALER_2")
            if m and event.isdigit():
                secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                self._offs[int(event)] = min(secs, self._offs.get(int(event), secs))
        self._read_to = start + len(blob) // rec_len
        return self._offs

    def mark(self, runners: list[dict]) -> list[dict]:
        """
        Gives each runner its race's off time as minutes from midnight ('off_mins', None if not off yet) and whether
        Betty sends its races off ('offs_tracked'): its feed has off slips today, and no later race at its meeting
        went off after this one was due while this one has none (a slip missed; a race sent off early, abandoned,
        says nothing). Runners of a feed Betty doesn't send off (the Tote) are never tracked.
        """
        offs = self.refresh()
        tracked = {r.get("feed") for r in runners if r.get("event_id") in offs}
        gone: dict[tuple, set] = {}  # (feed, meeting) -> (scheduled, off) of its races sent off
        for r in runners:
            if r.get("event_id") in offs and r.get("minutes") is not None:
                gone.setdefault((r.get("feed"), r["meeting"]), set()).add((r["minutes"], offs[r["event_id"]] / 60))
        for r in runners:
            off = offs.get(r.get("event_id"))
            due = r.get("minutes")
            missed = off is None and due is not None and any(
                later > due and went > due for later, went in gone.get((r.get("feed"), r["meeting"]), ()))
            r["off_mins"] = None if off is None else off / 60
            r["offs_tracked"] = r.get("feed") in tracked and due is not None and not missed
        return runners


RACING_SPORTS = {"HORSE": "Horses", "AHORSES": "Horses", "DOG": "Greyhounds", "ADOGS": "Greyhounds"}
REGION_ORDER = ("UK/IRE", "Australia", "International", "Virtual")


def todays_meetings(day: datetime.date | None = None, events_dir: str | None = None) -> list[dict]:
    """
    Every horse and greyhound meeting on Betty's cards for the day (all feeds labelled HORSE, AHorses, DOG or ADogs):
    [{meeting, sport, region, country, races, first, last, feeds}], UK/IRE first, then by sport and first race.
    For the launcher's Data tab and `python betty_feed.py --meetings`.
    """
    events_dir = events_dir or events_folder()
    prefix = feed_prefix(day or datetime.date.today())
    try:
        names = sorted(f for f in os.listdir(events_dir) if f.startswith(prefix) and f.lower().endswith(".dat"))
    except OSError:
        return []
    meetings: dict[tuple[str, str], dict] = {}
    for fname in names:
        path = os.path.join(events_dir, fname)
        sport = RACING_SPORTS.get(feed_sport(path))
        if not sport:
            continue
        try:
            with open(path, "rb") as f:
                races = decode_feed(f.read())
        except (OSError, ValueError, struct.error):
            continue
        for race in races:
            country = race["country"]
            virtual = country == "VR"
            name = re.sub(r"\d+$", "", race["meeting"]).strip() if virtual else race["meeting"]
            region = ("Virtual" if virtual else "UK/IRE" if country in DOMESTIC_COUNTRIES
                      else "Australia" if country == "AU" else "International")
            m = meetings.setdefault((name, sport), {"meeting": name, "sport": sport, "region": region, "country": country,
                                                     "times": set(), "feeds": set()})
            m["times"].add(race["time_str"])
            m["feeds"].add(fname[len(prefix):-4])
    out = []
    for m in meetings.values():
        times = sorted(m.pop("times"))
        out.append({**m, "races": len(times), "first": times[0], "last": times[-1], "feeds": ", ".join(sorted(m["feeds"]))})
    return sorted(out, key=lambda m: (REGION_ORDER.index(m["region"]), m["sport"] != "Horses", m["first"], m["meeting"]))


if __name__ == "__main__":
    import sys
    if "--meetings" in sys.argv:
        rows = todays_meetings()
        print(f"{'Meeting':24} {'Sport':11} {'Region':13} {'Races':>5}  {'First':5}  {'Last':5}  Feeds")
        for m in rows:
            print(f"{m['meeting'][:24]:24} {m['sport']:11} {m['region']:13} {m['races']:>5}  {m['first']}  {m['last']}  {m['feeds']}")
        print(f"{len(rows)} meetings")
