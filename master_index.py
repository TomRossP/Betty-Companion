"""
Betty's Master Index: a search across every folder, and how sports selections are entered. The same for a Request A Bet
(the request's typed text) and a handwritten slip. A list row is event and market on the left, the result in the middle
and the price on the right; the rows are 12 to a page, and Betty cuts off what doesn't fit.

The index is finicky (user, 5 Nov): a search can show nothing, "No selections found", or one record over and over, and
it can still show the last search for a moment after a key. So a list is believed only when every row holds what was
typed (classify_list), and a row is taken only when it fits the selection (choose_row).

No screen, no keys: betty_companion.py reads the screen, presses the keys and calls these.
"""
import json
import os
import re
from difflib import SequenceMatcher
from fractions import Fraction

import app_paths

MARKETS_FILE = "sports_markets.json"
GLYPHS_FILE = "index_price_glyphs.json"
LETTERS_SAME = 0.85       # how alike two readings' letters must be: OCR slips on small text, digits and signs must agree
PART_SAME = 0.8           # a typed part found in a row, allowing for a slip or Betty's cut-off
SEARCH_EVENT_CHARS = 12   # the start of the event typed: 'monaco v fc', 'agf aarhus'. Enough to leave a page or two
SHORT_EVENT_CHARS = 6     # a shorter start, tried when the longer one finds nothing
SEARCH_RESULT_CHARS = 24  # Betty stores a result in 24 characters
MARKET_MAY_BE_CUT = 17    # characters of a market (with spaces) from which the left column may have cut it off
GHOST_REPEATS = 3         # the same row this many times is Betty repeating one record, not a list


def clean(text: str) -> str:
    """Lower case, letters, digits and the signs that matter ('Handicap +1' is not 'Handicap -1'), nothing else."""
    return re.sub(r'[^a-z0-9+\-.]', '', str(text or '').lower().replace('–', '-').replace('—', '-'))


def _close(a: str, b: str) -> bool:
    """Two cleaned readings of one text: the same digits and signs in the same order (2.5 is never 3.5), and letters
    alike but for a slip or two."""
    if a == b:
        return True
    if not a or not b or re.sub(r'[a-z]', '', a) != re.sub(r'[a-z]', '', b):
        return False
    return SequenceMatcher(None, re.sub(r'[^a-z]', '', a), re.sub(r'[^a-z]', '', b)).ratio() >= LETTERS_SAME


def _holds(text: str, part: str) -> bool:
    """A cleaned `part` is somewhere in cleaned `text`, allowing for a slip in its letters, or for Betty's cut-off at the
    text's end. Its digits and signs must be there as they are ('over 3.5' is not in 'over 2.5')."""
    if not part or part in text:
        return True
    digits = re.sub(r'[a-z]', '', part)
    if digits and digits not in re.sub(r'[a-z]', '', text):
        return False
    n = len(part)
    return any(SequenceMatcher(None, text[i:i + n], part).ratio() >= PART_SAME for i in range(max(1, len(text) - n // 2)))


def price_fraction(price: str | None) -> Fraction | None:
    """A price as a fraction: '19/20' and '19-20' -> 19/20, 'Evens' and '1/1' -> 1, '5.00' (decimal) -> 4. None for SP,
    NR, NO and anything unread."""
    p = str(price or '').strip().lower()
    if p in ('evs', 'evens', 'ev', 'evn'):
        return Fraction(1)
    m = re.fullmatch(r'(\d+)\s*[/-]\s*(\d+)', p)
    if m and int(m.group(2)):
        return Fraction(int(m.group(1)), int(m.group(2)))
    if re.fullmatch(r'\d+\.\d+', p) and float(p) > 1:
        return Fraction(p) - 1
    return None


def same_price(a: str | None, b: str | None) -> bool:
    """The same price however it's written; False when either isn't a price."""
    x, y = price_fraction(a), price_fraction(b)
    return x is not None and x == y


# --- The market names: where a line's event stops and its result starts when Betty's files can't say ---
_markets: dict = {'path': None, 'mtime': None, 'names': []}


def known_markets() -> list[str]:
    """The market names in sports_markets.json (a shop's own copy wins), longest first, read again when it's edited."""
    path = app_paths.data_file(MARKETS_FILE)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    if (path, mtime) == (_markets['path'], _markets['mtime']):
        return _markets['names']
    try:
        with open(path, encoding="utf-8") as f:
            names = [str(n).strip() for n in json.load(f)['markets'] if str(n).strip()]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"[-] {MARKETS_FILE} can't be read: {e}")
        names = []
    _markets.update(path=path, mtime=mtime, names=sorted(set(names), key=len, reverse=True))
    return _markets['names']


def record_key(event: str, market: str, result: str) -> str:
    """What a request line and a record in Betty's files are matched on: nothing marks where the parts of a line end."""
    return clean(f"{event}{market}{result}")


def find_record(line: str, records: dict | None) -> dict | None:
    """The record in Betty's files for a line, allowing for an OCR slip in a name ('Lincoln RI' for 'Lincoln Rl'). The
    file's own spelling is then what gets typed. None when it isn't there, or when more than one is that close."""
    if not records:
        return None
    key = clean(line)
    if key in records:
        return records[key]
    close = [k for k in records if abs(len(k) - len(key)) <= 2 and _close(k, key)]
    return records[close[0]] if len(close) == 1 else None


def split_line(text: str, records: dict | None = None) -> dict:
    """
    'AGF Aarhus v Braga Goals Over Under Over 2.5' -> event, market, result (user: always that order, with nothing
    between them). Betty's files first (`records`, by record_key), then the market names, longest first. 'how' says
    which; neither leaves event, market and result empty, and the row is found from the whole line (fits_row).
    """
    line = " ".join(str(text or '').split())
    out = {'text': line, 'event': '', 'market': '', 'result': '', 'how': 'none'}
    found = find_record(line, records)
    if found:
        return dict(out, event=found['event'], market=found['market'], result=found['result'], how='files',
                    file_price=found.get('price'))
    for name in known_markets():
        hits = list(re.finditer(rf'(?<=\s){re.escape(name)}(?=\s)', line, re.IGNORECASE))
        if hits:
            m = hits[-1]
            return dict(out, event=line[:m.start()].strip(), market=m.group(0), result=line[m.end():].strip(),
                        how='markets')
    return out


def _typable(text: str, chars: int) -> str:
    """The start of `text` as typed in the search box: lower case, up to the first character that isn't plainly
    typable, no trailing ' v'."""
    text = re.sub(r"[^a-z0-9 .;'/\-].*$", '', str(text or '').lower())[:chars].strip()
    return re.sub(r'\s+v$', '', text).strip()


def search_wordings(sel: dict) -> list[str]:
    """
    What to type for a selection, best first. The user's way: the result, ';', the start of the event, which leaves a
    row or a page ('over 2.5; monaco v fc'). A shorter start next, since a letter misread in a name ('Lincoln Rl' as
    'Lincoln RI') finds nothing. Then the event alone, paged through, since a result typed wrongly or a line that
    couldn't be split must not stop the search.
    """
    event = sel.get('event') or sel.get('text') or ''
    start = _typable(event, SEARCH_EVENT_CHARS)
    short = _typable(event, SHORT_EVENT_CHARS)
    result = _typable(sel.get('result'), SEARCH_RESULT_CHARS)
    wordings = [f"{result}; {start}", f"{result}; {short}"] if result and start else []
    wordings += [start, short]
    return list(dict.fromkeys(w for w in wordings if w))


def market_may_be_cut(row: dict) -> bool:
    """The left column may have cut this row's market off, so another market could read the same."""
    return len(str(row.get('market') or '').strip()) >= MARKET_MAY_BE_CUT


def fits_row(row: dict, sel: dict) -> bool:
    """
    The row's event, market and result fit the selection's line, whole or as Betty cut them off. The line is matched
    as one text so it needn't have been split: it starts with the event, ends with the result, and what's between
    starts with the market. A market short enough not to have been cut off must be all that's between.
    """
    text = clean(sel.get('text') or f"{sel.get('event', '')}{sel.get('market', '')}{sel.get('result', '')}")
    ev, mk, rs = clean(row.get('event')), clean(row.get('market')), clean(row.get('result'))
    if not (text and ev and mk and rs) or len(ev) + len(rs) >= len(text):
        return False
    if not _close(text[:len(ev)], ev) or not _close(text[-len(rs):], rs):
        return False
    between = text[len(ev):-len(rs)]
    if market_may_be_cut(row):
        return _close(between[:len(mk) - 1], mk[:-1])  # the last letter shown may be half cut off
    return _close(between, mk)


def choose_row(rows: list[dict], sel: dict) -> dict:
    """
    The row to click. {'row': it or None, 'fits': rows that fit, 'why'}. Text decides, and the wager takes the price
    when struck, so a moved price doesn't stop it (user, 5 Nov). Price only tells rows apart that read alike ('Both
    Teams To Scor' is two markets): the requested price, then the price in Betty's files for this exact market.
    """
    fits = [r for r in rows if r.get('usable', True) and fits_row(r, sel)]
    if not fits:
        return {'row': None, 'fits': [], 'why': 'no row fits'}
    if len(fits) == 1:
        return {'row': fits[0], 'fits': fits, 'why': 'the only row that fits'}
    for name, price in (('the requested price', sel.get('price')), ("the price in Betty's files", sel.get('file_price'))):
        at_price = [r for r in fits if same_price(r.get('price'), price)]
        # Prices read by Tesseract aren't to be trusted alone (Betty's green top row, in bold, can only be): the row at the
        # price or every other row must have been read by its exact shape
        if len(at_price) == 1 and (at_price[0].get('price_sure', True)
                                   or all(r.get('price_sure', True) for r in fits if r is not at_price[0])):
            return {'row': at_price[0], 'fits': fits, 'why': f"{len(fits)} rows fit; this one is at {name}"}
        # The top row's bold price misread ('4-11' as '4-14', 5 Nov) with every other row surely not at the price
        unsure = [r for r in fits if not r.get('price_sure', True)]
        wanted = str(price or '').replace('/', '-').lower()
        if (price_fraction(wanted) is not None and len(unsure) == 1 and not at_price
                and SequenceMatcher(None, str(unsure[0].get('price')).lower(), wanted).ratio() >= 0.7):
            return {'row': unsure[0], 'fits': fits, 'why': f"{len(fits)} rows fit; the others aren't at {name}"}
    return {'row': None, 'fits': fits, 'why': f"{len(fits)} rows fit and their prices don't tell them apart"}


def classify_list(rows: list[dict], search: str) -> str:
    """
    Whether a drawn list can be believed. 'ghost': Betty showing one record over and over, white, with its raw $Away$
    and no price (screen mi_5). 'stale': a row without what was typed, the last search still showing for a moment after
    a key (video, 5 Nov, 'kups'). 'good': every row holds every part typed.
    """
    if not rows:
        return 'ghost'
    if any('$' in str(r.get('result')) for r in rows) or all(r.get('colour') == 'white' for r in rows):
        return 'ghost'
    same: dict = {}
    for r in rows:
        key = (clean(r.get('event')), clean(r.get('market')), clean(r.get('result')), r.get('price'))
        same[key] = same.get(key, 0) + 1
    if max(same.values()) >= GHOST_REPEATS:
        return 'ghost'
    if len(rows) >= GHOST_REPEATS and all(str(r.get('price')).upper() == 'NO' for r in rows):
        return 'ghost'
    parts = [clean(p) for p in str(search or '').split(';') if clean(p)]
    for r in rows:
        text = clean(f"{r.get('event')}{r.get('market')}{r.get('result')}")
        if not all(_holds(text, p) for p in parts):
            return 'stale'
    return 'good'


SLIP_LINE_PART_CHARS = 15  # Betty's betslip line: 'AGF Aarhus v Br  Goals Over Unde', each part cut to this many characters


def slip_line_fits(line: dict, row: dict) -> bool:
    """The betslip's new line is the row clicked: 1. <event>  <market> on its first text row, <result> <price> on its
    second. The price isn't compared: Betty's price box can have changed it to the price when struck."""
    first = clean(line.get('first'))
    event = clean(str(row.get('event'))[:SLIP_LINE_PART_CHARS])
    market = clean(str(row.get('market'))[:SLIP_LINE_PART_CHARS])
    if not (first and event and market) or not _close(first[:len(event) + len(market)], event + market):
        return False
    return _close(clean(line.get('result')).replace('.', ''), clean(row.get('result')).replace('.', ''))  # 'Over 2 5'


def search_box_reads(read: str, typed: str) -> bool:
    """The search box's text as read is what was typed. OCR takes ';' for ':', 'l' for 'i', and the caret for a stray
    mark at the end or as part of the last letter ('bournemoul'). Digits and signs must still agree."""
    def plain(s: str) -> str:
        return re.sub(r'[il1|!]', 'l', re.sub(r'[^a-z0-9.\-|!]', '', str(s or '').lower()))
    a, b = plain(read).rstrip('l|!') if not plain(typed).endswith('l') else plain(read), plain(typed)
    if a == b or a[:-1] == b:
        return True
    return len(b) >= 4 and _close(a, b)


def common_start(current: str, wanted: str) -> int:
    """How much of `current` in the box can stay for `wanted` ('over 2.5; ' between two selections, as the user does)."""
    n = 0
    for a, b in zip(current, wanted):
        if a != b:
            break
        n += 1
    return n


# --- Prices by their exact pixels. Tesseract read '5-2' as '3-2' and '9-2' and '2-5' as '2-9' (5 Nov), all believable ---
_glyphs: dict = {'path': None, 'mtime': None, 'table': []}


def price_glyphs() -> list[tuple[str, tuple[str, ...]]]:
    """(character, its rows of '#' and '.') from index_price_glyphs.json, widest first, read again when it's edited."""
    path = app_paths.data_file(GLYPHS_FILE)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    if (path, mtime) == (_glyphs['path'], _glyphs['mtime']):
        return _glyphs['table']
    try:
        with open(path, encoding="utf-8") as f:
            table = [(g['char'], tuple(g['rows'])) for g in json.load(f)['glyphs']]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"[-] {GLYPHS_FILE} can't be read: {e}")
        table = []
    _glyphs.update(path=path, mtime=mtime, table=sorted(table, key=lambda g: len(g[1][0]), reverse=True))
    return _glyphs['table']


def ink_rows(ink: list[str]) -> list[str]:
    """A cell's rows of '#' and '.', cut to the rows and columns holding ink."""
    rows = [r for r in ink if '#' in r]
    if not rows:
        return []
    left = min(r.index('#') for r in rows)
    right = max(r.rindex('#') for r in rows)
    return [r[left:right + 1] for r in rows]


def read_price_shapes(ink: list[str]) -> str | None:
    """
    A price cell's text from the exact shapes of its characters, left to right. None when a shape isn't in the table:
    never a guess. A shape is as tall as the cell's capitals and digits, with its blank rows ('-' sits mid-height), and
    is matched by position, not split by gaps, since '4-' can touch (mi_6).
    """
    rows = ink_rows(ink)
    if not rows:
        return None
    table = price_glyphs()
    height, width = len(rows), len(rows[0])
    x, out = 0, ""
    while x < width:
        if all(r[x] == '.' for r in rows):
            x += 1
            continue
        for char, shape in table:
            w = len(shape[0])
            if len(shape) == height and x + w <= width and all(rows[i][x:x + w] == shape[i] for i in range(height)):
                out += char
                x += w
                break
        else:
            return None
    return out
