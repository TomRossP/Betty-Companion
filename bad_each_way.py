"""
Bad each way races, for Data > Bad each way on the manager till: a log and nothing more. It never touches a bet.

A race is bad each way when its fixed place terms pay more than a runner's real chance of placing: usually a few short-priced
horses and a long tail. Each UK and Irish runner's chance of winning is taken from Betty's prices with the margin removed, its chance
of placing worked out from those, and its edge is what £1 on the place part should make at the place terms. A runner at EDGE_FLAG or
more is logged with its race, in Documents\\BettyCompanion Records\\bad_each_way\\<yyyymmdd>.json, and followed to its result.

Tried on 763 UK and Irish races at SP, 16 Oct - 6 Nov: 182 runners at 10% or more, in 67 races, returned +44.7% on the place part, but +11.7% without one 300/1 shot that
placed and -1.7% without the best five. The whole each way bet returned -10.0% without that one, so a punter gains mainly by laying the win part elsewhere. Too few races to
prove it, and the reason this only logs.
"""
import datetime
import json
import os
import time

import till_records

EDGE_FLAG = 0.10
NO_PRICE_BOTTOM = 10000  # 1/10001 is no price, only a row being added
DOMESTIC = "domestic"


def default_terms(handicap: bool, field: int) -> tuple[int, int, int] | None:
    """(places, top, bottom) of the fraction Betty settles on by default (every default race in SETTDATA, 16 Oct - 6 Nov), None when it's win only."""
    if field < 5:
        return None
    if field < 8:
        return 2, 1, 4
    if handicap and field >= 16:
        return 4, 1, 4
    if handicap and field >= 12:
        return 3, 1, 4
    return 3, 1, 5


def place_chances(wins: list[float], places: int) -> list[float]:
    """Each runner's chance of finishing in the first `places`, from its chance of winning: of those left, each next finisher in proportion to those chances."""
    chances = [0.0] * len(wins)
    layer = {0: (1.0, 0.0)}  # who has finished, as a bit mask -> (the chance of that, their share of the win chances)
    for _ in range(places):
        following: dict[int, tuple[float, float]] = {}
        for gone, (chance, share) in layer.items():
            left = 1.0 - share
            if left <= 1e-12:
                continue
            for i, win in enumerate(wins):
                if gone >> i & 1:
                    continue
                next_chance = chance * win / left
                chances[i] += next_chance
                key = gone | 1 << i
                following[key] = (following[key][0] + next_chance if key in following else next_chance, share + win)
        layer = following
    return chances


def price_odds(price: str) -> float | None:
    """'11-4' as 2.75; None for no price."""
    top, _, bottom = (price or "").partition("-")
    if not top.isdigit() or not bottom.isdigit() or not int(top) or not 0 < int(bottom) < NO_PRICE_BOTTOM:
        return None
    return int(top) / int(bottom)


def score_race(rows: list[dict]) -> dict | None:
    """
    One race's card rows scored: {'field', 'handicap', 'places', 'top', 'bottom', 'runners': [{'number', 'name', 'price', 'edge'}]}, without its
    non-runners. None when it can't be: win only, a runner still without a price, or prices that add up to less than a full book.
    """
    field = [r for r in rows if not r.get("out")]
    extra = rows[0].get("extra_terms") if rows else None
    terms = tuple(extra) if extra else default_terms(bool(rows and rows[0].get("handicap")), len(field))
    if not terms or terms[0] < 2:
        return None
    odds = [price_odds(r.get("price", "")) for r in field]
    if not field or None in odds:
        return None
    places, top, bottom = terms
    if len(field) <= places:
        return None
    raw = [1 / (1 + o) for o in odds]
    if sum(raw) < 1:  # no margin at all: these prices aren't a whole market (Bath 13:42, 29 Oct, 71%)
        return None
    wins = [x / sum(raw) for x in raw]
    chances = place_chances(wins, places)
    return {"field": len(field), "handicap": bool(rows[0].get("handicap")), "places": places, "top": top, "bottom": bottom,
            "runners": [{"number": r.get("number"), "name": r["name"], "price": r["price"],
                         "edge": round(chances[i] * (1 + odds[i] * top / bottom) - 1, 4)} for i, r in enumerate(field)]}


# --- The log ---

def _folder() -> str:
    return os.path.join(till_records.records_dir(), "bad_each_way")


def _path(date: str) -> str:
    return os.path.join(_folder(), date.replace("-", "") + ".json")


def load_day(date: str) -> dict:
    try:
        with open(_path(date), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"date": date, "races": []}


def days_on_file() -> list[str]:
    """'yyyy-mm-dd' of each day logged, newest first."""
    try:
        names = os.listdir(_folder())
    except OSError:
        return []
    return sorted((f"{n[:4]}-{n[4:6]}-{n[6:8]}" for n in names if n.endswith(".json") and len(n) == 13), reverse=True)


def _write(data: dict):
    path = _path(data["date"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _update_race(logged: dict | None, race: dict, scored: dict, seen: str) -> dict | None:
    """The race's log entry with `scored` on it: new runners at EDGE_FLAG or more added, those already logged kept up to date."""
    new = {r["name"]: r for r in scored["runners"]}
    flagged = [r for r in scored["runners"] if r["edge"] >= EDGE_FLAG]
    if not logged and not flagged:
        return None
    entry = logged or {**race, "runners": []}
    entry.update(field=scored["field"], handicap=scored["handicap"], places=scored["places"], top=scored["top"], bottom=scored["bottom"])
    for run in entry["runners"]:
        now = new.get(run["name"])
        if now:
            run.update(price=now["price"], edge=now["edge"], nr=False)
        else:
            run.update(nr=True)
    have = {run["name"] for run in entry["runners"]}
    for r in flagged:
        if r["name"] not in have:
            entry["runners"].append({"number": r["number"], "name": r["name"], "first_seen": seen, "first_price": r["price"], "first_edge": r["edge"],
                                     "price": r["price"], "edge": r["edge"], "nr": False})
    return entry


def _add_results(data: dict) -> bool:
    """Who placed, from the Past results record. True when anything changed."""
    on_file = {r.get("event_id"): r for r in till_records.load_day(data["date"]).get("races", [])}
    changed = False
    for race in data["races"]:
        result = on_file.get(race["event_id"])
        if not result or not result.get("settled"):
            continue
        places = {x["name"]: x.get("place") for x in result["runners"]}
        for run in race["runners"]:
            place = places.get(run["name"])
            if run.get("settled") is not True or run.get("place") != place:
                run.update(settled=True, place=place)
                changed = True
    return changed


def record_day(runners: list[dict], day: datetime.date | None = None) -> dict:
    """The day's log brought up to date from the card's rows (BettyFeedCard.get_runners), and written if it changed. The log."""
    day = day or datetime.date.today()
    data = load_day(f"{day:%Y-%m-%d}")
    races: dict[int, list[dict]] = {}
    for r in runners:
        if r.get("category") == DOMESTIC:
            races.setdefault(r["event_id"], []).append(r)
    before = json.dumps(data["races"], sort_keys=True)
    by_event = {r["event_id"]: r for r in data["races"]}
    seen, checked = time.strftime("%H:%M"), 0
    for event, rows in races.items():
        out = {r["name"] for r in rows if r.get("out")}
        for run in by_event.get(event, {}).get("runners", ()):  # whether or not the rest can be scored: a favourite out leaves less than a full book
            if run["name"] in out:
                run["nr"] = True
        scored = score_race(rows)
        if not scored:
            continue
        checked += 1
        entry = _update_race(by_event.get(event), {"event_id": event, "meeting": rows[0]["meeting"], "time": rows[0]["time_str"]}, scored, seen)
        if entry and event not in by_event:
            by_event[event] = entry
            data["races"].append(entry)
    data["races"].sort(key=lambda r: (r["time"], r["meeting"]))
    _add_results(data)
    counts = {"on_card": len(races), "checked": checked}
    if json.dumps(data["races"], sort_keys=True) != before or {k: data.get(k) for k in counts} != counts:
        data.update(counts, recorded=time.strftime("%Y-%m-%d %H:%M"))
        _write(data)
    return data


def record_results(day: datetime.date) -> None:
    """A late result or a resettled race, on a day that's over."""
    data = load_day(f"{day:%Y-%m-%d}")
    if data["races"] and _add_results(data):
        _write(data)


def _result_text(race: dict, run: dict) -> str:
    if run.get("nr"):
        return "Non-runner"
    if not run.get("settled"):
        return ""
    place = run.get("place")
    return f"Placed ({place})" if place and place <= race["places"] else "Lost"


def day_rows(date: str) -> dict:
    """What the tab shows: {'recorded', 'on_card', 'checked', 'flagged', 'rows': [{...}]}, a row for each runner logged, in race order, the biggest edge first."""
    data = load_day(date)
    rows = []
    for race in data["races"]:
        for run in sorted(race["runners"], key=lambda r: -r["edge"]):
            rows.append({"time": race["time"], "meeting": race["meeting"], "number": run.get("number"), "name": run["name"],
                         "race": f"{'Hcap' if race.get('handicap') else 'Non-hcap'}, {race['field']} runners",
                         "terms": f"{race['places']} at {race['top']}/{race['bottom']}", "price": run["price"].replace("-", "/"), "edge": run["edge"],
                         "first_seen": run["first_seen"], "first_price": run["first_price"].replace("-", "/"), "first_edge": run["first_edge"],
                         "result": _result_text(race, run), "dropped": run.get("nr") or run["edge"] < EDGE_FLAG})
    return {"recorded": data.get("recorded", ""), "on_card": data.get("on_card", 0), "checked": data.get("checked", 0), "flagged": len(data["races"]), "rows": rows}
