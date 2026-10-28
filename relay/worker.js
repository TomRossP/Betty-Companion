// Betty Companion relay (Cloudflare Worker). It holds the real Gemini keys so the tills never do.
// Each till pairs once: it shows a 6-digit code, you approve that code on /admin, and the till gets its own pass.
// On every slip read the relay checks the pass, counts the request against the till's daily limit and swaps the pass
// for the real key. The launcher's "Gemini online" light uses /ping, which is free. Paste this whole file into the
// Worker editor: see RELAY_SETUP.md.

const RELAY_VERSION = "1.2.0";
const PAIRING_MINUTES = 10;        // a code not approved within this time expires
const MAX_PENDING_PAIRINGS = 20;   // stops strangers filling the approval list
const ADMIN_FAILS_PER_HOUR = 10;   // wrong admin passwords from one address before it is locked out for an hour
const GEMINI_SLOTS = { paid: "GEMINI_KEY_PAID", free1: "GEMINI_KEY_FREE_1", free2: "GEMINI_KEY_FREE_2" };

const enc = new TextEncoder();
const now = () => Math.floor(Date.now() / 1000);
const today = () => new Date().toISOString().slice(0, 10);
const hex = (bytes) => [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");

async function sha256(text) {
  return hex(new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text))));
}

function randomHex(n) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  return hex(a);
}

function sixDigits() {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return String(a[0] % 1000000).padStart(6, "0");
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

// Same shape as Gemini's own errors, so the program reads the message the same way
function relayError(status, message) {
  return new Response(JSON.stringify({ error: { message, relay: true } }), {
    status, headers: { "content-type": "application/json", "x-relay-error": "1", "cache-control": "no-store" },
  });
}

function defaultLimit(env) {
  const n = parseInt(env.DAILY_LIMIT || "1000", 10);
  return Number.isFinite(n) && n >= 0 ? n : 1000;
}

let schemaReady = false;

async function ensureSchema(db) {
  if (schemaReady) return;
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS tills (id TEXT PRIMARY KEY, name TEXT NOT NULL, pass_hash TEXT UNIQUE NOT NULL,
      created_at INTEGER NOT NULL, last_seen INTEGER, daily_limit INTEGER, active INTEGER NOT NULL DEFAULT 1)`),
    db.prepare(`CREATE TABLE IF NOT EXISTS pairings (id TEXT PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL,
      poll_hash TEXT NOT NULL, ip TEXT, created_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending')`),
    db.prepare(`CREATE TABLE IF NOT EXISTS usage (till_id TEXT NOT NULL, day TEXT NOT NULL,
      requests INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (till_id, day))`),
    db.prepare(`CREATE TABLE IF NOT EXISTS admin_failures (ip TEXT NOT NULL, at INTEGER NOT NULL)`),
  ]);
  schemaReady = true;
}

// --- Pairing: the till asks for a code, you approve it on /admin, the till collects its pass once ---

async function pairStart(request, env) {
  const body = await request.json().catch(() => ({}));
  const name = String(body.name || "").trim().slice(0, 60);
  const pollSecret = String(body.poll_secret || "");
  if (!name || pollSecret.length < 32) return relayError(400, "name and poll_secret are required");
  const t = now();
  await env.DB.prepare("UPDATE pairings SET status = 'expired' WHERE status = 'pending' AND created_at < ?")
    .bind(t - PAIRING_MINUTES * 60).run();
  const pending = await env.DB.prepare("SELECT COUNT(*) AS n FROM pairings WHERE status = 'pending'").first("n");
  if (pending >= MAX_PENDING_PAIRINGS) return relayError(429, "too many pairings are waiting; try again later");
  const id = randomHex(16);
  const code = sixDigits();
  await env.DB.prepare("INSERT INTO pairings (id, code, name, poll_hash, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)")
    .bind(id, code, name, await sha256(pollSecret), request.headers.get("cf-connecting-ip") || "", t).run();
  return json({ pair_id: id, code, expires_in: PAIRING_MINUTES * 60 });
}

async function pairPoll(request, env) {
  const body = await request.json().catch(() => ({}));
  const row = await env.DB.prepare("SELECT * FROM pairings WHERE id = ?").bind(String(body.pair_id || "")).first();
  if (!row || row.poll_hash !== await sha256(String(body.poll_secret || ""))) return relayError(404, "unknown pairing");
  if (row.status === "pending" && row.created_at < now() - PAIRING_MINUTES * 60) return json({ status: "expired" });
  if (row.status !== "approved") return json({ status: row.status });
  // Approved: the pass is made now and handed over exactly once. The relay keeps only its hash.
  const claimed = await env.DB.prepare("UPDATE pairings SET status = 'collected' WHERE id = ? AND status = 'approved'")
    .bind(row.id).run();
  if (!claimed.meta.changes) return json({ status: "collected" });
  const pass = "btr_" + randomHex(32);
  const tillId = randomHex(8);
  await env.DB.prepare("INSERT INTO tills (id, name, pass_hash, created_at) VALUES (?, ?, ?, ?)")
    .bind(tillId, row.name, await sha256(pass), now()).run();
  return json({ status: "paired", pass, till_id: tillId, name: row.name });
}

// --- Slip reads: check the till's pass and daily limit, then forward with the real key ---

async function tillFor(request, env) {
  const auth = request.headers.get("authorization") || "";
  const pass = auth.startsWith("Bearer ") ? auth.slice(7)
    : (request.headers.get("x-api-key") || request.headers.get("x-goog-api-key") || "");
  if (!pass.startsWith("btr_")) return null;
  return env.DB.prepare("SELECT * FROM tills WHERE pass_hash = ? AND active = 1").bind(await sha256(pass)).first();
}

async function countRequest(env, till) {
  const day = today();
  const limit = till.daily_limit ?? defaultLimit(env);
  const used = (await env.DB.prepare("SELECT requests FROM usage WHERE till_id = ? AND day = ?")
    .bind(till.id, day).first("requests")) || 0;
  if (used >= limit) return false;
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO usage (till_id, day, requests) VALUES (?, ?, 1)
      ON CONFLICT (till_id, day) DO UPDATE SET requests = requests + 1`).bind(till.id, day),
    env.DB.prepare("UPDATE tills SET last_seen = ? WHERE id = ?").bind(now(), till.id),
  ]);
  return true;
}

async function proxyGemini(request, env, till, slot, rest) {
  const key = env[GEMINI_SLOTS[slot]];
  if (!key) return relayError(404, `no Gemini key is set for '${slot}' on the relay`);
  if (!/^v1beta\/models\/[\w.-]+:generateContent$/.test(rest)) return relayError(403, "only generateContent is allowed");
  const model = rest.split("/")[2].split(":")[0];
  const allowed = (env.ALLOWED_GEMINI_MODELS || "").split(",").map((s) => s.trim()).filter(Boolean);
  if (allowed.length && !allowed.includes(model)) return relayError(403, `model ${model} is not allowed on the relay`);
  if (!await countRequest(env, till)) return relayError(403, "this till has reached its daily limit on the relay");
  return fetch(`https://generativelanguage.googleapis.com/${rest}`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": key },
    body: await request.arrayBuffer(),
  });
}

// The launcher's "Gemini online" check: the till's pass, its reads today, and whether Gemini answers each key. Listing
// one model costs nothing and is not counted against the daily limit.
async function ping(env, till) {
  const gemini = {};
  for (const [slot, name] of Object.entries(GEMINI_SLOTS)) {
    if (!env[name]) continue;
    try {
      const r = await fetch("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1",
        { headers: { "x-goog-api-key": env[name] } });
      gemini[slot] = r.ok ? "ok" : `HTTP ${r.status}`;
    } catch (e) {
      gemini[slot] = "unreachable";
    }
  }
  const used = (await env.DB.prepare("SELECT requests FROM usage WHERE till_id = ? AND day = ?")
    .bind(till.id, today()).first("requests")) || 0;
  await env.DB.prepare("UPDATE tills SET last_seen = ? WHERE id = ?").bind(now(), till.id).run();
  return json({ ok: Object.values(gemini).includes("ok"), till: till.name, today: used,
    limit: till.daily_limit ?? defaultLimit(env), gemini, version: RELAY_VERSION });
}

// --- Admin: approve codes, revoke tills, set daily limits ---

async function adminCheck(request, env) {
  if (!env.ADMIN_PASSWORD) return "unset";
  const ip = request.headers.get("cf-connecting-ip") || "?";
  const t = now();
  const fails = await env.DB.prepare("SELECT COUNT(*) AS n FROM admin_failures WHERE ip = ? AND at > ?")
    .bind(ip, t - 3600).first("n");
  if (fails >= ADMIN_FAILS_PER_HOUR) return "locked";
  const given = enc.encode(await sha256(request.headers.get("x-admin-password") || ""));
  const wanted = enc.encode(await sha256(env.ADMIN_PASSWORD));
  if (crypto.subtle.timingSafeEqual(given, wanted)) return "ok";
  await env.DB.batch([
    env.DB.prepare("INSERT INTO admin_failures (ip, at) VALUES (?, ?)").bind(ip, t),
    env.DB.prepare("DELETE FROM admin_failures WHERE at < ?").bind(t - 86400),
  ]);
  return "wrong";
}

async function adminApi(request, env, action) {
  const auth = await adminCheck(request, env);
  if (auth === "unset") return relayError(500, "ADMIN_PASSWORD is not set on the relay");
  if (auth === "locked") return relayError(429, "too many wrong passwords from this address; try again in an hour");
  if (auth !== "ok") return relayError(401, "wrong password");
  const body = await request.json().catch(() => ({}));
  const db = env.DB;
  const t = now();
  if (action === "state") {
    const pending = (await db.prepare(`SELECT id, code, name, created_at FROM pairings
      WHERE status = 'pending' AND created_at > ? ORDER BY created_at DESC`).bind(t - PAIRING_MINUTES * 60).all()).results;
    const tills = (await db.prepare(`SELECT t.id, t.name, t.created_at, t.last_seen, t.daily_limit, t.active,
      COALESCE(u.requests, 0) AS today FROM tills t LEFT JOIN usage u ON u.till_id = t.id AND u.day = ?
      ORDER BY t.active DESC, t.name`).bind(today()).all()).results;
    return json({ pending, tills, default_limit: defaultLimit(env), now: t });
  }
  if (action === "approve" || action === "reject") {
    const r = await db.prepare("UPDATE pairings SET status = ? WHERE id = ? AND status = 'pending' AND created_at > ?")
      .bind(action === "approve" ? "approved" : "rejected", String(body.pair_id || ""), t - PAIRING_MINUTES * 60).run();
    return r.meta.changes ? json({ ok: true }) : relayError(404, "that code has expired or was already answered");
  }
  if (action === "revoke") {
    const r = await db.prepare("UPDATE tills SET active = 0 WHERE id = ?").bind(String(body.till_id || "")).run();
    return r.meta.changes ? json({ ok: true }) : relayError(404, "no such till");
  }
  if (action === "limit") {
    const limit = body.limit === null || body.limit === "" ? null : parseInt(body.limit, 10);
    if (limit !== null && !(limit >= 0)) return relayError(400, "the limit must be a whole number, or empty for the default");
    const r = await db.prepare("UPDATE tills SET daily_limit = ? WHERE id = ?").bind(limit, String(body.till_id || "")).run();
    return r.meta.changes ? json({ ok: true }) : relayError(404, "no such till");
  }
  return relayError(404, "unknown action");
}

const ADMIN_PAGE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Betty relay</title>
<style>
  :root { color-scheme: light dark; --bg:#f6f7f9; --card:#fff; --ink:#1b1f24; --muted:#5f6b76; --line:#d9dee3;
          --ok:#1b7f3b; --bad:#b3261e; --accent:#0d47a1; }
  @media (prefers-color-scheme: dark) { :root { --bg:#111418; --card:#1b2026; --ink:#e8ecef; --muted:#9aa6b1;
          --line:#2c343c; --ok:#5cc184; --bad:#f2817a; --accent:#8ab4f8; } }
  body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif; }
  main { max-width:640px; margin:0 auto; padding:16px; }
  h1 { font-size:20px; margin:8px 0 16px; } h2 { font-size:16px; margin:24px 0 8px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; margin-bottom:8px; }
  .row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .grow { flex:1 1 180px; } .hint { color:var(--muted); font-size:13px; margin:4px 0; }
  .code { font:700 24px/1 ui-monospace, monospace; letter-spacing:3px; }
  .off { opacity:.55; } .err { color:var(--bad); }
  input, button { font:inherit; padding:8px 12px; border-radius:8px; border:1px solid var(--line);
                  background:var(--card); color:var(--ink); }
  button { cursor:pointer; } button.ok { background:var(--ok); border-color:var(--ok); color:#fff; }
  button.bad { color:var(--bad); }
</style></head>
<body><main>
<h1>Betty relay</h1>
<div id="login" class="card">
  <div class="row"><input id="pw" class="grow" type="password" placeholder="Admin password" autocomplete="current-password">
  <button id="go">Open</button></div><p id="msg" class="err"></p>
</div>
<div id="main" hidden>
  <h2>Waiting to pair</h2>
  <p class="hint">Only approve a code you can see on a till's screen right now. Codes expire after ${PAIRING_MINUTES} minutes.</p>
  <div id="pending"></div>
  <h2>Tills</h2><div id="tills"></div>
  <p class="row"><button id="refresh">Refresh</button><button id="lock">Lock</button></p>
</div>
<script>
let pw = sessionStorage.getItem("pw") || "";
let serverNow = 0;
const $ = (id) => document.getElementById(id);
async function api(action, body = {}) {
  const r = await fetch("/admin/api/" + action, { method: "POST",
    headers: { "content-type": "application/json", "x-admin-password": pw }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((data.error && data.error.message) || ("HTTP " + r.status));
  return data;
}
function el(tag, text, cls) { const e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; }
function btn(text, fn, cls) {
  const b = el("button", text, cls);
  b.onclick = async () => { b.disabled = true; try { await fn(); } catch (e) { alert(e.message); } await load(); };
  return b;
}
function ago(t) {
  if (!t) return "never";
  const s = Math.max(0, serverNow - t);
  return s < 90 ? s + "s ago" : s < 5400 ? Math.round(s / 60) + " min ago" : s < 129600 ? Math.round(s / 3600) + " h ago" : Math.round(s / 86400) + " days ago";
}
function show(ok, msg) { $("main").hidden = !ok; $("login").hidden = ok; $("msg").textContent = msg || ""; }
async function load() {
  let s;
  try { s = await api("state"); } catch (e) { show(false, e.message); return; }
  serverNow = s.now; show(true);
  const p = $("pending"); p.replaceChildren();
  if (!s.pending.length) p.append(el("p", "No codes waiting.", "hint"));
  for (const x of s.pending) {
    const c = el("div", null, "card row");
    const who = el("div", null, "grow"); who.append(el("div", x.code, "code"), el("div", x.name + " · asked " + ago(x.created_at), "hint"));
    c.append(who, btn("Approve", () => api("approve", { pair_id: x.id }), "ok"), btn("Reject", () => api("reject", { pair_id: x.id }), "bad"));
    p.append(c);
  }
  const t = $("tills"); t.replaceChildren();
  if (!s.tills.length) t.append(el("p", "No tills paired yet.", "hint"));
  for (const x of s.tills) {
    const limit = x.daily_limit ?? s.default_limit;
    const c = el("div", null, "card row" + (x.active ? "" : " off"));
    const who = el("div", null, "grow");
    who.append(el("strong", x.name + (x.active ? "" : " (revoked)")),
      el("div", "Today: " + x.today + " of " + limit + " reads" + (x.daily_limit == null ? " (default)" : "") + " · last used " + ago(x.last_seen), "hint"));
    c.append(who);
    if (x.active) {
      c.append(btn("Daily limit", async () => {
        const v = prompt("Reads per day for " + x.name + " (empty = default " + s.default_limit + "):", x.daily_limit ?? "");
        if (v !== null) await api("limit", { till_id: x.id, limit: v.trim() });
      }), btn("Revoke", async () => {
        if (confirm("Revoke " + x.name + "? It stops reading slips at once and must be paired again.")) await api("revoke", { till_id: x.id });
      }, "bad"));
    }
    t.append(c);
  }
}
$("go").onclick = () => { pw = $("pw").value; sessionStorage.setItem("pw", pw); load(); };
$("pw").onkeydown = (e) => { if (e.key === "Enter") $("go").click(); };
$("refresh").onclick = load;
$("lock").onclick = () => { pw = ""; sessionStorage.removeItem("pw"); $("pw").value = ""; show(false); };
if (pw) load();
setInterval(() => { if (!$("main").hidden) load(); }, 5000);
</script>
</main></body></html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    try {
      if (!env.DB) return relayError(500, "the relay has no database: add the D1 binding named DB");
      await ensureSchema(env.DB);
      if (path === "/health") return json({ ok: true, relay: "betty-companion", version: RELAY_VERSION });
      if (path === "/admin" && request.method === "GET") {
        return new Response(ADMIN_PAGE, { headers: {
          "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-frame-options": "DENY",
          "referrer-policy": "no-referrer",
          "content-security-policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'",
        } });
      }
      if (request.method !== "POST") return relayError(405, "not found");
      if (path === "/pair/start") return await pairStart(request, env);
      if (path === "/pair/poll") return await pairPoll(request, env);
      if (path.startsWith("/admin/api/")) return await adminApi(request, env, path.slice("/admin/api/".length));
      const gemini = path.match(/^\/gemini\/(\w+)\/(.+)$/);
      if (!gemini && path !== "/ping") return relayError(404, "not found");
      const till = await tillFor(request, env);
      if (!till) return relayError(401, "this till is not paired, or its pass was revoked");
      if (path === "/ping") return await ping(env, till);
      return await proxyGemini(request, env, till, gemini[1], gemini[2]);
    } catch (e) {
      return relayError(500, "relay error: " + (e && e.message ? e.message : e));
    }
  },
};
0