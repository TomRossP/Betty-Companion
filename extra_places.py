"""
Extra places, for Data > Extra places on the manager till: a record kept for good, by date, of the UK and Irish races whose place terms were edited.

Head office's terminal edits a race's places first thing in the morning, and the card then holds them (betty_feed's extra_terms). No file says who made the edit or
when. Betty's archive of cards goes back to 3 Apr 2026, and all of it is read once. SETTDATA gives the terms each race was settled on, for about three weeks (21 of 22
agreed with the card, 16 Oct - 5 Nov; Newbury 14:25 on 5 Nov has 5 at 1/5 on the card and settled at 4 at 1/4).
In Documents\\BettyCompanion Records\\extra_places.json.
"""
import datetime
import json
import os
import struct
import time

import betty_feed
import till_records

FEEDS = ("HGB00", "BFTRP")  # they carry different meetings. The Tote's feed has no terms and names races by other ids
LOOK_BACK_DAYS = 366  # as far as Betty's files go
SETTLED_KEPT_DAYS = 25  # SETTDATA holds about three weeks: not looked for in it after this


def _path() -> str:
    return os.path.join(till_records.records_dir(), "extra_places.json")


def load() -> dict:
    """{'read': [days read for good], 'races': {'<date> <event id>': {...}}}."""
    try:
        with open(_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"read": [], "races": {}}


def _write(data: dict):
    path = _path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _card_races(day: datetime.date) -> list[dict] | None:
    """The day's UK and Irish races as on its cards, today's or archived. None when a card can't be read or there's none."""
    events = betty_feed.events_folder()
    races, found = [], False
    for feed in FEEDS:
        name = f"{betty_feed.feed_prefix(day)}{feed}.dat"
        path = next((p for p in (os.path.join(events, name), os.path.join(events, "ARCHIVE", name)) if os.path.exists(p)), None)
        if not path:
            continue
        try:
            with open(path, "rb") as f:
                races += [r for r in betty_feed.decode_feed(f.read()) if r["country"] in betty_feed.DOMESTIC_COUNTRIES]
        except (OSError, struct.error, IndexError) as e:
            print(f"[-] Extra places: {name} can't be read: {e}")
            return None
        found = True
    return races if found else None


def _record_races(data: dict, day: datetime.date, races: list[dict]):
    """The card's edited races on the record. One already there and back on the usual terms stays, marked taken off."""
    date = f"{day:%Y-%m-%d}"
    for race in races:
        key = f"{date} {race['event_id']}"
        terms = race["extra_terms"]
        if terms:
            entry = data["races"].setdefault(key, {"date": date, "event_id": race["event_id"]})
            entry.update(time=race["time_str"], meeting=race["meeting"], runners=len(race["runners"]) - sum(race["out"]), handicap=race["handicap"],
                         places=terms[0], top=terms[1], bottom=terms[2], off=False)
        elif key in data["races"]:
            data["races"][key]["off"] = True


def _add_settled(data: dict, today: datetime.date):
    """The terms each race was settled on. Today's and yesterday's are looked at again, as a race can be resettled (Newbury 14:25 on 5 Nov, five times in seven minutes)."""
    oldest, recent = f"{today - datetime.timedelta(days=SETTLED_KEPT_DAYS):%Y-%m-%d}", f"{today - datetime.timedelta(days=1):%Y-%m-%d}"
    pending = [e for e in data["races"].values() if e["date"] >= recent or (e["date"] >= oldest and not e.get("settled"))]
    table = till_records._settled_table() if pending else None
    if table:
        for entry in pending:
            terms = table.settled_terms(entry["event_id"])
            if terms:
                entry["settled"] = list(terms)


def backfill(today: datetime.date | None = None, pause: float = 0.02) -> int:
    """Every day Betty still has cards for and that isn't read yet, each once. How many days were read."""
    today = today or datetime.date.today()
    data = load()
    before, read, done = json.dumps(data, sort_keys=True), set(data["read"]), 0
    for back in range(2, LOOK_BACK_DAYS + 1):  # yesterday's is for update(): it can still change
        day = today - datetime.timedelta(days=back)
        if f"{day:%Y-%m-%d}" in read:
            continue
        races = _card_races(day)
        if races is not None:
            _record_races(data, day, races)
            read.add(f"{day:%Y-%m-%d}")
            done += 1
            time.sleep(pause)
    data["read"] = sorted(read)
    _add_settled(data, today)
    if json.dumps(data, sort_keys=True) != before:
        _write(data)
    return done


def update(today: datetime.date | None = None):
    """Today's and yesterday's cards and the settled terms brought up to date, and written if they changed."""
    today = today or datetime.date.today()
    data = load()
    before = json.dumps(data, sort_keys=True)
    for day in (today, today - datetime.timedelta(days=1)):
        races = _card_races(day)
        if races is not None:
            _record_races(data, day, races)
    _add_settled(data, today)
    if json.dumps(data, sort_keys=True) != before:
        _write(data)


def table_rows() -> list[dict]:
    """What the tab shows, the latest date first and each day in time order."""
    races = sorted(load()["races"].values(), key=lambda e: (e["time"], e["meeting"]))
    rows = []
    for e in sorted(races, key=lambda e: e["date"], reverse=True):
        settled = e.get("settled")
        rows.append({"date": e["date"], "time": e["time"], "meeting": e["meeting"], "runners": e["runners"], "race": "Handicap" if e["handicap"] else "Non-handicap",
                     "places": e["places"], "fraction": f"{e['top']}/{e['bottom']}", "settled": f"{settled[0]} at {settled[1]}/{settled[2]}" if settled else "",
                     "differs": bool(settled and settled != [e["places"], e["top"], e["bottom"]]), "off": bool(e.get("off"))})
    return rows
