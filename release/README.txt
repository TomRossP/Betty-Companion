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
   - Controls tab: check the Relay address and type a Till name, e.g. "Shop 1 - Till 2", then "Pair this till".
   - A 6-digit code appears. On the manager's phone, open the relay's /admin page and approve the same code.
   - Within a few seconds the window says "Paired". Nothing else to type, ever.


EVERY DAY
---------
- Double-click BettyCompanion.exe, then Start. The window steps aside so Betty is in front, and the overlay in the
  corner shows what it is doing.
- Pause: stops at once and touches nothing; Start carries on. Stop: closes the program (and the overlay).
- The orange button is the mode: LIVE places bets, TEST stops before placing. LIVE is the default.
- The light at the bottom: green = ready to automate; red says what is missing. The Gemini light shows whether
  slips can be read.
- Keys on the till still work: ` (backtick) watcher on/off, Shift + ` test/live, Esc stop now.
- A person using the keyboard or mouse pauses it; it carries on by itself after a minute with no activity.


WHEN SOMETHING GOES TO STAFF
----------------------------
System tab, Errors: every problem in plain English, with what to do.
System tab, Staff entries: each wager left for staff (with Betty's screen at that moment) and each selection staff
had to type in (what the reader saw, what was typed, and the slip).


UPDATING
--------
Close Betty Companion, then replace this folder with the new one, keeping the "logs" folder if you want the history.
The till stays paired: its pass is kept by Windows, not in this folder.
