# Setting up the Betty Companion relay

The relay is a small program that runs on Cloudflare, not on any till. It keeps the real Gemini keys, so
**no till ever holds a key.** Each till pairs with the relay once and gets its own pass. You can see each till's usage,
cap it, and cancel it with one click.

```
Till  --(slip + till pass)-->  Relay on Cloudflare  --(slip + real key)-->  Gemini
```

Everything below is done in a web browser. There is nothing to install. It takes about 20 minutes. Cloudflare
sometimes moves its menus around, so a button may be named slightly differently from what is written here.

## Before you start

You need:

- an email address for the Cloudflare account;
- a password manager, or somewhere safe to keep the admin password you'll create in step 5;
- the AI keys. These are the values in this PC's `.env` file:

  | In `.env` now | Name on the relay |
  |---|---|
  | `GEMINI_API_KEY` (paid) | `GEMINI_KEY_PAID` |
  | `GEMINI_API_KEY_2` (free project) | `GEMINI_KEY_FREE_1` |
  | `GEMINI_API_KEY_3` (free project) | `GEMINI_KEY_FREE_2` |

  If you can, create **new** keys for the relay in Google AI Studio instead of reusing these.
  Then, once the relay works, you can delete the old ones, along with the copies on this PC.

## Step 1: Create the Cloudflare account

1. Go to <https://dash.cloudflare.com/sign-up> and sign up. The **Free** plan is all you need, and no card is required
   for Workers.
2. Confirm your email.
3. **Turn on two-factor login:** click your profile icon at the top right, then **My Profile**, then
   **Authentication**, then **Two-Factor Authentication**. Anyone who gets into this account can read the keys, so
   this step matters.

## Step 2: Create the database

The relay keeps its list of tills, pairing codes and daily counts here. It never stores the keys or any slip.

1. In the left menu open **Storage & Databases**, then **D1 SQL Database**.
2. Click **Create database**.
3. Name: `betty-relay`. Leave the location as it is, then click **Create**.

You don't need to create any tables. The relay creates them itself the first time it runs.

## Step 3: Create the Worker and paste in the code

1. In the left menu open **Compute (Workers)**, then **Workers & Pages**, then click **Create**.
2. Choose **Start with Hello World!**, or **Create Worker**.
3. Name: `betty-relay`, then click **Deploy**. It deploys a sample page; you'll replace it next.
4. Click **Edit code**.
5. Select everything in the editor (Ctrl+A) and delete it.
6. Open `relay\worker.js` from this folder in Notepad, copy everything (Ctrl+A, Ctrl+C) and paste it into the editor.
7. Click **Deploy**, top right.

## Step 4: Connect the database to the Worker

1. Go back to the Worker's page, `betty-relay`, and open the **Bindings** tab.
2. Click **Add binding**, then **D1 database**.
3. Variable name: `DB`, in capitals and exactly that. Database: `betty-relay`.
4. Click **Add binding** or **Deploy**.

## Step 5: Add the keys and the admin password

1. On the Worker's page, open **Settings**, then **Variables and Secrets**, then click **Add**.
2. Add each of these with **Type: Secret**. Paste the value with no spaces before or after it.

   | Name | Value |
   |---|---|
   | `ADMIN_PASSWORD` | A new password for the relay's admin page. Let your password manager make it, at least 20 characters. |
   | `GEMINI_KEY_PAID` | The paid Gemini key |
   | `GEMINI_KEY_FREE_1` | The first free Gemini key |
   | `GEMINI_KEY_FREE_2` | The second free Gemini key |

3. Add these two with **Type: Text**. They aren't secret.

   | Name | Value | What it does |
   |---|---|---|
   | `DAILY_LIMIT` | `1000` | Most slip reads one till may make in a day. A slip takes 1 to 3 reads. You can change it for a single till later. |
   | `ALLOWED_GEMINI_MODELS` | `gemini-4-argon,gemini-3.8-flash` | The only Gemini models the relay will pass on. If the program is ever switched to another model, add it here. |

4. Click **Deploy**. Secrets only take effect once you deploy.

Once a secret is saved, Cloudflare never shows it again, not even to you. That is expected.

## Step 6: Check it works

1. On the Worker's page, find its address. It looks like `https://betty-relay.YOUR-NAME.workers.dev`.
2. Open that address with `/health` on the end, for example `https://betty-relay.YOUR-NAME.workers.dev/health`.
   You should see:

   ```
   {"ok":true,"relay":"betty-companion","version":"1.2.0"}
   ```

   If it says *"the relay has no database"*, step 4 didn't save. Check the variable name is exactly `DB`.
3. Open the address with `/admin` on the end and enter the admin password. You should see **Waiting to pair** and
   **Tills**, both empty. Bookmark this page on your phone: it's where you'll approve tills.

## Step 7: Put spending caps on the keys

The relay caps how many reads each till makes. These provider caps cap the money:

- **Gemini (paid project):** in Google Cloud Console, open **Billing**, then **Budgets & alerts**, and create a budget
  with email alerts for that project.
- **Gemini keys, optional extra:** in Google Cloud Console, open **APIs & Services**, then **Credentials**, and open
  each key. Under **API restrictions** choose **Restrict key**, then **Generative Language API** only.

## Step 8: The relay address in the program

Done: Betty Companion 1.0.0 has `https://betty-relay.splaterson92.workers.dev` built in. It isn't secret: without a
till pass it does nothing. To use another relay, put `RELAY_URL=https://...` in `.env` next to `BettyCompanion.exe`, or
change the address in the pairing box before pairing.

---

## Updating the relay's code to 1.3.0 (sharing what staff teach)

Relay **1.3.0** lets the tills of one shop share what staff have taught them (Betty Companion 1.2.0's Training tab).
Without it everything else works the same; each till keeps its own lessons.

1. Cloudflare dashboard: **Compute (Workers)**, then **Workers & Pages**, then `betty-relay`, then **Edit code**.
2. Select everything (Ctrl+A) and delete it. Paste in all of `relay\worker.js` from this folder. Click **Deploy**.
3. Open `/health`. It should say `"version":"1.3.0"`.
4. Open `/admin`. Each till now has a **Shop** button: give both tills of a shop the same shop name (for example
   `Shop 1`). See "Shops" below.

The relay adds its new tables by itself the first time it runs. Paired tills stay paired; nothing else changes.

## Updating the relay's code (1.0.0 or 1.1.0 to 1.2.0)

Betty Companion 1.0.0 needs relay **1.2.0**. That version adds `/ping`, the free check behind the window's Gemini
light. Slip reads work on older relays too, but the light can only say "relay online".

1. Cloudflare dashboard: **Compute (Workers)**, then **Workers & Pages**, then `betty-relay`, then **Edit code**.
2. Select everything (Ctrl+A) and delete it. Paste in all of `relay\worker.js` from this folder. Click **Deploy**.
3. **Settings**, then **Variables and Secrets**:
   - delete `CLAUDE_KEY` if it is there; the relay no longer passes anything to Claude;
   - check that `ALLOWED_GEMINI_MODELS` is `gemini-4-argon,gemini-3.8-flash`;
   - click **Deploy** if you changed anything.
4. Open `/health`. It should say `"version":"1.2.0"`.

Tills that are already paired stay paired. The database is kept.

---

## Pairing a till

Once per till, in the Betty Companion window:

1. **Controls** tab, **Relay** box. The relay address is filled in. Type a name for the till, for example
   `Shop 1 - Till 2`, then click **Pair this till**.
2. The window shows a **6-digit code**.
3. On your phone, open the relay's `/admin` page. The same code appears under **Waiting to pair**. Check the digits
   match, then tap **Approve**.
4. Within a few seconds the window says **Paired**. The till's pass is saved in that PC's Windows Credential Manager,
   as "BettyCompanion relay". Nobody types or sees it.
5. The Gemini light at the bottom turns green: *online via relay (paid, free1, free2; 0 of 1000 reads today)*.

From then on that till reads slips through the relay, even if its `.env` still has Gemini keys. **Unpair** (same box)
removes the pass from that PC. Also **Revoke** it on `/admin` if it won't be paired again.

**Only approve a code you can see on a till's screen at that moment.** Anyone on the internet can ask for a code. The
approval is what makes it count. Codes you don't recognise: tap **Reject**, or leave them; they expire after 10 minutes.

## Shops: sharing what staff teach

Staff can teach a till how this shop's customers write (System tab, Training). With relay 1.3.0 the tills of one
shop share those lessons:

- On `/admin`, press **Shop** on a till and type the shop's name. Give the shop's other till **exactly the same
  name**. Each till's card then says *Shop: ... · lessons shared with its other tills: N*.
- A till decides nothing itself: the relay knows each till by its pass, works out its shop, and only ever hands it
  that shop's lessons. A till can't see another shop's.
- A till in no shop keeps its own lessons (on the relay too, as a copy).
- When a till joins a shop, what it has already learned goes with it into the shop.
- Shop names are only ever seen on `/admin`. The tills just say they share with "shop ...".
- The tills share about once a minute while Betty Companion runs, and straight after something is taught. With no
  internet the lessons on each till still work; they catch up when it's back.

## Day to day

| To... | Do this |
|---|---|
| See what each till has used today | Open `/admin`. Each till shows *Today: N of 1000 reads* and when it was last used. |
| Stop a till at once (lost, stolen, replaced) | `/admin`, then **Revoke** on that till. Its next read is refused. To use it again, pair it again. |
| Change one till's daily limit | `/admin`, then **Daily limit** on that till. Leave it empty to go back to `DAILY_LIMIT`. |
| Replace a Gemini key | Worker, **Settings**, **Variables and Secrets**: edit the secret, then **Deploy**. The tills don't change at all. |
| Change the admin password | Same place: edit `ADMIN_PASSWORD`, then **Deploy**. |
| Put a till in a shop (or move it) | `/admin`, then **Shop** on that till. Empty = no shop. |
| Locked out of `/admin` | Ten wrong passwords from one address lock that address out for an hour. Wait, or use another network (for example your phone's mobile data). |

## Good to know

- **If the relay is ever unreachable,** the till can't read slips. Those wagers go to staff, as when every reader
  fails today. Nothing is guessed.
- **The free plan** covers 100,000 requests a day at the time of writing, far more than a few tills use.
  Cloudflare's pricing page has the current figures.
- **The relay keeps no keys in its database, and no slips it reads.** It stores: till names and shops, a
  scrambled copy (hash) of each till pass that can't be turned back into the pass, pairing codes, the daily read
  counts, and (1.3.0) the lessons staff teach: words as written and what they mean, how often each was used, and for
  a slip taught as a worked example, that slip's picture and its lines. Delete a lesson on a till's Training tab and
  the relay deletes it (and its picture) too.
- **The code is in this folder (`relay\worker.js`),** so it can go in the public GitHub repository safely: it contains
  no keys.
