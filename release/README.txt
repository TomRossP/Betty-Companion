BETTY COMPANION
===============

Works through Betty's unedited wagers: reads each slip, checks it against Betty's racecards, enters it, and places
it (LIVE) or stops just before placing (TEST). Anything it can't do is left for staff, with the reason.
Nothing needs installing: everything it uses is in this folder.


FIRST TIME ON A TILL
--------------------
1. Put this whole folder somewhere the till can write to, for example C:\BettyCompanion.
   (Not inside C:\Program Files: the program keeps its logs in a "logs" folder next to BettyCompanion.exe.)
2. If AVG stops it: open AVG, Menu, Settings, General, Exceptions, Add exception, and choose this folder.
   Then double-click BettyCompanion.exe again.
3. Double-click BettyCompanion.exe. The Betty Companion window opens.
4. Pair the till with the relay, once (the relay is what reads the slips):
   - System tab, Settings: check the Relay address and type a Till name, e.g. "Shop 1 - Till 2", then "Pair this till".
   - A 6-digit code appears. On the manager's phone, open the relay's /admin page and approve the same code.
   - Within a few seconds the window says "Paired". Nothing else to type, ever.
5. Once paired, it finds where Betty keeps its racecards and saves it in betty_paths.json: C:\ on the manager's
   till, the manager's shared drive (e.g. F:) on a cashier's till. The Data tab shows the folder in use.
   If the till's drives change, delete betty_paths.json and reopen the program to find them again.


EVERY DAY
---------
- Double-click BettyCompanion.exe, then Start. The window steps aside so Betty is in front, and the overlay in the
  corner shows what it is doing.
- Pause: stops at once and touches nothing; Start carries on. Stop: closes the program (and the overlay).
- The switch on the right is the mode: on (orange) = LIVE, places bets; off = TEST, stops before placing.
  LIVE is the default.
- The light at the bottom: green "Ready" = ready to automate; red "Not ready" (point at it to see what is missing). The Gemini light shows whether
  slips can be read.
- Keys on the till still work: ` (backtick) watcher on/off, Shift + ` test/live, Esc stop now.
- A person using the keyboard or mouse pauses it; it carries on by itself after a minute with no activity.


WHEN SOMETHING GOES TO STAFF
----------------------------
System tab, Errors: every problem in plain English, with what to do.
System tab, Staff entries: each wager left for staff (with Betty's screen at that moment) and each selection staff
had to type in (what the reader saw, what was typed, and the slip).


TEACHING IT THIS SHOP'S SLIPS
-----------------------------
Staff can teach it how this shop's customers write: the "Remember this" tick in the can't-read box, Teach from this
slip (System tab, Staff entries), and Add a lesson (System tab, Training). Everything it has learned is on the
Training tab, in lessons.json next to BettyCompanion.exe (keep it when updating, like the logs folder).
Both tills of a shop share what they learn once the relay is 1.3.0 and both are in the same shop on the relay's
/admin page (relay\RELAY_SETUP.md, "Shops").


SETTINGS FOR THIS SHOP OR TILL
------------------------------
Nothing needs setting: these are only for a shop or till that needs something different. Make a text file called
.env next to BettyCompanion.exe (if there isn't one) and add a line per setting, for example
    STAFF_IDLE_RESUME_SECS=120
then reopen Betty Companion. A setting left out, or not a number, keeps the usual value (in brackets).
- BETTY_SHARE=\\SERVER\share   where a cashier's till finds Betty's racecards when no drive letter has them
                               (otherwise it looks on C:\, every drive letter, and this PC's mapped network drives)
- STAFF_IDLE_RESUME_SECS (60)  after staff use the keyboard or mouse, carry on after this long with no activity
- WATCHER_POLL_SECS (5)        with no unedited wagers, look again this often
- OPEN_ELSEWHERE_RETRY_SECS (30)  a wager another till has open is tried again after this long
- SCAN_TIMEOUT_SECS (90), RECHECK_TIMEOUT_SECS (45)  longest wait for the slip reader (raise on a slow connection)
- GEMINI_QUOTA_PAUSE_SECS (600)   a reader out of quota is left alone this long
- LOG_UPLOAD_SECS (120), LESSON_SYNC_SECS (60)  how often logs and lessons go to the relay
- INDEX_LIST_SECS (3), INDEX_OPEN_SECS (8), INDEX_ADD_SECS (12)  how long Betty gets on the Master Index
- Kept in the logs folder: STAFF_SCREENSHOTS_KEPT (20), SLIP_IMAGES_KEPT (200), REUSE_SHOTS_KEPT (10),
  CORPUS_KEPT (1500 pictures, about 90 KB each), STAFF_JOURNAL_DAYS (30)
House rules and meetings: put this shop's own bookmaker_rules.json or meetings_directory.json next to
BettyCompanion.exe and it is used instead of the one inside the program (start from a copy of the one in _internal).
The screen must stay at 1366 x 768: that can't be changed.


UPDATING
--------
Close Betty Companion, then replace this folder with the new one, keeping the "logs" folder if you want the history,
and lessons.json, lessons_sync.json and the "lessons" folder (what staff taught it).
The till stays paired: its pass is kept by Windows, not in this folder. The new version finds Betty's drive again
by itself (or keep betty_paths.json from the old folder).
