// Betty Companion relay (Cloudflare Worker). It holds the real Gemini keys so the tills never do.
// Each till pairs once: it shows a 6-digit code, you approve that code on /admin, and the till gets its own pass.
// On every slip read the relay checks the pass, counts the request against the till's daily limit and swaps the pass
// for the real key. The launcher's "Gemini online" light uses /ping, which is free. Paste this whole file into the
// Worker editor: see RELAY_SETUP.md.
// 1.3.0: each till can be put in a shop on /admin. What staff teach a till (its lessons) is shared with the other
// tills of its shop through /lessons/sync; a till in no shop keeps its own. Which shop is never told by the till: the
// relay works it out from the till's pass, so a till only ever sees its own shop's lessons.
// 1.4.0: each till's logs (session logs, the staff journal, the screens kept when a wager goes to staff) come up as
// they grow (/logs/put), so the tills of a shop, and Claude on either of them, can read both tills' logs (/logs/list,
// /logs/get). The same rule as lessons: a till sees its shop's tills' logs, or only its own when it is in no shop.

const RELAY_VERSION = "1.4.1";
const PAIRING_MINUTES = 10;        // a code not approved within this time expires
const MAX_PENDING_PAIRINGS = 20;   // stops strangers filling the approval list
const ADMIN_FAILS_PER_HOUR = 10;   // wrong admin passwords from one address before it is locked out for an hour
const GEMINI_SLOTS = { paid: "GEMINI_KEY_PAID", free1: "GEMINI_KEY_FREE_1" };  // 1.4.1: no second free key (3 Nov)
const LESSONS_PER_SYNC = 500;      // most lessons one sync hands back (the till asks again for the rest)
const LESSON_IMAGE_MAX = 1500000;  // a whole-slip lesson's picture, base64 characters
const LESSON_KINDS = ["runner", "meeting", "wording", "slip"];
const LOG_NAME = /^(session_\d{8}_\d{6}\.log|staff_journal\.jsonl|(staff|slip|reuse)_[\w.-]{1,80}\.png)$/;
const LOG_CHUNK_MAX = 1000000;     // one upload, base64 characters (about 730 KB)
const LOG_GET_CHUNKS = 4;          // chunks one /logs/get hands back (the till asks again for the rest)
const LOG_KEEP_DAYS = 30;          // a log not added to for this long is dropped

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
    db.prepare(`CREATE TABLE IF NOT EXISTS lessons (id TEXT PRIMARY KEY, scope TEXT NOT NULL, kind TEXT NOT NULL,
      written TEXT NOT NULL, means TEXT NOT NULL, info TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'active',
      taught INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 0, placed INTEGER NOT NULL DEFAULT 0,
      staff INTEGER NOT NULL DEFAULT 0, last_used TEXT NOT NULL DEFAULT '', updated_at INTEGER NOT NULL,
      deleted INTEGER NOT NULL DEFAULT 0)`),
    db.prepare("CREATE INDEX IF NOT EXISTS lessons_scope ON lessons (scope, updated_at)"),
    db.prepare(`CREATE TABLE IF NOT EXISTS lesson_images (id TEXT PRIMARY KEY, scope TEXT NOT NULL, png TEXT NOT NULL)`),
    db.prepare(`CREATE TABLE IF NOT EXISTS log_files (till_id TEXT NOT NULL, name TEXT NOT NULL,
      size INTEGER NOT NULL DEFAULT 0, started_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
      PRIMARY KEY (till_id, name))`),
    db.prepare(`CREATE TABLE IF NOT EXISTS log_chunks (till_id TEXT NOT NULL, name TEXT NOT NULL, start INTEGER NOT NULL,
      length INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY (till_id, name, start))`),
  ]);
  // 1.3.0: the tills' shop, added to a database made by an older relay (an error only says it's there already)
  try { await db.prepare("ALTER TABLE tills ADD COLUMN shop TEXT").run(); } catch (e) { /* already there */ }
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

// --- Lessons: what staff taught a till, shared by the tills of one shop ---

// Whose lessons a till sees and adds to: its shop's, or its own when it is in no shop. From the till's row only.
const lessonScope = (till) => till.shop ? "shop:" + till.shop : "till:" + till.id;

const clip = (v, n) => String(v ?? "").slice(0, n);
const count = (v) => { const n = parseInt(v, 10); return Number.isFinite(n) && n > 0 ? Math.min(n, 100000) : 0; };

// One call both ways: the till's changes since it last synced go in, then everything of its scope changed since
// `since` comes back (deleted ones as deleted, so the till drops them too). Counts arrive as additions ('add'), so
// two tills counting the same lesson at once never overwrite each other. A lesson of another scope is never touched.
async function lessonsSync(request, env, till) {
  const body = await request.json().catch(() => ({}));
  const db = env.DB;
  const scope = lessonScope(till);
  const t = now();
  for (const c of Array.isArray(body.changes) ? body.changes.slice(0, LESSONS_PER_SYNC) : []) {
    const id = clip(c.id, 40);
    if (!/^[\w-]{6,40}$/.test(id) || !LESSON_KINDS.includes(c.kind)) continue;
    const row = await db.prepare("SELECT scope FROM lessons WHERE id = ?").bind(id).first();
    if (row && row.scope !== scope) continue;
    const add = c.add || {};
    await db.prepare(`INSERT INTO lessons (id, scope, kind, written, means, info, status, taught, used, placed, staff,
        last_used, updated_at, deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT (id) DO UPDATE SET written = excluded.written, means = excluded.means, info = excluded.info,
        status = excluded.status, deleted = MAX(lessons.deleted, excluded.deleted),
        taught = lessons.taught + excluded.taught, used = lessons.used + excluded.used,
        placed = lessons.placed + excluded.placed, staff = lessons.staff + excluded.staff,
        last_used = MAX(lessons.last_used, excluded.last_used), updated_at = excluded.updated_at`)
      .bind(id, scope, c.kind, clip(c.written, 200), clip(c.means, 200), clip(JSON.stringify(c.info || {}), 20000),
        c.status === "off" ? "off" : "active", count(add.taught), count(add.used), count(add.placed), count(add.staff),
        clip(c.last_used, 20), t, c.deleted ? 1 : 0).run();
    if (c.deleted) {
      await db.prepare("DELETE FROM lesson_images WHERE id = ?").bind(id).run();
    } else if (typeof c.image_png === "string" && c.image_png.length <= LESSON_IMAGE_MAX) {
      await db.prepare("INSERT OR REPLACE INTO lesson_images (id, scope, png) VALUES (?, ?, ?)")
        .bind(id, scope, c.image_png).run();
    }
  }
  const since = parseInt(body.since, 10) || 0;
  const rows = (await db.prepare(`SELECT l.*, (i.id IS NOT NULL) AS has_image FROM lessons l
      LEFT JOIN lesson_images i ON i.id = l.id WHERE l.scope = ? AND l.updated_at >= ? ORDER BY l.updated_at LIMIT ?`)
    .bind(scope, since, LESSONS_PER_SYNC).all()).results;
  await db.prepare("UPDATE tills SET last_seen = ? WHERE id = ?").bind(t, till.id).run();
  const lessons = rows.map((r) => ({ id: r.id, kind: r.kind, written: r.written, means: r.means,
    info: JSON.parse(r.info || "{}"), status: r.status, taught: r.taught, used: r.used, placed: r.placed,
    staff: r.staff, last_used: r.last_used, deleted: !!r.deleted, has_image: !!r.has_image, updated_at: r.updated_at }));
  return json({ ok: true, now: t, shop: till.shop || "", lessons, more: rows.length === LESSONS_PER_SYNC });
}

async function lessonImage(request, env, till) {
  const body = await request.json().catch(() => ({}));
  const row = await env.DB.prepare("SELECT png FROM lesson_images WHERE id = ? AND scope = ?")
    .bind(clip(body.id, 40), lessonScope(till)).first();
  return row ? json({ png: row.png }) : relayError(404, "no picture for that lesson");
}

// --- Logs: each till's logs, read by the tills of its shop ---

// The tills whose logs a till may read: its shop's (revoked ones too: their logs still tell what happened), or itself
async function logTills(db, till) {
  if (!till.shop) return [till];
  return (await db.prepare("SELECT * FROM tills WHERE shop = ?").bind(till.shop).all()).results;
}

const base64Bytes = (s) => Math.floor(s.length * 3 / 4) - (s.endsWith("==") ? 2 : s.endsWith("=") ? 1 : 0);

// One piece of a log, from where the relay's copy ends ('start' = its size here). A piece that doesn't start there
// is refused with the relay's size, and the till sends again from it, so a piece is never kept twice or skipped.
// 'restart' with start 0: the till rewrote the log (the staff journal loses its old lines at start-up), so the copy
// here starts again.
async function logsPut(request, env, till) {
  const body = await request.json().catch(() => ({}));
  const name = String(body.name || ""), data = String(body.data || "");
  const start = parseInt(body.start, 10);
  if (!LOG_NAME.test(name)) return relayError(400, "not a log the relay keeps");
  if (!(start >= 0) || !data || data.length > LOG_CHUNK_MAX || data.length % 4 || !/^[A-Za-z0-9+/]+={0,2}$/.test(data)) {
    return relayError(400, `start and base64 data (at most ${LOG_CHUNK_MAX} characters) are required`);
  }
  const db = env.DB, t = now(), length = base64Bytes(data);
  if (body.restart && start === 0) {
    await db.batch([
      db.prepare("DELETE FROM log_chunks WHERE till_id = ? AND name = ?").bind(till.id, name),
      db.prepare("DELETE FROM log_files WHERE till_id = ? AND name = ?").bind(till.id, name),
    ]);
  }
  const size = (await db.prepare("SELECT size FROM log_files WHERE till_id = ? AND name = ?")
    .bind(till.id, name).first("size")) ?? 0;
  if (start !== size) return json({ ok: false, size });
  await db.batch([
    db.prepare("INSERT OR REPLACE INTO log_chunks (till_id, name, start, length, data) VALUES (?, ?, ?, ?, ?)")
      .bind(till.id, name, start, length, data),
    db.prepare(`INSERT INTO log_files (till_id, name, size, started_at, updated_at) VALUES (?, ?, ?, ?, ?)
      ON CONFLICT (till_id, name) DO UPDATE SET size = excluded.size, updated_at = excluded.updated_at`)
      .bind(till.id, name, start + length, Date.now(), t),  // started_at in ms: a restart a second later still shows
    db.prepare("UPDATE tills SET last_seen = ? WHERE id = ?").bind(t, till.id),
  ]);
  if (Math.random() < 0.02) {  // now and then, the logs nobody has added to for LOG_KEEP_DAYS go
    const cutoff = t - LOG_KEEP_DAYS * 86400;
    await db.batch([
      db.prepare(`DELETE FROM log_chunks WHERE EXISTS (SELECT 1 FROM log_files f WHERE f.till_id = log_chunks.till_id
        AND f.name = log_chunks.name AND f.updated_at < ?)`).bind(cutoff),
      db.prepare("DELETE FROM log_files WHERE updated_at < ?").bind(cutoff),
    ]);
  }
  return json({ ok: true, size: start + length });
}

// Every log of the till's shop added to in the last `days` (default and most LOG_KEEP_DAYS); 'mine' = this till's own,
// 'started_at' = when the relay's copy began (a new one after a restart: a copy fetched before is out of date)
async function logsList(request, env, till) {
  const body = await request.json().catch(() => ({}));
  const days = Math.min(Math.max(parseInt(body.days, 10) || LOG_KEEP_DAYS, 1), LOG_KEEP_DAYS);
  const files = [];
  for (const x of await logTills(env.DB, till)) {
    const rows = (await env.DB.prepare(`SELECT name, size, started_at, updated_at FROM log_files WHERE till_id = ? AND updated_at > ?
      ORDER BY updated_at`).bind(x.id, now() - days * 86400).all()).results;
    for (const r of rows) files.push({ till_id: x.id, till: x.name, mine: x.id === till.id, ...r });
  }
  return json({ ok: true, shop: till.shop || "", files });
}

// A log's pieces from byte `from` on (the first may begin before it: the till skips what it has)
async function logsGet(request, env, till) {
  const body = await request.json().catch(() => ({}));
  const tillId = String(body.till_id || ""), name = String(body.name || "");
  if (!(await logTills(env.DB, till)).some((x) => x.id === tillId)) return relayError(404, "no such log for this till");
  const from = Math.max(parseInt(body.from, 10) || 0, 0);
  const chunks = (await env.DB.prepare(`SELECT start, length, data FROM log_chunks WHERE till_id = ? AND name = ?
    AND start + length > ? ORDER BY start LIMIT ?`).bind(tillId, name, from, LOG_GET_CHUNKS).all()).results;
  const size = (await env.DB.prepare("SELECT size FROM log_files WHERE till_id = ? AND name = ?")
    .bind(tillId, name).first("size")) ?? 0;
  return json({ ok: true, size, chunks });
}

// --- Admin: approve codes, revoke tills, set daily limits, put tills in shops ---

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
    const tills = (await db.prepare(`SELECT t.id, t.name, t.created_at, t.last_seen, t.daily_limit, t.active, t.shop,
      COALESCE(u.requests, 0) AS today,
      (SELECT COUNT(*) FROM lessons l WHERE l.deleted = 0 AND l.scope = CASE WHEN t.shop IS NOT NULL AND t.shop <> ''
        THEN 'shop:' || t.shop ELSE 'till:' || t.id END) AS lessons,
      (SELECT COUNT(*) FROM log_files f WHERE f.till_id = t.id) AS logs,
      (SELECT MAX(f.updated_at) FROM log_files f WHERE f.till_id = t.id) AS logs_at
      FROM tills t LEFT JOIN usage u ON u.till_id = t.id AND u.day = ?
      ORDER BY t.active DESC, t.shop, t.name`).bind(today()).all()).results;
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
  if (action === "shop") {
    // A till joins a shop: the lessons it learned on its own go with it, so the shop's other tills get them too
    const shop = String(body.shop || "").trim().replace(/\s+/g, " ").slice(0, 40) || null;
    const tillId = String(body.till_id || "");
    const till = await db.prepare("SELECT * FROM tills WHERE id = ?").bind(tillId).first();
    if (!till) return relayError(404, "no such till");
    const from = lessonScope(till), to = shop ? "shop:" + shop : "till:" + till.id;
    await db.batch([
      db.prepare("UPDATE tills SET shop = ? WHERE id = ?").bind(shop, tillId),
      db.prepare("UPDATE lessons SET scope = ?, updated_at = ? WHERE scope = ?").bind(to, t, "till:" + till.id),
      db.prepare("UPDATE lesson_images SET scope = ? WHERE scope = ?").bind(to, "till:" + till.id),
    ]);
    return json({ ok: true, from, to });
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
      el("div", "Today: " + x.today + " of " + limit + " reads" + (x.daily_limit == null ? " (default)" : "") + " · last used " + ago(x.last_seen), "hint"),
      el("div", (x.shop ? "Shop: " + x.shop + " · lessons shared with its other tills: " : "In no shop · its own lessons: ") + x.lessons, "hint"),
      el("div", "Logs: " + x.logs + " file(s) · last added " + ago(x.logs_at), "hint"));
    c.append(who);
    if (x.active) {
      c.append(btn("Shop", async () => {
        const v = prompt("Shop for " + x.name + " (the same name for both tills of a shop; empty = no shop).\\n"
          + "Its lessons go with it and are shared with that shop's other tills.", x.shop || "");
        if (v !== null) await api("shop", { till_id: x.id, shop: v.trim() });
      }), btn("Daily limit", async () => {
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
      const tillPaths = ["/ping", "/lessons/sync", "/lessons/image", "/logs/put", "/logs/list", "/logs/get"];
      if (!gemini && !tillPaths.includes(path)) return relayError(404, "not found");
      const till = await tillFor(request, env);
      if (!till) return relayError(401, "this till is not paired, or its pass was revoked");
      if (path === "/ping") return await ping(env, till);
      if (path === "/lessons/sync") return await lessonsSync(request, env, till);
      if (path === "/lessons/image") return await lessonImage(request, env, till);
      if (path === "/logs/put") return await logsPut(request, env, till);
      if (path === "/logs/list") return await logsList(request, env, till);
      if (path === "/logs/get") return await logsGet(request, env, till);
      return await proxyGemini(request, env, till, gemini[1], gemini[2]);
    } catch (e) {
      return relayError(500, "relay error: " + (e && e.message ? e.message : e));
    }
  },
};
