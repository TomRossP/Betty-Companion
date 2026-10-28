"""
The till's link to the Betty Companion relay (relay/worker.js on Cloudflare), which holds the Gemini keys so that no
till does. A till pairs once: it asks the relay for a 6-digit code, the owner approves that code on the relay's /admin
page, and the till collects a pass of its own. The relay address and the pass are kept together in this PC's Windows
Credential Manager ("BettyCompanion relay"): nothing secret is in a file, and nobody types or sees the pass.

Used by the program (the pass on every slip read) and by the launcher (pairing, the Gemini check).
"""
import ctypes
import ctypes.wintypes as wt
import os
import re
import secrets
import socket

import requests

DEFAULT_RELAY_URL = "https://betty-relay.splaterson92.workers.dev"  # not secret: without a till pass it does nothing
CREDENTIAL_TARGET = os.environ.get("BETTY_RELAY_CREDENTIAL", "BettyCompanion relay")  # the free tests use their own
RELAY_KEY_PREFIX = "relay:"  # a reader 'key' of 'relay:paid' means the relay's paid Gemini key slot
TIMEOUT_SECS = 8
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168


class RelayError(Exception):
    """The relay refused, or couldn't be reached. The message is fit to show staff."""


class _CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", wt.DWORD), ("Type", wt.DWORD), ("TargetName", wt.LPWSTR), ("Comment", wt.LPWSTR),
                ("LastWritten", wt.FILETIME), ("CredentialBlobSize", wt.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wt.DWORD),
                ("AttributeCount", wt.DWORD), ("Attributes", ctypes.c_void_p), ("TargetAlias", wt.LPWSTR),
                ("UserName", wt.LPWSTR)]


def _advapi():
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    api.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIAL), wt.DWORD]
    api.CredReadW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
    api.CredDeleteW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD]
    api.CredFree.argtypes = [ctypes.c_void_p]
    return api


# --- The saved link: {url, pass, name} in Credential Manager ---

def saved_link() -> dict | None:
    """This till's relay address, pass and name, or None when it isn't paired."""
    try:
        api = _advapi()
        ptr = ctypes.POINTER(_CREDENTIAL)()
        if not api.CredReadW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(ptr)):
            return None
        try:
            cred = ptr.contents
            secret = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize).decode("utf-8")
            return {"url": cred.UserName or "", "pass": secret, "name": cred.Comment or ""}
        finally:
            api.CredFree(ptr)
    except (OSError, ValueError, AttributeError):
        return None


def save_link(url: str, pass_: str, name: str):
    api = _advapi()
    blob = pass_.encode("utf-8")
    buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    cred = _CREDENTIAL(Type=CRED_TYPE_GENERIC, TargetName=CREDENTIAL_TARGET, Comment=name[:250],
                       CredentialBlobSize=len(blob), CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)),
                       Persist=CRED_PERSIST_LOCAL_MACHINE, UserName=url)
    if not api.CredWriteW(ctypes.byref(cred), 0):
        raise RelayError(f"Windows wouldn't save the relay pass (error {ctypes.get_last_error()})")


def forget_link():
    """Unpairs this till here (the relay still lists it until it is revoked on /admin)."""
    api = _advapi()
    if not api.CredDeleteW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0) and ctypes.get_last_error() != ERROR_NOT_FOUND:
        raise RelayError(f"Windows wouldn't remove the relay pass (error {ctypes.get_last_error()})")


def relay_route() -> tuple[str, str] | None:
    """(relay address, till pass) when this till is paired, for the program's slip reads."""
    link = saved_link()
    if link and link["url"] and link["pass"].startswith("btr_"):
        return link["url"], link["pass"]
    return None


def normalise_url(text: str) -> str:
    """'betty-relay.name.workers.dev/admin' -> 'https://betty-relay.name.workers.dev'. RelayError when it isn't one."""
    text = (text or "").strip()
    if not text:
        raise RelayError("Type the relay address first (it ends in .workers.dev)")
    if not re.match(r"^https?://", text, re.IGNORECASE):
        text = "https://" + text
    m = re.match(r"^(https?)://([A-Za-z0-9.-]+\.[A-Za-z]{2,}|localhost|127\.0\.0\.1)(:\d+)?(?:/.*)?$", text, re.IGNORECASE)
    if not m:
        raise RelayError(f"'{text}' isn't a web address")
    scheme, host, port = m.group(1).lower(), m.group(2).lower(), m.group(3) or ""
    if scheme != "https" and host not in ("localhost", "127.0.0.1"):  # plain http only for a test relay on this PC
        raise RelayError("The relay address must start with https://")
    return f"{scheme}://{host}{port}"


def default_relay_url() -> str:
    """The address offered for pairing: RELAY_URL in .env, else the shop's relay."""
    return os.environ.get("RELAY_URL", "").strip() or DEFAULT_RELAY_URL


def default_till_name() -> str:
    return socket.gethostname()


# --- Talking to the relay ---

def _relay_message(response: requests.Response) -> str:
    try:
        return str(response.json().get("error", {}).get("message", "")) or f"HTTP {response.status_code}"
    except ValueError:
        return f"HTTP {response.status_code}"


def _post(url: str, path: str, body: dict | None = None, pass_: str | None = None) -> requests.Response:
    headers = {"content-type": "application/json"}
    if pass_:
        headers["authorization"] = f"Bearer {pass_}"
    try:
        return requests.post(url + path, json=body or {}, headers=headers, timeout=TIMEOUT_SECS)
    except requests.exceptions.RequestException as e:
        raise RelayError(f"The relay can't be reached ({type(e).__name__}). Check the internet and the address.") from e


def start_pairing(url: str, name: str) -> dict:
    """Asks the relay for a code: {pair_id, code, poll_secret, expires_in}. The owner approves the code on /admin."""
    url = normalise_url(url)
    name = (name or "").strip() or default_till_name()
    poll_secret = secrets.token_hex(24)
    r = _post(url, "/pair/start", {"name": name, "poll_secret": poll_secret})
    if r.status_code != 200:
        raise RelayError(f"The relay refused to pair: {_relay_message(r)}")
    data = r.json()
    return {"url": url, "name": name, "pair_id": data["pair_id"], "code": data["code"],
            "poll_secret": poll_secret, "expires_in": data.get("expires_in", 600)}


def poll_pairing(pairing: dict) -> str:
    """'pending', 'paired' (the pass is saved now), 'rejected', 'expired' or 'collected' (taken by another poll)."""
    r = _post(pairing["url"], "/pair/poll", {"pair_id": pairing["pair_id"], "poll_secret": pairing["poll_secret"]})
    if r.status_code != 200:
        raise RelayError(f"The relay lost this pairing: {_relay_message(r)}")
    data = r.json()
    if data.get("status") == "paired":
        save_link(pairing["url"], data["pass"], data.get("name") or pairing["name"])
    return str(data.get("status", "pending"))


def check_relay(url: str, pass_: str) -> dict:
    """
    The relay's free check (/ping: the till's pass, its reads today and whether each Gemini key answers; nothing is
    read or charged). {'ok', 'text', 'till', 'today', 'limit', 'gemini'}.
    """
    r = _post(url, "/ping", pass_=pass_)
    if r.status_code == 401:
        return {"ok": False, "text": "this till isn't paired with the relay any more: pair it again"}
    if r.status_code in (404, 405) and r.headers.get("x-relay-error"):  # a relay from before /ping (worker.js 1.1.0)
        try:
            health = requests.get(url + "/health", timeout=TIMEOUT_SECS).json()
        except (requests.exceptions.RequestException, ValueError):
            health = {}
        if health.get("ok"):
            return {"ok": True, "text": f"relay {health.get('version', '?')} online (update worker.js for the Gemini check)"}
        return {"ok": False, "text": "the relay doesn't answer"}
    if r.status_code != 200:
        return {"ok": False, "text": f"relay: {_relay_message(r)}"}
    data = r.json()
    gemini = data.get("gemini") or {}
    working = [slot for slot, state in gemini.items() if state == "ok"]
    text = (f"online via relay ({', '.join(working)}; {data.get('today', 0)} of {data.get('limit', '?')} reads today)"
            if working else "the relay answers, but no Gemini key does: " + ", ".join(f"{k} {v}" for k, v in gemini.items()))
    return {"ok": bool(working), "text": text, "till": data.get("till"), "today": data.get("today"),
            "limit": data.get("limit"), "gemini": gemini}


def check_gemini_key(key: str) -> dict:
    """Without a relay: does Gemini answer this key? Lists one model (free, nothing is read)."""
    try:
        r = requests.get(f"{GEMINI_API}/models", params={"pageSize": 1}, headers={"x-goog-api-key": key},
                         timeout=TIMEOUT_SECS)
    except requests.exceptions.RequestException as e:
        return {"ok": False, "text": f"Gemini can't be reached ({type(e).__name__})"}
    if r.status_code == 200:
        return {"ok": True, "text": "online (key in .env)"}
    return {"ok": False, "text": f"Gemini refused the key in .env (HTTP {r.status_code})"}
