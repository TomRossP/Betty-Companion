"""
Each till's logs on the relay (relay/worker.js 1.4.0), so the tills of a shop, and Claude on either of them, can read
both tills' logs to find what went wrong and fix it (user, 2 Nov). The window uploads what is new every
LOG_UPLOAD_SECS: the session logs, the staff journal and the screens kept when a wager goes to staff (logs/staff_*.png,
slip_*.png, reuse_*.png). A log goes up as it grows, from where the relay's copy ends. The corpus and the f8_ folders
stay on the till (too big, and only for the replay tests). A till in a shop reads its shop's tills' logs; a till in
no shop only its own.

Fetching the other tills' logs (read only; the till's own relay pass, from Windows' Credential Manager):

    python relay_logs.py                  into scratch\\imported_logs\\<till>\\, where live_report.py looks
    python relay_logs.py --all            this till's own logs too
    python relay_logs.py --to <folder>    somewhere else
    BettyCompanion.exe --fetch-logs       on a till without Python: into relay_logs\\<till>\\ next to the exe
                                          (what was fetched: relay_logs\\fetch.txt)
"""
import base64
import json
import os
import re
import sys
import time

import app_paths

# The logs the relay keeps (worker.js LOG_NAME): session logs, the staff journal, the screens kept for staff
LOG_NAME = re.compile(r"^(session_\d{8}_\d{6}\.log|staff_journal\.jsonl|(staff|slip|reuse)_[\w.-]{1,80}\.png)$")
STATE_FILE = "relay_logs.json"  # next to the exe: how much of each log the relay has, the last upload, the last error
FETCHED_FILE = "fetched.json"   # in the fetch folder: when the relay began each copy fetched there
CHUNK_BYTES = 700_000           # one upload; base64 makes it ~933,000 characters, under the relay's 1,000,000
RECENT_DAYS = 14                # logs last written longer ago than this aren't uploaded (the relay keeps 30 days)
HEAD_BYTES = 300                # a log's first bytes, kept to see when it was rewritten
ROUND_SECS = 45                # one upload round stops after this long; the next carries on where it stopped
TIMEOUT_SECS = 30


class LogsError(Exception):
    """The relay couldn't be asked. The message is fit to show."""


def state() -> dict:
    """{'sent': {log: bytes the relay has}, 'last_upload', 'error'}."""
    try:
        with open(os.path.join(app_paths.app_dir(), STATE_FILE), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(st: dict) -> dict:
    tmp = os.path.join(app_paths.app_dir(), STATE_FILE + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, os.path.join(app_paths.app_dir(), STATE_FILE))
    return st


def _post(url: str, pass_: str, path: str, body: dict):
    import relay_link
    return relay_link.requests.post(url + path, json=body, timeout=TIMEOUT_SECS,
                                    headers={"authorization": f"Bearer {pass_}"})


def _refusal(r) -> str:
    import relay_link
    if r.status_code == 401:
        return "this till isn't paired with the relay any more"
    if r.status_code == 404 and r.headers.get("x-relay-error"):
        return "the relay is older than 1.4.0: update relay\\worker.js"
    return f"the relay said: {relay_link._relay_message(r)}"


def upload() -> dict:
    """
    This till's new log lines and screens up to the relay, oldest log first, for at most ROUND_SECS. Only the built
    program on a paired till uploads: a run from the source folder (the free tests, development) never sends its logs,
    unless a test opts in with its own relay. Never raises; the error is kept in the state. Returns state().
    """
    if not app_paths.is_frozen() and os.environ.get("BETTY_LOG_UPLOAD_TEST") != "1":
        return state()
    st = state()
    try:
        import relay_link
        route = relay_link.relay_route()
    except Exception as e:
        return _save_state(dict(st, error=f"the relay link can't be read ({e})"))
    if not route:
        return _save_state(dict(st, error="not paired with the relay"))
    url, pass_ = route
    folder = app_paths.log_dir()
    sent = dict(st.get("sent") or {})
    heads = dict(st.get("heads") or {})  # each log's first bytes when sent: different now = the log was rewritten
    try:
        names = [f for f in os.listdir(folder) if LOG_NAME.match(f)]
    except OSError:
        names = []
    recent = time.time() - RECENT_DAYS * 86400
    paths = sorted((os.path.join(folder, f) for f in names), key=lambda p: os.path.getmtime(p))
    paths = [p for p in paths if os.path.getmtime(p) >= recent]
    started, error = time.time(), ""
    try:
        for path in paths:
            name, size = os.path.basename(path), os.path.getsize(path)
            with open(path, "rb") as f:
                head = f.read(HEAD_BYTES).hex()
            done = sent.get(name, 0)
            restart = bool(done) and (size < done or not head.startswith(heads.get(name, "")))
            if restart:
                done = 0
            while done < size and time.time() - started < ROUND_SECS:
                with open(path, "rb") as f:
                    f.seek(done)
                    data = f.read(CHUNK_BYTES)
                if not data:
                    break
                r = _post(url, pass_, "/logs/put", {"name": name, "start": done, "restart": restart and not done,
                                                    "data": base64.b64encode(data).decode("ascii")})
                if r.status_code == 400:  # a log the relay won't keep: not tried again
                    done = size
                    break
                if r.status_code != 200:
                    raise LogsError(_refusal(r))
                reply = r.json()
                relay_size = int(reply.get("size", done))
                # Refused when the relay's copy ends elsewhere (this state file lost, the relay dropped an old log):
                # carry on from the relay's end. A relay copy longer than the file here: left be.
                done = relay_size if reply.get("ok") or relay_size <= size else size
            sent[name] = done
            if done:
                heads[name] = head[:2 * done]  # only the bytes the relay has
            if time.time() - started >= ROUND_SECS:
                break
    except LogsError as e:
        error = str(e)
    except Exception as e:
        error = f"the relay can't be reached ({type(e).__name__})"
    sent = {k: v for k, v in sent.items() if k in names}  # logs the program has since deleted
    heads = {k: v for k, v in heads.items() if k in sent}
    return _save_state(dict(st, sent=sent, heads=heads, error=error,
                            last_upload=st.get("last_upload", "") if error else time.strftime("%Y-%m-%d %H:%M")))


def default_folder() -> str:
    """Where fetch() puts the logs: relay_logs\\ next to the exe, else scratch\\imported_logs\\ (live_report.py's)."""
    if app_paths.is_frozen():
        return os.path.join(app_paths.app_dir(), "relay_logs")
    return os.path.join(app_paths.app_dir(), "scratch", "imported_logs")


def fetch(folder: str | None = None, own: bool = False, days: int = 30) -> dict:
    """
    The shop's other tills' logs (this till's own too with `own`) into folder\\<till name>\\, each log fetched from
    where the copy here ends; its time set to when it was last added to on the relay. Raises LogsError when the relay
    can't be asked. Returns {'folder', 'tills': {till: logs}, 'files' fetched, 'bytes' fetched, 'shop'}.
    """
    import relay_link
    route = relay_link.relay_route()
    if not route:
        raise LogsError("this till isn't paired with the relay: pair it in the window's Settings first")
    url, pass_ = route
    folder = folder or default_folder()
    try:
        r = _post(url, pass_, "/logs/list", {"days": days})
    except relay_link.requests.exceptions.RequestException as e:
        raise LogsError(f"the relay can't be reached ({type(e).__name__})") from e
    if r.status_code != 200:
        raise LogsError(_refusal(r))
    listing = r.json()
    out = {"folder": folder, "tills": {}, "files": 0, "bytes": 0, "shop": listing.get("shop", "")}
    try:  # when the relay began each copy fetched here: a different start means the till rewrote that log
        with open(os.path.join(folder, FETCHED_FILE), encoding="utf-8") as f:
            started = json.load(f)
    except (OSError, ValueError):
        started = {}
    for entry in listing.get("files") or []:
        if entry.get("mine") and not own:
            continue
        till = re.sub(r"[^\w.-]+", "_", entry["till"]).strip("_") or entry["till_id"]
        out["tills"][till] = out["tills"].get(till, 0) + 1
        path = os.path.join(folder, till, entry["name"])
        key = f"{till}/{entry['name']}"
        have = os.path.getsize(path) if os.path.exists(path) else 0
        if have > entry["size"] or started.get(key, entry["started_at"]) != entry["started_at"]:
            have = 0  # not the same log as the relay's now (the till rewrote it): fetched again
        started[key] = entry["started_at"]
        start_have = have
        while have < entry["size"]:
            g = _post(url, pass_, "/logs/get", {"till_id": entry["till_id"], "name": entry["name"], "from": have})
            if g.status_code != 200:
                raise LogsError(_refusal(g))
            chunks = g.json().get("chunks") or []
            if not chunks or chunks[0]["start"] > have:
                break  # a gap on the relay (shouldn't happen): what came is kept
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "ab" if have else "wb") as f:
                for c in chunks:
                    if c["start"] > have:
                        break
                    raw = base64.b64decode(c["data"])
                    f.write(raw[have - c["start"]:])
                    have = c["start"] + len(raw)
        if have > start_have:
            out["files"] += 1
            out["bytes"] += have - start_have
        if os.path.exists(path):
            os.utime(path, (entry["updated_at"], entry["updated_at"]))
    if started:
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, FETCHED_FILE), "w", encoding="utf-8") as f:
            json.dump(started, f, indent=1)
    return out


def report(got: dict) -> str:
    tills = ", ".join(f"{t} ({n} logs)" for t, n in sorted(got["tills"].items())) or "none"
    return (f"Fetched {got['files']} new or longer log(s), {got['bytes'] / 1e6:.1f} MB, into {got['folder']}\n"
            f"Tills{' of shop ' + repr(got['shop']) if got['shop'] else ''}: {tills}")


def main(argv: list[str]) -> int:
    folder = argv[argv.index("--to") + 1] if "--to" in argv and argv.index("--to") + 1 < len(argv) else None
    try:
        text = report(fetch(folder, own="--all" in argv))
        code = 0
    except LogsError as e:
        text, code = f"Couldn't fetch the logs: {e}", 1
    print(text)
    if app_paths.is_frozen():  # a windowed exe may have nowhere to print: the result is kept beside the logs too
        try:
            os.makedirs(folder or default_folder(), exist_ok=True)
            with open(os.path.join(folder or default_folder(), "fetch.txt"), "w", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n{text}\n")
        except OSError:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
