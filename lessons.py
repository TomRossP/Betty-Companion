"""
What staff have taught Betty Companion about this shop's slips (user, 31 Oct): kept as data in lessons.json next to the
exe (this installation's own), never in the code, so the program learns a shop's quirks without being changed.

Kinds:
  runner   handwriting -> runner: 'MOVIT LIKE MINNIE' was Moveit Like Minnie (from the can't-read box). Used when that
           runner is on today's card at the written time, after the usual name match has failed.
  meeting  a meeting as this shop's customers write it: 'N/M' = Newmarket.
  wording  bet wording: 'YANKIE' = 'yankee', 'X DOUB' = 'cross doubles'. The bet line is read as if the meaning was
           written, then costed and checked as usual.
  slip     a whole slip as staff corrected it: its picture and its lines, shown to the slip reader as a worked example.

A lesson is a hint, never a pass: the racecard match, the money against the payment, the betslip read-back and Betty's
total all still apply. Any member of staff can teach one; it is active at once. A lesson whose wagers keep going to
staff with none placed is turned off by itself (AUTO_OFF_STAFF). Both processes (the window and the program) read and
write the file: every change is a locked read-modify-write, and readers pick changes up by the file's time.

Shared by a shop's tills (relay 1.3.0, phase 4): sync() sends this till's changes to the relay and takes the shop's
back; the relay works out the shop from the till's pass (a till in no shop keeps its own). lessons.json stays the
working copy, so lessons work with no internet. Each lesson carries what is still to send: 'rev' / 'pushed_rev' (its
words or status changed), 'pending' (counts not yet added on the relay: counts go as additions, so two tills never
overwrite each other's), 'deleted' (gone, to be sent), 'image_sent' (a slip's picture).
"""
import base64
import difflib
import json
import os
import re
import shutil
import socket
import time
import uuid

import app_paths

LESSONS_FILE = "lessons.json"
SYNC_FILE = "lessons_sync.json"  # when this till last synced, its shop, the last error
LESSONS_DIR = "lessons"          # slip pictures of 'slip' lessons, next to lessons.json
KINDS = {'runner': "Handwriting", 'meeting': "Meeting", 'wording': "Bet wording", 'slip': "Whole slip"}
COUNTS = ('taught', 'used', 'placed', 'staff')
INFO_FIELDS = ('context', 'source', 'created', 'till', 'note', 'lines')  # sent to the relay as one 'info'
AUTO_OFF_STAFF = 3               # wagers to staff, none placed: the lesson is turned off
RUNNER_SIMILARITY = 0.9          # how close a read name must be to a taught one (letters only)
PROMPT_LESSONS_MAX = 40          # meeting and wording lessons given to the slip reader
LOCK_SECS = 3.0
SYNC_TIMEOUT_SECS = 15
SYNC_ROUNDS = 5                  # a relay with more to hand back is asked again, up to this many times

_cache: dict = {'mtime': None, 'items': []}


def path() -> str:
    return os.path.join(app_paths.app_dir(), LESSONS_FILE)


def images_dir() -> str:
    return os.path.join(app_paths.app_dir(), LESSONS_DIR)


def letters(text) -> str:
    return re.sub(r'[^a-z0-9]', '', str(text or '').lower())


def version() -> float | None:
    """The file's time: changes whenever a lesson does (callers cache on it)."""
    try:
        return os.path.getmtime(path())
    except OSError:
        return None


def _all() -> list[dict]:
    """Every lesson in the file, deleted ones still to be sent included; re-read only when the file has changed."""
    v = (path(), version())  # the file and its time: another folder with no lessons.json yet is not this one
    if v != _cache['mtime']:
        try:
            with open(path(), encoding="utf-8") as f:
                items = json.load(f)
            _cache['items'] = items if isinstance(items, list) else []
        except (OSError, ValueError):
            _cache['items'] = []
        _cache['mtime'] = v
    return _cache['items']


def load() -> list[dict]:
    """Every lesson (not the deleted ones waiting to be sent)."""
    return [x for x in _all() if not x.get('deleted')]


class _Locked:
    """A lock file: one writer at a time across the window and the program. `wait`: how long to wait for it."""

    def __init__(self, name: str = LESSONS_FILE + ".lock", wait: float = LOCK_SECS):
        self.lock = os.path.join(app_paths.app_dir(), name)
        self.wait = wait

    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:  # a lock left by a crash is old: taken over
                    if time.time() - os.path.getmtime(self.lock) > max(LOCK_SECS, self.wait) * 4 + SYNC_TIMEOUT_SECS:
                        os.remove(self.lock)
                        continue
                except OSError:
                    pass
                if time.time() - t0 > self.wait:
                    raise TimeoutError("lessons.json is busy")
                time.sleep(0.05)

    def __exit__(self, *exc):
        os.close(self.fd)
        try:
            os.remove(self.lock)
        except OSError:
            pass


def _change(fn):
    """Locked: the file as it is now, changed by fn(items), written back whole (a temporary file, then replaced)."""
    with _Locked():
        _cache['mtime'] = None
        items = [dict(x) for x in _all()]
        result = fn(items)
        tmp = path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=1, ensure_ascii=False)
        os.replace(tmp, path())
        _cache['mtime'] = None
        return result


def _pend(x: dict, field: str, n: int = 1):
    """A count up by n, here and in what is still to be added on the relay."""
    x[field] = x.get(field, 0) + n
    x['pending'] = dict(x.get('pending') or {})
    x['pending'][field] = x['pending'].get(field, 0) + n


def _edited(x: dict):
    x['rev'] = x.get('rev', 0) + 1


def add(kind: str, written: str, means: str, context: dict | None = None, source: str = "", image: str | None = None,
        lines: list[str] | None = None, note: str = "") -> dict | None:
    """
    A new lesson, active at once; the same lesson taught again counts it again (and turns it back on). A slip
    picture is copied into lessons/, so it outlives the logs. None for one with nothing to learn.
    """
    written, means = str(written or '').strip(), str(means or '').strip()
    if kind not in KINDS or not written or not means or (kind != 'slip' and letters(written) == letters(means)):
        return None
    if image and os.path.isfile(image) and kind == 'slip':
        os.makedirs(images_dir(), exist_ok=True)
        kept = os.path.join(images_dir(), f"slip_{uuid.uuid4().hex[:8]}{os.path.splitext(image)[1] or '.png'}")
        shutil.copy2(image, kept)
        image = kept

    def go(items):
        for x in items:
            if (x['kind'] == kind and kind != 'slip' and not x.get('deleted')
                    and letters(x['written']) == letters(written) and letters(x['means']) == letters(means)):
                _pend(x, 'taught')
                if x.get('status') != 'active':
                    x['status'] = 'active'
                    _edited(x)
                return dict(x)
        lesson = {'id': uuid.uuid4().hex[:10], 'kind': kind, 'written': written, 'means': means,
                  'context': context or {}, 'source': source, 'created': time.strftime('%Y-%m-%d %H:%M'),
                  'till': socket.gethostname(), 'status': 'active', 'taught': 0, 'used': 0, 'placed': 0, 'staff': 0,
                  'last_used': '', 'image': image, 'lines': lines or [], 'note': note,
                  'rev': 1, 'pushed_rev': 0, 'pending': {}, 'image_sent': kind != 'slip' or not image}
        _pend(lesson, 'taught')
        items.append(lesson)
        return dict(lesson)
    return _change(go)


def set_status(lesson_id: str, status: str):
    def go(items):
        for x in items:
            if x['id'] == lesson_id and x.get('status') != status:
                x['status'] = status
                _edited(x)
    _change(go)


def delete(lesson_id: str):
    """Gone here; when this till is paired, kept as 'deleted' until the relay has it, so the shop's other tills drop
    it too."""
    shared = _paired()

    def go(items):
        gone = [x for x in items if x['id'] == lesson_id]
        if shared:
            for x in gone:
                x['deleted'] = True
                _edited(x)
        else:
            items[:] = [x for x in items if x['id'] != lesson_id]
        return gone
    for x in _change(go):
        _remove_image(x)


def _remove_image(x: dict):
    img = x.get('image')
    if img and os.path.dirname(os.path.abspath(img)) == os.path.abspath(images_dir()):
        try:
            os.remove(img)
        except OSError:
            pass


def mark_used(ids):
    ids = set(ids)
    if not ids:
        return

    def go(items):
        for x in items:
            if x['id'] in ids:
                _pend(x, 'used')
                x['last_used'] = time.strftime('%Y-%m-%d %H:%M')
    _change(go)


def record_outcome(ids, placed: bool) -> list[dict]:
    """A wager that used these lessons was placed, or went to staff. A lesson with AUTO_OFF_STAFF wagers to staff
    and none placed is turned off; those are returned (for the log)."""
    ids = set(ids)
    if not ids:
        return []

    def go(items):
        off = []
        for x in items:
            if x['id'] in ids:
                _pend(x, 'placed' if placed else 'staff')
                if x['status'] == 'active' and x.get('placed', 0) == 0 and x.get('staff', 0) >= AUTO_OFF_STAFF:
                    x['status'] = 'off'
                    _edited(x)
                    off.append(dict(x))
        return off
    return _change(go)


def active(kind: str) -> list[dict]:
    return [x for x in load() if x['kind'] == kind and x.get('status') == 'active']


def runner_lessons(read_name: str) -> list[dict]:
    """Active handwriting lessons for a name as read (letters only, RUNNER_SIMILARITY or closer), closest first."""
    read = letters(read_name)
    if len(read) < 3:
        return []
    scored = [(difflib.SequenceMatcher(None, read, letters(x['written'])).ratio(), x) for x in active('runner')]
    return [x for s, x in sorted(scored, key=lambda p: -p[0]) if s >= RUNNER_SIMILARITY]


def meeting_for(written: str) -> dict | None:
    """The active meeting lesson for a meeting as written (letters only, exactly)."""
    w = letters(written)
    return next((x for x in active('meeting') if letters(x['written']) == w), None) if len(w) >= 2 else None


def apply_wording(text: str) -> tuple[str, list[dict]]:
    """Bet wording read as taught: each active wording lesson's words, whole and in any case and spacing, replaced by
    its meaning. (text, lessons used)."""
    used = []
    for x in sorted(active('wording'), key=lambda x: -len(x['written'])):  # longest first: 'SUPER YANKIE' before 'YANKIE'
        words = [re.escape(w) for w in re.split(r'\s+', x['written'].strip()) if w]
        pattern = r'(?<![A-Za-z0-9])' + r'\s*'.join(words) + r'(?![A-Za-z0-9])'
        new = re.sub(pattern, x['means'], text, flags=re.I)
        if new != text:
            used.append(x)
            text = new
    return text, used


def prompt_section() -> tuple[str, list[dict]]:
    """This shop's taught shorthand for the slip reader's instructions ('' when none), with the lessons in it."""
    taught = (active('meeting') + active('wording'))[-PROMPT_LESSONS_MAX:]
    if not taught:
        return "", []
    lines = [f"- \"{x['written']}\" = {x['means']}" for x in taught]
    return ("THIS SHOP'S SHORTHAND (taught by the shop's staff; use it where the handwriting allows it):\n"
            + "\n".join(lines) + "\n"), taught


def slip_examples(n: int = 2) -> list[dict]:
    """The newest active whole-slip lessons whose picture is still there, for the slip reader."""
    out = [x for x in active('slip') if x.get('image') and os.path.isfile(x['image']) and x.get('lines')]
    return out[-n:]


# --- Shared with the shop's other tills through the relay (phase 4) ---

def _paired() -> bool:
    try:
        import relay_link
        return relay_link.relay_route() is not None
    except Exception:
        return False


def sync_state() -> dict:
    """{'shared': paired with the relay, 'shop': the relay's shop for this till ('' = none), 'last_sync', 'error'}."""
    try:
        with open(os.path.join(app_paths.app_dir(), SYNC_FILE), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    return {'shared': False, 'shop': '', 'since': 0, 'last_sync': '', 'error': '', **state}


def _save_state(**changes) -> dict:
    state = {**sync_state(), **changes}
    tmp = os.path.join(app_paths.app_dir(), SYNC_FILE + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, os.path.join(app_paths.app_dir(), SYNC_FILE))
    return state


def _outgoing(x: dict) -> dict | None:
    """What a lesson still has to send to the relay, or None when it's all there."""
    pending = {k: v for k, v in (x.get('pending') or {}).items() if v}
    never_sent = 'pushed_rev' not in x  # taught by 1.1.12, before sharing: all of it goes, counts included
    if never_sent:
        pending = {k: x.get(k, 0) for k in COUNTS if x.get(k)}
    picture = x['kind'] == 'slip' and not x.get('image_sent') and x.get('image') and os.path.isfile(x['image'])
    if not never_sent and x.get('rev', 0) == x.get('pushed_rev', 0) and not pending and not x.get('deleted') \
            and not picture:
        return None
    change = {'id': x['id'], 'kind': x['kind'], 'written': x['written'], 'means': x['means'],
              'info': {k: x.get(k) for k in INFO_FIELDS}, 'status': x.get('status', 'active'),
              'deleted': bool(x.get('deleted')), 'add': pending, 'last_used': x.get('last_used', '')}
    if picture:
        with open(x['image'], "rb") as f:
            change['image_png'] = base64.b64encode(f.read()).decode('ascii')
    return change


def _merge(items: list[dict], sent: dict[str, dict], remote: list[dict]) -> list[str]:
    """Into the file's lessons: what the relay now has (sent) taken off what was still to send, then the shop's
    lessons as the relay has them. A lesson edited here since it was sent keeps its words and status. Returns the
    slip lessons whose picture is still to fetch."""
    by_id = {x['id']: x for x in items}
    for lid, change in sent.items():
        x = by_id.get(lid)
        if not x:
            continue
        x['pending'] = {k: v - change['add'].get(k, 0) for k, v in (x.get('pending') or {}).items()
                        if v - change['add'].get(k, 0) > 0}
        if x.get('rev', 0) == change['_rev']:
            x['pushed_rev'] = change['_rev']
        if 'image_png' in change:
            x['image_sent'] = True
        if change['deleted'] and x.get('rev', 0) == change['_rev']:
            items.remove(x)
            del by_id[lid]
    fetch = []
    for r in remote:
        x = by_id.get(r['id'])
        if r.get('deleted'):
            if x:
                _remove_image(x)
                items.remove(x)
                del by_id[r['id']]
            continue
        if not x:
            x = {'id': r['id'], 'rev': 0, 'pushed_rev': 0, 'pending': {}, 'image_sent': True, 'image': None}
            items.append(x)
            by_id[r['id']] = x
        if x.get('rev', 0) == x.get('pushed_rev', 0):  # nothing changed here since it was sent: the relay's word
            x.update(kind=r['kind'], written=r['written'], means=r['means'], status=r['status'],
                     **{k: (r.get('info') or {}).get(k) for k in INFO_FIELDS})
            x['context'] = x.get('context') or {}
            x['lines'] = x.get('lines') or []
        for k in COUNTS:
            x[k] = r.get(k, 0) + (x.get('pending') or {}).get(k, 0)
        x['last_used'] = max(str(x.get('last_used') or ''), str(r.get('last_used') or ''))
        if r['kind'] == 'slip' and r.get('has_image') and not (x.get('image') and os.path.isfile(x['image'])):
            fetch.append(r['id'])
    return fetch


def sync() -> dict:
    """
    This till's lessons and the shop's, made the same through the relay: what changed here goes up, what changed on
    the shop's other tills comes down (pictures of whole-slip lessons too). Not paired: nothing to do. One sync at a
    time across the window and the program (another one running: this one returns at once). Never raises: the
    lessons here keep working whatever the relay says; the error is kept for the Training tab. Returns sync_state().
    """
    if not app_paths.is_frozen() and os.environ.get("BETTY_LESSONS_SYNC_TEST") != "1":
        # Only the built program on a till shares: a run from the source folder (the free tests, this PC's own
        # development) never reaches the shop's relay with its made-up lessons, unless a test opts in with its own
        # relay (scratch/test_lessons_sync.py)
        return sync_state()
    try:
        import relay_link
        route = relay_link.relay_route()
    except Exception as e:
        return _save_state(shared=False, error=f"the relay link can't be read ({e})")
    if not route:
        return _save_state(shared=False, error='')
    url, pass_ = route
    try:
        with _Locked(SYNC_FILE + ".lock", wait=0.2):
            for _ in range(SYNC_ROUNDS):
                state = sync_state()
                with _Locked():
                    sent = {}
                    for x in _all():
                        change = _outgoing(x)
                        if change:
                            sent[x['id']] = dict(change, _rev=x.get('rev', 0))
                body = {'since': state.get('since', 0),
                        'changes': [{k: v for k, v in c.items() if k != '_rev'} for c in sent.values()]}
                r = relay_link.requests.post(url + "/lessons/sync", json=body, timeout=SYNC_TIMEOUT_SECS,
                                             headers={"authorization": f"Bearer {pass_}"})
                if r.status_code == 401:
                    return _save_state(shared=False, error="this till isn't paired with the relay any more")
                if r.status_code == 404:
                    return _save_state(shared=False, error="the relay is older than 1.3.0: update relay\\worker.js")
                if r.status_code != 200:
                    return _save_state(error=f"the relay said: {relay_link._relay_message(r)}")
                data = r.json()
                fetch = _change(lambda items: _merge(items, sent, data.get('lessons') or []))
                for lid in fetch:
                    _fetch_image(url, pass_, lid)
                state = _save_state(shared=True, shop=data.get('shop') or '', since=data.get('now', 0),
                                    last_sync=time.strftime('%Y-%m-%d %H:%M'), error='')
                if not data.get('more'):
                    return state
            return state
    except TimeoutError:
        return sync_state()  # another sync is running, or the file is busy: the next round catches up
    except Exception as e:
        return _save_state(error=f"the relay can't be reached ({type(e).__name__})")


def _fetch_image(url: str, pass_: str, lesson_id: str):
    """A shop slip lesson's picture, from the relay into lessons/."""
    import relay_link
    r = relay_link.requests.post(url + "/lessons/image", json={'id': lesson_id}, timeout=SYNC_TIMEOUT_SECS,
                                 headers={"authorization": f"Bearer {pass_}"})
    if r.status_code != 200:
        return
    os.makedirs(images_dir(), exist_ok=True)
    pic = os.path.join(images_dir(), f"slip_{lesson_id}.png")
    with open(pic, "wb") as f:
        f.write(base64.b64decode(r.json()['png']))

    def go(items):
        for x in items:
            if x['id'] == lesson_id:
                x['image'] = pic
    _change(go)
