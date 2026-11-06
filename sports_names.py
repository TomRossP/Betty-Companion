"""
Football on handwritten slips: what a customer writes, which team that is, and how Betty's shop feed names it
(sports_team_names.json, researched 5 Nov 2026; its '_how' says how it's kept). 'spurs' is Tottenham Hotspur, so that's what
is looked for in the feed and typed into the Master Index. Added to, never guessed: a written name that isn't in the table
isn't understood, and one under two teams means what the user ruled, or needs the opponent on the slip to settle it.
"""
import json
import re
import unicodedata

import app_paths

USE_OPPONENT = "use opponent"
MATCH_MARKETS = {"match betting", "full time result", "match result"}  # a team to win in 90 minutes, as the files call it
# Words on a football slip that mean some other bet than the team to win in 90 minutes
OTHER_MARKET = re.compile(r"\b(btts|both teams|over|under|correct score|corners?|cards?|scorer|goals?|hat.?trick|half.?time|"
                          r"ht|first half|double chance|draw no bet|handicap|to qualify|to lift|outright)\b", re.IGNORECASE)
_table: dict | None = None
_by_written: dict[str, list[dict]] = {}


def clean(text: object) -> str:
    """As the table compares names: no capitals, accents, full stops or apostrophes."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[.'’]", "", text).split())


def table() -> dict:
    global _table
    if _table is None:
        with open(app_paths.data_file("sports_team_names.json"), encoding="utf-8") as f:
            _table = json.load(f)
        for team in _table["teams"]:
            for written in {team["name"], *team.get("shorthand", []), *team.get("till", []), *team.get("former", [])}:
                listed = _by_written.setdefault(clean(written), [])
                if team not in listed:
                    listed.append(team)
    return _table


def teams_for(written: str) -> list[dict]:
    table()
    return list(_by_written.get(clean(written), []))


def _opponent_settles(teams: list[dict], slip_words: str) -> dict | None:
    """The one team of `teams` whose opponent is named with ' v ' on the slip: 'city v arsenal'. Else None."""
    words = clean(slip_words)
    found = []
    for team in teams:
        names = {clean(n) for n in (team["name"], *team.get("shorthand", []), *team.get("till", []))}
        for other in {clean(n) for t in table()["teams"] if t is not team for n in (t["name"], *t.get("till", []))}:
            if any(re.search(rf"\b{re.escape(n)} v {re.escape(other)}\b|\b{re.escape(other)} v {re.escape(n)}\b", words)
                   for n in names):
                found.append(team)
                break
    return found[0] if len(found) == 1 else None


def team_for(written: str, slip_words: str = "") -> dict | None:
    """The team a written name means: the only one, the user's ruling, or the one the opponent on the slip settles."""
    teams = teams_for(written)
    if len(teams) <= 1:
        return teams[0] if teams else None
    ruling = table()["rulings"].get(clean(written))
    if ruling and ruling != USE_OPPONENT:
        return next((t for t in teams if t["name"] == ruling), None)
    return _opponent_settles(teams, slip_words)


def other_market_words(slip_words: str) -> str | None:
    """Words on the slip saying it's some other bet than a team to win in 90 minutes, or None."""
    m = OTHER_MARKET.search(slip_words or "")
    return m.group(0) if m else None


def match_bet(team: dict, records: list[dict], after: float, price: object = None) -> dict | None:
    """
    The team's next match bet in Betty's files, kicking off after `after` (when the bet was struck). When more than one match
    is listed, the first at the written price, else the first. Ready for the Master Index, as a Request A Bet's line is.
    """
    names = {clean(n) for n in (*team.get("till", []), team["name"])}
    when = lambda r: r.get("kickoff", r.get("starts", 0))  # noqa: E731
    rows = sorted((r for r in records if clean(r.get("market")) in MATCH_MARKETS and clean(r.get("result")) in names
                   and when(r) >= after), key=when)
    if not rows:
        return None
    written = str(price or "").replace("/", "-").strip().lower()
    row = next((r for r in rows if r.get("price") == written), rows[0])
    return {"text": f"{row['event']} {row['market']} {row['result']}", "event": row["event"], "market": row["market"],
            "result": row["result"], "how": "team table", "file_price": row.get("price"), "team": team["name"]}
