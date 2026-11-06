"""
What's kept on the till from Betty's own files, for the Past results and Sports prices tabs, in Documents\\BettyCompanion Records:
outside the program's folder, so that a new version, wherever it's unzipped, finds them.

Past results: one compressed file a day, kept for good (past_results\\<yyyymmdd>.json.gz, about 50 KB): every UK, Irish, international and greyhound race, its
runners and their placings. The runners come from that day's feed files, in Events or, once the day is over, Events\\ARCHIVE;
the placings and SPs from SETTDATA (as far as Betty records them: some races list only the places paid). She keeps about three
weeks of results, so what's written here is the only record after that. Virtual races are left out: about 10,000 runners a day.

Sports prices: every change of price of every sports selection, copied from Betty's monthly price history, with who won
(sports_prices.db). Kept SPORTS_KEEP_DAYS after the event, so the file stops growing at about that much.

Both are kept on the manager till alone (user, 6 Nov), the one with Betty's files on its own disk. A cashier till, reading them
across the network, leaves them alone and doesn't show the tabs: this reading would add to the load that freezes Betty there.
"""
import calendar
import contextlib
import ctypes
import datetime
import gzip
import json
import os
import re
import sqlite3
import struct
import time

import betty_feed

SPORTS_KEEP_DAYS = 30
BACKFILL_DAYS = 60  # days back looked for on starting, for any not on file yet: as far as Betty's files go
GROUPS = {"domestic": "UK & Ireland", "international": "International", "greyhound": "Greyhounds"}


def records_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "Documents", "BettyCompanion Records")


def is_manager_till() -> bool:
    """The manager till: Betty's data files are here on this PC's own disk. A cashier till reads them across the network."""
    folder = betty_feed.dbf_folder()
    root = os.path.splitdrive(os.path.abspath(folder))[0] + "\\"
    try:
        return os.path.exists(os.path.join(folder, "SETTDATA.DBF")) and ctypes.windll.kernel32.GetDriveTypeW(root) == 3  # DRIVE_FIXED
    except Exception:
        return False


# --- Past results ---

def _day_file(day: datetime.date) -> str:
    return os.path.join(records_dir(), "past_results", f"{day:%Y%m%d}.json.gz")


def _feed_dir(day: datetime.date) -> str:
    """The folder holding the day's racing feeds: Events, or ARCHIVE once Betty has moved them there."""
    events = betty_feed.events_folder()
    archive = os.path.join(events, "ARCHIVE")
    prefix = betty_feed.feed_prefix(day)
    def count(folder):
        try:
            return sum(1 for n in os.listdir(folder) if n.startswith(prefix) and n.lower().endswith(".dat"))
        except OSError:
            return 0
    return archive if count(archive) > count(events) else events


def _settled_table():
    try:
        return betty_feed.SettledTable()
    except (OSError, KeyError, ValueError, struct.error) as e:
        print(f"[-] Past results: Betty's results can't be read: {e}")
        return None


def build_day(day: datetime.date, table=None) -> dict:
    """The day's races: [{'group', 'meeting', 'time', 'settled', 'runners': [{'number', 'name', 'price', 'place', 'sp',
    'dead_heat'}]}], each race finishing order first, then the rest by racecard number."""
    folder = _feed_dir(day)
    runners = betty_feed.BettyFeedCard(events_dir=folder, day=day).get_runners()
    dogs = betty_feed.BettyFeedCard(events_dir=folder, day=day, sports=betty_feed.DOG_SPORTS, greyhounds=True).get_runners()
    races: dict[tuple, dict] = {}
    for r in runners + dogs:
        group = "greyhound" if r.get("dogs") and r.get("category") != "virtual" else r.get("category")
        if group not in GROUPS:
            continue
        race = races.setdefault((r["event_id"], r["meeting"], r["time_str"]),
                                {"group": GROUPS[group], "meeting": r["meeting"], "time": r["time_str"],
                                 "event_id": r["event_id"], "runners": []})
        race["runners"].append({"number": r.get("number"), "name": r["name"], "price": r.get("price") or ""})
    settled = table or _settled_table()
    for key, race in races.items():
        placed = settled.placings(key[0], key[1], key[2], day, [x["name"] for x in race["runners"]]) if settled else []
        race["settled"] = bool(placed)
        for run in race["runners"]:
            run.update(place=None, sp="", dead_heat=False)
            for p in placed:
                if p.get("cloth") == run["number"] or p.get("name", "").lower() == run["name"].lower():
                    run.update(place=p["place"], sp=p.get("sp") or "", dead_heat=bool(p.get("dead_heat")))
                    break
        race["runners"].sort(key=lambda x: (x["place"] is None, x["place"] or 0, x["number"] or 0))
    ordered = sorted(races.values(), key=lambda x: (x["group"], x["meeting"], x["time"]))
    return {"date": f"{day:%Y-%m-%d}", "recorded": time.strftime("%Y-%m-%d %H:%M"), "races": ordered}


def record_day(day: datetime.date, table=None) -> int:
    """
    Writes the day's file, never over one with more results: Betty's files for a day can go, and what's on file then is the
    only record. The number of races on file.
    """
    data = build_day(day, table)
    path = _day_file(day)
    on_file = load_day(f"{day:%Y-%m-%d}")
    settled = lambda d: sum(1 for r in d.get("races", []) if r.get("settled"))  # noqa: E731
    if not data["races"] or settled(data) < settled(on_file):
        return len(on_file["races"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)
    return len(data["races"])


def backfill(today: datetime.date | None = None) -> list[str]:
    """Recent days with no file yet, as far as Betty's files still hold them. The days recorded."""
    today = today or datetime.date.today()
    done, table = [], _settled_table()
    for back in range(1, BACKFILL_DAYS + 1):
        day = today - datetime.timedelta(days=back)
        if not os.path.exists(_day_file(day)) and record_day(day, table):
            done.append(f"{day:%Y-%m-%d}")
    return done


def days_on_file() -> list[str]:
    """'yyyy-mm-dd' of each day on file, newest first."""
    try:
        names = os.listdir(os.path.join(records_dir(), "past_results"))
    except OSError:
        return []
    return sorted((f"{n[:4]}-{n[4:6]}-{n[6:8]}" for n in names if n.endswith(".json.gz") and len(n) == 16), reverse=True)


def load_day(date: str) -> dict:
    try:
        with gzip.open(os.path.join(records_dir(), "past_results", date.replace("-", "") + ".json.gz"), "rt", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"date": date, "races": []}


# --- Sports prices ---

def now_local() -> int:
    """Now as the price book holds times: local date and time, counted as if UTC."""
    return calendar.timegm(time.localtime())


def price_text(num: int, den: int) -> str:
    return f"{num}/{den}"


class SportsPrices:
    """
    The shop's own record of sports prices (user, 6 Nov: a slip with no price on a football match, and no way of seeing what it
    was). Copied from Betty's monthly price history (DBF\\PHST<mmyy>.DBF), new rows each look and the last SPORTS_KEEP_DAYS on the
    first. Only a change of price is kept, and names once each, so it stays small. Winners come from SETTDATA, kept here as Betty
    only holds about three weeks. Times are local, as if UTC. One connection for each job, so any thread can use it.
    """
    CHUNK_ROWS = 20000

    def __init__(self, path: str | None = None, dbf_dir: str | None = None, keep_days: int = SPORTS_KEEP_DAYS):
        self.path = path or os.path.join(records_dir(), "sports_prices.db")
        self.dbf_dir = dbf_dir
        self.keep_days = keep_days
        self._selections: dict[tuple, list] = {}  # (market, name) -> [its id, its last price], for the rows being copied
        self._sports: dict[str, str] = {}          # feed stem -> Betty's sport code, '' for racing, numbers and the like
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS market (id INTEGER PRIMARY KEY, event TEXT, name TEXT, sport TEXT, kickoff INTEGER, result TEXT);
                CREATE TABLE IF NOT EXISTS selection (id INTEGER PRIMARY KEY, market INTEGER, name TEXT, UNIQUE (market, name));
                CREATE TABLE IF NOT EXISTS price (selection INTEGER, at INTEGER, num INTEGER, den INTEGER, PRIMARY KEY (selection, at))
                    WITHOUT ROWID;
                CREATE TABLE IF NOT EXISTS copied (file TEXT PRIMARY KEY, rows INTEGER);
                CREATE INDEX IF NOT EXISTS market_day ON market (kickoff);
            """)

    @contextlib.contextmanager
    def _connect(self):
        """A connection for one job: committed if it went well, always closed."""
        db = sqlite3.connect(self.path, timeout=20)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            with db:
                yield db
        finally:
            db.close()

    # --- Copying from Betty ---

    def _files(self, now: int) -> list[str]:
        """Her monthly files that can hold rows inside the keep period, oldest first."""
        folder = self.dbf_dir or betty_feed.dbf_folder()
        day = datetime.datetime.fromtimestamp(now - self.keep_days * 86400, datetime.timezone.utc).date().replace(day=1)
        last = datetime.datetime.fromtimestamp(now, datetime.timezone.utc).date()
        found = []
        while day <= last:
            path = os.path.join(folder, f"PHST{day:%m%y}.DBF")
            if os.path.exists(path):
                found.append(path)
            day = (day + datetime.timedelta(days=32)).replace(day=1)
        return found

    def _sport_of(self, event_file: str, event_name: str) -> str:
        """Betty's sport code for a row's feed; '' for racing, dogs and the numbers, which aren't kept here."""
        stem = event_file[3:]
        if stem not in self._sports:
            sport = ""
            events = betty_feed.events_folder() if not self.dbf_dir else ""
            for folder in (events, os.path.join(events, "ARCHIVE")):
                path = os.path.join(folder, event_file + ".dat")
                if events and os.path.exists(path):
                    sport = betty_feed.feed_sport(path)
                    break
            racing = (betty_feed.RACING_SPORT.search(sport) or sport in ("LOT", *betty_feed.DOG_SPORTS)) if sport else False
            self._sports[stem] = "" if racing else (sport or "SPORT")
        if re.fullmatch(r"\d{1,2}[:.]\d{2}", event_name):  # a race, whatever the feed says
            return ""
        return self._sports[stem]

    def ingest(self, now: int | None = None, pause: float = 0.02) -> dict:
        """The rows Betty has added since the last look. {'rows' read, 'moves' kept, 'markets' new}. `pause`: between chunks."""
        now = now_local() if now is None else now
        oldest = now - self.keep_days * 86400
        totals = {"rows": 0, "moves": 0, "markets": 0}
        with self._connect() as db:
            done = dict(db.execute("SELECT file, rows FROM copied"))
        for path in self._files(now):
            name = os.path.basename(path)
            with open(path, "rb") as f:
                n, header_len, rec_len = struct.unpack_from("<IHH", f.read(12), 4)
                f.seek(32)
                fields, pos = {}, 1
                while (desc := f.read(32)) and desc[0] != 0x0D:
                    fields[desc[:11].split(b"\0")[0].decode("latin-1").upper()] = (pos, pos + desc[16])
                    pos += desc[16]
                start = done.get(name)
                if start is None:
                    start = self._first_row_after(f, header_len, rec_len, n, fields, oldest)
                if start > n:  # Betty rewrote the file: from the start again, what's kept already isn't added twice
                    start = 0
                while start < n:
                    f.seek(header_len + start * rec_len)
                    count = min(self.CHUNK_ROWS, n - start)
                    blob = f.read(count * rec_len)
                    got = len(blob) // rec_len
                    if not got:
                        break
                    self._copy_chunk(blob, got, rec_len, fields, totals)
                    start += got
                    with self._connect() as db:
                        db.execute("INSERT OR REPLACE INTO copied (file, rows) VALUES (?,?)", (name, start))
                    totals["rows"] += got
                    if pause:
                        time.sleep(pause)
        if len(self._selections) > 300000:
            self._selections.clear()
        return totals

    @staticmethod
    def _first_row_after(f, header_len: int, rec_len: int, n: int, fields: dict, oldest: int) -> int:
        """The first row inside the keep period: her rows are in time order. Betty's clock is ahead, by hours, so a day's grace."""
        a, b = fields["CUPDTIME"]
        low, high = 0, n
        while low < high:
            mid = (low + high) // 2
            f.seek(header_len + mid * rec_len)
            value = f.read(rec_len)[a:b].strip()
            if value.isdigit() and int(value) >= oldest:
                high = mid
            else:
                low = mid + 1
        return low

    def _copy_chunk(self, blob: bytes, count: int, rec_len: int, fields: dict, totals: dict):
        get = lambda rec, key: rec[fields[key][0]:fields[key][1]]  # noqa: E731
        ahead = None
        markets, moves = {}, []
        with self._connect() as db:
            known = self._selections
            for i in range(count):
                rec = blob[i * rec_len: (i + 1) * rec_len]
                if rec[:1] == b"*":
                    continue
                num_raw, den_raw = get(rec, "ODDSNUM").strip(), get(rec, "ODDSDEN").strip()
                if not num_raw.isdigit() or not den_raw.isdigit():
                    continue
                num, den = int(num_raw), int(den_raw)
                if not num or not den or den >= 10000:  # 1/10001 is no price, only a row being added
                    continue
                event_name = get(rec, "EVENTNAME").decode("latin-1").strip()
                event_file = get(rec, "EVENTFILE").decode("latin-1").strip()
                sport = self._sport_of(event_file, event_name)
                if not sport:
                    continue
                market_id = get(rec, "EVENTID").strip()
                updated = get(rec, "CUPDTIME").strip()
                if not market_id.isdigit() or not updated.isdigit():
                    continue
                market_id, updated = int(market_id), int(updated)
                if ahead is None:  # how far her clock is ahead: her own row says, in clock time and in her count
                    clock = time.strptime(f"{get(rec, 'UPDDATE').decode('latin-1')} {get(rec, 'UPDTIME').decode('latin-1').strip()}", "%Y%m%d %H:%M:%S")
                    ahead = updated - calendar.timegm(clock)
                name = get(rec, "SELNNAME").decode("latin-1").strip()
                key = (market_id, name)
                entry = known.get(key)
                if entry is None:
                    if market_id not in markets:
                        starts = get(rec, "CEVENTTIME").strip()
                        kickoff = int(starts) - ahead if starts.isdigit() and int(starts) else 0
                        cur = db.execute("INSERT OR IGNORE INTO market (id, event, name, sport, kickoff) VALUES (?,?,?,?,?)",
                                         (market_id, get(rec, "EVENTGROUP").decode("latin-1").strip(), event_name, sport, kickoff))
                        totals["markets"] += max(cur.rowcount, 0)
                        markets[market_id] = True
                    row = db.execute("SELECT id FROM selection WHERE market=? AND name=?", key).fetchone()
                    if row:
                        last = db.execute("SELECT num, den FROM price WHERE selection=? ORDER BY at DESC LIMIT 1", row).fetchone()
                        entry = [row[0], last]
                    else:
                        sid = db.execute("INSERT INTO selection (market, name) VALUES (?,?)", key).lastrowid
                        entry = [sid, None]
                    known[key] = entry
                if entry[1] != (num, den):
                    moves.append((entry[0], updated - ahead, num, den))
                    entry[1] = (num, den)
            db.executemany("INSERT OR REPLACE INTO price (selection, at, num, den) VALUES (?,?,?,?)", moves)
        totals["moves"] += len(moves)

    def settle(self, table=None, now: int | None = None) -> int:
        """Winners from SETTDATA, for markets started with none yet: kept here for good, as Betty's goes. How many found."""
        now = now_local() if now is None else now
        try:
            table = table or betty_feed.SettledTable(self.dbf_dir)
        except (OSError, KeyError, ValueError, struct.error):
            return 0
        found = []
        with self._connect() as db:
            for (market_id,) in db.execute("SELECT id FROM market WHERE result IS NULL AND kickoff>0 AND kickoff<?", (now,)):
                row = table.by_id.get(market_id)
                placed = table._placings(row) if row else []
                if placed:
                    found.append((json.dumps([[p["place"], p["name"]] for p in placed], ensure_ascii=False), market_id))
            db.executemany("UPDATE market SET result=? WHERE id=?", found)
        return len(found)

    def prune(self, now: int | None = None) -> int:
        """Markets past the keep period go, and their selections and prices. The file's space is used again, so it stops growing."""
        now = now_local() if now is None else now
        oldest = now - self.keep_days * 86400
        with self._connect() as db:
            gone = "SELECT id FROM market WHERE kickoff>0 AND kickoff<?"
            db.execute(f"DELETE FROM price WHERE selection IN (SELECT id FROM selection WHERE market IN ({gone}))", (oldest,))
            db.execute(f"DELETE FROM selection WHERE market IN ({gone})", (oldest,))
            count = db.execute("DELETE FROM market WHERE kickoff>0 AND kickoff<?", (oldest,)).rowcount
        self._selections.clear()
        return count

    # --- Reading, for the tab ---

    def days(self) -> list[str]:
        """Each day with a market starting on it, newest first."""
        with self._connect() as db:
            return [r[0] for r in db.execute("SELECT DISTINCT date(kickoff, 'unixepoch') d FROM market WHERE kickoff>0 ORDER BY d DESC")]

    def sports(self) -> list[str]:
        with self._connect() as db:
            return [r[0] for r in db.execute("SELECT DISTINCT sport FROM market ORDER BY sport")]

    def events(self, day: str = "", search: str = "", sport: str = "", limit: int = 500) -> list[tuple]:
        """(kick-off, event, finished) on the day, or any day, by kick-off. The search looks through event, market and selection."""
        where, args = ["1"], []
        if day:
            where.append("date(m.kickoff, 'unixepoch')=?")
            args.append(day)
        if sport:
            where.append("m.sport=?")
            args.append(sport)
        if search:
            like = f"%{search}%"
            where.append("(m.event LIKE ? OR m.id IN (SELECT market FROM selection WHERE name LIKE ?))")
            args += [like, like]
        sql = (f"SELECT MIN(m.kickoff) k, m.event FROM market m WHERE {' AND '.join(where)} AND m.event<>'' "
               "GROUP BY m.event, date(m.kickoff, 'unixepoch') ORDER BY k LIMIT ?")
        now = now_local()
        with self._connect() as db:
            return [(k, e, 0 < k < now) for k, e in db.execute(sql, (*args, limit))]

    def markets(self, event: str, kickoff: int) -> list[tuple]:
        """(id, market, its result is in) of the event on that day."""
        with self._connect() as db:
            return [(i, n, r is not None) for i, n, r in db.execute(
                "SELECT id, name, result FROM market WHERE event=? AND date(kickoff, 'unixepoch')=date(?, 'unixepoch') ORDER BY name",
                (event, kickoff))]

    def selections(self, market_id: int) -> list[dict]:
        """Each selection: 'id', 'name', 'first' price, 'last' before the start ('final' once it has started) and 'place'."""
        with self._connect() as db:
            row = db.execute("SELECT kickoff, result FROM market WHERE id=?", (market_id,)).fetchone()
            if not row:
                return []
            kickoff, result = row
            placed = json.loads(result) if result else []
            out = []
            for sid, name in db.execute("SELECT id, name FROM selection WHERE market=? ORDER BY name", (market_id,)).fetchall():
                prices = db.execute("SELECT at, num, den FROM price WHERE selection=? ORDER BY at", (sid,)).fetchall()
                before = [p for p in prices if not kickoff or p[0] <= kickoff] or prices
                place = next((p for p, who in placed if betty_feed._same_name(who, name) or betty_feed._same_name(name, who)), None)
                out.append({"id": sid, "name": name, "place": place, "moves": len(prices),
                            "first": price_text(*prices[0][1:]) if prices else "",
                            "last": price_text(*before[-1][1:]) if before else "",
                            "final": bool(kickoff and kickoff <= now_local())})
            return out

    def history(self, selection_id: int) -> list[tuple]:
        """Every price the selection has had, oldest first: (when, price)."""
        with self._connect() as db:
            return [(at, price_text(n, d)) for at, n, d in
                    db.execute("SELECT at, num, den FROM price WHERE selection=? ORDER BY at", (selection_id,))]

    def counts(self) -> dict:
        with self._connect() as db:
            return {"markets": db.execute("SELECT COUNT(*) FROM market").fetchone()[0],
                    "prices": db.execute("SELECT COUNT(*) FROM price").fetchone()[0]}
