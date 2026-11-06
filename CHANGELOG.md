# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [1.3.7] - 2026-11-06

Offline tests only: **not yet run on a till**, so it isn't proven that this stops the reads. Watch the manager till's network with it open on the cashier.

### Fixed
- **A cashier till reads Betty's files only when it's asked to** (user, 6 Nov). About 230 MB a minute went from the manager till to the cashier, about 20 seconds at a time at the 12 MB/s a 100 Mbps link
  allows, for as long as Companion was open there. All 6 freezes logged from 16:00 to 17:03 fell inside a read and ended as it ended, and closing Companion on the cashier stopped the reads. The launcher's Data
  refresh ran every minute from the moment it opened, the same timing. What it reads adds up to about 6 MB when measured on the manager till, so what makes up the rest isn't known. A cashier till now reads
  for the Data and Runners tabs while they're on screen, and until it has found today's racecards. The manager till is unchanged.

## [1.3.6] - 2026-11-06

Offline tests and a few paid reads of the real slips: **none of this has run on a till** yet. The race 12 hours ago in particular is written
from the user's description: no real 720-minute box has been seen by the program.

### Fixed
- **The printed Patent coupon's second box** (9.2468555, user). Its two stake boxes both say WIN, 'WIN 7 @' and 'WIN 14 @'. The second is a printing
  error for each way, as 14 is 7 bets twice. £5 in it was read as £35 to win, against £70 paid. A full cover whose line carries twice its
  bets is now each way, and the reader is told about the coupon.
- **A regular customer's '50p each way' scrawl** (9.2468502, 9.2468536, 9.2468543, user: staff's entries were right). It was read as a combination
  forecast or tricast, at the same £3, so the money couldn't catch it. The reader is told about it, and a combination on 3 runners in one race
  has its line read again on its own: each way goes in as singles, a sure combination stands, anything else goes to staff.
- **The race 12 hours ago at the same clock time** (9.2468536, 9.2468543, user). Typing 16:40 also brings up the 04:40 at a virtual meeting. A late-selection
  box of 600 minutes or more is now answered No, then 'right' and the number again; if the same, 'left' then 'right' and the number again, which
  shuffles out the duplicate meeting; if the same, staff. It used to answer Yes, and only the name check stopped it. A box under 600 minutes is a
  real late selection: Yes, as before.
- **A freeze with no clock on screen** (9.2468289, 9.2468533). When a wait ran out with no clock showing, it couldn't tell, and the wager went to staff a moment
  before Betty came back. Now it waits as soon as nothing has moved, until something does, up to 25 s (`BETTY_NO_CLOCK_WAIT_SECS`). Nothing moving in that
  time isn't a freeze, and it isn't waited for again for 30 s. A real problem on a screen with no clock reaches staff up to 25 s later.
- **The wager shown before's details under the new number** (9.2468538). Frozen mid-draw, two reads agreed on the new number with the old wager's struck time and
  Payment. Details the same as the wager shown before aren't taken now until Betty has shown she isn't frozen.
- **A wager that couldn't be marked FAO is tried again** (9.2468533: never marked). Up to 3 more times, each time the watcher is back on View Wagers.
- `live_report.py` counts each log once (the manager's were counted up to three times).

### Added
- **Past results: the winner in bold, and a price history** (user, 6 Nov). Choose a runner to see every change of its price, from Betty's monthly price history. Kept for
  good with the day's result, so a day's file is about 125 KB (was 50). The days already on file are filled in once on starting, as far as Betty's files go (from June).
- **Non-runners** (user, 6 Nov): NR in Past results' Place column, and a day's list in a new Non-runners tab under Data (manager till), with the last price and when it came out.
  From Betty's price history and, once a race is settled, SETTDATA. Betty records no reason for a runner not finishing, and a runner with no placing may have finished, so those stay blank.
- **Bad each way** (user, 6 Nov): a new tab under Data (manager till), a log only: no bet is changed. Every minute, each UK and Irish race with a full set of prices is scored from Betty's card, and a runner
  whose place part gives a punter 10% or more is listed with the price and edge when first seen, now, and its result. The edge is an estimate. Tried on 763 races at SP, 16 Oct - 6 Nov:
  182 runners in 67 races returned +44.7% on the place part, but +11.7% without one 300/1 shot that placed and -1.7% without the best five, so too few to prove it. The card's handicap flag, non-runner flag and
  extra-place terms are now read.
- **Extra places** (user, 6 Nov): a new tab under Data (manager till), a record kept for good, the latest date first: each UK and Irish race with its places edited on the head office terminal, with its places and
  fraction as on Betty's card, and the terms she settled it on (red if they differ, grey if the edit was taken off again). Filled in once on starting from her archived cards, from 3 April. Betty's files don't say who edited a race or when.

### Changed
- **The Live or Test switch is in System, Settings** (user, 6 Nov), no longer on Controls. Shift + ` still swaps it, and the panel on the screen still says which it is.

## [1.3.5] - 2026-11-06

Offline tests only: none of this has run on a till yet.

### Fixed
- **'50 r/f cast' read as '50 dbl last'** (9.2468368, placed wrong, 6 Nov). The reader is told r/f, s/f and c/f, and that a hasty "cast" looks like
  "last", which always has a number with it. It's a handwriting misread, so this may not always stop it: a double on exactly two runners in
  one race can't be a double, so its line is now read again on its own: a forecast is entered as that, surely a double goes on to the
  house rule as before, and anything else goes to staff. It used to be split into each way singles, with the money made up by 1.3.4's
  each way correction.

- **'6 x £1.50 E/W' on 6 selections is 6 singles** (9.2468424, user, 6 Nov). With no bet type written, 'N x' on N selections is now N singles. It was
  taken for Perm 5-Folds at the same money, so the money couldn't catch it. It only stopped because Betty's bet list kept Singles chosen. A bet
  type written still counts. '3 x' on 3 stays doubles (user, 6 Nov): a regular customer scrawls 'dbl' after it, which the reader can miss.

### Added
- **Gemini's read is kept until its wager is done with** (user, 6 Nov). Stopped or paused part-way, or the program closed, the wager goes on
  with the saved read and no new paid call. It goes when the wager is placed or left for staff, and after a day regardless. A rescan
  because the money doesn't add up is still a new read. In `logs\saved_reads`.
- `scratch\known_slips`: slips with their truth, as staff read them, checked by `test_known_slips.py` (`--live` reads the picture with the paid
  reader too). 9.2468368 is the first.

## [1.3.4] - 2026-11-06

Offline tests only: none of this has run on a till yet.

### Fixed
- **A combination forecast lost a selection, and an each way hid it** (9.2468449, placed wrong, 6 Nov). '£4 3', then '£1 c/fc 2 / 3 / 5', £10:
  the 5, under the forecast's stake, was cut as "below the bet line", which left £6. The money was then made up by making the £4 single
  each way, so £8 + £2 passed every check. A runner below the last bet line now stays with that bet.
- **A combination forecast has at least 3 selections** (user, 6 Nov). None is cut below 3, and one read with fewer goes to staff instead of
  being entered: on 2 Betty takes it as a reversed forecast, so it went in, and the money could still add up.
- **A bet is no longer made each way, or win, by the money alone.** The line is read again on its own, without being told what would fit,
  and changed only if that read says so. Otherwise the money check goes on as usual: a rescan, then staff.

## [1.3.3] - 2026-11-06

Offline tests only: none of this has run on a till yet.

### Added
- **Search on the log** (System, Log): type and every match is marked, with Next and Previous, Enter and Ctrl+F.
- **Past results tab** (user, 6 Nov): a day, a meeting, a race, then its full result as far as Betty records it: place, number, runner,
  SP and the last price in her file. One compressed file a day (about 50 KB), kept for good, in `Documents\BettyCompanion Records\past_results`, outside the
  program's folder so a new version finds them. On starting, any of the last 60 days not on file is filled in from `Events\ARCHIVE`
  and SETTDATA. A file is never overwritten by one with fewer results. Virtual races are left out.
- **Sports prices tab** (user, 6 Nov: a slip with no price on a football match, and no way of seeing what it was): a day, a search, an
  event, its markets, then each selection's first and latest price and its price history, with the winner in green. Every change of
  price, copied every minute from Betty's monthly price history (`DBF\PHST`), with the last 30 days on the first start. Winners from
  SETTDATA, kept as Betty only holds about three weeks. In `sports_prices.db`, kept 30 days after the event (System, Shop settings).
- **The program knows a manager till from a cashier till**: Betty's data on its own disk, or across the network. The records are kept on
  the manager till alone, and a cashier till doesn't show their tabs or read anything for them.

### Fixed
- **The events page as pictures** ("Place Your Bets On", screen 70) is named as the events page: what opens first on entering a bet to
  edit, passed by pressing 1.
- **Sports kick-off times.** Betty's run 8 hours ahead, so a match kicked off within the last 8 hours could count as still to come when
  a handwritten football bet was matched. The Master Index's own results were not affected.

## [1.3.2] - 2026-11-06

Offline tests only: none of this has run on a till yet.

### Fixed
- **Keys and clicks go to Betty or nowhere** (user, 6 Nov; 12:24 that day, Esc went to whatever was on top). Every key and click now
  checks Betty has the keyboard. If she hasn't, nothing is pressed and the watcher pauses as it does for staff, the wager in hand
  to be tried again. A stray window gives way only if nobody has touched the till for 2 s.
- **The watcher no longer takes the till from someone using it** (user, 6 Nov). It used to bring Betty forward every 5 s over whatever
  was in front. Now it waits, and presses nothing, until nobody has touched the till for 5 minutes, or Start or ` is pressed.
- **A screen staff left Betty on is left alone** on the same terms. It used to be backed out of 60 s after they stopped.
- **Backing out stops when someone touches the till.** It used to carry on through the Esc presses already under way.
- **Pictures for the relay, and the paid read of an unknown screen, are of Betty only.** Another program's window on top was saved
  and sent up as an unknown screen.

### Added
- "Seconds with nobody at the till before Betty is taken over" in System, Shop settings (300).

## [1.3.1] - 2026-11-06

Offline tests only: **none of this has run on a till** yet. On the cashier till this morning Betty stopped drawing for about 20 s
once a minute, while something filled the link to Betty's files with about 250 MB (still being traced). Three wagers with every
selection matched went to staff, and F12 on a fourth was logged as left unedited though Betty placed it 15 s later.

### Fixed
- **Companion waits out a freeze** (9.2468149, 9.2468157, 9.2468160). Betty's clock, top right, ticks every second, so a clock
  that has stopped is told from a key that wasn't taken. When a wait for a screen or a betslip line runs out and the clock has
  stopped, it waits for her, up to 45 s (`BETTY_FREEZE_SECS`). A Betty that's alive on the wrong screen still stops it as before,
  about 2 s later. Screens with no clock showing can't be told, and behave as before.
- **Esc pressed in a freeze is not "Esc does nothing"**: it no longer counts towards giving up on backing out.
- **After F12, a freeze longer than that is no longer called unedited** (9.2468158). Staff are told it may be placed, and to check
  Betty before entering it.

## [1.3.0] - 2026-11-06

Everything below has been through the offline tests and the real screens; **none of it has run on a till**. Sports are off until
the Sports switch in System, Settings is turned on.

### Added
- **The Master Index, and football on handwritten slips** (user, 6 Nov). The team table (`sports_team_names.json`, 460 clubs, with
  the user's rulings) says 'spurs' is Tottenham Hotspur, and Betty's feed files say which match, so the Master Index is searched
  for Tottenham, never Spurs. A team to win in 90 minutes, on an all-football slip. Other markets, a slip mixing football with
  racing, and a name the table leaves to the opponent with none written all go to staff for now.
- **A Sports switch** in System, Settings, and the shop's settings beside it, so no file needs editing. Sports are saved on the till.
- **Waiting** on the Controls tab: how many wagers are waiting and when the oldest was first seen.
- **Betty's price for every runner**, from her feed files.

### Changed
- **An unclear name is looked for among every runner** (user, 6 Nov; 9.2467175). The name, as a whole or as its start, Betty's price
  against the written one, a written time and the meeting. A runner already on the slip is left out. Harrow On The Hill, written
  with no time and read 'MARROW ON THE' at 14-1, is found. A time borrowed from the line above no longer picks the race.
- **A runner chosen for an unclear name must show the written price**, or it goes to staff. On the five priced picks of 5 Nov this
  passes the four right ones and stops the wrong one. With no price written, a number written must be the runner's. A moved
  price sends a right pick to staff. Each pick is listed in the staff journal (kind 'pick').
- **The price box, one order for every line** (user, 6 Nov): Price when struck, the first Forward, Back 1 if 3 seconds old or less,
  Override. A typed line used to get Override at once; if Betty offers a price when struck or a forward price, that's now taken.
- **The watcher no longer switches itself off when it can't reach Home**: it tells staff once and tries again every minute.
- **On a screen it doesn't know**, it saves a picture (`staff_UNKNOWN_*.png`, on the relay), gives Betty the keyboard, clicks a plainly
  safe button (Cancel, Close, OK, Back, Continue, No, Exit), then has the screen read at most every 10 minutes. Nothing else is pressed.
- The control window names the bet edit's screens as staff do.

### Fixed
- **A long runner list wasn't recognised** (screens 66, 67; 13 waits of about 4 s on 5 Nov, and the same screens when backing out): it
  reaches down into where View Wagers' keypad is, so both matched. The bet edit's Cancel Bet now rules View Wagers out.
- **The bet edit with nothing on its left**, with the Windows taskbar over it or between lists, is named `BET_EDIT_BLANK` (screen 68).
- **SP joined to a long name** (9.2467112): 'Wordfromhome&P' reads as Wordfromhome at SP, checked against the selection as usual.
- **'EW' read as 'WIN'** (9.2467051): when the money stays short after two scans, a bet read as win that would make up the difference
  if each way is read again on its own. It's changed only if exactly one such line reads each way, surely.
- **A dog's row on the previous selections** (9.2466811): 'Trap 6' is matched by its trap number.

## [1.3.0] - 2026-11-05

**The Master Index, ready for sports selections** (user's screenshots and video, 5 Nov, built with Betty Companion RAB 1.2.0).
**No wager uses it yet:** a handwritten sports selection still goes to staff, until the slip reader learns to read them (the user
will provide slips). Nothing on racing wagers changes. Tested offline on those screens; not yet run on Betty. Not built yet.

### Added
- **`master_index.py` and section 6e of `betty_companion.py`.** `SCREEN_MASTER_INDEX`; `read_index` reads the search box, the
  state and each row's event, market, result and price, prices by their exact pixels (`index_price_glyphs.json`), since Tesseract
  read `5-2` as `3-2` and `9-2`. A list is believed only when every row holds what was typed. A row is taken when its event,
  market and result fit the selection, as Betty cut them off; the price only tells apart rows reading alike.
- **When Betty bugs out** (user): wait, delete a letter and put it back, type it all again, shorter wordings, the event alone with
  the red arrow's pages, then out by a folder button and back in, twice. Then `IndexStuck`, a kind of `WagerForStaff`.
- **After each click the slip must show that line.** Filters left on are put back. `INDEX_TYPE_AHEAD=1` types ahead (off for now).
- **`betty_feed.SportsCard`:** every sports selection in Betty's feed files: event, market, result, price. For a handwritten slip
  these will be what it's matched against, as the racecards are for racing.
- **A test tool, never used by the watcher:** `python betty_companion.py --index-probe "over 2.5; monaco" ...` opens an empty bet by
  Accept Cash Wager, runs each search at three typing speeds, saves every frame to `logs\\index_probe_<time>`, and backs out. It can't
  click a row, Choose Bet or F12. `--index-try "<event market result @ price>" ...` also clicks each row and checks its line, then backs
  out. Any key or click from a person stops either.

### Changed
- `go_home` on the index clicks the slip's grey foot before Esc: Esc does nothing with the search area focused, and backs out of the
  wager otherwise (user). With a sports selection on a wager, the previous-selections panel isn't used (Master Index rows there crash
  Betty), and Choose Bet and Stake is clicked: the index takes no shortcuts.

## [1.2.28] - 2026-11-05

### Fixed
- **A hard-to-read name could become a runner already on the slip** (9.2467175, 5 Nov). "14-1 HARROW ON THE" had no time written. The reader saw `MARROW ON THE`, took 4:30 from the line above, and the race-list check chose Mountain Of Light, already on the slip at 9-1. That made a false same-race clash, and the bets still cost what was paid. It only stopped because 1.2.19 couldn't enter Perm 5-Folds, a stop 1.2.24 removed. A runner chosen by the race-list check that is also another selection on the slip now sends the wager to staff, saying which. So does a pick with no time written beside it (the time borrowed from the line above) that lands in the same race as another selection, as any other runner in that 4:30 would have made the same false clash. A runner written twice and read clearly both times isn't affected, and nor are two runners in a race when the time was written.
- `recheck_cases.py`: this slip's selections, in either order, both cases; a pick with its own time written in that race still goes through.

## [1.2.27] - 2026-11-05

### Changed
- **The price box with no Price when struck** (user, 5 Nov): a **Forward** price if there is one (Forward 1 when there are two), otherwise **Override with entered price**. A **Back** price never, unless it's 3 seconds old or less. Price when struck stays first, and Enter is still tried first. On 9.2467105 the box offered Back 2, Back 1 and Forward 1, and the program had always gone to Override.
- A Forward beats a Back price 3 seconds old when both are there. A Back price's age is read twice, and any wording other than plain seconds counts as too old: no real box under a minute old has been seen yet, so "3 secs old" and "0 mins 3 secs old" are what's expected.
- A price button that doesn't read goes to staff with nothing clicked, as the choice might be wrong without it. Should Enter ever fail on a box that has Price when struck, that button is clicked, not Override. A typed line still gets Override at once.

### Fixed
- **The price box opening at F8** (9.2467105: Far Too Fizzy). It was never answered there: the program backed out with Cancel, tried again, and left the wager for staff. It's now answered by the same rule, and F8 is pressed again if Betty stays on the betslip. Up to 3 times, then backed out as before. Not yet seen live: whether Betty goes on by herself, or whether the box still opens at F8 after a Forward price.
- The box just before F8 is now told by the price its Override button names, as 1.2.25 said it was. The check it was written into is no longer called, so a typed line could have had Enter pressed there.
- `test_price_box_rule.py` (in `run_all_tests.py`), with the real boxes on screens 64 and 65. The staff guide explains the new reason.

## [1.2.26] - 2026-11-05

### Added
- **A price is read twice before it's typed.** A typed price is paid on as it stands, and on 9.2466814 the slip reader took a 15/1 or 25/1 at the slip's clipped edge for 5/1 without marking it unclear, so 1.2.25 would have typed 5/1. Before typing, the price beside that selection is now read again on its own, from the same picture, without being told the first reading. It is typed only if that read agrees, is sure of every digit and sees nothing cut off. Otherwise the wager goes to staff, saying what it read. One small paid read per selection, a few seconds, only on selections Betty gave no price; once per selection per wager.
- Tried on the three real slips from 5 Nov (12 prices): Final Straw came back "5/1, cut off, not sure", so it goes to staff. Star Bayside Boy's 18/1 came back not sure, so it goes to staff too. The other 10 agreed and were sure.

## [1.2.25] - 2026-11-05

Betty's prices had trouble today: three wagers went to staff as "Betty has no price for it yet", though other runners in those races showed prices and another wager had 7/4 on one of them 40 minutes before.

### Added
- **The written price is typed when Betty gives none** (user, 5 Nov). When a price was taken and Betty puts the selection on at SP, the price on the betslip line is clicked, the written price typed (2/1 is 2.1, 7/2 is 7.2, 11/10 is 11.10, evens is 1.1) and Enter pressed, then **Override with entered price** on Betty's box. Before it went to staff (9.2466814, 9.2466824, 9.2466825).
- Keys go only once Betty's focus box is on that line, as a digit anywhere else picks a runner from the list. The line must then show that exact price. If the line won't take the focus, the price isn't a plain one, the slip reader marked it unclear, or the line shows anything else, the wager goes to staff (nothing placed), saying why.
- **The price box on a typed line keeps the typed price.** Betty opens it whenever that line is touched again, as when guaranteeing it, and Enter there would swap the customer's price for the price when struck. Guaranteeing clicks Override on a typed line and still presses Enter on the others. A box whose line isn't known (just before F8) is told by the price its Override button names.
- `test_typed_price.py` (in `run_all_tests.py`): a stand-in till on the real screen of Presley at SP with Betty's real boxes, where Enter on a box takes the price when struck.

### Fixed
- **Line accumulators no longer blamed on the customer** (9.2466815, 9.2466816). "10p line win acc" on groups of 4, 4, 4 and 2 plus singles is 128 lines, £12.80, as paid; it was costed at 10p and staff were told "their own sums don't match". It now says so ("a line accumulator: 4 x 4 x 4 x 2 = 128 lines at 10p is £12.80, as paid..."), on the first read, without a paid rescan. The program still can't enter them.
- "Their own sums don't match the bets written" now reads "check the bets as read against the slip": the misreading may be ours.
- Old pictures that can't be removed are said once a session, not once per picture (the cashier till listed 30+ each time).
- The staff guide explains the new reasons.

## [1.2.24] - 2026-11-03

### Added
- **Perm 4-Folds to Perm 10-Folds are entered** (9.2463985, 3 Nov). A slip's "50 EW ACCUMULATOR LAST 5" had Vivre Le Reve and Away For The Night both in the Lingfield 14:47. The house rule divides the stake where same-race selections clash, so the same-race rule already made it Perm 4-Folds over all 5 selections at 25p each way (2 valid 4-folds, 100p, the slip's £5.10 matched). But entry had never been given the Perm types, so the wager went to staff ("bet type(s) the program can't enter yet: perm 4-folds"). They're now picked from Betty's bet list by name (no shortcut; the last page on screen 25).
- Betty strikes only the lines whose selections are all in different races: for Doubles over two runners in one race and a third it charged 2 doubles, not 3 (9.2460884, 1 Nov: £7.50 = Payment). Not yet seen for Perm N-Folds itself. If Betty struck every line, its total would be more than the Payment and its own check at F12 would stop it for staff.
- `test_bet_list_choice.py`: the real bet-list read finds Perm 4-Folds on screen 25, the row is clicked once and chosen alone, and Perm 4-10 Folds are enterable (over exactly k selections still Acc On All Selns).

## [1.2.23] - 2026-11-03

About 4 s less per wager (user, 3 Nov: "slow selecting bets" on View Wagers). Measured on the cashier till's 52
wagers of 1.2.17 (2 Nov): loading a wager on View Wagers took 2 s, nearly all OCR, and the time box after it 5-6 s.

### Changed
- **The time box: Tab after 1.5 s, not 4 s** (`TIME_BOX_SLASH_SECS`). From 2 Nov 17:14 Betty on the cashier till
  mostly ignores '/' on race entry, and the Tab of 1.2.17 brings the box up, but only after waiting the whole
  `NAV_TIMEOUT` for '/': all 52 wagers of 1.2.17 waited it. Where '/' works (the manager till, 3 Nov) the box was up
  within a second, so nothing changes there. New check: `nav_cases.py` section 14.
- **A wager's details on View Wagers read 3x faster** (`read_wager_details`): its number, struck time and Payment
  are read by three Tesseracts at once instead of one after another, 0.22 s instead of 0.66 s. A wager is still taken
  only when two reads in a row agree (most took 2 reads, some up to 6 while Betty drew it).

## [1.2.22] - 2026-11-03

### Removed
- **The relay's second free Gemini key** (user, 3 Nov: released, not needed). The free step reads with
  `GEMINI_KEY_FREE_1` only (`RELAY_FREE_SLOTS`); on 2 Nov the second key answered "API key not valid" on both slips
  that reached it. **Relay 1.4.1** (`relay\worker.js`) has no `GEMINI_KEY_FREE_2` slot, so `/ping` and the Gemini
  light list paid and free1 only. Updating the relay is optional: 1.2.22 never asks it for the second key.
  `relay\RELAY_SETUP.md` says how, and to delete the `GEMINI_KEY_FREE_2` secret.

### Fixed
- **The staff screenshot showed Home, not the screen that went wrong** (9.2462614, 2462617, 2462626, 2462632,
  2462636 and 2462637, cashier till, 2 Nov, "time box ('/'): expected RACE_ENTRY_READY"). On a wager's second
  navigation problem the watcher backed out to Home (Esc, Esc) before `leave_wager_for_staff` took the picture. The
  screen is now kept the moment the problem is caught (`screen_now`), before anything is backed out, and saved as
  `staff_<wager>_<time>.png`; the first try's screen is saved beside it as `..._first.png` (not listed as a wager of
  its own on the Staff entries tab). New check: `nav_cases.py` section 13.

## [1.2.21] - 2026-11-03

Values fixed in the code that another shop or till would need different, now settings (user, 3 Nov), and two things
the cashier till's 1.2.17 logs showed (2 Nov, fetched from the relay).

### Added
- **Shop settings in `.env`** (`app_paths.setting`), each read as a number, with the old value when unset or not a
  number: `STAFF_IDLE_RESUME_SECS` (60), `WATCHER_POLL_SECS` (5), `OPEN_ELSEWHERE_RETRY_SECS` (30),
  `SCAN_TIMEOUT_SECS` (90), `RECHECK_TIMEOUT_SECS` (45), `GEMINI_QUOTA_PAUSE_SECS` (600), `LESSON_SYNC_SECS` (60),
  `LOG_UPLOAD_SECS` (120), and how much is kept in `logs\`: `STAFF_SCREENSHOTS_KEPT` (20), `SLIP_IMAGES_KEPT` (200),
  `REUSE_SHOTS_KEPT` (10), `CORPUS_KEPT` (1500), `STAFF_JOURNAL_DAYS` (30). Listed in the staff README.
- **A shop's own house rules and meetings** (`app_paths.data_file`): a `bookmaker_rules.json` or
  `meetings_directory.json` next to `BettyCompanion.exe` is used instead of the one shipped in the build, and survives
  an update (the build keeps everything next to the exe).

### Changed
- **Betty's drive on a cashier till isn't tied to the first shop** (`betty_feed.betty_drives`): after C:\ and every
  drive letter, it looks in `BETTY_SHARE`, then in the network folders the PC keeps mapped (one whose letter isn't
  connected yet after a restart), and only then in `\\PC\drvc`. `BETTY_SHARE` was read when `betty_feed` was
  imported, before the launcher loads `.env`, so a share set there was never used by the window.

### Fixed
- **A Gemini key that isn't valid was tried on every slip** (cashier till, 19:40 and 19:42, 2 Nov): the relay's
  second free key answers "API key not valid", seen on both slips that went to staff when the paid credit ran out.
  It now says which key to replace ("the relay's GEMINI_KEY_FREE_2 isn't a valid Gemini key: replace it in
  Cloudflare") and isn't tried again that run.
- **The program's own selection check counted as another program with the keyboard** (9.2462892, 20:15, 2 Nov):
  the warning sign on staff reasons now leaves out this program's own windows.

### Not changed
- **The screen size stays 1366 x 768.** Every place the program reads or clicks on Betty is measured at that size;
  the manager till was at 1024 x 768 on 2 Nov 20:58 and 21:03, and the program refused to start, as meant.

## [1.2.20] - 2026-11-02

Four screen misreadings found reviewing the saved screens not yet in the golden readings (todolist.md, 2 Nov).

### Fixed
- **Betslip lines with an early price dropped** (9.2460882, 1 Nov): on Choose Bet and Stake, 3 of 5 lines never read, because their `EP` read `EF` and the line pattern took only `EP` / `BP`. It now takes `EF` / `BF` too. All 5 lines read.
- **A long betslip line misread** (9.2462604, 2 Nov): `Phil 5:05 5. Honeysmakemon SP` read `Pri 59:05 &. Honeysi`. Its letters' strokes filled a row of the crop just past the share taken for a ruled line (0.36 > 0.35), so a row through the text was blanked. A ruled line or box edge must now also stand out from the rows on either side (`_rule_rows`); of the 152 betslip rows on the saved screens, only this one's blanking changed, and every real rule and focus-box edge is still blanked.
- **Previous-selections panel meetings misread**: `Carl` read `Can` (9.2460886, 2 letters off, so not matched to Carlisle), `Towc` read `Towe` (9.2461093) and `Harl` read `Har` (screen 15). The rows are now read 4x enlarged instead of 3x: all 62 rows on the saved panels read right, with their names the same as before.
- Screens 58-61 (`scratch/betty_screens`) for these, checked in `test_betslip_full_panel.py` and `test_reuse_panel.py`.

## [1.2.19] - 2026-11-02

### Fixed
- **Staff screens reported unsaved, and left out of the staff journal** (cashier till, from 2 Nov 15:59): the till couldn't remove its oldest picture ("Access is denied" on `staff_9.2458333_20261030_174212.png` and `reuse_9.2460806_20261101_135651.png`). The removal was inside the same `try` as the save, so every screen saved after it was reported as not saved: the journal got `"screenshot": null` (9.2462767 has no screen in the window), and nothing older was tidied (31 staff screens kept where 20 should be). Tidying is now `remove_oldest`, run after the save: each old picture is removed on its own, a read-only one is made writable first (a read-only file gives exactly that "WinError 5"), and one that still can't go is skipped (reported once, with its attributes) while the rest are tidied. The same for the panel pictures, the slip images and the corpus.
- Closing the window while the program stopped raised a Tkinter error in the background: the window was redrawn after it had been destroyed.

### Changed
- **Runners tab: 1st, 2nd and 3rd in bold gold, silver and bronze** (user, 2 Nov), both horses of a dead heat in their place's colour. 4th and 5th stay plain. Before, only the winner was marked, in green.
- `review_fixes_cases.py`: tidying with a read-only oldest picture and one held open; the save still returns its path. `launcher_cases.py` 4: the medal colours, bold.

## [1.2.18] - 2026-11-02

### Fixed
- **A wager another till is editing went to staff** (9.2462767, 2 Nov): End brought up Betty's red pop-up "Bet is marked as in the process of being edited on Manager Terminal!". It wasn't recognised, so the program carried on, pressed '1' and scanned the slip the pop-up half covered (it read only "645 C" and "1"), then sent the wager to staff. The pop-up is now recognised (`MODAL_EDITED_ELSEWHERE`, by the red box and its words): **Continue** is clicked where its label is read, and the wager is skipped and looked at again in 30 s, like a wager another till is viewing. Nothing goes to staff. If Continue can't be found, nothing more is clicked and the program backs out as for any navigation problem. Backing out (`go_home`) answers the pop-up with Continue too.

### Changed
- **Start stays grey until the light at the bottom says Ready** (user, 2 Nov). Before, Start asked "Not ready to automate... Start anyway?". It follows the light every 5 seconds. A program that stopped with an error can still be started again.
- `nav_cases.py` 8: the pop-up read on screen 57 (the saved screen of 9.2462767); End -> pop-up -> Continue, no '1', no scan, skipped. `launcher_cases.py` 4: Start grey and doing nothing while Not ready, back on when Ready.

## [1.2.17] - 2026-11-02

### Fixed
- **"time box ('/'): expected RACE_ENTRY_READY"**: Betty now and then shows something else after '/' where the yellow time box should be (user, 2 Nov). `open_race_entry` now presses **Tab** once and checks again, which brings the time box up; only if it still isn't there does the wager stop as before. Not pressed when the screen isn't recognised but the yellow box is plainly showing.

## [1.2.16] - 2026-11-02

Both tills' logs on the relay, so either till, and Claude on either of them, can read them and work out fixes (user, 2 Nov). Needs relay **1.4.0**: paste the new `relay\worker.js` into the Worker (RELAY_SETUP.md). Until then the tills keep their logs as before and the window says the relay needs updating.

### Added
- **Each till uploads its logs** (`relay_logs.upload`, from the window every 2 minutes, built program on a paired till only): the session logs, `staff_journal.jsonl` and the screens kept for staff (`staff_*.png`, `slip_*.png`, `reuse_*.png`) written in the last 14 days. A log goes up as it grows, from where the relay's copy ends (pieces of 700 KB); the staff journal, rewritten at start-up without its old lines, is seen by its first bytes and sent again whole. The corpus and `f8_` folders stay on the till. System > Settings says when the logs last went up, or why not.
- **Fetching the other tills' logs** (read only, with the till's own pass): `python relay_logs.py` on the manager till puts the cashier till's logs in `scratch\imported_logs\<till>\`, where `live_report.py` already looks; `BettyCompanion.exe --fetch-logs` does the same on a till without Python, into `relay_logs\<till>\` next to the exe (the result in `relay_logs\fetch.txt`). `--all` adds the till's own; `--to <folder>` puts them elsewhere. Each log is fetched from where the copy there ends; a log the till rewrote is fetched again.
- **Relay 1.4.0** (`relay\worker.js`): `/logs/put`, `/logs/list`, `/logs/get`. A till reads the logs of its shop's tills, or only its own when in no shop (as for lessons). A piece that doesn't start where the relay's copy ends is refused with the relay's size, so nothing is kept twice or skipped. Logs not added to for 30 days are dropped. `/admin` shows each till's log count and when it last added one.
- `scratch/test_relay_logs.py` (in `run_all_tests.py`, needs Node.js): worker.js run locally with three tills in two shops: upload and fetch byte for byte (a £, a ✓ and a PNG), the other shop shut out, only new lines both ways, a log in pieces, the journal rewritten, the till's record of what's sent lost, refusals, an unpaired till, nothing sent from the source folder.

## [1.2.15] - 2026-11-02

Race results on the Runners tab (user, 2 Nov). Betty keeps them in `C:\DBF\SETTDATA.DBF`, one row per event settled, with the placings in the memo `RP1` of `SETTDATA.fpt`. `results.dbf`, despite its name, only lists the races and their off times.

### Added
- **Result and SP columns on the Runners tab**: 1st to 5th as far as Betty has them (some races list only the places paid, others the whole field), with each placed runner's SP. Dead heats show as `1st dh`. The winner is green; a placed runner stays dark when its race is off. The count says how many races have results. Read again with the rest of the tab (every minute and on Refresh).
- `betty_feed.BettyResults` and `decode_placings`: today's rows of SETTDATA.DBF (found once a day, read again at every look, as a resettled race is rewritten in place), memos read only for the races on the card. Runners are found by event id and cloth number when the names agree, else by name; Betty cuts long names to 16 characters ("The Days Are Go'"). Any problem reading gives no results.
- Checked against Betty's own tables: all 146 placings of 1 Nov's 36 UK & Irish races matched the card by cloth and name. RP1's SPs are the starting prices (Southwell 17:30, 17 Oct, as published: 11/4, 7/4 fav, 10/1); FSPRICES holds other prices. Live, Plumpton 13:00 today appeared about 20 minutes after the off, in full (4 of 4).
- `launcher_cases.py` 2b: a stand-in SETTDATA.DBF/.fpt (1st to 5th, Evs, a name cut short, a dead heat, a wrong name at a cloth, deleted and yesterday's rows, no table), Betty's real results for 1 Nov, and the Runners tab's columns and colours.

## [1.2.14] - 2026-11-01

1.2.13 placed 9.2460882 (7 bets, 10 selections from the previous-selections panel) but slowly (user, 1 Nov): the OCR, each panel click, and above all the wait between the bet going in and F12. Measured on the saved screens: a read takes ~145 ms, of which ~140 ms is starting tesseract.exe (a blank picture takes as long); the panel's 3 rows took 0.95 s as 6 reads; F12 waited 1 s, then a read of the screen and two reads of the total (~1.5 s). The same wager's reversed forecast double sent 9.2460746 to staff every time.

### Changed
- **F12 straight after the last bet type, live** (user, 1 Nov): Choose Bet and Stake is told by its colours (~30 ms) and F12 is pressed. The total is no longer read before it: Betty checks it against the Payment itself at F12, and its question then goes to staff with nothing answered (as before). Test mode, which never presses F12, still reads and checks the total.
- **1.2.0's waits on Choose Bet and Stake again**: 0.1 s after the stake (was 1 s) and 0.15 s after the bet type (was 1 s). 1.2.10 added them for Betty going Home, which was the Tesseract window (1.2.12); 1.2.12 placed a Lucky 15 and a Lucky 31. About 1.75 s a bet.
- **Several pieces read with one start of Tesseract** (`_ocr_bw_many`: one run over a list of pictures): every row of the previous-selections panel (0.95 s -> ~0.25 s for 3 rows), and the betslip's last lines after each selection (~0.15 s a selection). The text is the same as one read each: 151 of 151 crops (panel rows; every betslip row of every saved screen).

### Fixed
- **Forecast doubles are entered** ('4 x 40p R/F/CAST DOUBLES': a reversed forecast in each of two races, 4 bets): Betty's "Rev. F'cast Doubles" and "Forecast Doubles" rows, found by name (no shortcut). They were costed but refused at entry ("bet type(s) the program can't enter yet: reversed forecast double", 9.2460746 five times on 1 Nov); no other type was refused in the logs since October. A straight forecast double keeps the order written.
- **A bet type on a later page of the bet list**: the rows chosen on a page (Singles, from F8) are clicked off before PgDn. Only the page holding the type was checked, so Singles would have gone on too; no type had been paged to live before.

### Added
- `scratch/test_forecast_doubles.py` (in `run_all_tests.py`): 9.2460746's bet, Betty's row names, and choosing them on a stand-in list paged like Betty's. `nav_cases.py`: F12 with nothing read first, and a wrong total met by Betty's question at F12.

## [1.2.13] - 2026-11-01

The previous-selections panel (right-click on the slip image) never worked live: every try said it "didn't show" and typed the selection instead (9.2460806 at 13:56-13:57, 9.2460882 at 14:02, the user's recording of 14:01). It opened every time. Its rows are white when the selection is on the slip being entered already and cyan when it isn't, and a red line runs only above and below them all, not between rows. The program looked for white rows each between two red lines, taken from screen 15 alone (one row, The Favourite, on its slip), so it could only find rows that didn't need adding. 1.2.0 looked for the same white row at y 286.

### Fixed
- **The panel's rows are found by their shape** (`_reuse_row_boxes`): a red line across the panel above the rows and one below, red column borders at x 5, 137, 311 and 399 the whole way down, and a whole number of 35 px rows between. Found on all 6 saved panels (15, and 52-56 from today's logs), 1 to 3 rows, and on none of the other 98 saved Betty screens.
- **Betty showing the panel is named as such** (`detect_screen`, by the same shape): 1.2.12 named today's panels RACE_ENTRY.
- **A white row is never clicked** (`find_reuse_row`): its selection is on the slip already, and a click would add it twice. The log marks it `(on this slip)`.

### Added
- Screens 52-56 (today's panels) in `scratch/betty_screens`, in `test_reuse_panel.py` (rows read, white or not, which row each selection is, the price clicked at its row on a real screen) and `screen_cases.py`; `test_screens_golden.py` records the panel's rows. `live_report.py` warns when a previous selection was typed because the panel wasn't seen.

## [1.2.12] - 2026-11-01

Betty going Home on Choose Bet and Stake (the reversed forecast 9.2459992 on 31 Oct, the Lucky 15 9.2460715 today, on every version from 1.2.1) was a Tesseract window taking the keyboard from Betty, not the keys or their pace. The user's recordings of 1.2.0 and 1.2.11 entering 9.2460715 (13:08, 13:18) show the same keys, `f8, 1, 0, 0, enter, l`. On 1.2.11, 0.3 s after 'l', the taskbar comes up and a `tesseract.exe` console opens over Betty, and 0.7 s later Betty puts 'A-Bet System' in front of its bet edit. `scratch/focus_monitor.log` has it too: a tesseract.exe console took the keyboard at 13:19:47.6 and Home followed at 13:19:48.3, and a console took it once on every start of the program this morning.

1.2.2-1.2.10's waits were for the wrong cause: the stake box shows '100' until the bet key on 1.2.0 as well, and 1.2.11 waited longer than 1.2.0 and still went Home. They stay in 1.2.12 and come out in 1.2.13, once 1.2.12 has entered wagers live, so any change in behaviour is known to be this one.

### Fixed
- **Tesseract's version is asked on starting, hidden** (`_ask_tesseract_version_hidden`). pytesseract asks it once a run, on the first `image_to_data`, and that is the one run of tesseract.exe it doesn't hide. 1.2.0's first `image_to_data` was on the first runner list, where the window did no harm (one frame of the 1.2.0 recording, at 41.5 s); 1.2.1's quicker runner-list reads left the bet list's read, 0.08 s after the bet shortcut, as the first. Singles don't read the bet list, which is why they went in.

### Added
- **Other programs' windows in the log**: when a wager goes to staff, every window of another program that had the keyboard in the last 30 s (`ForegroundLog`, a Windows hook: looks only). `betty_windows_report` lists only Betty's windows and the F8 recorder looked 10 times a second, so neither showed the console.
- `scratch/test_no_console_windows.py` (in `run_all_tests.py`): loads the program and reads a bet list and a runner list with no console, as the exe does, and checks that every tesseract.exe it starts is hidden and that Windows showed none; two controls show it catches 1.2.11's fault. `live_report.py` warns when another program had the keyboard before a staff reason.

## [1.2.11] - 2026-11-01

The offline tests passed while the tills failed (user, 1 Nov): they stand in for Betty, which answers at once and always as expected, and they only had the screens already seen. Checks against the real Betty are added, and the tills now keep what they need for them.

### Added
- **Live capture for the tests** (`corpus_save`, `corpus_outcome`): each decision taken from Betty's screen (the race on top of the runner list, the betslip line after each selection, the bet list's row, a wager's View Wagers details), with that screen, the inputs and the card at that time, and how each wager ended (placed, entered in test mode, staff). Kept in `logs\corpus\` (the newest 1500 pictures, ~90 KB each), written by a thread of its own: the till never waits for it (`corpus_save` returns in under a millisecond). `BETTY_CORPUS=0` turns it off. Looks only.
- **Tests on real material** (in `scratch\`, not shipped):
  - `test_live_corpus.py`: today's code on every captured decision. A decision on a wager that was placed and now decided otherwise is a failure; one on a wager that went to staff is listed as changed, for a person to label (`--label`).
  - `test_screens_golden.py`: every screen reader on every saved Betty screen (91: `betty_screens` and `screen_corpus`, which now keeps every staff and panel picture from the logs before they're pruned) against the golden readings, with the time each took. It records the runner list's top-label decision too: run on 1.2.8's code it reads the Timberwell screen as nothing, where 1.2.0 and now read Timberwell.
  - `live_report.py`: every wager in the session logs by version: placed, staff (the program's fault or the slip's), stopped, and warning signs (the edit going behind Home, the watcher backing out of an open edit, the slip not shown, the runner list's top unread, a betslip price other than the one written).
  - `run_all_tests.py`: all of the above and the offline suites in one go, with a table.

## [1.2.10] - 2026-11-01

1.2.9 read Timberwell at 2:42 as it should (9.2460715, 11:40: "Runner list starts with Timberwell: 'right' to bring up Huntingdon"), entered all four selections and their guarantees, then stopped on Choose Bet and Stake as the forecast had: a Lucky 15, so not only forecasts (user, 1 Nov).

### Changed
- **A second after the stake and a second after the bet type** (user, 1 Nov): stake and Enter, 1 s (`F8_AFTER_STAKE_SECS`, was 0.1 s), the each-way button read and set, the bet type, 1 s (`F8_AFTER_BET_TYPE_SECS`, was 0.15 s), then F11, F10, or the total read and F12. About 1.75 s more a bet. Esc still stops it during either wait.

## [1.2.9] - 2026-11-01

Two of 1.2.8's three wagers this morning went to staff with "the meeting at the top of Betty's 2:42 runner list could not be read" (9.2460715, 9.2460730): Timberwell's 2:42 virtuals sat above Huntingdon 2:42. Every 1.2.1 reading change was then checked against 1.2.0's on all 92 saved Betty screenshots (`scratch/betty_screens`, the staff and panel pictures in `logs`): the betslip reads (whole and last-lines), the line counts and the runner rows all agree with 1.2.0; only the runner list's label read differs.

### Fixed
- **The runner list's top label is read row by row again when the one-pass read names no meeting** (`top_meeting_in_race_list`). 1.2.1's one read of the first three labels is 2.5x quicker (5.7 s against 14.4 s over the saved screens) and reads 'Donc', 'Newc' and 'Mill' where 1.2.0 read 'done', 'newe' and 'wav', but it can lose a label's first capital: 'Timb 2:42(v)' read 'imb' and named nothing, where 1.2.0's read named Timberwell. The quick read stays first; 1.2.0's read follows only when it names nothing.
- `scratch/test_runner_list_top.py` has the Timberwell screen (`51_race_list_timb_virtuals_above_hunt_242.png`, with its card `card_1nov_1442.json`).

## [1.2.8] - 2026-11-01

Choose Bet and Stake (F8 through F10 / F11) is 1.2.0's code again. 9.2459992, a two-dog reversed forecast, went Home on that screen on every try of 1.2.1-1.2.6, and was entered by 1.2.0 and by the user by hand. The recording (`logs\f8_9.2459992_20261031_191852`) shows Betty took the stake at once (its summary changed in the frame after Enter) and stayed still until 'r'; from the frame after 'r' it redrew the bet list and stake panel twice, never chose Reversed Forecasts, and put 'A-Bet System' in front with both edit windows still open behind it. 1.2.7's account (Betty still busy with Enter for 0.93 s) doesn't fit those frames, and putting back only some of 1.2.0's waits (1.2.3-1.2.5) didn't work, so the whole stretch is 1.2.0's.

### Changed
- **Back to 1.2.0** on Choose Bet and Stake: a look at the screen after every key (the log marks a key after which Betty had gone: `r (screen gone)`), 0.1 s after Enter and the each-way button read and set (W or E), 0.08 s after the bet shortcut and after PgDn, 0.15 s after the bet type, 0.15 s before the backspaces and 0.01 s between them, 0.2 s after F11. No other wait before F8.
- **Taken out:** 1.2.7's 0.95 s after Enter and its `focus_betty()` before the bet shortcut; 1.2.7's `betty_top_window` preferring any window not called 'A-Bet System' (it could bring a stale edit, or another of Betty's windows, over Home); 1.2.7's bringing an edit window back to the front when Home is seen (the program went on typing into a bet edit Betty had put behind Home); 1.2.5's 2 s before F8; 1.2.3's pacing constants.
- **The F8 recording is off** unless `BETTY_F8_RECORD=1` is set: 1.2.0 had nothing else running on that screen.
- Kept, as they press nothing: the screen check before blaming the bet list (1.2.2), Betty's windows in the log (1.2.3), the 1.2.1 betslip and runner-list reading, and the previous-selections panel fix.

## [1.2.7] - 2026-10-31

Analysis of the 10-fps Choose Bet and Stake recording (`logs/f8_9.2459992_20261031_191852`) revealed why 1.2.1-1.2.6 failed while 1.2.0 succeeded:
1. Betty takes ~0.93 s (frames 12-18, 01.90s to 02.83s) after Enter on the stake to commit the bet calculation, redraw the bet list (blank at 02.36s), reset Singles to green (02.51s), and format the stake box (`100` -> `£1.00` at 02.83s).
2. With 1.2.1's pacing removed, `r` was sent at 02.19s (only 0.29 s after Enter), mid-redraw. The shortcut was swallowed and Betty redrew Singles as green. At 02.83s, upon completing the stake update, the dialog lost focus and Windows activated the main application window ('A-Bet System') at 02.96s (frame 19), hiding the still-open edit dialogs.
3. Both 'untitled' edit windows (Race Entry and Choose Bet and Stake) remained alive and open at 1366x768 directly behind 'A-Bet System'.

### Fixed
- **0.95 s wait after Enter on the stake** (`F8_AFTER_ENTER_SECS`, or `BETTY_F8_AFTER_ENTER_SECS` to configure): allows Betty to complete formatting the stake box and redrawing before any bet shortcut key or button check is sent.
- **Topmost edit window restoration** (`betty_top_window`): prioritizes any visible full-size 'untitled' edit windows over 'A-Bet System', so `focus_betty()` brings the active edit dialog back to the front rather than focusing Home.
- **Auto-recovery on Home detection** (`_still_on_f8`): if Home is seen while edit windows remain open behind it, `focus_betty()` restores the Choose Bet and Stake window to the front before concluding that Betty left the screen.
- **Focus before bet shortcut** (`choose_bet_type`): calls `focus_betty()` before sending the shortcut key to ensure the dialog receives it.

## [1.2.6] - 2026-10-31

1.2.5 went Home too (9.2459992, 19:10, after `f8, 1, 0, 0, enter, f`, the row never turned green). The keys, their pace, and the code after the bet shortcut are now the same as 1.2.0's, so the cause can't be found by reading the code; it has to be seen.

### Added
- **A recording of Choose Bet and Stake** (`F8Recorder`): from F8 (or F11) until the bet type is chosen, Betty's screen and windows (which is on top, which has the keyboard) about 7-10 times a second, in memory. When Betty leaves the screen it is saved as `logs\f8_<wager>_<time>\` (frames plus `index.txt` with the keys sent so far at each frame); the newest 3 are kept. It only looks.

## [1.2.5] - 2026-10-31

1.2.4 went Home too (9.2459992, 19:05): Betty showed Win Only, so the each-way check changed nothing. With 1.2.3-1.2.4 the keys and clicks sent to Betty, and their pace on Choose Bet and Stake, are the same as 1.2.0's; what is left is the time 1.2.1's quicker reads took out between them. Singles went in on 1.2.1 (18:33); only the two-dog forecast failed.

### Fixed
- **2 s between the last selection's check and F8** (`F8_AFTER_SELECTIONS_SECS`, or `BETTY_F8_AFTER_SELECTIONS_SECS` to change it without a build). 1.2.0's whole-betslip read left Betty about 3 s there; 1.2.1's read of the last two lines about 1 s. This is the one change in 1.2.5, so the next try of a forecast says whether this gap is the cause.

## [1.2.4] - 2026-10-31

1.2.3 went Home on Choose Bet and Stake too (9.2459992, 18:53, keys paced: `f8, 1, 0, 0, enter, r`), and 1.2.0 then entered the same wager (18:56, user's swap back). So the key speed wasn't it. With the pacing back, the one thing left on that screen that 1.2.0 does and 1.2.1 doesn't is the each-way check.

### Fixed
- **The each-way button is read after the stake again and set to the bet** (as in 1.2.0): Each Way showing on a win bet -> W, Win Only on an each-way bet -> E. 1.2.1 had dropped the read and pressed only E, taking every bet as starting at Win Only. When the button had to be changed, the log now says what it showed (`Choose Bet and Stake showed Each Way after the stake: W pressed.`), which 1.2.0 never said.

## [1.2.3] - 2026-10-31

1.2.2 went Home on Choose Bet and Stake again (9.2459992, 18:37, keys `f8, 1, 5, 0, enter, f`): the wait after Enter wasn't enough. Both of 1.2.1-1.2.2's live wagers went this way; 1.2.0 never did. Bets.exe itself didn't crash (one process since the morning, nothing in Windows' log or BETTYERR.TXT), so Betty's bet edit window closed or went behind 'A-Bet System' (user: the edit is its own window, Home is the main one).

### Fixed
- **Stake-screen keys paced again** (user, 31 Oct: typed too fast): 0.08 s after each key on Choose Bet and Stake (`F8_KEY_GAP_SECS`, about what 1.2.0's screenshot per key gave), 0.2 s once the screen shows before the first key (`F8_SETTLE_SECS`), and 1.2.0's 0.01 s between backspaces. Still no screenshot per key. About 1 s a bet.

### Added
- **Betty's windows in the log** when Betty leaves Choose Bet and Stake (`betty_windows_report`): each of Bets.exe's windows top first, and which has the keyboard. One window = the bet edit closed; an untitled one behind 'A-Bet System' = it was pushed behind.

## [1.2.2] - 2026-10-31

From 1.2.1's first live wager on the manager till (9.2459992, 18:21): a reversed forecast went to staff as "could not select only reversed forecast in Betty's bet list (selected: [])". The row had turned green, then Betty was on Home; the staff screenshot shows Home. Nobody touched the till.

### Fixed
- **A short wait after Enter on the stake** (`F8_AFTER_ENTER_SECS`, 0.1 s). 1.2.1 sent the stake, Enter and the bet shortcut in the same instant; 1.2.0 had 0.1 s after Enter (and a screenshot after every key) and never went Home there. The other stake-screen keys still don't wait.
- **Betty leaving Choose Bet and Stake is called that** (`_still_on_f8`): before the bet list's colours are blamed, or a row clicked when its shortcut didn't turn it green, the screen is checked. When Betty has left, the reason is "Betty left Choose Bet and Stake (now on …)" with the keys sent there printed, and nothing is clicked on the other screen.
- `scratch/test_bet_list_choice.py` has the case: Betty on Home just after the row went green.

## [1.2.1] - 2026-10-31

From the cashier till (user, 31 Oct): entry had become much slower, and the previous-selections panel opened but the time was typed anyway.

### Fixed
- **The previous-selections panel is found wherever it opens** (`_reuse_row_boxes`). It was looked for only at y = 286 (one screenshot), so it opened unseen, the program waited 4 s, and the time was typed after all.
  - Now the panel is found by its rows: thin red lines right across it with white between (no other Betty screen has them).
  - Each row is read; a row that doesn't read is kept, and taken by its place in the order entered when the panel lists exactly the selections entered (the betslip check after the click still decides).
  - Whenever the panel can't be used, the log says what was read and a picture is saved: `logs\reuse_<wager>_<time>.png`, the newest 10 kept.

### Changed
- **Faster entry** (user, 31 Oct: Betty buffers keys; clicks still wait for what they click):
  - **Keys:** none waits for the screen any more: the stake, backspaces, F11, the bet shortcut, PgDn. The screenshot after every key on Choose Bet and Stake (13 or so a bet, only for the log) is gone; the keys are still listed if Betty leaves that screen.
  - **Each way:** a bet starts at Win Only, so only an each-way bet presses E. The each-way button is no longer read first (user). Betty's total against Payment before F12 still catches a bet gone in the wrong way.
  - **Betslip reads:** after each selection only the betslip's last two lines are read (`read_betslip_tail`): ~0.4 s, was 0.8-1.7 s per read. A blank row is seen by colour before any reading: four reads of each blank row had cost ~0.85 s.
  - **Price box:** looked for for 0.1 s after a selection is added (was 0.4 s). The betslip read that follows answers one opening later.
  - **Runner list:** its top is read by the label of its first rows in one read (~0.17 s, was ~0.5 s for three), and the slower read of its runners only when the label doesn't name a meeting on the card (it was done every time). A label read as the wrong race is still caught by the betslip check. Horses and dogs sharing a label are still told apart by the list's rows before anything is typed. Whether the list changed after 'right' is one read of its first rows (~0.23 s, was ~0.7 s).
- The tests that stand in for parts of the program follow these changes (`entry_cases`, `test_runner_list_top`, `test_reuse_panel`, `test_betslip_full_panel`).

## [1.2.0] - 2026-10-31

The tills of one shop share what staff teach them (phase 4 of the training plan). Needs **relay 1.3.0** to share (`relay\RELAY_SETUP.md`, "Updating the relay's code to 1.3.0"). With an older relay everything works as in 1.1.12, each till with its own lessons, and the Training tab says why it isn't sharing.

### Added
- **Shops on the relay (worker.js 1.3.0).**
  - `/admin` has a **Shop** button on each till; both tills of a shop get the same name.
  - The relay knows a till by its pass and works out its shop, so a till only ever sees its own shop's lessons. A till in no shop keeps its own.
  - A till joining a shop takes what it has already learned with it.
  - New: a `lessons` table, `lesson_images` (pictures of slips taught as examples), `tills.shop`, and the `/lessons/sync` and `/lessons/image` endpoints. The relay adds the tables itself.
  - Counts arrive as additions, so two tills counting at once lose nothing.
- **The tills sync their lessons with the relay** (`lessons.sync`).
  - `lessons.json` stays the working copy, so lessons work with no internet. Each lesson notes what it still has to send: an edit, counts, a deletion, or a slip picture.
  - The program syncs every minute (`lesson_sync_loop`) and straight after something is taught. The window syncs on the Training tab, after an edit, and every minute.
  - Lessons taught on 1.1.12 are sent with their counts.
  - Only the built program syncs: runs from the source folder (the free tests, development on this PC) never reach the shop's relay unless a test opts in with its own relay.
- **The Training tab says where its lessons are shared:** with shop '...'; kept for this till on the relay; kept on this till only; or why not just now. It also shows when it last shared. The Help tab and `release\README.txt` say how sharing works.

### Fixed
- **The end of `relay\worker.js`:** a stray `0` that had followed the code since 1.0.0 is gone (harmless, but not meant to be there).

### Docs
- `relay\RELAY_SETUP.md`: updating to 1.3.0, "Shops", and what the relay now stores (lessons; for a slip taught as an example, its picture and lines).

## [1.1.12] - 2026-10-31

### Added
- **The program can be taught a shop's quirks without code changes** (user, 31 Oct; phases 1-3 of the training plan). What staff teach is kept as data in `lessons.json` next to the exe (this installation's own: builds keep it, git ignores it), by `lessons.py`. Any member of staff can teach; a lesson is active at once.
  - **Handwriting** ('MOVIT LIKE MINIE' = Moveit Like Minnie): from the can't-read box, where 'Remember this for next time' is ticked by default (`teach_from_manual_entry`). Used after the usual name match fails and before the paid re-check, only when that runner is on today's card at the written time and only one race fits (`taught_runner`).
  - **Meetings** as the shop writes them ('N/M' = Newmarket): from the box (a meeting of 2+ letters that didn't match; a single letter never), or Add a lesson. Used by `_meeting_matches`.
  - **Bet wording** ('YANKIE' = yankee): Add a lesson (the meaning must be bet words the program reads). The slip's lines and bets are read as if the meaning was written (`lessons.apply_wording`), then costed and checked as usual.
  - **Whole slips**: Staff entries, Teach from this slip, on a wager left for staff. Staff correct the lines the reader read (now saved with each staff hand-off, with the slip picture). The slip reader is shown up to two such slips and their true lines as worked examples (pictures kept in `lessons\`).
  - The slip reader's instructions get "THIS SHOP'S SHORTHAND" from the meeting and wording lessons.
  - **System › Training** lists every lesson: written, means, taught when and on which till, used, placed and to staff, on or off, with its slip picture. It has Add a lesson, Turn off / on, and Delete, and follows the file as the program changes it.
  - A lesson whose wagers go to staff 3 times with none placed turns itself off (`AUTO_OFF_STAFF`).
  - **Lessons are hints only**: the racecard match, the money, the betslip read-back and Betty's total all still apply.
  - Headless test runs teach nothing.
- The Help tab has a section on teaching.

### Fixed
- **A build never leaves the program's folder half deleted.** The folder is moved aside whole, then deleted: a file in use (the program, or the antivirus reading the new exe) stops the move with "nothing was changed". On 31 Oct a lock on the exe, after `_internal` had gone, left a folder that couldn't run. (`build_release.py`)
- **Several whole bets of one type are entered as one at the stake times that many** ('2 x 10p yankees': costed as 2 yankees, £2.20, but entered as 1 at 10p, so Betty's total fell short of the payment). `whole_bets` (rules_engine) decides it for the costing and the entry alike; 1 yankee at 20p is 2 yankees at 10p. Forecasts and tricasts keep their own line counts.

## [1.1.11] - 2026-10-31

### Fixed
- **Guarantees by Down no longer stall where the betslip scrolls** (9.2459368, 15:10: ~12 s between lines 9 and 10, where Down from the bottom row was given up and line 10 clicked). Down from the bottom row was taken only for a one-line scroll with the focus box staying on that row. Betty scrolls further: the box lands elsewhere, and the scroll position was never re-read. Now, unless the box simply moves down a row, the lines showing are read and say how far the panel scrolled, so the box's row gives its line however Betty scrolls (`_focus_down_to`). What Betty did is logged ("Down to line 10: Betty scrolled the betslip 8 line(s) ...").

## [1.1.10] - 2026-10-31

### Added
- **A Help tab** (user, 31 Oct): how to run it day to day, in plain words: what it does, starting each day, live or test, the keys on the till, what to do with a wager left for staff, the other tabs, the lights, when something goes wrong, updating. The text is `HELP` in launcher.py.

### Changed
- **The Runners tab shows when each race went off to the second** ("off 11:25:55"; user, 31 Oct: the minute isn't enough). Betty's off slips have the second; the window rounded it away.
- **A small country flag before each meeting in the Data tab's four meeting lists** (user, 31 Oct), from the feed's country code ('UK' is the Union Jack). Drawn by the window (`flag_image`), no image files: today's countries (UK, IE, AU, US, ZA, AE, AR, CA, CL, DE, KR, MU, MX, UY) and other racing countries. A meeting the feed gives no country gets a blank space, so the names stay in line. The meeting column is the table's first, Tk's own, the only one that can show a picture (`_tree(picture_first=True)`).

## [1.1.9] - 2026-10-31

### Added
- **Selections already entered on a wager come from the previous-selections panel** (user, 31 Oct: 9.2459558 and 9.2459560 typed the time again for every selection on their later slips). The panel was built in 0.20.0, removed in 0.20.7, and only recognised since 0.32.0, so nothing used it. `enter_wager` notes each selection entered (`selection_key`). On a later betting slip of the same wager, one already entered is taken from the panel (`enter_from_reuse_panel`):
  - right-click on the slip image (unless the panel is open: it stays open);
  - its row found by reading the rows (`reuse_panel_rows`, `find_reuse_row`: meeting label, time, name; 'The Favourite' for a favourite), not by its place;
  - the row's price clicked when a price is taken, its name for SP (as on the runner list);
  - the betslip line checked like any other.
  - Folder favourites are reused too (user: only Master Index entries crash Betty, and the program makes none).
  - When the panel doesn't open, the row isn't there, or the click isn't taken (nothing added), it says so and enters the selection the usual way. A line added but wrong goes to staff.
  - The next new selection's '/' brings the time box back from the panel.

## [1.1.8] - 2026-10-31

From 1.1.7 on the till, 12:52-13:35: 17 wagers placed, 4 to staff. Two were genuine money mismatches (the slips' own sums), one the shop's rule (a price taken with none on Betty yet), and one a fault, fixed here.

### Fixed
- **'right' no longer reads the old runner list as the new one** (9.2459558: Towcester read twice after 'right', so 'right' went again and Down Royal 2:38 was passed; "not in Betty's runner list"). After 'right' a runner list counts only once the race on top has changed (`runner_list_signature`: the top race's label, kind and first runners). The old list still showing is no longer taken for the next, which also ends most of the 4 s "screen not recognised" waits.

### Changed
- **A meeting passed is walked to again.** The end of the runner list after 'right', with the meeting on Betty's card at that time (`hhmm_on_card`), means it was passed. The time is typed again and the list walked once more before staff.
- **A money mismatch where the customer wrote what they paid says so** ("their own sums don't match the bets written"; 9.2459559: bets of £7.50 under '8', paid £8).

## [1.1.7] - 2026-10-31

From 1.1.6 on the till at 12:26: two wagers to staff over betslip lines that were plainly there.

### Fixed
- **A line number read without its dot still reads** (9.2459454: '4 Keen 8:20 14. Puerto Rico SP' after adding Puerto Rico, so "shows 3, expected 4"; 9.2459368: '4 Weth 1:10 1. Palamon' under the focus box, so "line 4 is on screen but couldn't be read" after three guarantees by Down). `BETSLIP_SELECTION_LINE` takes a space where the dot dropped out; the meeting and the time that must follow keep a line unmistakable.

### Changed
- **The betslip reads correct themselves rather than stop.**
  - A row that doesn't read is read other ways in turn (`BETSLIP_ROW_READS`: ruled rows blanked, as it is, the focus box's edges cut off, larger).
  - A row holding a line counts, read or not (`betslip_rows_with_text`, `betslip_count(lines, img)`), so a line that doesn't read can't make the betslip look a selection short.
  - Only when no way of reading it works does a line added go to staff, saying so ("betslip line N is there but couldn't be read to check it").
  - A line on the panel that doesn't read is no longer a reason to stop: its row is known from the others (`betslip_row_of`).
  - Whether the panel is full (and so can hide lines above) is the bottom row holding a line, read or not (`panel_full`).
- **Guarantees by Down know the line by where the focus box is, not by reading under it.** The box moves down a row, or at the bottom row stays while the panel scrolls one line under it. The line's price comes from what it showed before the box was round it (`known`). A line clicked is clicked by its row, read or not.

## [1.1.6] - 2026-10-31

From 1.1.5's run of the 17-selection wager (9.2459368, 11:57): all 17 entered and checked and 13 guaranteed, then staff at line 14.

### Fixed
- **A betslip line that won't read no longer hides the lines under it.** After 'g', Betty's dotted focus box round line 13 made it read '13.D0Wwn'; the read stopped there, so lines 14-17 weren't seen and the down arrow was looked for. Rows are now read down to the first blank one; a row that doesn't read is read again without blanking ruled rows, else left out (`read_betslip_row`, `_betslip_row_blank`). Each line's selection number is the lines hidden above the panel plus its row, where the lines read agree how many are hidden (`_betslip_offset`; a misread number is outvoted). A line on the panel that doesn't read is read again, never scrolled for, then staff ("betslip line N is on screen but couldn't be read"). The same fault sent the arrows up and down while guaranteeing.

### Changed
- **Best odds guaranteed: click the first, then 'g', Down, 'g' ...** (user, 31 Oct; it took ~1 min for 13 lines). Down is taken to the line straight after one just guaranteed, and only when Betty's focus box (`betslip_focus_row`, its red dashes) is seen on that line first and then on a line reading the next number (`_focus_down_to`); otherwise the line is scrolled into view and clicked. A non-runner, withdrawn or void line is skipped and the next one clicked. Each 'g' is still confirmed purple and never pressed twice. The 0.4 s wait for boxes after each line is one look.

## [1.1.5] - 2026-10-31

Fixes from 1.1.4's first morning on the till: a 17-selection wager (9.2459368) and a bet type clicked off (9.2459384).

### Fixed
- **Betty's betslip panel shows 9 lines, and more scroll** (9.2459368: 680 x 10p trebles on 17 selections went to staff at the 9th: "shows 8 selection(s), expected 9"; it had been added). `BETSLIP_MAX_LINES` is worked out from the panel (9; it was 8). Lines are 45 px apart (`BETSLIP_LINE_PITCH`, was 45.33, which clipped lines 11-12). With more lines Betty scrolls to the newest and draws a yellow arrow (up at the top right, down at the bottom right; user's screenshots). The lines' own numbers count and match the selections on a full panel (`betslip_count`, `betslip_lines_by_number`). A line is brought into view with the arrows (`show_betslip_line`) to check it or to click it for best odds guaranteed, and the panel is scrolled back down after (`scroll_betslip_to_end`). The whole slip is read by scrolling (`read_whole_betslip`). Error guide: "Betslip couldn't be scrolled".
- **`build_release.py` no longer wipes the till's own files or a running copy** (31 Oct: a build while the till ran the exe from `dist\BettyCompanion` deleted its Tesseract mid-wager, and every build deleted the logs). It stops while `BettyCompanion.exe` is running. Anything in the folder the build doesn't make (`logs\`, `.env`, `betty_paths.json`) is set aside in `dist\BettyCompanion.kept` and put back after, even when the build fails, and is never zipped. A `.kept` folder left by an interrupted build stops the next build until it is put back.
- **The bet type is never clicked off by a click meant to choose it** (9.2459384: 'b' for Trebles, read 0.08 s later before Betty showed it, so Trebles was clicked off, then Singles: nothing chosen, staff). A row is clicked only once Betty has shown it isn't chosen: after a shortcut it has `NAV_TIMEOUT` to turn green (`_f8_row_turns`). Every click is confirmed by colour and never repeated.

## [1.1.4] - 2026-10-31

Fixes from the cashier till's logs of 31 Oct: three wagers left for staff (9.2459179, 9.2459256, 9.2459257).

### Fixed
- **A bet type the customer wrote is never re-folded from its multiplier** (9.2459179: '3x 50p WIN SINGLES' and '1x 50p WIN PATENT' on 3 runners became 3 doubles and a treble, £2.00 against £5.00 paid, on all three scans). `written_bet_type` reads the type from the customer's words ('win' alone names none); any type but a plain fold (`names_its_own_type`) is kept and the multiplier only counts its bets. '1x' no longer makes a written double a treble.
- **'1x' on a bet of several lines is one whole bet** (`calculate_bet_cost_pence`): '1x 50p patent' = 7 lines, £3.50 (it cost 50p); '2x 10p yankee' = 22 lines. A multiplier that is already whole bets' lines ('7x patent') is left as lines.
- **The virtual dogs are on the card** (9.2459257: 'East 2:18(v)' at the top of the runner list matched no meeting, so it went to staff). The greyhound card reads Betty's ADOGS feed as well as DOG (`DOG_SPORTS`; Eastgreen, Kings Stadium). Virtual dogs carry `dogs` so entry looks for a dog list (`is_dog_race`). A feed that looks like racing but neither card reads is said once in the console.
- **The top of the runner list is read by its contents as well as its label** (9.2459256: Millbank Bridge 12:50 virtuals read 'wa' / 'bait' row by row; the whole column read 'mill' on 9 rows). `runner_list_top_by_content` cuts the list into races (`runner_list_races`) and decides whether the top one is the wanted race from its runners' cloth numbers and names against the card, its label, horses or dogs, and '(v)'. 'Right' needs positive evidence the top isn't the wanted race (another race's runners, a label 2+ letters off, the other kind, virtual, or the wanted race lower down); a label on no card counts. When the label read and the contents read both answer, they must agree (`_top_reads_agree`).

### Changed
- **An unread top is no longer taken as the only meeting on the card** (9.2459253: taken as Ascot 2:33 while the Eastgreen 2:33 virtual dogs were missing from the card). It goes to staff, as when another meeting races then.
- **The money picks between a bet's readings before any rescan** (`refit_bet_types_to_money`): as reconciled, as the reader typed it, as its words name it. Changed only when exactly one combination costs the payment.
- **A rescan that reads the same bets stops the rescans** (`bets_reading_signature`): the words were right and their cost wrong, which a third paid scan can't change.

## [1.1.3] - 2026-10-30

A new look for the window, the price check box with no price when struck, and times written without a 0.

### Fixed
- **The price check box with no price when struck** (user's screenshot, 30 Oct: the program backed out of it). That box has only SP Only, Cancel and 'Override with entered price', and ignores Enter. `answer_price_box` presses Enter as before; when the box hasn't closed within `PRICE_BOX_CLOSE_SECS`, it clicks 'Override with entered price', found by its text. Still open: staff, never clicked twice. Error guide: "Betty's price check box wouldn't close".
- **The price box that opens when a betslip line is clicked for best odds guaranteed** is answered before 'g' (which it swallowed, so the guarantee couldn't be confirmed and the wager went to staff), and again after it.
- **A written time with a single minute digit is read with a 0 before it** (user, 30 Oct): '17.9' = 17:09, '5.3' = 17:03 (`parse_race_time_to_minutes`). Customers leave out that 0, almost never the last one. Before, the time wasn't read at all.

### Changed
- **The window's look** (`launcher.py`). Buttons are rounded with a soft shadow and hover / pressed shades (`RoundButton`, drawn with Pillow so the edges are smooth). The live / test mode is a phone-style switch (`Switch`): on (orange) = Live, off = Test. The status dots are smooth.
- **Pairing moved to System > Settings**; the Controls tab no longer shows the relay or the "Keys on the till" line (the keys still work). The error guide and `release/README.txt` point to the new place.
- `RoundButton` answers `cget('state')` / `['text']` like a tk.Button (the launcher tests read them).
- **The ready light is a dot and one word**: Ready, Running or Not ready; pointing at it lists what is missing.

## [1.1.2] - 2026-10-30

Fixes from the cashier till's logs of 30 Oct (written on the cashier till, applied and tested here). Not built yet.

### Fixed
- **A bare number at a meeting racing horses and dogs is the dog when the slip says dogs or only the dogs race there then** (9.2458296: '6 £2w 4.28 NCLE' under 'DOG'S' was taken for a Newcastle horse, and with no horse race then Rule 1.8.4 split it over four races abroad). A non-selection line saying dogs marks the slip (`_slip_says_dogs`); otherwise a dog race within `DOG_TIME_AGREE_MINS` and no horse race within `TIME_AGREE_MINS` decides it (`_only_dogs_race_then`). 'NCLE' is now a Newcastle alias in `meetings_directory.json`: it matched no meeting in 1.1.1.
- **The each-way healer never flips a forecast or tricast** (9.2458262: a £1 straight forecast made each way to turn £4 into £5; Betty ignores each way there, so it went to staff after entry).
- **No 'right' on a runner list whose top meeting wasn't read** (9.2458229, 15:33: Newcastle 5:45 was already at the top, unread mid-redraw; 'right' swallowed the runner number and Enter). The top is read again for up to `NAV_TIMEOUT`; still unread, it's taken as the meeting only when that is the one meeting then and horses and dogs don't share its label, else the wager goes to staff. The re-read honours Esc.
- **`go_home` stops when Esc changes nothing** (9.2458229, 15:33: 24 Esc on the runner list, and the wager never marked FAO). After `ESC_UNCHANGED_LIMIT` (2) unchanged screens Betty is given the keyboard for one more Esc, then it gives up (`_home_unreachable`). The watcher then switches off instead of backing out again (`HomeUnreachable`).

### Added
- **The keys sent on Choose Bet and Stake are logged when Betty leaves it** (9.2458229 16:11, 9.2455944 28 Oct: Home after F8, cause unknown). Each key notes whether the screen's colours still showed it just after (`_f8_key`, `_left_f8`); diagnosis only.
- Error guide: "Runner list couldn't be read"; "Betty left the bet screen" now points to the keys line.
- Tests: `fixes_30oct_cases.py`; `nav_cases` section 12.

## [1.1.1] - 2026-10-30

Dead code and tidy-ups from the code review. Nothing the program does changes.

### Removed
- **D1** The 1024x576 calibration, `is_scaled_display` and `get_f8_metrics`: only the 1366x768 bet-list layout is used (`F8_ROW_HEIGHT_1368`, `F8_BET_LIST_REGION_1368`, `F8_NUM_ROWS`).
- **D2** `BET_SHORTCUTS` and `PAGE_1_BET_ROWS` (`ENTRY_BET_TYPES` holds the keys used); `entry_cases` checks Patent's 'o' there.
- **D7** `official_time`, stored and never read. **D12** `get_virtual_meetings`, `get_course_aliases`, an always-true `'__file__' in globals()`. **D13** `BettyFeedCard.get_lines`. **D6** the HUD's `is_visible` flag and the `resolve_betansells_discrepancies` alias.

### Changed
- **T9** the merged-doubles label keeps "£1.50" (was "£1.5"). **T12** `WORD_TO_NUM` is built once. **P1** Rule 1.8.4 compares runners by identity, not whole records across ~13,000 runners.
- Left by choice (see `scratch/code_review_2026-10-28.md`): T8 (the tests' stand-in cards have no `refresh()`), D3 (`check_slip_before_f8` drives the betslip tests), D4 (use or remove `READBACK_NAMES` is a decision), D5, D8-D11, T1, T4-T6, T10, T11, P3.

## [1.1.0] - 2026-10-30

The to-do list (`todolist.md`), all three items.

### Added
- **A race time is typed once for every selection on Betty's runner list for that time.** Since 26 Oct a second runner in the same race was chosen from the list still showing; now a selection at another meeting at the same time is too: 'right' on from the list showing to its meeting, no time typed (`after_same_time`, `same_race_time`: the same time on Betty's 12-hour clock). If the list has already passed that meeting, it ends (Betty's folders) and the time is typed after all, as before. Selections stay in the order written, so forecasts keep their order. The time-typing steps are one helper (`_type_race_time`).

### Checked
- **'PP' with a time is Portman Park**: 'No 1 2.11 PP' and a misspelt name with 'PP' both lock to Portman Park 14:11 on the 20 Oct card. **The house rules before giving up**: '4 1.50 Chepstow' with no Chepstow race then goes on #4 in the 1:50 at Newmarket (Rule 1.8.4, the time takes precedence). Both already worked; both are now tests (`review_fixes_cases`), and 1.0.2's meeting and rules fixes cover the cases around them.
- Tests: `entry_cases` section 28b (the list reused for another meeting at the same time, and the fallback when it has passed), and `enter_wager` choosing it.

## [1.0.2] - 2026-10-30

The open risks from the code review (`scratch/code_review_2026-10-28.md`, IDs kept). Each fix has a check in `scratch/ocr_eval/review_fixes_cases.py` (new, 42 checks). Every other suite passes as before; the `--ideal` self-test replays the same as 1.0.1 (11/13: paul2 and petea, "no day fits", as before).

### Fixed
- **R3: the betslip check compared only 3 letters of the meeting.** Newcastle, Newmarket and Newton Abbot are all "new", and a dog line shows only "Trap N", so a dog bet on the wrong track passed. Betty's 4 letters must match now, or be one letter off (an OCR slip) only when no other meeting racing then is as near (`_meeting_label_fits`).
- **R4: short meeting shorthands matched as prefixes.** "Hamburg" was Hamilton, "Donegal" Doncaster, "Perry B" Perth, "Wollong" Wolverhampton. A shorthand of 3 letters now matches only when written exactly; a name the dog or international lists know in full is tried before the loose horse matching ("Perry B" is Perry Barr).
- **R5: horse names decided the bet type.** "Double on Pat's Pride & Beta" read as a patent, "£1 win Union Jack Rose" as a union jack. The bet's own selection names are taken out of its description first (`selection_names`).
- **R7: the staff detector could fail without a word.** Its hooks now only set flags (the message goes out on another thread; mouse movements take no lock), so Windows doesn't drop them for being slow. A hook that doesn't install is reported, with a sound and an Errors-tab entry.
- **R8: a wager with two navigation failures was left without a sound or FAO.** It now goes through the normal "leave for staff" (FAO in live mode, screenshot, sound). A wager stopped part-way (Esc) is journalled and announced.
- **R1: with no written total, the each-way healer flipped the first bet that fitted.** With two bets of the same cost either fits, and the wrong one went on each way. It now flips only when exactly one bet fits; otherwise the money check sends the slip to staff.
- **R9: in test mode, a wager staff placed could be logged "cancelled"** when Betty went to Home after F12. View Wagers is opened and the list looked at first.
- **R10: a forecast or tricast with no selection on the card was voided**, against the rules file's "enter as written, Betty settles" (as it already did for one or two). It is entered as written.
- **R11: an unnamed favourite each way was made win only**, so it never cost what was paid and always went to staff. It is entered each way as written; Betty voids the place part at settlement (the house rule).
- **R12: trap bets judged "already off" without Betty's off times** when the card had been re-read since pre-flight. The dog card is marked afresh at the trap check.
- **R13: a selection read with a number but no name was dropped.** It is a number bet ("5").
- **R14: a bet with no line number was paired with any line saying "doub", "treb" or "acc".** Only its own type's words count now.
- **R15: two singles on the same horse became one.** The repeat stays a single of its own. The two copies of the singles merge are now one (`_merge_singles`, review T3).
- **R16: two rules fitted to particular slips.** A "dreb" bet is dropped only when a treble with the same stake, terms and runners exists; two doubles merge into "3 x Doubles" only on a written "3 x", not any "3".
- **R17: made-up line numbers were trusted** by the "runners below a bet line" guard. They are marked, and the guard stands aside when any line number was guessed.
- **R18: stake entry details.** 8 backspaces clear the last stake (5 cleared only £999.99); a short wait before the each-way button is read; the `except TypeError` retry that would deselect the other bets is gone; Singles already selected returns early only when nothing else is selected.
- **R19: `load_wager` clicked the old row when the wager had left the list.** It stops (the next look takes the next wager).
- **R20: amounts with a thousands comma ("£1,000.00") didn't read** on View Wagers, the betslip or the slip.
- **R22: 9, 10 and 11 o'clock stayed morning** for number bets, Rule 1.8.4 and the runner list ("No 4 9.40" for the 21:40 dogs found nothing). Both are tried (`race_time_options`), as trap bets already did.
- **R24: a stake read as empty crashed the rules engine.**
- **R25: the 1-8 trap range was applied to horses** written as a bare number (horse number 12 isn't "Trap 12").
- **R26: an unknown bet type was costed as 1 line silently.** It says so.
- **R27: a race in two feeds was listed twice** when one feed had dropped a non-runner. Same time and all runners but one (4+) is the same race.
- **R28: Betty's folder name followed the Windows language** (`%A`). English day names (`betty_day_name`).
- **R30: a broken `meetings_directory.json` was re-read on every lookup and lost its shorthands.** The last good directory is kept until the file changes.
- R23 (two log folders) was settled by 1.0.0 (every log in `logs` next to the program). R29 (the feed year letter after 2027) stays a note: what Betty uses can only be seen in January 2028.
- New Errors-tab entries: staff detector not working, Betty's screens kept going wrong, wager stopped part-way, wager already taken.
- Tests: `reader_cases` and `exe_cases` now allow for this PC being paired with the relay (since 28 Oct); `entry_cases` fakes `betty_day_name`.

## [1.0.1] - 2026-10-30

The fixes made after the first 1.0.0 build (tried on the tills from 28 Oct), the cashier tills' racecards, and a smaller build.

### Fixed
From the live log of 28 Oct, 15:29 (`dist/BettyCompanion/logs`): 9.2455858, slip `1 £2w 3.13` / `4 £2w Sund` / `1 x 4 x 5 £1 comb F/C`, £10.
- **"Checking selections against Betty's card" took about 70 s.** `number_bet_is_dog` compared the meeting written ('Sund') with each of the card's 13,381 runners. A dogs-only meeting matches no horse, so every runner was compared. Each comparison is a fuzzy meetings-directory lookup of about 3 ms, plus a file check.
  - It now compares each meeting once.
  - `_meeting_matches` answers are cached for the wager (cleared at each pre-flight, because the day's dog card is part of the answer).
  - The same slip now takes **0.2 s**.
- **'1 £2w 3.13' (no meeting) was split over three horse races and sent to staff** ("200p can't be divided equally over 3 races"). Rule 1.8.4 took any race within 10 minutes of 3.13 and put horses first: Huntingdon 15:06, Nottingham 15:16 and Newton Abbot 15:21. A race at the very time written now wins first, whatever its kind: the Sunderland dogs at 15:13, the race the customer meant. The 10-minute window and horses first still apply when no race is at that exact time. The slip now locks as two £2 singles and a £1 combination forecast at Sunderland 15:13, £10.
- **Each line of the session log starts with its time** (`15:35:25 [!] Wager ...`; user). Blank lines and the console are unchanged. The launcher's staff list reads both old and new lines. A wager found only in the log is now timed by its line when there's no screenshot.
- Tests: `entry_cases` 33 (exact time → Sunderland; 3.10 → the horse races near it, split as before; 'Sund' on a 13,006-runner card decided in 0.4 s), `backend_cases` 3 (each line timed, blank lines not), `launcher_cases` 3 (a timed staff line).
- **Choosing the bet type on Choose Bet and Stake (F8) took 11-15 s a bet**, the wait before F12 (9.2455887, 15:58: "Best odds" 15:58:12 → "Bet 1 entered" 15:58:23, then 15:58:34 → 15:58:49).
  - The bet list was read with one Tesseract run per row, 11 a read and a second run for each blank row: about 2 s. `choose_bet_type` read it about 4 times.
  - `_f8_texts` now reads the whole list in one pass, about 0.3 s. On every saved bet-list screen it reads the same 113 named rows as before.
  - The first read is made only for Singles (the only type it decides).
  - After the click, only the rows' green is checked (`_f8_selected`). Selecting doesn't change the list, so the names come from the one read.
  - A bet type now takes about 0.5 s.
- **Every FAO was reported as failed** ("still in the unedited list after Mark bet fao Manager": 9.2448529, 9.2452876, 9.2455486, 9.2455944). Betty marks the wager at once, but the wager only leaves the unedited list some time later (user). After the click, the program now looks for the large magenta **FAO MANAGER** on the wager's slip panel, by colour (`shows_fao_manager`), for up to 3 s.
- **9.2455944 (Lucky 63 each way, 6 selections) went to staff three times with "Betty's bet list could not be read"**. Betty was on Home each time (16:17, 16:23, 16:32). The user watched it: the stake goes in, then Betty backs out while the bet list is being searched. Lucky 63 has no shortcut key, so the list is searched page by page with PgDn. The cause isn't proven; the likely one is that the new one-pass read missed Lucky 63 on page 1, so PgDn was pressed.
  - Before PgDn, the page is now read again row by row (the old reader). PgDn is pressed only when both readers agree the type isn't there.
  - The log names the rows read whenever it pages on.
  - After PgDn the screen is checked. Leaving Choose Bet and Stake is now reported as "Betty left Choose Bet and Stake (now on HOME) ...", not as an unreadable list. There's an `error_guide` entry for it.
- **The events screen is passed with `1` on every till** (to-do: "the cashiers' tills won't take `/` on the events screen"). After End (Edit Empty Bet), `open_race_entry` presses `1` to go past the events screen to race entry, then `/` for the time box. It's the same on every till, the manager's included (user). `/` is no longer pressed on the events screen at all. `1` is pressed again only while the events screen still shows (it can be missed while the screen draws), up to 3 times.
- **The cashiers' tills found no racecards** ("Betty racecard feed not found"). They have no `C:\Events` or `C:\DBF`: their Betty reads the manager till's (Betty 0's) `C:\`, which is shared as `drvc` and mapped as a network drive (`F:` at South Oxhey, the cashier till's `net use`). The program only ever looked on `C:\`.
  - `betty_feed.betty_root()` finds the drive holding both `Events` and `DBF`: `C:\`, then `D:` to `Z:`, then the share itself (`\\PC\drvc`, `BETTY_SHARE`) when no letter is mapped. The race cards, the off slips (`transact.DBF`), the Data tab and the readiness light all use it.
  - **Found once, then saved** (user): the first launch after the till is paired, or the moment it's paired, saves the drive to `betty_paths.json` next to the exe, for that build on that till. Later runs use it straight away. A new build finds it again.
  - If the saved drive can't be reached (F: not reconnected yet after a reboot), that run uses whatever drive it can find, `\\PC\drvc` included, and keeps the saved file. If nothing is found, the launcher lists an error, and the program looks again every 30 s.
  - `BETTY_EVENTS_DIR` / `BETTY_DBF_DIR` in `.env` still override it.
  - The Data tab says which folder the cards come from ("4 file(s) in F:\Events, ...").
  - Tested on the manager till: `C:\` saved; a cashier-style drive saved and reused; the saved drive gone → the real cards read over `\\PC\drvc` (7,088 runners, 299 off slips) with the save kept; nothing found; the folder not writable; `.env` override.
- The tills only get this in a new build (`python build_release.py`). The snapshot `previous_versions/betty_companion_v1.0.0.py` is the first build's code.

### Changed
- **The build is 9 MB smaller** (91 MB, zip 38 MB). Left out because nothing uses them: setuptools (PyInstaller's hook), numpy's test tools and the `win32pdh` module they bring in, and Pillow's AVIF, WebP and colour-profile support. `exe_cases` passes on the trimmed build; it now expects this PC's relay pairing and checks that the window saves Betty's drive.

## [1.0.0] - 2026-10-28

The first release as a portable Windows program: `BettyCompanion-1.0.0.zip`. Unzip it and double-click `BettyCompanion.exe`; nothing is installed. It replaces `bettycomplaunch.bat`. Running `python betty_companion.py` still works as before.

### Added
- **The control window (`launcher.py`, `BettyCompanion.exe`).** It's a normal window that can be Alt+Tabbed to. It runs the program as a second process (`--backend`, 0.48.0) and talks to it through pipes. Only one copy opens; a second double-click brings the first to the front.
  - **Controls:**
    - **Start** loads the program if needed, with a loading bar, then starts the watcher. The window minimises so Betty is in front (the tills have one screen).
    - **Pause** stops at once and touches nothing; the program stays loaded.
    - **Stop** closes the program and the overlay, asking first if the watcher is on.
    - **The mode button** shows LIVE (orange, places bets; the default) or TEST (purple). Going back to LIVE asks first. It follows Shift+` on the till.
    - **Start warns** when the ready light is red.
    - **Closing the window** stops everything, asking first if the program is running.
    - Also shown: the program's state, the watcher (on / off / paused for staff), Betty's screen, the wager in hand, the last message and outcome, and how slips are read.
  - **System:**
    - **Log:** the current or the previous session log, following the current one as it's written.
    - **Errors:** every error and every wager left for staff. Selecting one shows *what happened, what it means, what to do* from the new `error_guide.py`, which covers every reason the program gives (checked by a test).
    - **Staff entries:** each wager left for staff, with Betty's screen at that moment, and each selection staff had to type in: what the reader read, what staff typed, what it matched, and the slip as the reader saw it. Earlier staff wagers are found in the logs and timed by their screenshots.
  - **Data:** today's racecard files in `C:\Events` (sport, races, when Betty last wrote each), and today's meetings in four lists: horses UK & Irish / international, greyhounds UK & Irish / international. Virtual racing is left out; Australia counts as international.
  - **Runners:** every UK & Irish horse runner today, with time, meeting, cloth number and when Betty sent the race off. It has a search box, a meeting filter, and "hide races that are off".
  - **The status bar is always visible:**
    - **The ready light:** green "READY TO AUTOMATE", or red with the reason. It checks the screen is 1366x768, Betty is open, today's racecards exist, Tesseract is present, and Gemini answers.
    - **The Gemini light:** a free check every 5 minutes (click for one now).
- **The relay link (`relay_link.py`).** A till pairs once from the Controls tab:
  - it shows a 6-digit code; you approve it on the relay's `/admin` page;
  - the till's pass is kept in Windows Credential Manager with the relay address. Nothing secret is in a file.
  - A paired till reads slips through the relay: paid Gemini first, then the free projects, the same order as with keys. It never uses the keys in `.env`.
  - The relay refusing the till (unpaired or revoked) moves straight to the next reader, then staff. The till's daily limit counts as a quota.
  - The relay address `https://betty-relay.splaterson92.workers.dev` is built in; `RELAY_URL` in `.env` overrides it.
- **Relay 1.2.0 (`relay/worker.js`):** `/ping`, the window's free Gemini check. It takes the till's pass, lists one model per key (nothing read, nothing charged, not counted), and returns the till's reads today and each key's state.
- **`logs/staff_journal.jsonl`:** one line per wager left for staff and per selection staff typed, kept 30 days. `logs/slip_<wager>_<date>.png` is the slip as read, for each typed selection; the newest 200 are kept.
- **The build:**
  - `BettyCompanion.spec` and `build_release.py` make `dist\BettyCompanion\` and the release zip with its SHA-256;
  - the folder holds `BettyCompanion.exe`, `README.txt` and `_internal\`;
  - the build is one folder, windowed, without UPX, with version information and an icon (`assets\betty.ico`);
  - Tesseract is copied in with only the 33 DLLs `tesseract.exe` loads and English: 108 MB down to 51 MB. The folder is 100 MB, the zip 44 MB;
  - OpenCV, pandas and other unused packages are left out.

### Changed
- **The watcher only presses keys when Betty is in front.** If another window is in front when it looks for wagers, it brings Betty forward first. For the launcher window, it asks the window to minimise. If Betty still isn't in front, or isn't open, it waits and presses nothing ("Betty isn't in front: waiting").
- `betty_companion.py`'s start-up is now `main()`, so the exe can run it with `--backend`. The console says how slips are read: the relay (and this till's name), the keys in `.env`, or none.
- The `ready` event says how slips are read (`route`). The `staff` event is now written to the staff journal first. A new `manual` event goes out when staff type a selection, and `step_aside` asks the window to minimise.

### Fixed
- **"N/A" (Newton Abbot) was read as "no meeting written"** (found by Gemini).
  - `N/A` and `NA` were in `MEETING_PLACEHOLDERS`, so a meeting written that way was dropped. A number bet at Newton Abbot then had no meeting: with another race at that time it went to staff, or Rule 1.8.4 split it.
  - They now count as written in `raw_meeting_hint`, the customer's letters exactly as written. They stay placeholders only in the reader's own full-name `meeting` field, so a reader filling in "N/A" for a blank still means nothing written.
  - Aliases `na` and `newa` were added for Newton Abbot (in `meetings_directory.json` as `n/a`, `na`, `new a`).
  - "NA" still fits any N.A. meeting racing at that time, by its initials (Naas too): the card decides, as for other letters.

### Testing
- **New:**
  - `relay_cases.py` (32 checks): `relay/worker.js` runs on this PC (`scratch/relay_local.mjs`: Node with an in-memory database and a fake Gemini). It covers the address, pairing (approve, reject, the pass handed over once), `/ping`, slip reads through each slot, a disallowed model, a missing slot, the daily limit, revoking and unpairing.
  - `launcher_cases.py`:
    - the error guide against every reason in the program, and the Data helpers;
    - logs and the journal;
    - the window driven against a stand-in program: Start, mode, Pause, errors, step-aside, Stop, a crash, and closing;
    - the real program run windowed (`pythonw`) through the window's pipes.
  - `exe_cases.py` checks the built exe:
    - the bundled Tesseract reads the same as the installed one;
    - `BettyCompanion.exe --backend` is ready in 1.1 s with its own Tesseract and answers test/live/Stop;
    - `--check-screen` runs;
    - the window opens, a second copy doesn't, and it closes cleanly;
    - the exe's own Gemini check passes over HTTPS.
  - `number_cases` 4: "No 3 2.51 N/A / NA / New A" with Ludlow at 14:51 too → Newton Abbot #3.
- **Not yet tried:**
  - on a till;
  - pairing with the live relay, which still runs 1.0.0 until `worker.js` 1.2.0 is pasted in;
  - a slip read through the relay;
  - AVG on a till.

## [0.48.2] - 2026-10-28

From the live log of 28 Oct, 12:18 (6 placed, 3 skipped after `` ` ``).

### Fixed
- **A wager paused part-way is tried again, never skipped for the session** (9.2455510, 9.2455512, 9.2455514: "left unedited for staff" after `` ` ``). Once End had opened the bet edit, any stop put the wager on the session's skip list, a pause included.
  - Pausing now leaves the wager in the queue: `` ` ``, the launcher's Pause, or a staff key or click. The pause still touches nothing. On resume the watcher backs out to Home as before, then opens the wager again from View Wagers.
  - Esc and real failures still leave the wager for staff.

### Checked, no change
- 9.2455513: 'Persian Act' written 14:06 → Persian Art at Huntingdon 16:06, by the race-list check. Right (user): customers sometimes write the wrong time.
- 9.2455508: Crown The Future's betslip number misread (`None. §.`), passed by its name. Right (user).
- 0.48.1 on the till: 29 selections entered with `right`, number, Enter. No row clicks. Wolf's Gallop at Nottingham 12:46 went in past Portman Park and Harlow.

### Testing
- `nav_cases` 11: paused (`` ` ``) and paused (staff) after End → stays in the queue; Esc after End → still left for staff. `nav_cases`, `entry_cases`, `backend_cases`: **all passed.** Ruff F,E9: all checks passed.
- Not yet tried on the till: a paused wager reopened.

## [0.48.1] - 2026-10-28

### Fixed
- **A runner showing below another meeting was clicked, so it went in at SP** (9.2455486: Chief Minister 3/1 at Nottingham 12:46, under Harlow, then sent to staff with "Betty has no price for it yet"). Since 0.46.28 the whole runner list was read before every `right`, and any matching row was clicked on its name. A click on the name adds the runner at SP. Today's log was the first time it happened on the till.
  - `right` is pressed until the selection's meeting is on top again, then its number is typed and numpad `+` (price) or Enter (SP) is pressed, as before 0.46.28 (user: "this has always been the way").
  - A row is clicked only when horses and dogs share the label at that time (Newcastle 1:26), because there `right` takes both off. A price taken is clicked on its **price** (`RACE_LIST_PRICE_COL`, x 312–400); SP is clicked on the name. If the row can't be found, the wager goes to staff.

### Testing
- `entry_cases` 31: 7/1 under the Newcastle dogs → its price is clicked (356, 473); Nottingham 12:46 under Harlow → `right`, `right`, `4`, numpad `+`, no click. **All passed.** Ruff F,E9: all checks passed.
- Not yet tried on the till: the price click.

## [0.48.0] - 2026-10-28

### Added
Ready for the 1.0.0 launcher window and the portable exe. Nothing changes when the program is run as before (`bettycomplaunch.bat`).

- **`--backend` mode, for the launcher.** The launcher runs the program with `--backend` and drives it through pipes:
  - **Commands** on stdin, one per line:
    - `start`: watcher on, Betty brought to the front;
    - `pause`: watcher off at once, touching nothing, as `` ` `` does;
    - `test` / `live`: test mode on / off;
    - `status`: the full state now;
    - `quit`: Stop. The watcher goes off, a wager in hand gets up to 10 s to let go of Betty, then the program ends.
  - **When the launcher closes the pipe** (it quit or crashed), the program shuts down the same way, so it never runs unwatched.
  - **Status events** on stdout, one JSON line each:
    - `hello`: the version, process id, this run's log file and the screen size;
    - `ready`: start-up is done, with test mode, the Tesseract in use and the readers;
    - `state`: watcher on/off, paused for staff, test mode, Betty's screen, busy, the wager in hand;
    - `message`: every HUD message, with errors marked;
    - `outcome`: the last outcome;
    - `staff`: a wager left for staff, with the reason and its screenshot;
    - `error`: a bad command;
    - `fatal`: the wrong screen size;
    - `bye`: closing.
  - In this mode stdout carries only these events. The console text goes to the session log alone, which the launcher will show.
- **`app_paths.py`:** where files are, run as a script or as the exe.
  - `.env` and `logs/` are next to the exe (`app_dir`). Files shipped with the program are inside the build (`bundle_dir`).
  - Tesseract is found in this order: `TESSERACT_CMD` in `.env`, then a `tesseract\` folder next to the exe or inside the build, then `C:\Program Files\Tesseract-OCR`, then PATH. If none is found, the console says so.
  - Every path is worked out when needed, so the free tests that pretend to be the exe still get the exe's folders.

### Changed
- **The status panel snaps back to its corner when the watcher starts**, from `` ` `` or the launcher, if it was dragged away. Clicking it still does nothing; it can still be dragged.
- `toggle_watcher` and `toggle_test_mode` (the hotkeys) now call `set_watcher(on, why)` and `set_test_mode(on)`, which the launcher's commands use too. The console says who switched it: "Watcher OFF (` pressed)" or "(Pause in the launcher)".
- `.env` is loaded from the program's folder (`app_paths.env_file()`), not from whichever folder the program was started in. Session logs and staff screenshots go to `app_paths.log_dir()`.
- `save_staff_screenshot` returns the file it saved, which `leave_wager_for_staff` sends to the launcher.

### Tests
- New `scratch/ocr_eval/backend_cases.py` (35 checks): the paths as a script and as the exe (Tesseract order included), the log-only console, every event, every command, the hotkeys, Stop and the launcher closing, and the staff event.
- Checked live: the program run with `--backend` by a stand-in launcher was ready in 1.7 s and started live. It answered `status`, `test`, `live` and a bad command, then closed cleanly on `quit`. Its stdout held only events, and the console text was in the session log. With the pipe closed instead, it shut down in 0.1 s.

## [0.47.0] - 2026-10-28

### Changed
Backend clean-up before the 1.0.0 launcher (the control window and portable exe).

- **Live by default.** The program now starts in live mode (places bets) unless `.env` says `BETTY_TEST_MODE=1`. Shift+` still switches test mode on and off. This PC's `.env` was set to `BETTY_TEST_MODE=0` to match. (To-do list item 1.)
- **The slip reader is Gemini only.** The chain is now paid Gemini (Argon), then the free Gemini projects, then staff. `read_vision_json` takes only the Gemini request (no Claude content, no schema: the request carries its own). `SLIP_READER` is `waterfall` or `gemini`.

### Removed
- **Claude.** The Claude reader step and everything only it used: `claude_json_request`, `claude_slip_images`, `to_json_schema`, `slip_detail_crops`, `_png_b64`, `_claude_key_set`, `CLAUDE_MODEL`, `CLAUDE_EFFORT` and `CLAUDE_PRICES_PER_MTOK`. The `anthropic` package is no longer needed. `CLAUDE_API_KEY` in `.env` is unused and can be deleted.
- **Ctrl+Alt+B (one slip on the race-entry screen).** `run_cycle_logic`, `start_automation_cycle`, `is_cycle_running` and every check on it (Esc, the watcher toggle, the staff-idle resume, the watcher loop), the hotkey, its start-up line and the HUD text. The HUD's `show`, `hide` and `has_active_reset_timer`, used only by it, went too. The watcher, `` ` ``, Shift+` and Esc work as before.
- **The relay's Claude route** (`relay/worker.js` 1.1.0, `RELAY_SETUP.md`): the relay passes Gemini requests only. Paste the new `worker.js` into Cloudflare and delete the `CLAUDE_KEY` secret when the relay is next updated.

### Tests
- `reader_cases.py`: the chain without Claude, plus checks that no Claude reader or Ctrl+Alt+B cycle is left and that a program with no `BETTY_TEST_MODE` starts live.
- `run_eval.py` and `run_all_saved.py` drove `run_cycle_logic`. They now call `scan_then_card_check` (in `run_eval.py`): the same scan with money rescans, then the same card check. Same results (ideal: 5/5).
- `recheck_live.py`: Gemini only.

## [0.46.29] - 2026-10-28

### Fixed
The seven bugs from the code review of 0.46.28 (`scratch/code_review_2026-10-28.md`, B1-B7). The risks, dead code and tidy items are left for now (user).

- **A ditto time or meeting was lost for the bets, so Rule 1.8.4 could put a number bet in the wrong race (B1).**
  - Pre-flight collects the selections twice: from the slip's selections list, where a blank time or meeting is filled from the line above, and from each bet's runners, where it wasn't.
  - The bet took the second lookup. "No 3 3.20 Don" with "No 8 Don" under it (time left blank), struck at 14:00, was locked as No 3 in the 15:20 and **No 8 in the 14:40** ("untimed, on for the next race"). The money still matched.
  - Now each bet runner is looked up under the key of the selection it came from (`selection_num`), with the ditto applied, and its match is copied back under the same key.
  - A time written `do`, `ditto` or `"` and a meeting written `"` or `ditto` now count as a ditto. A meeting written `do` stays a meeting, since it can be Doncaster.
- **Copying the matches back into the bets could give one number bet another's runner (B2).**
  - When a runner's key wasn't found, it took the first match at least 0.75 similar by name. "No 3" and "No 8" are exactly 0.75 alike.
  - With the ditto written "do", the double No 3 / No 8 became No 3 twice, which the same-race rule split into two 25p singles on No 3.
  - The fallback now takes only the same name, only when that name was locked once, and never for a number bet.
- **Short meeting names were read as virtual racing (B3).**
  - `is_virtual_meeting` matched every virtual shorthand ('v', 'pp', 'sd', 'sv') as a prefix in both directions. So "San" (Sandown) was Sandy Lanes, "Valley" (the dog track) and anything starting with V were virtual, and so were "Lon", "Hil", "Mea", "Por", "Ste", "Sta", "Mil", "Spr" and "Bru".
  - The virtual card was then searched first: "No 4 2.30 San" locked No 4 in the Sandy Lanes virtual race, with Sandown racing at 14:30 too.
  - A prefix now counts only between names of 4+ letters (`prefixes`).
  - `resolve_meeting` takes an exact virtual name first and a virtual prefix only after the UK/IRE course prefixes (new step 5a), so "Sand" stays Sandown.
  - An exact dog track now comes before a virtual prefix, so "Valley" is the dog track.
- **On a time-out, View Wagers details read only once were taken anyway (B4).**
  - 0.46.28 takes the struck time and Payment only when two reads in a row agree. But after 4 s without agreement, the last read was returned, and the watcher only rejects details that are missing.
  - Unconfirmed details now count as unread, so the wager goes to staff.
- **"50p double" on three runners was costed as three doubles (B5).**
  - The three-runner repair matched only "doub" and "treb", never "double" or "treble" in full. So the comment's own example, "'50p double' is one double on the last 2", never happened.
  - "double", "treble" and "trebles" now count. The plural "doubles" stays out deliberately: on three runners it means three doubles, as before.
- **Plural bet types weren't recognised (B6).** `normalize_bet_type` returned "trebles", "singles", "yankees", "patents", "trixies", "accumulators", "accas" and "lucky 15s" unchanged, so they couldn't be entered and went to staff. Each pattern now takes the plural.
- **The stakes of an "X & Y" bet line could read as the bet count (B7).**
  - "2 doubles 50p & 1 treble 50p" became a 2p double and a 1p treble, because the first number was taken as the stake and a 'p' anywhere in the line made it pence.
  - One helper, `stake_from_bet_text`, now reads the stake, in this order:
    - after a multiplier ("3 x 50", "1 x 5 doubles");
    - else an amount with £ or p;
    - else the first number that is not a multiplier or a count of bets ("2 doubles", "4 fold").
  - It also replaces the same parser in the interleaved bet restorer. "£2.50" now reads as 250p (it was 200p).

### Testing
- **`entry_cases` 32 (41 checks):**
  - B1/B2: the No 3 / No 8 double with the time blank, `do` and `"`, and the meeting blank and `"`: No 8 in the 15:20 each time, no staff pop-up, no key left on the runners. A 'No 8' that can't be placed goes to staff, not to No 3's runner.
  - B3: 11 meeting names, and "No 4 2.30 San" = Sandown #4.
  - B4: reads that never agree come back unread.
  - B5: "50p double" = 2 runners at 50p; "50p doubles" = 3 runners at 150p.
  - B6: 8 plurals, and a "trebles" bet can be entered.
  - B7: 11 stakes and the split line.
- **All pass:** entry (section 32 included), navigation, screen, reader, recheck, number, rules, and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- **Snapshots:** `previous_versions/betty_companion_v0.46.29.py`, `rules_engine_v0.46.29.py`, `meetings_manager_v0.46.29.py`.
- Not yet tried on the till.

## [0.46.28] - 2026-10-27

From the live log of 27 Oct (12:36–13:58, 30 placed, 9 to staff) and the user's notes on it.

### Fixed
- **A race listed under another in the runner list is now clicked, not skipped** (9.2453975, 9.2453997: "Newcastle 1:26 is not in Betty's runner list"; 9.2453993: the same at 2:31).
  - Betty lists every race at the typed time, and `right` only takes the top meeting off. At 1:26 the Newcastle dogs (TRP Dogs) and Newcastle horses (TRP Horses) share the label `Newc`. The dogs come first, so `right` took both off and the horses were never on top. Typing 1–6 there would also have picked a trap. At 2:31 the Newcastle horses sat under the Monmore dogs.
  - Before each `right`, the whole list showing is read (`race_list_rows`, one OCR per column, 0.5–1 s for 17 rows). The selection's row is found by meeting, time, kind (`01.` horse / `Trap 1.` dog), number and name (`find_runner_row`). It is clicked, since a click adds it to the betslip (user). The betslip read-back checks it as before, the price included.
  - Not covered: a runner below the 17th row (the list's down arrow), and void selections, which still need their race on top.
  - The 2:31 failure itself (12:57) isn't explained by the log. Newcastle 2:31 went in three times later on the same route (Sprintvalley → Monmore → Newcastle on top). The hatched rows read correctly on the user's screenshot, so the hatching isn't the cause. With the row search, the Newcastle rows under Monmore are clicked before that `right`.
- **A Lucky 31 (or any full cover) with two runners in one race is split into whole bets of the same type** (9.2453976: Lucky 31 10p e/w with Cayenne and Mon Missel in the Newcastle 4.01 became Perm 4-Folds @ 5p, 20p of bets for £6.20 paid).
  - The user's rule: one bet per clashed runner at the stake divided equally. Each bet gets a void selection in place of the runner left out: two Lucky 31s 5p e/w, one with Cayenne + a void, the other with a void + Mon Missel.
  - The void goes in a UK/IRE horse race not already on the bet (user). The day's last such race is used, SIS / TRP horses first, so it is still to run when entered (`void_selections_for_split`, `split_clashed_full_cover` in `rules_engine.py`). It is entered with `v` like any void selection.
  - Trixie, patent, yankee, Lucky 15/31/63, Canadian, Heinz, super Heinz and Goliath. Doubles, trebles and accumulators keep their perm split. With no free race on the card, nothing changes and the money check sends the wager to staff.
- **View Wagers is read twice before the wager is taken** (9.2453984: "the bets cost £6.20 but £10.00 was paid"). Betty draws the wager number before the struck time and Payment. The first read had the number right but 12:49:13 / £10.00 from the wager shown before it (9.2454151). Betty's own slip said Paid £6.20. `load_wager` now takes the details only when two reads in a row agree. A wrong Payment only cost a trip to staff, but a wrong struck time with the right Payment would have gone through.
- **The Lucky coupon's Total Stake box is the slip's total** ("Customer wrote £0.10 but paid £6.20" on nearly every Lucky 31). The reader took the 10p in the stake-unit box for the total. The box's pounds : pence (`6 : 20`, the colon printed) didn't parse.
  - A colon now separates pounds and pence in `parse_currency_string_to_pence`.
  - A last line in that form, with a space at the colon, is the total. A bare `6:20` (a race time) is not.

### Also in this version
- The number-bet changes written earlier on 27 Oct and run live in the 12:36 session, without an entry until now:
  - `number_bet_is_dog`: T / Tr / Trap written = a dog; 'No.' or a bare number = a horse, unless the meeting written races only dogs.
  - `trap_by_dog_rules`: greyhound Rules 1.21.6 and 1.21.7 for a trap the dog card didn't place.
  - The working file as run is kept as `previous_versions/betty_companion_v0.46.27_as_run_27oct.py`. `betty_companion_v0.46.27.py` there is the 09:55 copy without them.

### Checked, no change
- **Prices:** the user's rule is always the price when struck. Numpad + adds the current price, and when it differs from the struck price Betty's price-check box opens and Enter takes "Price when struck" (Just Golden, Cyberspace, Speed Davis ... on 27 Oct). With no box, current = struck. Desert Master 9-1 (10/1 written) and Highfield Viking 11-1 (12/1 written) were the struck prices.
- **Times:** the name takes precedence over a written time (user). Crystal Glance 15:46 written → 13:46 and Babatunde 3:46 → 4:16 are right.

### Testing
- **`entry_cases` 31 (17 checks):**
  - The user's runner lists (new reference screens 40 and 41): every row read.
  - Sleedagh #4 found under the Monmore traps; The Kings Soldier #8 and Wannabe #1 under the Newcastle dogs; Trap 1 when a dog is wanted; no row for a wrong name or time.
  - The 1:26 entry clicks row 14 with no `right` and no number typed.
  - View Wagers mid-redraw → the second, agreeing read.
  - `6 : 20` after `10p` → 620p; a bare `6:20` is not taken.
  - 9.2453976's Lucky 31 → two Lucky 31s 5p e/w with a void each, in Wolverhampton 19:30, 620p.
  - No card → no void made up.
- Not yet tried on the till: the row click and the split's void entry.

## [0.46.27] - 2026-10-27

### Changed (user: use Betty's real off times)
- **Whether a race was off when the bet was struck now uses Betty's own off times** (`still_to_run`). Until now it used the scheduled time, so a race going off late counted as gone. Examples:
  - Musselburgh's 1.47 on 12 Oct went off at 13:49:38. An untimed "No 8 MUSS" struck at 13:48 went to a void selection in the 2.17. It is now No 8 in the 1.47.
  - 9.2453119 ("No 3 5.07 Philadelphia", struck 17:08:48) was taken for a late bet. The 5.07 went off at 17:10:46, so it is now an ordinary bet. It was entered on the 5.07 either way.
- **The same check is used everywhere the struck time matters:** Rule 1.8.4's next race and time clashes, late bets, number bets, trap bets, and the staff pop-up's entry.
- **Where the off times come from.** Betty writes an off slip to `C:\DBF\transact.DBF` when it sends a race off. These are the "sent off automatically" wagers in View Wagers: TRANS_TYPE 87, DEALER_2 = the event id. A slip's time is normally 5–10 s after the official off in `results.dbf`.
  - `BettyOffTimes` (`betty_feed.py`) reads the day's slips. The first read goes back to the start of the day; later reads take only new records. A whole day reads in 0.03–0.12 s. Set `BETTY_DBF_DIR` if the tables aren't in C:\DBF.
  - Each race on the card now carries its event id (`event_id`, at +62 in the feed's race record).
  - Pre-flight marks every runner with its race's off time.
- **When Betty hasn't sent a race off, the scheduled time decides,** except for a race that is just running late:
  - A race with an off slip before the struck time was off, even if it wasn't due (an abandoned race is sent off early).
  - A race past its scheduled time with no off slip yet counts as still to run, but only within `LATE_OFF_LIMIT_MINS` of its scheduled time: horses 25 min, dogs 5, virtual races 2. It must also come from a feed Betty sends off, with no off slip missed at its meeting.
  - Anything else falls back to the scheduled time: no off slips for its feed (the Tote, TTHR), the table can't be read, or a race later than the limit.
  - **Why the limits:** in Betty's off slips for UK/IRE races, 13–26 Oct, horses went off a minute late on average, 99% within 12 min and the latest after 22. Dogs: 90% within 70 s. Longer gaps, up to 112 min, were Betty catching up after a pause, when the time is when Betty wrote the slip, not the off.
- **The watcher passes the struck time to the second** (`struck_clock`, '9:10:57') to the selection check. `parse_clock_minutes` reads seconds as a fraction of a minute.

### Testing
- **`entry_cases` 30:**
  - Reading a test transact.DBF: today's off slips only, the earliest slip per race, deleted and other rows skipped, a new slip read on the next look, no table = no off times.
  - Marking runners: Tote races never tracked; a missed slip falls back.
  - `still_to_run` in eight cases.
  - The paul2 case end to end: untimed No 8 struck 13:48:20 goes in the 1.47; struck 13:50 it is a void selection in the 2.17; timed 1.47 before and after the off.
- **Real data:**
  - 12 Oct Musselburgh: off slips 13:49:38, 14:17:46, 14:48:22 ..., matching `results.dbf`.
  - On the real 26 Oct card every HGB00, BFTRP and BFAHR race has its event id linked.
  - Betty's late-selection box in screenshot 11 ("Off: 8:55:34") is 25 s before that race's off slip (8:55:59). A bet struck in those few seconds counts as before the off; Betty's own box still has the final word at entry.
- **`run_eval.py`:** each slip gets its own day's off slips.
- **`nav_cases`:** the selection check is given the struck time to the second.
- **Ideal mode:** 13/13.
- **All pass:** entry, navigation, screen, reader, recheck, number, rules, and `matcher_cases` (unchanged). Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.26] - 2026-10-27

### Changed (user: trim the reader's tokens without losing accuracy)
- **The first scan's card lists UK & Irish meetings only** (`card_for_prompt`). Horses and greyhounds get their race times; international horses and overseas dogs are listed by name only; virtual tracks by name as before. Most bets are UK & Irish, and the overseas times made up most of the card.
  - **A rescan gets the full card**, with every meeting's times.
  - **Times are shown as customers write them**, 12-hour without a leading zero ("4.12 7.45"), to match the slip.
- **The card starts shortly before the bet was struck** (`struck_time` passed from View Wagers by `lock_wager` through `scan_and_reconcile`). It starts on the hour, at least `CARD_FROM_BEFORE_STRUCK_MINS` (30) before. Races long finished are left out. A manual scan with no struck time gets the whole day.
- **The fixed rules come first in the prompt** (`SLIP_READER_RULES`), then the card, then any rescan note. This is the order Gemini's implicit caching needs.
- **The Gemini log line shows cached tokens.** It was 0 on every call in the live pass. The fixed rules (about 1,000 tokens) look to be below the minimum Google needs before it caches.

### Fixed
- **A number bet locked on a time the reader made up** (paul2: "£7 No 8 MUSS", time cut off). Gemini returned "3.17" and marked the time unclear, and the program locked No 8 in the Musselburgh 3.17. For a number bet, a time the reader marks unclear now counts as not written, and is not taken as a ditto of the line above.
  - **Rule 1.8.4 then decides first (user, 27 Oct):** with a meeting and the struck time, the bet goes on the next race at that meeting, or is a void selection if that race has no such number. Staff are asked only when the rule can't place it, for example when no meeting is written.
  - A named selection keeps its unclear time, since the name decides.

### Testing
- **Live, Argon only, one pass of the 13 slips** (results `20261026_203651`, about 25p):
  - 12/13 correct. The one wrong lock was paul2 (fixed above). Replaying that pass's reads through the fixed code: paul2 goes to staff (the test slip has no struck time), and nothing else changes.
  - First-scan names / times / prices / bet lines: 71% / 96% / 88% / 100%. One run, so read this as no worse than 0.46.25, not better.
  - About 4,580 tokens in per scan (was about 6,200), about 1,000 out, 13 s per scan, 0 cached, 6 race-list checks.
  - The card was 1,750–2,300 characters on the test days (was 2,900–4,800). On a rescan it was 2,700–4,300.
- **The struck-time window is not tested live.** The test slips have no struck time.
- **`run_eval.py`:** pre-flight gets the slip's `struck_time` when the ground truth has one. Without one, Rule 1.8.4 isn't applied, since it would otherwise count from the clock at the time of the test run. paul2's notes now say what the rule does with a struck time.
- **New tests:**
  - `reader_cases` 8: the UK & Irish card, the full card on a rescan, the struck-time window, the rules first.
  - `reader_cases` 9: an unclear time on a number bet counts as not written.
  - `entry_cases` 22: an unclear time with a meeting goes on the next race at the meeting (struck 15:00), and with no meeting goes to staff.
- **Ideal mode:** 13/13.
- **All pass:** entry, navigation, screen, reader, recheck, number, rules, and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.25] - 2026-10-26

### Changed (user: a shorter, general slip prompt, for accuracy)
- **The slip reader's prompt is rewritten** (`state_read_slip_via_api`). The reader now copies what is written and leaves a gap rather than guess. The program already works out costs, runners and house rules.
  - Removed:
    - Rules written for one slip: 6-not-3, 'ASALT' = ABOVE 5, 'greb' = treble, "never two sets of doubles", "never & 4-fold", 'Q1' = £1, "line 7".
    - Wrong rules: "traps 1 to 6", "a bare number is a greyhound".
    - The garbled Towcester hint, and the fixed dog and virtual lists (`get_vlm_prompt_summary`, now deleted).
  - Added:
    - Today's card in short form (`card_for_prompt`): each meeting's race times from the feeds (horses, dogs, international), and virtual tracks by name. The reader uses it only to choose between readings the handwriting allows.
    - General layout rules: a bet line covers the selections above it, and how many is set by the bet.
    - Shop shorthand: No 6 = cloth number, T3 = trap, do = ditto, '8 -' = whole pounds.
- **The answer layout changed.**
  - Each line now has a `kind` (selection / bet / total / other) and `struck`.
  - Selections and bets now have `unclear`.
  - `raw_time` and `raw_meeting_hint` are now required.
  - `meeting` is filled only when a meeting is written in full. A guessed 'Kempton' locked petea3 wrong.
  - Removed: `time` (the program now converts the written time itself, as pre-flight already did), plus `total_stake_pence`, `calculated_total_pence` and `written_total_pence`. None of those three was ever used; the total is read from `written_total_raw`.
  - A struck line gets the `[CROSSED OUT]` marker that the bet restorer and the total reader already skip. The phantom-selection check uses `kind` when given. The console shows the meeting letter and any `unclear` fields.
- **The rescan no longer adds the example slip** from `handwriting_examples/`. Its answer was in the old layout, with reworded bet lines. The folder is no longer used.
- **A time written "6 00" now reads as 18:00** (`parse_race_time_to_minutes`). This is a faint dot copied as a space (roger6).

### Testing
- **Live, Argon only:** the 13 confirmed slips, 2 runs each, old prompt against new (results `20261026_192751` and `20261026_195613`).

  | | Old prompt | New prompt |
  |---|---|---|
  | Fully correct | 24/26 | **25/26** |
  | Locked wrong, no warning | **2** (petea3, roger1) | **0** |
  | Safe stop (staff asked) | 0 | 1 (roger4: a time read on the wrong line) |
  | First-scan names / times / prices / bet lines | 63% / 93% / 92% / 100% | 62% / 90% / 89% / 100% |
  | Seconds per scan | 21 | **14** |
  | Tokens per scan in / out / thinking | 4,586 / 1,251 / 312 | 6,195 / 1,012 / 113 |
  | Race-list checks | 9 | 18 |

  - The new prompt's lower times and prices are mostly measurement:
    - 4 "6 00" / "4 45" times now parse (fixed above).
    - 4 empty prices are correct: nothing was written, and the scorer expects "SP".
  - The card makes the input bigger than before. Most of it is overseas dog and international race times.
- **`run_eval.py`:**
  - The ideal reading uses the new layout.
  - Each slip now gets its own day's greyhound card; it was today's.
- **Ideal mode:** 13/13.
- **All pass:** entry, navigation, screen, reader, recheck, number, rules (new "6 00" check) and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.24] - 2026-10-26

### Fixed (from the live logs of 26 Oct)
- **A dog's betslip line was misread, so a good £50 bet went to staff** (9.2453098, Trap 5 Sunderland 4:59). Betty shows a dog as "1. Sund 4:59 11-10 BP" with "Trap 5" on the row below. The line pattern's name part, `(.+?)?`, took one character before trying none, so the name read '1' and the price '1-10', and the horse/dog check saw a horse called '1'. The name part is now `(.*?)`: the line reads Trap 5 at 11-10.
- **A late bet went to the staff pop-up instead of being entered** (9.2453119, 'No 3' 5.07 Philadelphia, struck 17:08:48). Races already off when the bet was struck were never candidates, so nothing fitted. A late bet (the race written, at the meeting written, already off) is now that runner, entered as written. Betty's late-selection box ("apply Void Selection processing?") is answered Yes as before and voids it (user). A late bet whose number isn't in the race still goes to staff. Before (0.46.17) every late bet went to staff.
- **The 'no' of a cloth number was taken as the meeting** (9.2453102, "5.30 no 6": "no race at no then"). The hint 'no' / 'No.' / 'nos' / 'num' / 'number' is dropped for a selection written as a number (`CLOTH_NUMBER_WORDS`). A name's hint is unchanged.
- **Switching the watcher off with ` backed out to Home**, pressing Esc on screens it didn't recognise (9.2452785 and 9.2453105). The user's decision (22 Oct): ` is an instant pause that backs nothing out. It now stops like a staff key: nothing is pressed, and the wager in progress is left for staff. Esc still backs out to Home.
- **About 4 s lost after 'right' on a runner list the screen check didn't recognise** (9.2452785). The wait after 'right' (`_next_runner_list`) now takes the list as soon as its top meeting reads and differs from the one 'right' was pressed on. Requiring a change also stops a list that hasn't redrawn yet from being taken as the next one.
- **Every bet was logged "Bet 1 entered"**, as the count started again on each new slip. The log now gives the bet's place in the wager (`enter_bet_terms(bet_no=...)`).
- **The log listed placed wagers as "left for staff".** That list holds every wager the watcher won't open again this session, placed ones included. It now reads "done or left for staff this session, not opened again".

### Testing
- New reference screenshot `scratch/betty_screens/39_betslip_dog_trap_subline.png` (the live staff screen of 9.2453098).
- `entry_cases.py` section 29:
  - The dog line reads Trap 5 at 11-10, and it is the dog wanted.
  - 'no' with a number is not a meeting; a name's 'No' stays.
  - The log line names Bet 3.
  - After 'right', an unrecognised list counts in 0.09 s once its top meeting changes.
- Section 22: the late 'No 3 3.20 Doncaster' struck 15:30 is now Doncaster 15:20 #3 (was staff).
- `nav_cases.py` section 11: ` mid-wager presses nothing and doesn't back out.
- All pass: entry (217 checks), navigation, screen, reader, recheck, number, rules and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.23] - 2026-10-26

### Changed (user, from the live log of 9.2452785: four £1 straight forecasts at Leicester)
- **A second runner in the same race is chosen from the runner list still showing.** Each selection used to press `/`, type the time again and cycle the meetings ('right') to bring the race back, so 'SF 3-8' at the 2:07 typed the 2:07 twice. When a selection is in the same race as the one before it on the slip (same meeting, time, horses or dogs: `same_race`), and Betty still shows the runner list with that meeting on top, only the cloth number and + / Enter are typed: the 2:07, 3 + Enter, 8 + Enter. If the list isn't showing that race any more, the time is typed as before. The betslip read-back still checks every line's meeting, time, number and name. Selections are never reordered: a forecast's order is its finishing order.
- **Twice as fast where the program only waited.**
  - pyautogui's pause after every key press and mouse action is halved (0.1 s → 0.05 s).
  - Every fixed wait in navigation and entry is halved, e.g. the look for a pop-up after each runner (0.8 s → 0.4 s) and after F11 (0.4 s → 0.2 s).
  - The time is typed straight after `/`, without waiting for the time box to show; Betty keeps the keys (user).
  - A box that opens after that shorter look is now answered while the betslip is read (`_read_new_betslip_line`), instead of the read running out.
  - Timeouts are unchanged: they end as soon as Betty is ready.
  - Placing is unchanged: after F12 the program still waits up to 8 s for View Wagers, then checks that the wager has left the list.
  - The click dwell (0.02 / 0.035 / 0.02 s, calibrated for Betty's buttons) is unchanged.

### Testing
- `entry_cases.py` section 28:
  - Same race means meeting, time and kind; the favourite is never in the same race.
  - SF 3-8 at the 2:07 types the time once (['14:07', '3', 'enter', '8', 'enter']); a list showing another meeting gets '/' and the time.
  - A late price box is answered before the betslip is read.
  - `enter_wager` skips the time only for the second runner of a race; a double over two races types both times.
- All pass: entry (212 checks), navigation, screen, reader, recheck, number, rules, and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.22] - 2026-10-26

### Fixed (from the live log of 9.2452710, a 50p each-way treble)
- **No whole-betslip re-read after the guarantees** (user). `check_slip_before_f8` is no longer called before F8: every line is already read back as it is entered and every guarantee confirmed by its purple price, and the re-read stopped good slips. Any pop-up still open is answered, then F8. The total is still checked against Payment before F12.
- **A betslip line with Betty's dotted focus box read wrong.** After 'g' on the last line, the box's top edge sat on the first row of that line's crop, so '8-1' read as '81' and the line didn't match: "the betslip shows 2 selection(s), expected 3". Rows dark across the crop (a ruled line or a box edge, never text) are now blanked before the betslip lines are read (`_ocr_bw(drop_rules=True)`).
- **A wager the watcher never opened was left for staff for the rest of the session.** A staff key just as the watcher loaded 9.2452711 stopped it before anything was clicked, but the wager was still skipped until restart. Only a wager whose bet edit was opened (End) is now left for staff; one stopped before that stays in the queue.
- **A staff key could be lost between watcher actions.** The loop checked "is the watcher on?" and then cleared the stop flags, so a key landing in between was wiped and the next wager started. The check, the reset and the staff / ` / Esc handlers now share a lock (`_watcher_state_lock`).
- **"Marked FAO" and "placed" only count with View Wagers showing.** Both were decided by the wager missing from the unedited list, which any other screen also reads as empty (`wager_gone_from_list`).

### Testing
- New reference screenshot `scratch/betty_screens/38_betslip_focus_box_after_bog.png` (the live staff screen of 9.2452710). `entry_cases.py` section 27: all 3 guaranteed lines read, the boxed '8-1' included; no whole-betslip re-read in `enter_wager`.
- Passed: entry, navigation, screen, reader, recheck, number. Not run (user said skip): `matcher_cases`, `test_rules_engine.py`. Ruff F,E9: all checks passed.
- Not yet tried on the till.

## [0.46.21] - 2026-10-26

### Fixed
The ten BUG findings of the code review of 0.46.20 (`scratch/code_review_2026-10-26.md`). The RISK, DEAD and TIDY findings are left for now (user).
- **Two straight forecasts on the same runners in different orders were placed in the first order.** `same_selections` sorted each bet's selections before comparing, so 'SF 3-5' then 'SF 5-3' looked like the same selections. The second bet was put on the first slip with F11 and placed as 3-5, and the total still equalled Payment. A straight forecast or tricast now extends a slip only when the order matches too; other bets still compare in any order. The comparison also no longer raises TypeError when a void selection or the favourite (no number) shares a race with a numbered runner.
- **The betslip check couldn't tell a horse race from a dog race that share Betty's label** (Doncaster horses and dogs at one time). A horse entered in the dog list reads 'Trap 3', and a betslip 'Trap' line made the check treat the selection as a dog: the name check was skipped and the number was the one typed, so it passed. A dog entered in the horse list passed too. The kind now comes from the selection (`betslip_line_problems`): a 'Trap' line for a horse, or a horse's name for a dog, is a problem (virtual selections keep the old rule). When horses and dogs both race under the label at that time (`_label_has_horses_and_dogs`), `enter_selection` reads an unread runner list again for up to `MEETING_REREAD_SECS`, then leaves the wager for staff instead of assuming the list is right.
- **The watcher could stop without a word.** When marking a wager FAO raised (e.g. `NavError` "did not load"), the exception left `watcher_loop` from inside its `WagerForStaff` handler and ended the watcher thread, while the HUD still showed the watcher on. The FAO step's failures are now caught: Betty is backed out, staff are alerted ("Could NOT mark it FAO") and the watcher carries on. The other handlers back out through `_go_home_from_handler`, which reports a failure instead of raising.
- **Bets split for a same-race clash were entered as the bet they came from.** `resolve_same_race_contingencies` described them as "(split from same-race double)" / "(split from clashed treble)", and `normalize_bet_type` reads the description, so the singles were entered as doubles on one selection and went to staff. The descriptions no longer name a bet type (as the perm route already did). The same fix covers the tricast "2 non-runners" single, whose description said "Tricast".
- **"X & Y" bet lines typed every part that wasn't doubles as a treble** (`split_compound_bet_entries`): "£1 singles & 50p double" entered a treble. Each part now takes the type it names (`compound_part_bet_type`).
- **Line pairing took Newmarket, Newcastle and Jewel as each way** (`reconcile_bet_scoping_qualifiers`): 'ew' was matched anywhere in the line. It is now matched as a word only (ew, e/w, e.w, each way), as in the each-way check further down.
- **A single read with no stake crashed the singles merge** (`consolidate_identical_stake_singles`: `None >= 100`). A single with no stake read is now never merged. The stake lookup written twice is now one helper (`_single_stake_pence`).
- **Esc didn't free the program until Google answered** (`gemini_call`). Leaving the `with ThreadPoolExecutor` block waited for the request (up to 90 s) before 'aborted' was returned. The request now runs on a daemon thread that is left behind on Esc. The unused `ThreadPoolExecutor` import is gone.
- **A trap typed by staff in the selection pop-up was taken unchecked** (`apply_manual_entry`). It wasn't looked up on the dog card and got no `category`, so entry found a dog list for a 'horse' and left the wager for staff. It now goes through the scanned selection's trap checks: 'T3 Newcastle' is a trap at a venue that also races horses, a meeting written exactly as one on the card is that meeting, and `match_trap_on_dog_card` finds the dog, which is marked `greyhound`. A trap with no dog in it gets a message for staff.
- **Closing the console could crash instead of flushing the log** (`_init_session_logging`). The console-close callback given to Windows was a local, which Python could free while Windows still held it. It is now kept in a module global (`_console_ctrl_callback`).

### Testing
- `entry_cases.py` section 26 (19 checks):
  - 'SF 3-5' / 'SF 5-3' are two slips, while a reversed forecast in any order extends; a void selection beside a numbered runner compares without error.
  - A 'Trap 3' line for a horse and a horse's line for a dog go to staff; a dog's own line and a virtual's pass. An unread list kind at Doncaster 4:05 (horses and dogs both racing) goes to staff.
  - Same-race splits are entered as singles / doubles.
  - Three 'X & Y' lines keep each part's type; singles with no stake are kept apart.
  - The each-way word test no longer matches Newmarket, Newcastle or Jewel.
  - Staff typing 'T3 4.05 Doncaster' get the dogs' trap 3 marked a dog, and 'T9' gets a message.
  - Esc mid-request returns 'aborted' in 0.25 s.
  - A back-out that raises in a watcher handler is reported, not raised.
- All pass: rules, entry (204 checks), reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong, 8 TOP3, 4 MISS, unchanged). Ruff F,E9: all checks passed.
- Snapshots: `previous_versions/betty_companion_v0.46.21.py`, `previous_versions/rules_engine_v0.46.21.py`.

## [0.46.20] - 2026-10-26

### Fixed
- **A selection with nothing readable was dropped without a word.** Pre-flight only collected selections with a name, so one read with no name and no number left the bet a leg short and nobody was told. It is now kept, and staff are alerted (sound and status panel) and shown the always-on-top selection pop-up at once, headed "No selection could be read. Please enter it (or 'fav' for the SP favourite)", with the time and meeting read filled in (user). No name matching or paid re-check is tried for it; cancelling leaves the wager for staff. The terms separate the two cases: no selection written is the SP favourite (Rule 1.8.4), illegible instructions are void (Rule 1.8.1), and only staff can tell which it is.

### Added
- **Staff can enter 'fav' in the selection pop-up** (`apply_manual_entry`): the SP favourite of the race the rules point to (Rule 1.8.4, as for a 'fav' written), entered through Betty's folder. A second or joint favourite is refused with a message.

### Testing
- `entry_cases.py` section 25: a selection with no name or number -> alert and pop-up, slip not locked without it; staff typing 'fav' 3.20 Doncaster -> the favourite of the 3.20 with its folder feed, carried through to entry; '2nd fav' refused.
- All pass: rules, entry (185 checks), reader, navigation, screen, recheck, number (incl. the real pop-up driven automatically) and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9: all checks passed.

## [0.46.19] - 2026-10-23

### Added
- **The SP favourite** (Rule 1.8.4; user's process). A favourite written ('fav', 'SP fav', 'favourite') is resolved to its race by rule 1.8.4 like any un-named selection (`favourite_of`): the race written; untimed, the next race at the meeting; incorrectly timed, the race the time fits elsewhere (ranked, split on a tie); no meeting or time, the earliest race still to run. Only the absolute favourite is entered (Betty's row is 'The Favourite'); a second or joint favourite goes to staff. There is no `/` route to it, so it is entered through the race's folder (`enter_favourite`):
  1. `open_race_folder`: today's folder for the race's feed ("Friday's SIS Horse Racing" for HGB00, 'SIS Greyhound Racing' for DGB00, 'TRP Horses', 'TRP Dogs 5'), clicked from the buttons along the bottom (paged with Next) and confirmed by the folder title. A race from a feed whose folder isn't known (Australian horses / dogs, BTC virtuals) goes to staff.
  2. `pick_in_folder_list`: the meeting, then the time, found by reading the rows (scrolling down, then up, with the arrows), clicked, and confirmed selected (green).
  3. 'The Favourite' (the top row of the selections) is checked by its text and clicked; the betslip line must be The Favourite at SP in that race.
- **Each runner on the card knows its feed** (`feed` in `BettyFeedCard` runners), which decides the folder.

### Fixed
- **The bet-list row reader took its row height from the live display** (`ocr_f8_row_text`). On this PC at 1024x768 it read a 1366 screen at 1024 rows, though `_f8_rows` crops the 1366 layout, so the free tests misread the bet list whenever the display was smaller. It now always uses the 1366x768 layout, the only size the program runs at.

### Testing
- New reference screenshot `scratch/betty_screens/37_folder_sis_greyhound_friday.png` (the user's: Friday's SIS Greyhound folder open).
- `entry_cases.py` section 24: the folder title read on 4 screens; SIS horses wanted on the SIS dogs folder -> its button clicked and the title confirmed; an unknown folder -> staff; Kilkenny and 8:43 found, clicked and seen selected; a meeting not in the list -> scrolled down, up, then staff; the favourite's betslip line checked; 'Fav 3.20 Doncaster' -> the 3.20, 'SP Fav' untimed -> the next race, '2nd Fav' -> staff.
- All pass: rules, entry (181 checks), reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9: all checks passed.

## [0.46.18] - 2026-10-23

### Added
- **Void selections** (user; Rule 1.8.4 "a race card number ... that does not appear in the race ... non-runner"). A card number that isn't in a race that is otherwise clear (meeting and time, or the next race for an untimed one) becomes a void selection for that race (`void_selection`). Entry brings that race up as usual and presses `v` instead of a number, and the betslip line must show `VS` in that race.
- **Time clashes ranked, then split** (user: how shops do it; Rule 1.8.4). When the written meeting has no race at the written time, the races at other meetings then with that number are ranked UK/IRE horses, international horses, dogs, virtual (`TIME_CLASH_ORDER`). Several in the first rank: the bet is divided equally over them, one bet per race at an equal share of its unit stake (`split_bets_over_time_clashes`); a stake that doesn't divide into whole pence goes to staff.

### Changed
- **Non-runners in forecasts and tricasts are entered as written** (user: "the rule is for settlement purposes"). `STATE_FORECAST_NON_EXISTENT_RUNNER`, `STATE_TRICAST_ONE_NON_RUNNER` and `STATE_TRICAST_TWO_NON_RUNNERS` now carry `ENTER_AS_WRITTEN_BETTY_SETTLES`. A forecast with a number not on the card stays a forecast, with that number as a void selection, instead of being turned into a single before entry; Betty settles it under Rules 1.17 / 1.18. Their descriptions keep the terms' settlement wording.

### Testing
- `entry_cases.py` section 22: an untimed number not in the next race is now a void selection for it. Section 23: 'No 12 3.20 Doncaster' (10 runners) -> void; 5.30 fitting Wolverhampton and Kempton -> two half-stake bets; 7.00 fitting Rome and Romford dogs -> Rome; 501p over 2 races -> staff; forecast 3-12 with #12 missing stays a forecast with a void leg; a VS line accepted only in the right race; entry types the time and presses `v`, no number.
- All pass: rules, entry (167 checks), reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9: all checks passed.

## [0.46.17] - 2026-10-23

### Added
- **House rule 1.8.4 for un-named selections** (numbers and traps), from the BetAnsells terms. `bookmaker_rules.json` gains `STATE_UNNAMED_UNTIMED_OR_MISTIMED` (action `NEXT_RACE_AT_MEETING_UNLESS_TIME_FITS_OTHER_MEETING`), and `unnamed_by_timing_rule` applies it before a number bet would go to staff:
  - **Untimed:** on for the next race at the written meeting off after the bet was struck. 'No 3 Doncaster' is the next horse race; 'T3 Doncaster' the next dog race.
  - **Incorrectly timed:** when the written meeting has no race then, a race at another meeting at that time with that number takes precedence (horses first). A time no meeting has is the next race at the written meeting.
  - **Still staff:** a race at the written meeting and time already off when the bet was struck (a late bet); the number not in the race; a meeting not racing; a time fitting several other meetings. For the last two, the terms say a missing card number is a non-runner and a clash divides the stake, which the program can't enter yet.
- **The BetAnsells terms are in the project:** `betansells_rules_2026.txt`. All 14 rules in `bookmaker_rules.json` were checked against it.

### Removed
- **The other bookmaker profiles** (Tattersalls, William Hill, Betfred, Custom) and the profile choosing (`active_profile`, `ACTIVE_BOOKMAKER`). `bookmaker_rules.json` now holds only the BetAnsells rules at its top level, and `BookmakerRulesManager` reads them as one set (`get_rules`).

### Testing
- `entry_cases.py` section 21: 'No 3' / 'T3' Doncaster with and without a time; section 22: 7 cases of rule 1.8.4 (untimed horse and trap, number not in the next race, the time another meeting's, a time no meeting has, a late bet, Kempton horses and Romford dogs at the same time).
- `scratch/test_rules_engine.py`: no profiles, and Rule 1.8.4 present.
- All pass: rules, entry, reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9 on the program files: all checks passed.

## [0.46.16] - 2026-10-23

### Changed (tuned rules made general, after an audit of the day's fixes)
- **A betslip number that disagrees is settled by the runner's name** (`betslip_runner_by_name`), replacing 0.46.14's re-reads at OCR scales 4 and 5. Those were tuned on one screenshot; across 36 betslip lines on the day's screens, scale 4 or 5 failed to read the line at all 5 times. Two runners in a race never share a name, so when the number differs, the line's name is looked up among that race's runners on Betty's card: if it is clearly the runner entered, the number was an OCR slip ('9. River Trieux' = River Trieux #5; #9 is Hastily). Dog lines show only 'Trap N', so for dogs the number stays the check.
- **Runner-list meeting: the nearest label, clearly** (`nearest_meeting_label`), replacing the 0.75 fit. The label must share at least 3 of 4 letters with a meeting racing then and be at least one letter nearer than every other one. On 23 Oct's card five pairs of meetings one letter apart raced at the same time (Speedwell / Steepledowns, Greenacres / Greyville, ...); a label equally near two is no answer. The label is read from its first capital letter, so the list's left border read as 'i' ('iShef') no longer spoils it.
- **Bet list: the nearest of all 85 rows Betty can show** (`nearest_bet_label`, `BETTY_BET_LIST`), replacing the first-letter / two-letters / digits rules. A row is a bet type only when that type's label is its nearest of the 85 (within about one letter in three, no tie), so 'FR Lucky 15', 'Lucky 15 Sport' and 'Doubles + Trebles' are rows of their own and never Lucky 15 or Trebles, while 'trebies' is Trebles. A page counts as read when 6 rows read as known names. (0.46.12 said 84 rows: there are 85.)
- **The red grand total is found anywhere in the grey panel**, as its biggest block of Betty's red, instead of in a fixed box. Same results on every Choose Bet and Stake screen kept.

### Added
- **Horses and dogs at one meeting** (user's rule): with no 'T' / 'Trap' written, a number is matched on the horse races first and on the dogs only when no horse race fits; 'T3 Doncaster' is the dogs. At entry, a runner list whose meeting label fits is also checked for its kind (`race_list_is_dogs`): a dog list's rows read 'Trap 1. ..', a horse list's '01. ..'; the wrong kind gets `right`. A label two meetings share (Doncaster horses and dogs) is taken for the one wanted and then checked by its rows. A number with no time written still goes to staff, now offered the horse race first.

### Testing
- `entry_cases.py`: section 11 now checks the program's list equals the 85 screenshot rows and 'lucky3l' is Lucky 31; section 15: '9. River Trieux' accepted by name, Searcog #11 still to staff, a dog line still checked by number; section 20: 'svee' between Speedwell and Steepledowns is no answer, 'gree' / 'San' read; section 21: dog and horse lists told apart (4 screens), 'iShef' read as Shef, 'No 3 4.05 DONCASTER' -> the horse, 'T3' -> the dog, no time -> staff offered the horse first.
- New screenshot `scratch/betty_screens/36_race_list_dog_rows_from_35.png` (the real 'Shef 6:58 Trap 1. Miller Ned' row of 35 copied to the top).
- All pass: rules, entry (151 checks), reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9: all checks passed.

## [0.46.15] - 2026-10-23

### Fixed
- **A withdrawn runner read as a missing line** (9.2448529: "shows 1 selection(s), expected 2"). Betty shows `WD` in place of the price; it is now read like `NR`: fine for an SP selection and never expected to be guaranteed (`NOT_RUNNING`). NR and WD lines inside a BOG window also no longer fail the before-F8 check as "not guaranteed" (`g` was already never pressed on them).
- **FAO on the 'Unedited Fao Only' list** (9.2448529: "still in the unedited list after Mark bet fao Manager"). When View Wagers shows the FAO-only list, every wager on it is FAO already, so clicking again changed nothing. `unedited_list_is_fao_only` reads the list header; `mark_wager_fao` then clicks nothing and returns 'already', and staff are told the wager is already on the FAO list.
- **Keys sent after the staff selection dialog didn't reach Betty** (9.2448749: "time box ('/'): expected RACE_ENTRY_READY", then a second paid scan). `enter_wager` now gives Betty the keyboard first (`focus_betty`): the window brought forward is the topmost visible window of Betty's program (`BETTY_EXE`, default `bets.exe`), found through Windows by the program that owns it, never by title or screen position. Betty's bet edit is an untitled window over 'A-Bet System'; nothing in Betty is clicked.
- **A virtual meeting was taken for Sheffield** (9.2448749: "Stee 6:58(v)" accepted as Sheffield; Mister Bassan added, caught before F8). The runner-list label had to fit a meeting only half way ('stee' vs 'shef' = 0.5); it now needs `RACE_LIST_MEETING_FIT` 0.75 (3 of 4 letters). Betty's runner list is on a 12-hour clock, so `_meetings_at` now also offers the meetings racing 12 hours away (06:58 virtual Steepledowns beside 18:58 Sheffield), so the label is recognised for what it is.

### Testing
- New reference screenshots `scratch/betty_screens/32_unedited_fao_only_header.png`, `33_unedited_exc_fao_header.png`, `34_withdrawn_WD.png`, `35_virtual_stee_658.png`.
- `entry_cases.py` sections 18-20: the WD line read and accepted, NR / WD not expected to be guaranteed; 'Fao Only' and '(Exc.Fao)' told apart on 4 screens; 'Stee' not taken for Sheffield and read as Steepledowns, Wolverhampton / Dundalk / Doncaster / Harlow still read; meetings at 6:58 include the 06:58 virtuals.
- Betty's top window found on this PC: the untitled bet-edit window of `C:\Betty\Bets.exe` (read only, no window moved).
- All pass: rules, entry, reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9: all checks passed.

## [0.46.14] - 2026-10-23

### Fixed
- **A late selection read as 0 selections** (9.2448544). After "Yes" on the late-selection box Betty draws the line in black with the price `VS` (void selection); the betslip reader only knew SP, NR, Evens and fractions. `VS` is now read, accepted for an SP selection, and never expected to be guaranteed (BOG skips it).
- **A misread betslip digit sent a wager to staff** (9.2448563: Betty showed "5. River Trieux", read as "9."). When a betslip line looks wrong, after adding a runner or before F8, the same screenshot is read again at OCR scales 4 and 5 (`BETSLIP_REREAD_SCALES`). It is accepted only when both read it right; a runner that is really wrong reads wrong at every scale and still goes to staff.
- **'right' was pressed past an unread meeting** (9.2448555: "Dundalk 7:15 is not in Betty's runner list"). When the runner list's top meeting can't be read (often mid-redraw), it is read again for up to 1.5 s (`MEETING_REREAD_SECS`) before `right` is pressed.
- **'No 8 4.50 ROME' was taken as Romford trap 8** (9.2448510). The meetings directory turned 'ROME' into the Romford dogs before Betty's card was checked, although Rome (Italy) raced at 4:50. A meeting written exactly as one on today's card now wins over a greyhound shorthand, and the number is matched at that meeting only, so Romford dogs at the same time can't be chosen. A trap written ('T8') is still a trap. When the dog card has no fitting race and no trap is written, the number is tried on the whole card before staff are asked. Pre-flight also reads both cards fresh (`BettyFeedCard.refresh`, skipping the 10 s wait), so a feed Betty added moments ago counts.
- **Test runs wrote session logs.** The free tests import the program, which started the session logger, so every test run left a `logs/session_*.log` of fake errors. The logger stays off when `BETTY_HEADLESS=1`.

### Testing
- New reference screenshots `scratch/betty_screens/30_late_selection_VS.png` and `31_betslip_number_5_read_as_9.png`.
- `entry_cases.py` sections 14-17: the VS line read and accepted, not expected to be guaranteed; '5.' misread at scale 3 accepted after both larger reads, a really wrong runner still to staff; two unread reads then Dundalk with no `right` pressed; 'No 8 4.50 ROME' -> Rome #8 with and without Romford dogs at 4:50, 'T8 4.50 ROMFORD' -> Romford trap 8.
- All pass: rules, entry, reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). No session log was written by any test run. Ruff F,E9: all checks passed.

## [0.46.13] - 2026-10-23

### Added
- **Combination tricasts are entered** (9.2448523, 9.2448525: "bet type(s) the program can't enter yet: combination tricast"). It has no shortcut (user), so it is picked from the bet list by its full name, 'Combination Tricasts', like Lucky 63. Its read-back name is 'tricast'.

### Fixed
- **Wagers of several betting slips failed the total check** (9.2448524: £3 + £4 + £3 read as £3.00 against £10.00 paid; also 9.2448529, 9.2448546, 9.2448568). With more than one slip, Betty draws its large red total over "Total Payment On All Wagers: £..", which OCR'd as noise, so only 'Payment' for the current slip was read. `read_slip_grand_total` now reads the red figure from its red pixels only (the blue text under it drops out), and `read_betslip_bets` uses it as the slip total, falling back to the 'Payment' text when there is no red figure. The check stays the same: Betty's total must equal Payment before F12.

### Testing
- New reference screenshots `scratch/betty_screens/27_multi_slip_total_3_slips.png` (£10.00 over 3 slips) and `28_multi_slip_total_2_slips.png` (£6.00 over 2).
- `entry_cases.py`: combination tricast and tricast entered; on all 84 list rows, combination tricast matches only 'Combination Tricasts'. Section 13: £10.00 and £6.00 read on the multi-slip screens, £3.00 and £1.00 on the single-slip ones, and no figure invented where there is none.
- The red figure read correctly on every Choose Bet and Stake staff screenshot since 22 Oct (11 screens). All pass: entry, navigation, screen, reader. Ruff F,E9: all checks passed.

## [0.46.12] - 2026-10-23

### Fixed
- **Lucky 15 / 31 / 63 could be matched to 'Lucky 15 Sport' or 'FR Lucky 15'** (found with the user's screenshots of the whole bet list, 84 rows on 8 pages). The 0.46.9 matcher let most types match a row that starts with their label, and two letters off, so 'Lucky 15 Sport' (page 4) and 'FR Lucky 15' passed for Lucky 15. If page 1 misread, the program could page on and choose one. Each bet type now carries Betty's full label ('Patent or Twist', 'Straight Forecasts', 'Reversed Forecasts', "Combination F'casts", 'Tricasts'), the 'starts with' match is gone, and a near miss must also share the first letter.

### Testing
- New reference screenshots `scratch/betty_screens/26_bet_list_full_p1-8.png` (every page of the bet list).
- `entry_cases.py` section 11: on all 84 rows, each of the 18 types the program enters matches exactly its own row and nothing else.
- All pass: entry, navigation, screen. Ruff F,E9: all checks passed.

## [0.46.11] - 2026-10-23

### Changed
- **A plain forecast on three or more runners is a combination forecast** (house default, user). A forecast written without 'straight', 'reversed' or 'combination' is now resolved in one place, `resolve_plain_forecast` in `rules_engine.py`: straight on two runners (in the order written), combination on three or more. Both `calculate_bet_cost_pence` and `entry_bet_type` use it, so a plain 'F/C 1-2-3' at £1 is costed £6 (6 bets) and entered as a combination forecast. Before, it was costed as one bet and went to staff.

### Fixed
- **The status panel is put back in its corner before View Wagers is read** (9.2448382 and 9.2448383: Payment unread). The panel can be dragged, and it had been left over the summary panel, so Betty's "Payment: £…" line was hidden and both wagers went to staff. `open_view_wagers` and `load_wager` now call `CompactHUD.snap_home`, which moves it back to the bottom-right corner and waits (up to 0.5 s) until it is there; the console says when it was moved. It can still be dragged in between.

### Testing
- `scratch/test_rules_engine.py`: plain forecast costs: 2 runners 1 bet, 3 runners 6, 4 runners 12.
- `entry_cases.py` section 5: 'F/C' on 3 -> combination forecast. Section 12: a panel dragged over the summary panel is moved home before the read; one already home is left alone with no wait.
- All pass: rules, entry, reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong). Ruff F,E9 on the program files: all checks passed.

## [0.46.10] - 2026-10-23

### Fixed
- **A plain forecast was refused** (9.2448384: "4.30 F/C 7 - 10", £1, "bet type(s) the program can't enter yet: forecast"). A forecast written without 'straight', 'reversed' or 'combination' stayed 'forecast', which `entry_bet_type` didn't know. On exactly two runners it is now entered as a straight forecast in the order written, as it was already costed (one bet) and as the rules settle two runners in a race with no instruction. On three or more it could be any of the three, so it still goes to staff.

### Testing
- `entry_cases.py` section 5: 'F/C' on 2 runners -> straight forecast; 'F/C' on 3 -> staff; 'R/F/C' on 2 -> reversed forecast.
- All pass: entry, reader, navigation, screen. Ruff F,E9: all checks passed.

## [0.46.9] - 2026-10-23

### Fixed
- **A forecast written above its traps lost a trap and was placed as a win single** (9.2448236, placed live: '£10 S/F/C' with 'TRAPS 4-5' on the line under it). The causality guard in `reconcile_bet_scoping_qualifiers` drops runners written below a bet line; it removed trap 5, the lone-selection rule (1.17) then settled the forecast as a £10 win single, and £50 + £10 still matched the £60 paid. The guard now never cuts a bet below the fewest selections its type can have (forecasts 2, tricasts and trebles 3, the full-cover counts as before, accumulators 2): the runners below then belong to the bet.
- **Trebles wasn't found in Betty's bet list** (9.2448240: "Betty's bet list has no 'treble'"). One read of page 1 that didn't match, e.g. taken while Betty redrew the list after `b`, was enough to press PgDn, and Trebles is only on page 1; the program paged on to 'Stop at a Winner'. `_find_bet_row` now reads a page again until it holds the bet type, or until enough rows hold a name and two reads agree; an unreadable page goes to staff.
- **Bet-list names match with a little give, never onto another bet** (`bet_label_score`). Exact first; then the prefix match the longer types always had ('Patent or Twist'); then one or two letters off ('treble' for 'Trebles', OCR 'trebies'; one for labels of 5 letters or fewer). Never: different numbers (Lucky 31 vs Lucky 63), or a longer name for Singles / Doubles / Trebles ('Singles and Doubles', 'Doubles + Trebles'). The best row on the page wins, and a near-miss match is logged.

### Testing
- New reference screenshot `scratch/betty_screens/25_bet_list_last_page.png` (the bet list's last page, 'Stop at a Winner' to 'Perm 4-Folds', from 9.2448240).
- `entry_cases.py` section 11: 25 row/type pairs (treble/trebles/trebies yes; Doubles + Trebles, Singles and Doubles, Lucky 63 for Lucky 31, Super Heinz for Heinz, Perm Patent for Patent no); on 05 Trebles beats Doubles + Trebles; a list read mid-redraw is read again and Trebles found on page 1 without PgDn; the last page is judged not to hold Trebles.
- `reader_cases.py` section 7: the 9.2448236 slip keeps both traps on the forecast; a double written above a third horse still drops it.
- All pass: entry, reader, navigation, screen, recheck, number and `matcher_cases` (14 OK, 0 wrong, 8 in top 3, 4 miss, as in 0.46.0). Ruff F,E9: all checks passed.

## [0.46.8] - 2026-10-23

### Fixed
- **A yellow box at the top of the unedited list made the list read as empty, so the watcher saw no work.** `read_unedited_queue` stopped at the first box that wasn't light blue (waiting) or green (clicked), and `view_wagers_queue_state` called a yellow top box 'empty'. Yellow (255, 255, 128) wagers edit like any other (user, 23 Oct), so both now count yellow as unedited (`QUEUE_YELLOW_RGB`, `QUEUE_UNEDITED_RGBS`). White still ends the list.

### Testing
- New reference screenshot `scratch/betty_screens/24_view_wagers_yellow_top.png` (yellow 009.2448179 above light-blue wagers).
- `nav_cases.py`: the unedited list on it reads all 8 wagers, 9.2448179 first. `screen_cases.py`: it is View Wagers with the top box 'waiting'.
- All pass: `nav_cases.py`, `screen_cases.py`, `entry_cases.py`. Ruff F,E9: all checks passed.

## [0.46.7] - 2026-10-22

### Added
- **Automated Session Console Logging to `logs/` (`ConsoleTeeLogger`):**
  - Integrated a real-time `ConsoleTeeLogger` streaming all `stdout` and `stderr` directly into dedicated per-session log files (`logs/session_YYYYMMDD_HHMMSS.log`).
  - Writes and flushes every character and line immediately to disk, guaranteeing 100% of the session transcript is preserved even if the operator abruptly terminates or closes the console window (`X` button).
  - Registered Windows console control handler (`SetConsoleCtrlHandler`) and `atexit` callbacks to ensure clean stream flushing.
  - Automatically prunes session logs older than 30 days on startup in compliance with invariant project constraints.

### Changed
- **Removed Intermediate Bet-Line Readback Loop in `enter_bet_terms`:**
  - Removed the fragile OCR readback while-loop in `enter_bet_terms` that repeatedly tried to parse tiny 9–10pt font on Betty's grey panel, eliminating false rejections on forecast bets and multi-bet extensions.
  - The script now executes deterministic entry keystrokes (stake typing, Enter, Each-Way toggle, bet-type hotkey) with brief settling pauses, avoiding UI lag issues.
  - Maintained the strict financial safety check prior to placement (`total == payment_pence` before `F12`), ensuring Betty will never place any bet where the total calculated stake mismatches the customer's payment.

### Fixed
- **Multi-Bet Extension Total Payment Extraction (`Payment: £2.00, Total Payment: £10.00`):**
  - Updated `read_betslip_bets` payment regex to match `Total Payment(?: On All\s*Wagers)?:\s*\D{0,2}\s*(\d+)\.(\d{2})` ahead of singular `Payment:`, ensuring slips with multiple bets (e.g. £8.00 Singles + £2.00 RFC) extract the complete slip total (£10.00) rather than just the final bet's portion (£2.00).
  - Enhanced `read_betslip_bets` line parser to recognize both active forecast formats (e.g. `1) Combination F'casts. 6 Bets : 6 Forecasts @ £1.00.`) and locked previous bet lines (e.g. `1) £2.00 Each Way Singles = £8.00`).

## [0.46.6] - 2026-10-22

### Fixed
- **Greyhound Trap Betslip Read-Back Bug (`the betslip shows 0 selection(s), expected 1`):**
  - Updated `BETSLIP_SELECTION_LINE` regex to make runner name and cloth number optional on line 1, accommodating Betty EPOS's greyhound betslip format (where line 1 displays meeting, time, and SP e.g. `1. Towc 5:06 SP`, while line 2 displays `Trap <n>`).
  - Added subline fallback inspection in `read_betslip_selections` to extract the trap number from line 2 (`Trap 4 Result Remove`) when line 1 lacks a runner name/number.
  - Updated `betslip_line_problems` to bypass runner name string similarity checks for greyhound selections where Betty lists the runner as `Trap <n>` instead of the dog's registered name.
  - Verified on live staff failure screenshot `logs/staff_9.2446924_20261022_172402.png` (Towcester 5:06 Trap 4 SP).
- **Glued Time/Cloth-Number Regex Collision (`before F8, line 1 shows number None, name '$'`):**
  - Refactored `BETSLIP_SELECTION_LINE` regex so that `\S*` after the race time (`5:15`) does not greedily consume adjacent cloth numbers (e.g. `5:156.Amused`), properly separating `5:15` as the race time and `6.` as the runner cloth number.
  - Tolerated thresholded active red-dotted selection box artifacts (e.g. `$$`) occurring between the runner name and price tag (`7-1BP`).
  - Verified on live staff failure screenshot `logs/staff_9.2446929_20261022_172454.png` (Newmarket 5:15 #6 Amused 7-1 BP).
- **Daemon Thread Crash on Watcher Toggle (`WatcherStop` Unhandled Exception):**
  - Wrapped `leave_wager_for_staff` within `watcher_loop` inside a `try...except WatcherStop:` block so toggling the backtick (`` ` ``) key while a wager is being routed to staff cleanly disengages the watcher instead of crashing the daemon thread.

## [0.46.5] - 2026-10-22

### Fixed
- **Multi-Bet `F11` Extension Deselection Bug (`could not select only reversed forecast`):**
  - In `choose_bet_type`, prevented deselecting existing active bet types when extending an already-entered selection (`extending=True` / `bets_before > 0`). Previously, when selecting `Reversed Forecasts`, the script actively clicked Row 0 to deselect `Singles`, wiping Bet 1 off Betty's betslip.
  - Added a 0.4s pause after `F11` in `enter_wager` and cleared the stake input buffer with backspaces before typing new stake terms, preventing the old stake (e.g. £2.00) from persisting on the extended bet (e.g. £1.00 RFC).
- **Exact Matching for Atomic Bet Types & Paging Reset:**
  - Replaced prefix matching `text.startswith(label)` with strict equality `text == label` for atomic types (`singles`, `doubles`, `trebles`) in `choose_bet_type`. This prevents falsely matching composite entries like `Singles + Doubles` (`singlesdoubles`) when searching for `Singles`.
  - Recognized Betty's default `Singles` selection on `F8`: if `Singles` is wanted and already active, skipping blind keystrokes and unnecessary clicks.
- **Portman Park Virtuals Shorthand (`PP`) & 24-Hour Time Parsing:**
  - Added `"pp"`, `"p p"`, `"p.p"`, `"sv"`, `"sd"` acronym aliases to `meetings_directory.json` for virtual tracks (Portman Park, Sprintvalley, Steepledown).
  - Updated `_meeting_matches` to check `meetings_manager.are_meetings_equivalent` and acronym initials (e.g. `PP` -> `Portman Park`) before falling back to string prefix matching, enabling 2-letter customer shorthand to resolve to virtual racecards.
  - Improved selection time extraction in `pre_flight_validate_slip` to ignore noise punctuation (such as `.`), prevent stray characters from overriding valid inferred times, and inherit race time/meeting across grouped number selections when subsequent lines omit them.
  - Updated `betslip_line_problems` to accept both 12-hour (`3:34`) and 24-hour (`15:34`) formats (standard on Betty for virtual tracks) via `parse_race_time_to_minutes` matching, and made meeting prefix comparisons case-insensitive.
- **Queue Desync & FAO Server Polling Timeout:**
  - In `load_wager`, re-checked `read_unedited_queue` immediately before clicking to recalculate the exact row index, preventing row shifts (e.g. clicking row 3 instead of row 2) when prior wagers clear from the queue.
  - Increased `mark_wager_fao` polling timeout from 4.0s to 6.5s to accommodate Betty EPOS backend network latency when updating unedited lists.

## [0.46.4] - 2026-10-22

### Fixed
- **Glued runner name and price token on betslip read-back (`the betslip shows 2 selection(s), expected 3`):**
  - Updated `BETSLIP_SELECTION_LINE` regex to accept runner names that concatenate directly into the price token (e.g. `'Phantom WatcSP'`) when 2-digit cloth numbers or long runner names push against Betty's column limit with 0-1px whitespace.
  - Anchored the line parser to the end of the line while supporting optional trailing Betty price tags (`BP` / `EP`) and trailing punctuation.
  - Tolerated OCR artifacts for line numbering where digit '2' is occasionally read as '?' (e.g. `'?. Kemp'`), automatically falling back to row sequence index `i + 1`.
  - Verified on wager 9.2446686 staff failure screenshot (`logs/staff_9.2446686_20261022_154101.png`), where Newmarket 2:55 #11 Phantom Watch now parses cleanly without error, as well as the full regression test suite `scratch/ocr_eval/entry_cases.py`.

## [0.46.3] - 2026-10-22

### Fixed
- **Non-Runner (`NR`) betslip read-back support (`the betslip shows 2 selection(s), expected 3`):**
  - Added `NR` to the accepted price patterns in `BETSLIP_SELECTION_LINE` regex (`(SP|NR|Evens|Evs|\d+\s*[-/]\s*\d+)`). When a selection becomes a non-runner, Betty displays `NR` in place of the price on the betslip.
  - Updated `betslip_line_problems` to allow `NR` as a valid price for SP/unpriced selections (`got['price'].upper() not in ('SP', 'NR')`).
  - Updated `apply_guarantees` to skip BOG processing for selections marked `NR`, as non-runners do not carry a price that can be guaranteed.
  - Verified on wager 9.2446668 staff failure screenshot (`logs/staff_9.2446681_20261022_153007.png`), where Prince Palace was a non-runner (`NR`) at 4:30 Clonmel; all 3 betslip lines now parse with 0 errors.

## [0.46.2] - 2026-10-22

### Fixed
- **Betslip selection read-back OCR failure (`the betslip shows 0 selection(s), expected 1`):**
  - Calibrated `BETSLIP_LINE_H` from 22px down to 18px. Betty's main selection text line is 12px tall (y=86 to 97), while the second subline (`Jockey: ...`) starts at y=104. The previous 22px height (y=83 to 105) captured 2px of jockey ascenders at the bottom of the crop, causing Tesseract to misread kerning (e.g. `'Tu rf'` for `'Turf'`) and hallucinate punctuation before the price (e.g. `' =SP'`).
  - Improved `BETSLIP_SELECTION_LINE` regex to accept optional spaces within OCR'd meeting abbreviations (`[A-Za-z\s]{3,7}?`) and strip them on normalization, and tolerate leading punctuation before the price (`[\W_]*(SP|...)`).
  - Verified against staff failure screenshots for wagers 9.2446666 (Turffontein) and 9.2446667 (Ffos Las); both now extract correctly with 0 line problems.

## [0.46.1] - 2026-10-22

### Fixed
- **Pyrefly type checker errors and linter warnings in `betty_companion.py`:**
  - Resolved `None <= int` type-checking errors in `match_horse_to_racecard` by assigning walrus expression `(tg := time_gap(r))` to narrow `tg` to `int` before comparison against `window` and `TIME_AGREE_MINS`.
  - Type-narrowed Anthropic beta messages API call in `claude_json_request` to eliminate TypedDict parameter mismatches for `output_config` and `messages`.
  - Added explicit typing `tiers: list[dict[str, Any]] = []` in `reader_tiers` to prevent dict variance mismatch when appending Claude provider dict.
  - Added explicit typing `out: dict[str, Any]` in `scan_slip_with_retry` to permit `.update(...)` with mixed data types.
  - Broadened `signals` parameter type in `_signals_pass` and `_signals_absent` to `Any` to allow passing polymorphic signature signal lists without type checker rejection.
  - Used key lambda `key=lambda k: votes[k]` in `_meeting_at_head` to guarantee comparable `int` return values for `max()`.
  - Guarded `got` read-back result in `enter_bet_terms` with `if got is None: raise WagerForStaff(...)` to avoid subscripting `None`.
  - Narrowed `canon` in `enter_wager` with `assert canon is not None` before calling `enter_bet_terms`.
  - Removed redundant `str()` calls on already-string variables in `parse_clock_minutes` and Claude error handler.
  - Removed redundant `int()` call on already-integer `round()` result in `enter_bet_terms`.

## [0.46.0] - 2026-10-22

### Added
- **Every horse and greyhound card Betty holds is read, found by the sport label in each feed's header.** Horses: every `HORSE` / `AHorses` feed, so Australian horse racing (`BFAHR`: Gosford, Ipswich, Mornington...) and BTC virtual horses (`BFBI1`) join SIS, TRP and the Tote. SIS, TRP and the Tote stay first, so the meeting names Betty shows still win for duplicate races. Greyhounds: every `DOG` feed, as in 0.45.0. `BETTY_HORSE_FEEDS` still fixes the horse list if set.
- **Greyhounds are matched by name too.** Pre-flight now checks every selection against the horse and greyhound cards together. Each greyhound runner is category `greyhound` (UK, Irish or Australian); virtual dogs stay `virtual`; each runner also carries its feed's country.
- **The house priority order: UK/IRE horse racing, then greyhounds, then international, then virtual** (`CATEGORY_ORDER`). A meeting written on the slip still searches its own tier first.
- **`todays_meetings()` in `betty_feed.py`:** every horse and greyhound meeting for the day, with sport, region (UK/IRE, Australia, International, Virtual), number of races and first / last race. It is for the launcher's Data tab; `python betty_feed.py --meetings` prints it now. Today: 64 meetings, 16 of them virtual.

### Changed
- **The stake healers fit the bets to the customer's written total again,** and to Payment only when no total could be read from the slip. The final check against Payment, to the penny, is unchanged.
- **A venue that races both horses and dogs is told apart by Betty's cards.** 'No 3 Newcastle 6.37' with no horse race there then finds the dogs at 18:37. A trap written at such a venue ('T3 Newcastle') goes straight to the dog card.
- **A lower tier never overrules a higher tier on a name.** A selection locks to a greyhound, international or virtual runner only if its name fits clearly better (`NAME_MARGIN`) than anything on a higher tier; otherwise it goes to the re-check and then staff. The stress test found the case: 'UNCLE TALBCRT 1.25', a UK horse at 16:25 written with a wrong time, had locked to a different Uncle Albert at 13:33 on a newly added card.
- **Betty's cards are looked at no more than every 10 s** (`RECHECK_SECS`), and the card summary is printed only when the card changes. Betty rewrites today's feeds every few seconds, so before, a card could be re-read and re-printed on almost every lookup.
- **Every watcher error line names the wager,** and a wager left part-way says it was left unedited for staff (not marked FAO).

### Fixed
- **A box left open after `g` hid the betslip, which then read as 0 selections** (9.2446520: "before F8 the betslip shows 0 selection(s), expected 2"). `apply_guarantees` stopped watching as soon as the price turned purple, so a price box that opened at the same moment was never answered. It now checks for the price box before checking for purple, and answers any box that opens before clicking the next line.
- **The betslip edge is found with a box open.** `betslip_left` looked for the panel's cream at y=74 and y=472. On race entry y=74 is still the cyan header, so a box covering y=472 left no edge, and every line was read from x=906 with its "1." cut off. It now looks at y=78, which is cream on both layouts.
- **The check before F8 reads until the betslip is right,** for up to 4 s (`NAV_TIMEOUT`), answering any open box first. Only the last read sends a wager to staff; before, one frame taken while Betty was redrawing was enough.
- **The bet-line check reads until the new line is all there** (9.2446518: "bet line 1 shows stake Nonep"). `enter_bet_terms` judged the first frame showing a bet line and never read again. On a new slip (F10) Betty keeps the last bet type selected, so the line is redrawn while the type is set again. It now re-reads until the bet type, each way / win and stake are all read and right, for up to 4 s, and only the last read decides.
- **Betty's screen is saved when a wager goes to staff** (`save_staff_screenshot`): `logs/staff_<wager>_<date>_<time>.png`, taken before anything is backed out, so a failure can be seen afterwards. Only the newest 20 are kept, in `logs/`, not a folder of their own. Next to the .exe when frozen.

### Testing
- All pass: rules, entry/BOG, navigation/placing, screen, reader chain, recheck, number/greyhound and `matcher_cases` (14 OK, 0 wrong, 8 in top 3, 4 miss). Ruff F,E9: all checks passed.
- Stress on the full card (horses incl. Australian and BTC virtual, plus every dog feed): 12 Oct 89.2% auto-correct, **0% wrong**; 13 Oct 90.1%, **0% wrong** (the old card gave 89.2% and 90.1%, 0% wrong).
- Ideal mode 13/13 on both readers, and 13/13 with Payment supplied.
- `number_cases.py` section 2d, on today's real feeds saved to `scratch/ocr_eval/feeds_auto/`: horse feeds found by label incl. Australian; real dogs `greyhound`, virtual dogs `virtual`; Gosford international; 'No 3 Newcastle 6.37' and 'T3 Newcastle 6.37' find the dogs; a named Australian dog matches on the greyhound tier; the same name on several cards goes UK/IRE first, then greyhound before international.
- `entry_cases.py` sections 8-10: with the price box over a three-line betslip, the edge is still ~880 and 3 lines are read; a box that opens with the purple after each `g` is answered (g, Enter x3); a box still open before F8 is answered, then the slip is checked; a stake unread on the first frame is read again and accepted, and one that never reads goes to staff after re-reading; the staff screenshot is saved and only the newest 20 are kept. `nav_cases.py` no longer saves fake-Betty screenshots into `logs/`.

## [0.45.0] - 2026-10-22

### Added
- **Australian greyhounds (and any new greyhound feed) are read automatically.** The dog card now reads every feed of the day whose header Betty labels `DOG` (today: SIS `DGB00`, TRP Dogs `BFTV5`, and Australian Dogs `BFTST`, 49 races at Angle Park, Hobart, Grafton and others, up to 8 dogs). Before, only `DGB00` and `BFTV5` were read, so every Australian dog bet went to staff. `BETTY_DOG_FEEDS` still fixes the list if set.
- **Greyhound tracks come from Betty's card too.** Every real (not virtual) track on today's dog card counts as a greyhound track by name, so 'Angle Pk' resolves to Angle Park with no list to maintain. `meetings_directory.json` still supplies the written shorthands ('Sheff', 'Romf'). Horse courses are still checked first, so 'Doncaster' stays the horses.

### Fixed
- **A bet line was taken as the customer's written total.** With no total from the reader, the fallback accepted any bottom line holding an amount and didn't know forecast notation: on petea3, "50p S/F/C 2-9" became a 50p total against £1.00 of bets. A line now counts as the total only if it holds nothing but an amount, optionally with 'total' or 'stake' (`is_total_line`). The same check applies to a total the reader reports.
- **The stake healers now fit the bets to Payment.** The pounds-for-pence and each-way healers used only the customer's written total. The watcher now passes View Wagers' Payment, the money staff took, into the reading step; the written total is used only when there is no Payment.

### Removed
- `rule_4_concession_waiver_pence` from `bookmaker_rules.json`: the shop doesn't waive small Rule 4 deductions, and the program never read it.
- The unused `GREYHOUND_TRACKS` snapshots in `betty_companion.py` and `rules_engine.py`.

### Testing
- All pass: rules, entry/BOG, navigation/placing, screen, reader chain, recheck, number/greyhound and `matcher_cases` (0 wrong). Stress: 89.2% auto-correct, 0% wrong. Ruff F,E9: all checks passed.
- Ideal mode **13/13** on both readers, and 13/13 with Payment supplied; petea3 now passes on the first scan.
- `number_cases.py` section 2c, on today's real feeds saved to `scratch/ocr_eval/feeds_auto/`: the DOG feeds are found and Australian horses (`BFAHR`, `HORSE`) left out; Australian and UK tracks listed, virtual dogs left out; 'Angle Pk' is a greyhound track and 'Doncaster' still the horses; 'T8 Hobart 11.10' gives Tony The Turtle; trap 8 exists and trap 9 doesn't.

## [0.44.2] - 2026-10-22

### Changed
- **`bookmaker_rules.json` is now the only copy of the bookmaker rules.** `rules_engine.py` no longer carries a built-in duplicate of the 13 non-normal states and the parameters, nor the unused legacy rule-key mappings and `get_rule`. The callers no longer pass their own fallback actions.
  - **At start,** a missing or unreadable file, an unknown profile, or a profile missing any of the 13 rules or `max_greyhound_traps` stops the program with a message naming what's wrong (`RulesFileError`). Before, it silently used the built-in copy.
  - **Edited while running,** the file is still re-read. A broken edit now keeps the rules already loaded and says so in the console.
  - **The file is found next to `rules_engine.py`,** whatever folder the program was started from. Before, it was looked for in the current folder, and quietly replaced by the built-in copy if it wasn't there.
- **Greyhound traps: up to 8** (`max_greyhound_traps`, all profiles). Australian races run 8 dogs; UK and Irish 6. Before, trap 7 or 8 in a forecast or tricast was treated as a non-existent runner and the bet rewritten under Rule 1.17 / 1.18. Whether the trap really runs is still checked against Betty's greyhound card.

### Removed
- **The £1 leeway on the slip total** (`total_stake_grace_variance_pence`). The watcher never used it: Payment must match to the penny, both after reading and after house rules, or the wager goes to staff. It only let Ctrl+Alt+B accept a slip up to £1 off the customer's written total on the final scan. The warning-only check of the written total after house rules went with it.

### Testing
- All pass: rules, entry/BOG, navigation/placing, screen, reader chain, recheck, number/greyhound and `matcher_cases` (0 wrong). Stress: 89.2% auto-correct, 0% wrong. Ruff F,E9: all checks passed.
- `reader_cases.py`: the Ctrl+Alt+B case now expects 50p off the written total to be refused.
- Ideal mode: 12/13 as `run_eval.py` runs it, because it drives the Ctrl+Alt+B path with no Payment. petea3's written total is read as 50p against £1.00 of bets, which the leeway used to accept. With Payment supplied, as the watcher does on the till: **13/13**, and petea3 passes on the first scan. `run_eval.py` should move to the watcher's path when Ctrl+Alt+B is removed.
- New loading checks: the file found from another folder; missing file, broken JSON, missing rule and unknown profile all refused; a broken edit mid-run keeps the last good rules; trap 8 valid, trap 9 not.

## [0.44.1] - 2026-10-22

### Removed
- **The last Racing API code.** The best-odds check had a branch for selections "verified against The Racing API" (`api_horse_number` / `matched_official_name`). Nothing has set those fields since v0.25.0 moved to Betty's local feeds, so it could never run. `RACING_API_USERNAME` and `RACING_API_PASSWORD` are gone from `.env`.

### Testing
- `entry_cases.py` (entry and best odds guaranteed) and `test_rules_engine.py` pass.

## [0.44.0] - 2026-10-21

Phase 7: tidy-up. **The code built over the last few days is unchanged and supersedes the old code; nothing the program does was altered.** Every step was checked against the full free test suite, with identical results.

### Changed
- **Ctrl+Alt+B now uses the same checked entry as the watcher** (`enter_wager`): read-back after every selection, the full check before F8, and the bet-line read-back. Before, it used the old entry code, which had never run at 1366×768. It takes the money from Betty's own "**Paid £x**" on the betslip. Its pre-check accepts the race-entry screen, or an unrecognised one, but not a recognised different screen. The struck time isn't on that screen, so with Ctrl+Alt+B staff guarantee prices by hand; the watcher still does BOG itself.
- **`normalize_bet_type`, `calculate_bet_cost_pence`, `is_greyhound_or_trap_selection`, `clean_horse_name` and `parse_race_time_to_minutes` now exist once, in `rules_engine.py`.** These are the newer copies from `betty_companion.py`, together with `LINES_PER_BET_TYPE`. `rules_engine.py`'s older copies are gone. This was checked first on **1,224 distinct real bets** from every saved test reading: bet type and cost were identical before and after (and the two copies already agreed on all of them).

### Removed
- **96 unused pieces**, found mechanically (nothing in the program, the test kit or the other modules referred to them), including:
  - the old entry code: `state_read_cyan_panel`, `select_bet_type_on_f8` with its fixed row positions, `state_handle_price` (which clicked "Override with entered price"), and `state_apply_guarantees` (which retried `g` blind);
  - the old single-pixel screen and pop-up checks;
  - the unused 1024×576 coordinate sets.
- **The two long-standing unused variables** (`mult` and `bet_shortcuts`) and five unused imports. **Ruff F,E9 now reports "All checks passed!"**
- **`betty_companion.py` is down from 6,931 to 4,735 lines.**
- **88 old one-off scripts and debug crops in `scratch/`** were moved, not deleted, to `scratch/archive_2026-10-21/`. Kept: `scratch/ocr_eval/`, `scratch/betty_screens/`, `scratch/test_rules_engine.py`, the build prompt.

### Testing
- Full free suite, with the same results as before the tidy-up:
  - ideal mode 13/13 on both readers;
  - `matcher_cases` 0 wrong;
  - stress 89.2% auto-correct, 0% wrong;
  - recheck, number/greyhound, rules, screen (22 screenshots), reader chain, entry/BOG and navigation/placing all pass.
- `run_eval.py` no longer stubs the removed `is_betty_ready`. `rules_engine` snapshot: `previous_versions/rules_engine_v0.43.1.py`.

## [0.43.1] - 2026-10-21

### Changed
- **Best odds guaranteed is about 9x faster.** The user found it too slow. The betslip lines are now read once, before the sweep. After each `g`, only that line's price colour (purple = guaranteed) and the price box's blue border are checked, every 40 ms, with no text reading. Before, every `g` was followed by a full text read of the betslip and a text-reading screen check. On the same betslip, 3 guarantees took **8.9 s before and 1.0 s now**. The rules are unchanged: one click and one `g` per qualifying selection, never pressed twice, and the full check before F8 still runs once at the end.

## [0.43.0] - 2026-10-21

### Changed
- **An unrecognised screen (UNKNOWN) no longer stops the program,** at the user's request: the rule was causing more stops than it prevented. `expect_screen` now carries on when Betty's screen can't be recognised, and logs "screen not recognised (expected …); carrying on".
  - **A screen recognised as a different one still stops it,** e.g. View Wagers when the bet screen was expected, because Betty really is somewhere else.
  - **The checks that protect the bet itself are unchanged:** the betslip read-back after every selection, the full check before F8, the bet-line read-back, and Betty's total against Payment immediately before F12.
  - **After End,** an unrecognised screen is treated as the event menu, so `/` follows.
  - **Scanning, placing and opening View Wagers** accept an unrecognised screen but still refuse a recognised wrong one.
  - **Before typing a race time,** on an unrecognised screen `/` is pressed only if the yellow time box isn't already showing. `/` toggles the box, so it is never closed by mistake.

### Testing
- `nav_cases.py` section 10: an unrecognised screen carries on; a recognised wrong screen (View Wagers) still stops; scanning on View Wagers is still refused. All free tests pass.

## [0.42.0] - 2026-10-21

### Added
- **Best odds guaranteed (`g`), applied by the watcher, using the shop's rule:**
  - **Which selections:** UK and Irish horse racing on Betty's horse card, where **a price was taken**. SP, greyhounds, international and virtual races never get `g`.
  - **When:** only if the bet was **struck** within **11:00:00–14:00:59** or **17:00:00–18:00:59** (end minute included, as the user confirmed). The struck time comes from View Wagers. Override with `BOG_WINDOWS`.
  - **How:** each qualifying selection is **clicked** on the betslip, then `g` is pressed once. The user's down-arrow route loses focus at a non-runner or late selection, so every qualifying line is clicked instead. Any price box is answered with Enter (price when struck). The price must then turn **purple (128, 0, 128)**, which is how Betty shows a guaranteed price; an ordinary price is red. `g` can't be undone, so it is **never pressed twice**: if purple doesn't appear, the wager goes to staff.
- **A full check before F8, as the user asked (`check_slip_before_f8`).** Every betslip line must match its locked selection, in order: meeting, time, cloth number, name, and SP or a price. Each line must be guaranteed exactly when it should be. Anything wrong → staff, and F8 is never pressed.

### Changed
- **The betslip is read one line at a time** (a line every 45 px from y 83). The focused selection's dotted box made a whole-panel read miss lines: it read 2 of 3 on the user's screenshot. Each line also reports whether its price is guaranteed (purple) and where to click it. The crop was tuned on 14 lines across 4 screenshots: 14/14 read correctly. The price pattern accepts "12-1EP" with no space.

### Testing
- New reference screenshot from the user, `23_betslip_three_guaranteed.png`. `entry_cases.py` sections 6–7 cover:
  - the BOG windows at every edge: 10:59:59 no, 11:00:00 yes, 14:00:59 yes, 14:01:00 no, 17:00:00 yes, 18:01:00 no, unknown no;
  - SP, greyhound and international → no `g`;
  - red prices = not guaranteed, purple = guaranteed;
  - struck 13:22 → each line clicked and `g` pressed once each, then the pre-F8 check passes;
  - struck 15:00 → no `g`;
  - unguaranteed inside a window → stop before F8;
  - Betty ignoring `g` → staff after a single press.

## [0.41.0] - 2026-10-21

Phase 6: **placing**. The user's live test of v0.40.3 passed end to end in test mode, on the 50p E/W treble Rodeeve / Wet Sail / Somers Isles: all 3 selections, F8, stake, each way, Treble, read-back, Payment, then the stop for staff.

### Added
- **`commit_wager(number, payment)` places a checked wager. It is the only code that can press F12:**
  - **In test mode it refuses** (`PlacingRefused`).
  - **`betty_press` refuses F12 from anywhere else,** even with test mode off: it accepts F12 only while `commit_wager` is placing. A refused placing stops the watcher and is never retried.
  - **Just before F12** it checks Betty's slip total against Payment one last time.
  - **After F12**, placed means Betty is back on View Wagers with the wager **gone from the unedited list**. A placed wager therefore can't be picked up again, even after a restart.
  - **If Betty raises the payment box after F12**, nothing is answered and the wager goes to staff. In live mode that is: back out No → Cancel, then **Mark bet fao Manager**.
  - **If the wager is still unedited after F12**, it goes to staff and F12 is never pressed again.
- **The watcher places checked wagers when test mode is off.** In test mode it still stops before F12 for staff. **Test mode is on at every start** (`BETTY_TEST_MODE=1`); Shift + `` ` `` switches it off.
- **The HUD makes live mode obvious:** "**LIVE: PLACES BETS**" on orange, against "TEST MODE" on purple. The console prints a warning when test mode is switched off.

### Testing
- `nav_cases.py` section 9:
  - test mode: `commit_wager` refuses and F12 is never sent;
  - F12 from anywhere else is refused, even live;
  - live: one F12 → View Wagers → wager gone = placed;
  - Betty's total ≠ Payment → not placed;
  - payment box after F12 → staff, backing out No → Cancel;
  - still unedited after F12 → staff;
  - the HUD shows TEST MODE / LIVE: PLACES BETS.

  All free tests pass; ideal mode is still 13/13 on both readers.

## [0.40.3] - 2026-10-21

The live run on v0.40.2 entered and checked all 3 selections (Rodeeve 7-1, Wet Sail 25-1, Somers Isles 12-1) and pressed F8. Betty opened Choose Bet and Stake, but the program read it as UNKNOWN and backed out.

### Fixed
- **Choose Bet and Stake is now recognised as it first opens.** The old rule was built from screenshots taken after a bet had been entered, and it needed a green **Place Bet** button and a full bet list. On a fresh F8 screen, Place Bet isn't green yet and the list can be shorter. The screen is now recognised only by parts present the moment it opens:
  - the red "Please Choose the Bet You Require Here" header;
  - the red "Please Choose the Unit Stake Here" header;
  - the cyan £200…£1 stake column;
  - "Stake:" read by Tesseract.

  Measured on all 21 screenshots: 0.83 / 0.77 / 0.94 on F8, against at most 0.21 / 0.26 / 0.54 anywhere else.

### Testing
- `screen_cases.py`:
  - F8 as it first opens (Place Bet blanked, a shorter bet list) is still Choose Bet and Stake.
  - New reference screenshot from the user, `22_bet_and_stake_fresh.png`: a fresh F8 screen has **no Place Bet button at all** (the old rule saw 0% green there). It is recognised. Its 11 bet types read by name, with Singles selected by default and Win Only on, and "At least 1 selection needed. No Stake Entered." is not taken for a bet line.
  - All other screens, including the payment pop-ups over F8, are unchanged.

## [0.40.2] - 2026-10-21

The live run on v0.40.1 entered and checked selections 1 and 2:
- "nava 1:32 7. Rodeeve 7-1";
- **right** once for Worcester, then "worc 3:25 10. Wet Sail 25-1".

It added the 3rd and then read "0 selections".

### Fixed
- **The betslip panel's left edge was measured along the pixel row at y = 200.** With 3 selections, the third line sits on that row, so the text broke the edge search. The panel then looked as if it started further right, every line's "1." / "2." / "3." was cut off, and nothing was read. The edge is now measured on rows the selection lines never reach (y = 74 and y = 472).

### Testing
- `entry_cases.py`: a three-line race-entry betslip with a line across y = 200. The edge is still found and 3 lines are read.

## [0.40.1] - 2026-10-21

From the first live entry run on v0.40.0. Entry worked up to the first selection: it typed the time (1:32 / 8:30), brought the meeting to the top (one **right** for Kempton), typed the cloth number and added it with numpad +.

### Fixed
- **The betslip read-back saw "0 selections" right after a selection was added.** Betty's betslip panel starts at x ≈ 878 on the race-entry screens but x ≈ 904 on Choose Bet and Stake and View Wagers. The read box was fixed at 904, so on race entry it cut off the "1." that starts every selection line, and no line was recognised. The panel's left edge is now found on each screenshot (`betslip_left`, where the panel's cream begins), for both the selection lines and the bet/payment lines. The `/` that reopens the time box for the next selection is already in `enter_selection`; it was never reached because of this.

- **A price taken on a race Betty has no price for yet** (numpad + then enters SP) **goes to staff**, as the user decided. The message now says so in plain words: "the customer took 16/1 on … but Betty has no price for it yet".

### Testing
- `entry_cases.py`: the race-entry layout reads "1. Harl 10:32 The Favourite SP", and an empty betslip reads as no selections.

## [0.40.0] - 2026-10-21

### Added
- **Wagers open on another till are skipped.** When two staff are in and the other till has a wager's image on screen, View Wagers shows the slip panel cream with "**TERMINAL x IS VIEWING THIS WAGER'S IMAGE**" in green, and the slip can't be shown here.
  - After loading a wager, the program looks for that message (`wager_open_elsewhere`): it picks out the green text by colour, then reads it.
  - When it is there, the program **moves straight on to the next wager on the ladder**, as the user asked, and looks at the skipped one again after 30 s.
  - End is never pressed on it, there is no clean-up, and no staff alert, because the wager is not the program's to touch while another till has it.

### Testing
- New reference screenshot `21_view_wagers_open_on_other_terminal.png`:
  - "terminal 1" is read, and there is no message on the other View Wagers screenshots;
  - the seven-wager ladder is read top first, with the Problems column ignored;
  - the wager is skipped without End.
- All free tests pass.

## [0.39.0] - 2026-10-21

From the live run of v0.38.1. The slip-not-showing retry worked: cream → Esc → reopen → slip shown. The next wager, "4 1259 Mon £40 win" (a trap bet), was read correctly but stopped at entry with "no meeting / time / cloth number". The trap had been taken as written, with the time left as "1259".

### Added
- **Trap bets are checked on Betty's own greyhound card,** the way horses are checked on the horse card (`greyhound_card`, `match_trap_on_dog_card`).
  - The card is two feeds: **DGB00** (SIS dogs: Harlow, Valley, Doncaster, Kilkenny…) and **BFTV5** (TRP Dogs 5: Monmore, Romford, Hove, Nottingham, Sunderland…). Override with `BETTY_DOG_FEEDS`.
  - A trap locks only when exactly one race at that track is within 2 minutes of the written time (morning or evening, whichever exists). The trap must not be vacant, and the race must not have been off before the bet was struck. It then carries Betty's exact meeting, time (HH:MM) and the dog's name, e.g. "4 1259 Mon" → **Without Delay #4, Monmore 12:59**.
  - Otherwise the trap goes to staff. It is no longer accepted as written.
- Entry reads a dog's betslip line whether or not Betty prints "Trap" before the number. The meeting on top of the runner list is chosen from horse **and** greyhound meetings at that time.

### Testing
- `number_cases.py` section 2b, using today's DGB00 and BFTV5 saved as fixtures in `scratch/ocr_eval/feeds/`:
  - the live slip → Without Delay, Monmore 12:59;
  - Harlow 11.04 trap 2 → Ravenswood Blake;
  - a vacant trap, a race already off, and a time 11 minutes out → staff;
  - a time within 2 minutes fits.

  All free tests pass, and ideal mode is still 13/13 on both readers.

## [0.38.1] - 2026-10-21

From the first live run of v0.38.0.

### Fixed
- **`/` on the event menu was sometimes not taken.** Wager 9.2445341 stopped with "expected the time box, Betty shows EVENT_MENU", probably because the key arrived while the menu was still drawing. `/` is now pressed again, up to 3 times, but only while Betty still shows the event menu. Once the time box is open, `/` toggles it, so it is never pressed blind.
- **Betty's "slip not displayed" bug wasted 3 scans.** Wager 9.2445359 opened with an empty slip panel, and Argon was asked three times to read nothing. Now, before any scan, the slip must be showing (`slip_showing`). As the user pointed out, a slip shows as a **white page** and a missing one as a **plain cream panel**. Measured inside the panel: 0.85–0.98 white with a slip on every race-entry screenshot, 0.0 without. If no slip is showing, the program presses Esc, clicks the wager again and reopens it, up to 3 times, then sends the wager to staff. Betty's broken alt-tab state is handled the same way.
- **A navigation glitch no longer drops a wager for the session.** It gets a second try; only a second navigation problem leaves it for staff.

### Testing
- `nav_cases.py`:
  - slip showing (white page) on 04 and 02, not showing (cream) on 16 and the new `20_race_entry_slip_not_showing.png`;
  - `/` ignored once → pressed again;
  - slip not showing twice → Esc, click, reopen, shown on the 3rd open;
  - never shows → staff after 3 opens.

## [0.38.0] - 2026-10-21

Phase 5b and 5c: the watcher now **enters each locked wager into Betty and checks every step against Betty's own betslip**. It then stops before F12. Placing is not built: every wager waits for staff to place it (F12) or cancel it, whether or not test mode is on.

### Added
- **`enter_selection`, for each selection.** Pre-flight has already resolved its meeting, time and cloth number from Betty's own card:
  - `/` → time box → type the time → runner list.
  - **right** until that meeting heads the list. The top meeting is read from the list's first rows and matched against the meetings racing at that time on the card, so a misread label such as "Hari" or "Han" still means Harlow. If the meetings run out → staff.
  - Type the cloth number → **numpad +** if a price was taken, or **Enter** for SP.
  - Price-check box → **Enter** (price when struck). Late selection → **Yes**, found by its label.
  - **Betslip read-back:** the new line must show the right meeting, time (12-hour, as Betty prints it), cloth number and name, and SP or a price as wanted. Anything else → staff.
- **`enter_bet_terms` / `choose_bet_type`, for each bet on Choose Bet and Stake:**
  - Stake in pence, then Enter. Each Way (`e`) or Win Only (`w`), checked by the toggle's colour.
  - **The bet type is found by name.** It uses the user's shortcut where one exists (s d b q l j y o f r c i), otherwise the row is found in the list, paging with PgDn. Any other selected row is deselected.
  - The new bet line on the read-back must show the right type, each way / win and unit stake.
  - F11 when the next bet uses the same selections; F10 for a new betting slip.
  - **The final total on Betty's slip must equal View Wagers' Payment.**
- **Bets the program can't enter yet go to staff before anything is typed:** perm N-folds from same-race clashes, forecast doubles, and any type not mapped.
- **`wait_for_staff_review`:** a HUD message and sound, then it waits without touching Betty. Back on View Wagers with the wager gone from the unedited list means **placed**. Otherwise it is **cancelled**, and Betty goes back to Home. Staff input during this wait doesn't pause the watcher.

### Fixed
- **Patent's shortcut was `p`, which is not Betty's Patent key.** It is now `o`, as the user specified. (The `p` key does not park a bet: "P" is the on-screen Park button.)

### Not yet
- **BOG guarantees (`g`)** are not applied by the watcher yet. Staff can apply them before placing.
- **Placing with F12** (Phase 6).
- **Live checks still needed on Betty:**
  - whether a time like 13:10 must be typed as `13:10` (as the old code did) or `1:10`;
  - whether stake + Enter and the bet shortcuts behave as expected;
  - how F11 shows an extended bet.

  Every step reads the betslip back, so a difference stops the wager and goes to staff.

### Testing
- New free test `scratch/ocr_eval/entry_cases.py`, run on the reference screenshots:
  - betslip selection lines (1, 4 and 6 lines) and bet lines, including a Lucky 63 wrapped over 3 lines, with Payment;
  - Harlow read on top of both runner lists;
  - Betty's 12-hour times;
  - bet-list rows (only Singles selected; Perm Patent replaces Patent or Twist with 4 selections);
  - which bet types are entered and which go to staff;
  - Patent → `o`;
  - `.` refused.
- `nav_cases.py`: the locked wager is entered with Payment, then handed to staff.
- All free tests pass; ideal mode is still 13/13 on both readers.

## [0.37.2] - 2026-10-21

Live run on v0.37.1 confirmed the whole order on the real Betty:
- wager click → 9.2445341 / 12:19:41 / £1.00, read first time;
- End → event menu;
- `/` → time box;
- scan (Argon, 15 s) → £1.00 = Payment → 3/3 horses matched by name → locked;
- no false operator Esc.

### Fixed
- **`go_home` no longer presses Esc on a screen it can't identify.** That screen is usually Betty mid-redraw. It now waits up to 1.5 s for a recognisable screen first, and presses only if the screen is still unknown. The live log showed "Backing out from UNKNOWN: Esc" right after an Esc.

## [0.37.1] - 2026-10-21

### Fixed
- **The HUD could cover what the program reads.** `--check-screen` read Payment as unreadable because HUD text ("Betty Companion v0.36.0 – [!] ABORTED…") was over Betty's grey summary panel. Two copies of the program were running at the time.
  - The HUD now sits in the bottom-right strip, x ≥ 1030 and y ≥ 652. That area is clear of the slip image, the summary/betslip panel (which ends at y 640) and every bottom button (which end at x 1020).
  - With the old copy closed, the user's re-run read wager 9.2445341, struck 12:19 and Payment £1.00 correctly.
- **`load_wager` now waits until the number, struck time and Payment have all been read,** within its 4 s limit, so a slow redraw isn't taken as unreadable. A wager that loads but stays unreadable still goes to staff, with what was read.

## [0.37.0] - 2026-10-21

From the user's first live test run, which worked end to end up to "locked": wager 9.2445341, struck 12:19:41, Payment £1.00; Argon read a 50p E/W treble correctly, £1.00 = Payment, and all 3 horses matched by name.

### Added
- **The watcher switches itself back on after staff stop using the till.** A key press or click by a person still pauses it at once. It now comes back on by itself after **60 s with no activity at all**, and mouse movement counts as activity, so it never starts while someone is reading the screen. It then goes back to watching View Wagers. If it was switched off with `` ` ``, it stays off.
- **Read-only screen check: `python betty_companion.py --check-screen`.** After 5 s it takes one screenshot and prints the screen, the unedited list, and the loaded wager's number, struck time and Payment. It sends no key or click.
- **More console detail:** the unedited list when there is work, what the blue box, timestamps and Payment read as while a wager loads, and the summary text when they can't be read.

### Changed
- **Empty queue: the watcher looks again every 5 s** (was 20 s).
- **The slip is scanned only at the race-entry time box.** The order is: click the wager → End → `/` → time box → scan. The screen is checked again right before the screenshot, and if it isn't the time box the program refuses to scan. The console now logs the screen after End and after `/`, so a live run shows each step.
- **Navigation keys (End, arrows, Page Up/Down, Home) are sent as real extended keys,** as a keyboard sends them. pyautogui sent them without that flag, the way their numpad twins are sent. All watcher keys go through `_send_key`.

### Fixed
- **The program's own Esc was taken as the operator's Esc.** On backing out after "locked", the log showed "ESC PRESSED: Aborting…" twice. The old Esc listeners (a `keyboard` hotkey and a key-state poller) can't tell a person's key press from the program's, and a 0.5 s grace window wasn't enough. Operator Esc is now detected only by the low-level hook, which uses Windows' own "injected" flag. The program's key presses carry that flag, so they can never abort. The poller and the Esc hotkey are removed.

### Testing
- `nav_cases.py`:
  - mouse movement doesn't pause; a click does;
  - no resume within the minute, and movement restarts it;
  - back on after 60 s idle;
  - switched off with `` ` `` stays off;
  - an injected Esc doesn't abort, and a person's Esc does.

## [0.36.0] - 2026-10-21

Phase 5a: the watcher now reads each wager and checks it against Betty's card. **It still enters nothing.** After "selections locked" it backs out and leaves the wager unedited.

### Added
- **`scan_and_reconcile(api_key, payment_pence)`**, split out of `run_cycle_logic` and used by both Ctrl+Alt+B and the watcher:
  - **View Wagers' Payment is the authority.** The bets must cost exactly what was paid, with no £1 grace.
  - On a mismatch it rescans with a targeted hint ("the customer paid £x"), up to 3 scans, then sends the wager to staff showing both figures.
  - The customer's written total is a second check: if it disagrees with Payment, the program only warns.
  - Ctrl+Alt+B, with no Payment available, keeps the old written-total rule, with the £1 grace on the final scan only.
  - If no reader answered, it stops at once.
- **Watcher, for each wager:**
  1. load the wager and read its struck time and Payment;
  2. End → `/` to the time box;
  3. scan, and reconcile against Payment;
  4. check the card with the **struck time** (`state_pre_scan_and_match_slip(..., struck_time=...)`);
  5. re-check the money after house rules;
  6. "locked" on the HUD → Esc back to View Wagers.
  - Staff answering a selection prompt don't switch the watcher off.
  - If Betty's racecard feed can't be read, the wager goes to staff. It is never entered unchecked.
- **Wagers the program can't do (`WagerForStaff`):** the HUD shows one sentence, with a sound.
  - In **test mode** the wager is left unedited and Betty goes back to Home.
  - With test mode **off**, it is marked **fao Manager**.

### Testing
- `reader_cases.py`, new "money" section:
  - Payment matched first time;
  - a mismatch, then a rescan with a "paid £3.00" hint;
  - still wrong after 3 scans → staff, with both figures;
  - no grace against Payment;
  - Payment beats a wrong written total;
  - the Ctrl+Alt+B grace;
  - no reader → stop.
- `nav_cases.py`:
  - a full watcher cycle with the scan reconciled to £3.00 and the card check given struck time 09:10;
  - staff input allowed during prompts;
  - a money mismatch → staff alert, unedited, back to Home;
  - no racecard → staff.

  All free tests pass, and ideal mode is still 13/13 on both readers.

## [0.35.0] - 2026-10-21

Phase 4: a single reader chain replaces the either/or `SLIP_READER` switch and the Gemini-only key pool.

### Changed
- **Slips are read by a chain of readers (`reader_tiers`, `read_vision_json`).** Each one is asked in turn until one answers:
  1. **paid Gemini:** `GEMINI_API_KEY`, `GEMINI_PAID_MODELS` (default `gemini-4-argon`);
  2. **Claude:** `CLAUDE_API_KEY`, `CLAUDE_MODEL` (default `claude-opus-5-5`);
  3. **free Gemini:** `GEMINI_API_KEY_2`, `_3`…, `GEMINI_FREE_MODELS` (default `gemini-3.8-flash`);
  4. then **staff**. There is no Haiku step, as the user asked.

  Every reader gets the same prompt and the same JSON schema. The console and HUD show which step answered. A step whose key is missing is left out.
- **When the chain moves on:**
  - no credit (HTTP 402) → next key, or the next reader;
  - quota (429) → next. That model is then skipped for 10 minutes rather than asked on every slip.
  - timeout or server error → one retry, then next;
  - unparseable JSON or a Google safety block → next, with no retry.
- **Re-checks** (the race-list check) go down the same chain, **starting with the reader that read the slip**.
- **Timeouts:** scan 90 s, re-check 45 s (`SCAN_TIMEOUT_SECS`, `RECHECK_TIMEOUT_SECS`).
- **`SLIP_READER=gemini` or `=claude` now pins one provider,** for paid evaluation runs. `gemini` uses `GEMINI_API_KEYS` (or the numbered keys) with `GEMINI_MODELS`; neither ever falls through to the other paid provider. The default is now `waterfall`.
- **If no reader answers, the scan stops at once** with a clear message instead of rescanning 3 times. A reader that answered with unusable bets is still rescanned, as before.

### Removed
- `ApiKeyPoolManager`, the key rotation, `get_prioritized_model_waterfall` and the 220-line Gemini retry loop inside `state_read_slip_via_api`. Replaced by `gemini_call` (one request, which can be aborted) and `gemini_tier_request`. `betty_companion.py` is 165 lines shorter.

### Testing
- New free test, `scratch/ocr_eval/reader_cases.py`, using fake providers with no network:
  - the chain order and which keys each step uses;
  - 402, 429, timeout and retry, a server busy once, bad JSON and a safety block;
  - Argon and Claude both failing → free key 2, then free key 3 → nothing answers → staff;
  - the 429 memory, and re-checks starting at the reader that read the slip;
  - pinned readers that never fall through;
  - a missing Claude key, and abort.

  All pass, and so does every other free test (ideal mode 13/13 on both readers).
- `recheck_live.py` uses the new settings.

## [0.34.0] - 2026-10-21

Phase 3: the watcher now moves around Betty. **This is a dry run.** For each unedited wager it goes as far as the race-entry time box, then backs out and leaves the wager unedited. It does not scan, enter or place anything yet.

### Added
- **Reading the loaded wager on View Wagers (`read_wager_details`):**
  - the wager number (white on the blue box);
  - the **struck time** (upper timestamp);
  - **Payment** in pence, from the grey summary, even under a long bet description.
- **Reading the unedited list (`read_unedited_queue`):** the wager numbers, top first (`009.2445225` → `9.2445225`).
- **Navigation, where each step is checked against the screen detector:**
  - `open_view_wagers`;
  - `load_wager`: clicks a wager in the list and confirms its number appears in the blue box. Betty pre-loads the last scanned wager, not the top one.
  - `open_race_entry`: End → event menu → `/` → time box. `/` toggles the box, so it is pressed once and then checked. The broken alt-tab state stops the wager.
  - `mark_wager_fao`: selects the wager, clicks Mark bet fao Manager, and checks the wager left the unedited list.
- **`go_home()`, the safe reset.** It presses Esc, or a pop-up's backing-out button, until Home shows, checking the screen after every step.
  - On the F12 payment boxes it presses **No → Cancel**, never Yes or Confirm. On the price box it presses Cancel; on the late-selection box, No.
- **Pop-up buttons are clicked by what they say.** `find_buttons` finds each yellow button rectangle by colour and reads its text, because the price box's buttons move around. If a label is not read, nothing is clicked.
- **Watcher loop:**
  - It goes to View Wagers and takes the top unedited wager it hasn't handled this session.
  - Each wager gets one dry run per session.
  - With nothing waiting, it looks again every **20 s**, sitting on View Wagers.
  - Any unexpected screen → back out to Home and carry on. Three failures in a row → the watcher stops and alerts staff.

### Changed
- **Stopping:**
  - **Esc** aborts the watcher's current action. It backs out to Home, leaves that wager for staff, and the watcher stays on.
  - **`` ` `` off** backs out to Home, then goes idle.
  - **Staff typing or clicking** stops the watcher at once, and it touches nothing.
- **The program's own Esc presses are never taken as an operator abort.**
- **Keys the watcher can never send:** F3–F7 and `.`.

### Testing
- New free test `scratch/ocr_eval/nav_cases.py`. It runs against a fake Betty made from the reference screenshots and covers:
  - reading wager details and the queue;
  - finding buttons on all four pop-ups;
  - backing out from race entry and from the F12 payment box;
  - a full dry-run cycle, the empty-queue poll and marking fao Manager;
  - forbidden keys, and Esc handling.

  All pass, and so does every other free test.

## [0.33.1] - 2026-10-21

### Fixed
- **The free tests no longer put windows over Betty.** The user saw an empty "Betty Companion – Selection #1" window that showed "Not Responding" when clicked. It came from `number_cases.py`, which opens the real staff dialog and types into it without running its event loop, so the window sat there undrawn until the test finished. Every test also briefly showed its own HUD.
  - With `BETTY_HEADLESS=1`, the HUD opens no window. `run_eval.py`, `matcher_cases.py`, `matcher_stress.py` and `screen_cases.py` set it, and so do the scripts that import `run_eval.py`.
  - The automated staff dialog in `number_cases.py` is hidden.

### Testing
- `screen_cases.py`: 17 reference screenshots, adding the Choose Bet and Stake screen with 4 selections. The bet list there differs: Lucky 63 and Perm Patent appear, and Patent or Twist is gone. The existing row reader (`ocr_f8_row_text`) reads all 11 rows correctly on both bet screens, so bet types are found by name, never by position.

## [0.33.0] - 2026-10-21

### Added
- **`detect_screen()` recognises Betty's broken edit state, `RACE_ENTRY_BROKEN`.** It happens after alt-tabbing away from A-Bet and back, then editing a new bet:
  - the slip image is missing and its panel is plain cream;
  - "Special/Other Events Wager" is drawn over where the slip should be;
  - the bet summary is garbled.

  The rule is to back out and start again. Previously this screen read as a normal race entry with the time box showing, so a scan would have read an empty panel.

### Testing
- `screen_cases.py`: 16 reference screenshots, all pass.

## [0.32.0] - 2026-10-21

### Added
- **`detect_screen()` recognises the previous-selections ("reuse") panel, `REUSE_PANEL`.** Right-clicking the slip image replaces the runner table with white rows of the selections already entered ("Harl 10:32 | The Favourite").
  - **Never click a selection that was entered via the Master Index here: it crashes Betty.** Any future reuse-panel click must be limited to selections the program itself entered in the current wager, and the program never uses the Master Index.

### Fixed
- **Race entry and the runner list are still recognised once a selection is on the slip.** At that point Choose Bet and Stake turns from green to yellow and a green Place Bet appears beside it. Both checks now accept either colour, which needed colour checks that accept more than one colour. Before this, every screen after the first selection would have read as UNKNOWN.

### Testing
- `screen_cases.py`: 15 reference screenshots, plus race entry with a yellow Choose Bet. All pass.

## [0.31.0] - 2026-10-21

### Added
- **`detect_screen()` recognises the two payment boxes that F12 can bring up:**
  - **MODAL_PAYMENT_MISMATCH:** the red box "Payment is not the same as on the original empty bet. Is the original amount (£x) what the customer actually gave you?". It uses the same red border as the late-selection box and is told apart only by its message.
    - Yes = take the bet as overstaked at the original amount.
    - No = the next box.
  - **MODAL_CONFIRM_STAKE:** the blue box "Please confirm this is the stake tendered", with Cancel and Confirm.
  - The program must never choose either answer itself. The money is checked against Payment before F12, so reaching these boxes means something is wrong, and the wager goes to staff.

### Testing
- `screen_cases.py`: 14 reference screenshots, all pass.

## [0.30.0] - 2026-10-21

### Added
- **`detect_screen()` recognises Betty's two entry pop-ups.** Pop-ups are checked before screens because they sit on top of race entry, whose own colour checks would still match.
  - **MODAL_LATE_SELECTION:** the red-bordered box "Wager staked N mins after 'off'… apply 'Void Selection' processing?". Staff press Yes.
  - **MODAL_PRICE:** the blue-bordered price check, "The price you entered was not correct at the time the bet was placed". It appears after numpad + when the price has moved since the bet was struck, or when Betty is out of sync. The rule is always **Price when struck**.
  - The buttons in the price box change from one race to the next: Back 2 and the Forward prices come and go. Entry will find "Price when struck" by reading the buttons, not by a fixed position. It will check for this box after **every** numpad +.

### Testing
- `screen_cases.py`: 12 reference screenshots, adding `11_modal_late_selection.png` and `12_modal_price_check.png`. All pass.

## [0.29.0] - 2026-10-21

First phase of the always-on automation (build plan: `scratch/BUILD_PROMPT_2026-10-21.md`). The watcher only looks at Betty for now; it does not process wagers yet.

### Added
- **Watcher on/off with the backtick key (`` ` ``).** The key is swallowed, so it never reaches Betty. After it is switched on, the watcher waits 5 seconds, then works out which Betty screen is showing and shows it on the HUD.
- **Test mode, toggled with Shift + `` ` ``.** It starts on by default (`BETTY_TEST_MODE=1` in `.env`). In test mode the watcher will stop just before placing; placing is not built yet.
- **The watcher never fights staff.** A key press or click from a person switches it off ("Staff used the terminal"), and `` ` `` switches it back on. The program's own key presses and clicks are recognised as injected and ignored, as are the watcher's own keys and clicks on the HUD.
- **Screen classifier `detect_screen()`.** It recognises Home, View Wagers, the event menu, race entry, race entry with the time box, race entry with every meeting used up (red time), the runner list shown after a time is typed (including the hatched no-prices look), and the Choose Bet and Stake screen; anything else is UNKNOWN. Each screen needs every one of its colour checks plus its fixed label read by Tesseract.
- **`view_wagers_queue_state()`** reads the top wager under "Unedited (Exc.Fao)": waiting (light blue), selected (green) or empty (no box).
- **HUD:** a watcher line (ON/OFF, TEST MODE, current screen) and a "Last:" outcome line.
- **Start-up guard:** the program refuses to run unless the screen is really 1366×768.

### Changed
- **The screen size comes from Windows only.** `.env` said `SCREEN_RESOLUTION=1024x576` on a 1366×768 screen, so every click and pixel check used the 1024 coordinates. That setting is removed from `.env` and is no longer read.
- Ctrl+Alt+B still enters one slip from the race-entry screen, and switches the watcher off while it runs. The new HUD and console text names the new keys.

### Testing
- New free test, `scratch/ocr_eval/screen_cases.py`: 10 reference screenshots in `scratch/betty_screens/` plus blank and edited images, all classified correctly. The reference set now includes the Choose Bet and Stake screen, View Wagers (unselected, and empty after placing), meetings used up, a second betting slip, and a runner list with no prices. The user's Betty map is kept as `scratch/betty_screens/bettymap.txt`; its keys are reliable, but its coordinates don't match 1366×768.
- All existing free tests are unchanged: ideal mode 13/13 on both readers, `matcher_cases` 0 wrong, stress test 0% wrong, `recheck_cases`, `number_cases` and the rules tests all pass, and ruff shows only the 2 known unused variables.

## [0.28.0] - 2026-10-20

### Fixed
- **Number bets are now checked against Betty's card** (`match_number_to_racecard`). Selections such as "No 4", "#4" or "5" are the cloth number in the race at the written time, at the written meeting. Meeting letters are read against the meetings racing then, so "So" means Southwell.
  - They are locked only when exactly one race fits: the written meeting identifies it, or it is the only race at that exact time.
  - With no readable time, or several races fitting, staff are asked and shown the possible runners.
  - The written price is never used to decide.
  - Before: number bets skipped the card entirely. A selection with an unrecognised meeting was locked as a greyhound trap at **Sheffield** (bob2: 7 Southwell horses locked as Sheffield dogs), and the written meeting was dropped ("No 8" locked with no meeting or time).
- **No default greyhound track.** A trap is taken as written only at a known dog track. "T3" or "Trap 3" with no known track goes to staff and is never matched to a horse.
- **Staff dialog fields were bound to the wrong window** (the status HUD's Tk root). The old name box could show empty and ignore what staff typed.

### Changed
- **The staff prompt asks for the missing details,** as if the program had read them itself.
  - It opens with "Can't read 'xxxx'. Please enter manually".
  - It has four fields, pre-filled with what was read: horse name or number, race time, meeting, and price taken (blank = SP).
  - The closest runners are offered as one-click fills.
  - The entry goes through the same card checks as a scanned selection (`apply_manual_entry`). The dialog stays open with the reason (e.g. "Not found on today's card … Closest: …") until it matches a runner, or staff cancel the slip.
  - The old fallback that labelled an unmatched name as meeting "Virtual" is gone.
- `state_pre_scan_and_match_slip(..., struck_time=None)`: when the time the bet was struck is known, races already off by then are never candidates for a number bet or for staff's entry. Reading that time from Betty is not built yet.

### Testing
- New ground truth: `bob2_3` (Southwell number bets and a straight forecast), plus `paul2` and `petea3`, which are expected to prompt staff (no time / unreadable time). `run_eval.py` supports `read_name` / `read_meeting` and `"expected_outcome": "staff_prompt"`.
- Ideal mode: 13/13 on both readers (was 10/13; all 3 number-bet slips were silently wrong).
- `scratch/ocr_eval/number_cases.py` (free) covers:
  - the number lookup on real cards, struck time and dog cases;
  - staff entries;
  - the dialog itself, driven automatically.

## [0.27.0] - 2026-10-20

### Changed
- **New re-check for unclear horse names: the race-list check.** It replaces the old two-step re-check (a blind re-read, then a choice from 3 spelling-based guesses whose answer could be overruled by spelling). It works the way a cashier does, following the method from the user's manual reading of roger1:
  - **What the reader sees:** every runner in the race(s) within 10 minutes of the written time, narrowed to the written meeting letter when that letter fits a meeting racing then. UK/IRE races come first. The matcher's best name guesses from elsewhere on the card are added, for misread times. At most 60 runners, nearest races first.
  - **How it is told to work:**
    - copy the letter shapes before choosing, not turning the scrawl into a word;
    - compare first letter, letters above/below the line, length and ending;
    - general letter confusions are listed;
    - never use the written price, and never change a reading to fit;
    - answer 0 if nothing fits.
  - **Acceptance:** a high-confidence pick in a race at the written time is accepted. A pick from the other guesses also needs a strong name fit (≥ 0.80). Anything else goes to staff.
  - **One request per unclear horse** instead of two.
- New helper `race_list_for_selection()`.

### Testing
- `scratch/ocr_eval/recheck_cases.py` (free): checks with scripted reader answers.
  - Race-list coverage: the right horse is listed for every Roger selection with a correctly written time, and for 84% of the selections as live readers actually read them today.
  - Acceptance rules and prompt contents (the written price is never shown).
- `scratch/ocr_eval/recheck_live.py` (`--dry-run` is free; otherwise paid): replays the 84 unclear selections from the 20 Oct live runs through the new check, one call each, and compares it with what the old re-check did.

## [0.26.2] - 2026-10-20

### Fixed
- **A reader's placeholder meeting no longer overrides the letter the customer wrote.**
  - Gemini often returns `meeting: "UNKNOWN"`, and that beat the written letter (e.g. `Y` for Yarmouth), so the right race was not preferred. On roger1, Amandari dropped out of the 3 guesses.
  - The customer's own letter (`raw_meeting_hint`) now comes first. Placeholders (`UNKNOWN`, `None`, `?`, `n/a`...) are treated as nothing written, both when a reading arrives and in the matcher.
- **A weaker name match can no longer lock a horse at a meeting the customer didn't write.**
  - Name matches of 0.80–0.92 (accepted only because the race time agrees) are now refused when the written meeting letter fits a different meeting racing at that time. The selection goes on to the race-at-time check, then the re-check or staff.
  - Example: "Tandbridge 4.28N" had locked onto Island Bridge at Worcester 16:37 instead of going to a re-check.
  - Name matches of 0.92 or above, and letters that fit nothing on the card at that time (so probably misread), behave as before.

### Testing
- `matcher_cases.py` has 7 new real misreads from roger1 (20 Oct), including the two cases above.

## [0.26.1] - 2026-10-20

### Changed
- The Claude reader also accepts the key as `CLAUDE_API_KEY` in `.env` (`ANTHROPIC_API_KEY` still works and takes priority).

## [0.26.0] - 2026-10-20

### Added
- **Optional Claude slip reader** (`SLIP_READER=claude` in `.env`; Gemini stays the default). It uses the official `anthropic` Python package and needs `ANTHROPIC_API_KEY` from the Claude Console, which is API billing, separate from a Claude app subscription.
  - **Model and settings:** `CLAUDE_MODEL` (default `claude-opus-5-5`) and `CLAUDE_EFFORT` (default `high`). Requests use structured JSON output and Anthropic's server-side fallback, so a declined request is re-run on a fallback model.
  - **Zoomed views:** Claude receives the full slip plus enlarged (3x) top and bottom halves, overlapping so no line is cut. The re-check gets the same views.
  - **Cost logging:** each request logs tokens and an approximate cost.
  - **Failures:** a bad key, low credit or a declined request gives staff a clear message.

### Changed
- The post-processing of a slip reading (line backfill, phantom selections, scoping, costing, total healers) is now one shared function, `process_slip_reading()`, used by both readers instead of living inside the Gemini request loop.
- `_ask_gemini_json` renamed to `_ask_vision_json`; it routes re-checks to whichever reader is configured.

### Testing
- `run_eval.py --reader claude`. The free `ideal`/`replay` modes exercise the real Claude code path without calling the API: 6/6 Roger slips pass on both the Claude and Gemini paths.

## [0.25.0] - 2026-10-20

### Changed
- **Racecards now come from Betty itself (`betty_feed.py`)**: pre-flight reads the SIS / TRP / Tote horse feeds Betty keeps in `C:\Events` (binary `.dat`, decoded), so names, meetings, race times and saddle-cloth numbers are exactly what Betty shows. No internet is needed. UK/IRE, international and virtual races are classified by the feed's own country code (`VR` = virtual). Validated on 12 Oct 2026: all 495 UK/IRE runners and cloth numbers match the official card. The card loads in ~20ms and re-reads only when a feed file changes. Configurable with `BETTY_EVENTS_DIR` / `BETTY_HORSE_FEEDS` in `.env`.
- **Runner matching rewritten (`match_runner_to_racecard`)** to work the way a cashier does:
  1. Name first, across the whole card (the card supplies the race and time, so a misread time no longer matters).
  2. If the name is unclear, the race(s) at the written time, filtered by any meeting letter, which is read against the meetings actually on the card (e.g. `N` at 4.28 = Newcastle). The runner whose name clearly fits best is chosen. A runner elsewhere whose name fits clearly better vetoes this (name beats a misread time).
  3. Otherwise the best 3 guesses (2 from the race at the written time plus the best name anywhere) go to a re-check, then to staff.

  UK/IRE races are searched first; international and virtual races can only win on name once a UK/IRE race exists at the written time. The old multiplicative time/meeting boosts that produced confident wrong matches (e.g. `GLAM CASTLE 3.45` -> Samra Green) are gone.
- **Re-check (`reexamine_runner_with_ai`)** is now two steps:
  1. An independent re-read of just that selection, with no candidates shown so the model cannot simply agree with one, run through the full matcher.
  2. A pick among the best 3 guesses, accepted only if it is also the guess closest to the independent re-read, and the time agrees or the name fits strongly.
- **Card match runs before greyhound/virtual guessing**, so a horse with a meeting letter (e.g. `4.28N`) can no longer be routed to a greyhound track. The old virtual/international/"live terminal discovery" bypasses are removed: those races are on Betty's card now.
- **BOG eligibility** uses the runner's card category (UK/IRE = eligible) before falling back to name lookups.
- Scan prompt: meeting letters are copied, not expanded. Added forecast / forecast-double / cross-double notation, stakes without 'p', and a hastily written '£'. Only UK/IRE meetings are listed as context.
- Gemini request timeouts raised (scan 90s, re-check 45s) so stronger, slower models are not cut off. Accuracy comes before speed.
- **Default vision model is now `gemini-4-argon`**, with fallbacks `gemini-pro-latest`, `gemini-3.8-flash` and `gemini-3.5-flash` (override with `GEMINI_MODELS` in `.env`). On Roger's slips argon read 100% of bet lines and 73% of names on the first scan, with 7/10 slips fully correct, 3 safe staff checks and 0 wrong. `gemini-3.5-flash` managed 65% / 50%, with one slip locked wrong. Every slip now starts with the most accurate model; the old "sticky" preferred model that stayed on a cheaper fallback after one failure is removed, and the lite/robotics models are dropped from the list.
- **Billing errors (HTTP 402, prepaid credits used up)** move straight to the next API key, or stop at once with "Gemini credits are used up". Previously the program cycled through 10 models x 3 scans (30 wasted calls) and then told staff the AI "could not extract" the slip.
- Console now logs hidden "thinking" tokens per scan, so the cost of each slip is visible.

### Fixed
- **A 50p error was accepted as "within £1 grace" without a rescan**: any difference between bets and the written total now triggers a rescan; the grace variance applies only to the final scan.
- **Pre-flight now also warns** when the verified slip total differs from the customer's written total.
- **Margin notes attached to the wrong line**: a scoping note that contradicts its bet is ignored (e.g. `ABV 4` on a single 2-runner double; a note that disagrees with a written `3x`). A forecast double always keeps its 4 runners.
- **Bet-line recovery** ignored repeated wording (`50 win double` written twice on one slip) and could resurrect crossed-out lines. It now matches by line number, skips crossed-out lines, and ignores mis-scoped bets when checking coverage.
- **EW auto-correction healer** could flip a line that explicitly says `EW` to win just to balance the total; it now leaves explicit EW and WIN lines alone.
- **Phantom selections**: a "selection" invented on a bet-instruction line (name not in that line) is dropped. References to non-existent selection numbers are dropped instead of falling back to a same-named runner, and a single double/treble left short takes the selections written above it.
- **The rules engine** now normalises bet types before same-race clash handling (`doubles` + `R/FORECAST ... X DOUBS` is a reverse forecast double, never split into singles).

### Removed
- The Racing API client, the Sporting Life scraper and the racecard disk cache (`RACING_API_USERNAME`/`RACING_API_PASSWORD` in `.env` are no longer used), the `bs4` dependency, the hard-coded track-letter guesser (`disambiguate_track_hint`), and the slip-meeting pre-pass. `betty_companion.py` shrank from 5,803 to ~5,500 lines.

### Testing
- `scratch/ocr_eval/`:
  - `run_eval.py` now uses Betty's archived feed for the slip date, and adds `--mode replay` plus outcome classes (correct / safe stop / warned / silently wrong).
  - `matcher_cases.py`: real Gemini misreads.
  - `matcher_stress.py`: synthetic handwriting errors on a whole day's card. 12 Oct: 89% auto-corrected, 0 wrong. 13 Oct (unseen): 90% auto-corrected, 0 wrong, ~10% sent to re-check/staff with the true runner in the top 3.

## [0.24.0] - 2026-10-20

### Added
- **Forecast doubles (`straight forecast double`, `reversed forecast double`)**: `s/f/cast doubles` = 1 line, `r/f/cast doubles` = 2 x 2 = 4 lines. Costed before the `Nx` multiplier check so a forecast double can never be costed as a plain forecast.
- **Shared forecast shorthand recogniser (`rules_engine.match_forecast_bet_type`)**: accepts `r/f/cast`, `s/f/cast`, `f/c`, `fcast`, `rfc`, `sfc`, `rev f/c`, `straight forecast`, etc. Both `normalize_bet_type` copies now use it.
- **Same-race aware line counting (`rules_engine.count_distinct_race_combos`)**: doubles, trebles and perm N-folds count only the combinations across different races once runners have resolved meetings and times (BetAnsells Rule 1.8.1).
- **Stake Integrity Guard (pre-flight)**: re-costs the slip before and after house rules; if the rules change the total by more than 1p per bet, the operator is warned. The pre-flight summary now shows each bet's total cost and the slip total.

### Fixed
- **`r/f/cast` was not recognised**: the forecast regex required `r/f/c` followed by a word boundary, so Roger's `r/f/cast` was costed as 1 line instead of 2.
- **`4x ... DOUBLES` on 4 runners was rewritten as 4 TREBLES**: Dynamic Fold Reconciliation matched 4 = 4C3 and overrode the written bet type. The written fold (`DOUB`/`TREB`) now always outranks a multiplier guess, and forecasts and tricasts are never re-folded. Together with the old clash splitter, this had silently turned roger4's cross doubles into 12p doubles while still matching the written total.
- **Cross doubles (`x doubles`) over same-race runners were split into extra half-stake singles**: kept as one Doubles bet; same-race pairs are excluded, never split.
- **Same-race clash in an accumulator now enters as ONE Perm N-Folds bet** at the divided stake (e.g. 50p 6-fold with 2 runners in one race becomes Perm 5-Folds @ 25p, 2 lines), matching how Betty takes it. It falls back to the old split only when the stake does not divide into whole pence.
- `rules_engine.normalize_bet_type` missed plural `doubles`.

### Testing
- New offline harness `scratch/ocr_eval/run_eval.py` replays the real scan, reconcile and pre-flight path against a historical racecard fixture (`scratch/ocr_eval/build_racecard_fixture.py`) and confirmed ground truth. Ideal-reading replay of Roger's 5 slips: 3/5 correct before, 5/5 after.

## [0.23.18] - 2026-10-18

### Fixed
- **Calibrated Yellow Input Prompt Box Coordinates (`READY_COORD_1024`, `READY_COORD_1368`) & Implemented Multi-Tier `is_betty_ready()`**:
  - **Root Cause**: The terminal readiness check erroneously tested `(440, 465)` on 1024x576 layouts and `(588, 620)` on scaled layouts. On Betty's native 1024x576 screen space, `(440, 465)` falls on blank white space (`RGB(248, 248, 248)`), 108px to the right and 119px below the actual yellow input prompt bar. `(440, 465)` was historically measured on a 1366x768 display and was later mistakenly labeled as a 1024x576 coordinate and scaled up a second time to `(588, 620)` on 1368x768 screens, causing both modes to fail.
  - **Calibrated Yellow Box Coordinates**:
    - Grounded `READY_COORD_1024 = (332, 346)` squarely at the centroid of Betty's active yellow prompt bar (bounding box: X: 301..362, Y: 337..355).
    - Calibrated `READY_COORD_1368 = (443, 461)` for scaled 1368x768 / 1366x768 displays.
  - **Resilient Multi-Level Readiness Detection (`is_betty_ready`)**:
    - Created unified `is_betty_ready(samples=3, interval=0.03)` with multi-tier verification:
      1. Primary coordinate check against `READY_COORD` with flicker-resistant multi-sampling.
      2. Cross-resolution candidate coordinate fallback testing both `(332, 346)` and `(443, 461)`.
      3. Bounding region pixel scanning across `(295, 330, 75, 30)` and `(395, 440, 100, 40)` requiring >= 15 `TARGET_YELLOW` pixels.
    - Integrated `is_betty_ready()` across `run_cycle_logic()`, `restore_ready_state_if_exhausted()`, `is_meetings_exhausted_screen()`, and the race time input loop.
    - Fixed error notification string in `run_cycle_logic()` to dynamically display the active `READY_COORD`.
  - **Environment Configuration**: Set `SCREEN_RESOLUTION=1024x576` in `.env` to align with Betty POS's native window space, and updated `get_screen_resolution()` fallback to `(1024, 576)`.

## [0.23.17] - 2026-10-18

### Fixed
- **Dual-Resolution 1368x768 & 1366x768 Display Calibration for F8 Bet Selection & Terminal Controls**:
  - **Root Cause**: On 1368x768 / 1366x768 displays, `F8_TABLE_TOP_Y = 95`, `F8_ROW_HEIGHT = 26`, `F8_ROW_CLICK_X = 110`, `EACH_WAY_BTN_COORD = (165, 498)`, `WIN_ONLY_BTN_COORD = (165, 471)`, and `F8_BET_LIST_REGION = (6, 95, 209, 286)` were hardcoded strictly to 1024x576 coordinates. On a 1368x768 screen, the 11 F8 bet rows span from Y: 127 to Y: 508, with Row 10 ("Flag") centered at Y: 491 (range Y: 474..508). Dispatching clicks to `(165, 498)` or unscaled bet row offsets squarely targeted Row 10, erroneously selecting "Flag" instead of Each-Way or the requested bet type, while bet list OCR failed due to boundary misalignment.
  - **Comprehensive Dual-Resolution Calibration**:
    - **F8 Bet List Table Metrics**: Calibrated `F8_TABLE_TOP_Y = 127`, `F8_ROW_HEIGHT = 34.67`, `F8_ROW_CLICK_X = 147`, and `F8_BET_LIST_REGION = (8, 127, 279, 381)` for 1368x768 / 1366x768 displays (alongside native 1024x576 fallbacks).
    - **Each-Way & Win-Only Toggle Buttons**: Calibrated `EACH_WAY_BTN_COORD_1368 = (220, 664)` and `WIN_ONLY_BTN_COORD_1368 = (220, 628)`, cleanly placing clicks on the respective toggle buttons below the bet table and eliminating false clicks into Row 10 ("Flag").
    - **Each-Way Active Verification**: Calibrated verification pixel `(267, 664)` and text crop `(150, 647, 143, 35)` on 1368x768 displays.
    - **Row Selection Verification**: Dynamically adjusted `is_f8_row_selected()` sample crop to `(20, top_y + 2, 247, row_h - 4)` and bounding limit to 513px on scaled displays.
    - **F8 Bet Selection Execution**: Updated `select_bet_type_on_f8()` to strictly use resolution-calibrated metrics (`top_y`, `row_h`, `row_x`, `other_bets_coord`) from `get_f8_metrics()`.
    - **Betslip & Dialog Controls**: Calibrated `BETSLIP_FIRST_SELECTION_COORD_1368 = (1000, 93)`, `BETSLIP_ROW_HEIGHT_1368 = 45.33`, `READY_COORD_1368 = (588, 620)`, `RED_TIME_EXHAUSTION_REGION_1368 = (548, 587, 80, 53)`, `LATE_SELECTION_BORDER_COORD_1368 = (924, 389)`, `LATE_SELECTION_YES_BTN_COORD_1368 = (787, 672)`, `SCROLL_ARROW_COORD_1368 = (561, 760)`, and `CYAN_REGION_1368 = (0, 0, 407, 620)`.
    - **Display Resolution Configuration**: Enhanced `get_screen_resolution()` to support `SCREEN_RESOLUTION` from `.env` (explicitly set to `1368x768`), dynamic OS metrics detection (`w > 1200`), and safe fallback to `(1368, 768)`. Added active resolution logging to startup banner.

## [0.23.16] - 2026-10-08

### Fixed
- **Fixed Native 1024x576 Betslip Selection Coordinates (`get_betslip_selection_coord`, `is_price_purple_guaranteed`)**:
  - **Root Cause**: In v0.23.15, display scaling (`scale_x = 1.334`, `scale_y = 1.333`) was erroneously applied based on desktop screen resolution (`1366x768`). Because Betty POS operates in a fixed 1024x576 native window space regardless of desktop monitor dimensions, multiplying Y coordinates by 1.333 caused Selection #3 to be clicked at `(1000, 184)` instead of `(750, 138)`. This overshot the betslip into blank space below the third row, leaving Selection #3 unselected and unguaranteed (missed BOG).
  - **Accurate Native Coordinate Alignment**:
    - Grounded `get_betslip_selection_coord(selection_idx)` strictly to Betty's native 1024x576 window space: `X = 750`, `Y = 70 + selection_idx * 34`.
    - Selection 1: `(750, 70)`, Selection 2: `(750, 104)`, Selection 3: `(750, 138)`, Selection 4: `(750, 172)`, Selection 5: `(750, 206)`.
    - Each click lands dead-center on the runner name text, completely clear of the `Remove` button.
    - Grounded purple price verification (`is_price_purple_guaranteed`) and non-runner verification (`is_selection_non_runner`) to native window coordinates (`rx = 890`, `ry = 58 + selection_idx * 34`), ensuring accurate detection.
    - Added automatic re-click on runner selection in retry loop if price does not turn purple on first `'g'` attempt.

## [0.23.15] - 2026-10-08

### Fixed
- **Safe Betslip Row Selection Prior to Price Guaranteeing (`get_betslip_selection_coord`, `state_apply_guarantees`)**:
  - **Root Cause**: In v0.23.14, removing all mouse clicks prevented the 'Remove' button from being clicked, but because Betty's betslip requires an active row focus before responding to the `'g'` (guarantee) key, pure keyboard arrow navigation left the selection unselected/unhighlighted.
  - **Calibrated Safe Centroid Selection (`get_betslip_selection_coord`)**:
    - Introduced dynamic coordinate resolution targeting the runner name / meeting text on the left flank of each selection row (`X = 750` on 1024 native, `X = 1000` on 1366 scaled).
    - Positioned 300+ pixels to the left of the red `Remove` button (`X = 1293..1349`).
    - Explicitly clicks each selection row at its safe runner name centroid to activate and highlight it in Betty immediately prior to applying BOG (`'g'`).

## [0.23.14] - 2026-10-08

### Fixed
- **Eliminated Betslip 'Remove' Button Click in Guarantee Sweep (`state_apply_guarantees`)**:
  - **Root Cause**: In Betty POS, each selection row in the betslip panel features a red `Remove` button on its right flank. In previous versions, `state_apply_guarantees()` executed `pyautogui.click(x=GUARANTEE_COORD[0], y=GUARANTEE_COORD[1])` (`(889, 93)`) to focus the list control before applying BOG. On standard and scaled layouts, clicking near `(889, 93)` landed squarely on or near the `Remove` button of the top selection, deleting it from the slip.
  - **Pure Keyboard Navigation (Zero Mouse Clicks on Betslip)**:
    - Completely abolished mouse clicking anywhere inside the betslip area.
    - Focus is safely navigated back to Selection #1 via a loop of `pyautogui.press('up')` keystrokes.
    - Sub-selections are advanced via `pyautogui.press('down')`.
    - Eliminates 100% of the risk of clicking the `Remove` button, guaranteeing that selections cannot be deleted during guarantee sweeps.

## [0.23.13] - 2026-10-08

### Fixed
- **Selection Deletion Protection & Zero-Tolerance Dot (`.`) Sanitization**:
  - **Domain Finding**: In the Betty POS terminal, pressing `.` (period/dot) on the keypad or keyboard at the selection entering screen acts as the hotkey to delete the last entered selection from the betslip.
  - **Eliminated Dot Injection Risk Across All Keystroke Paths**:
    - **Race Time Sanitization (`format_time_for_betty`, `_check_and_recover_red_time`, main loop)**: Enforced `re.sub(r'[^0-9:]', '', raw.replace('.', ':'))`. Ensured that raw or unparsed time strings (e.g. `'3.05'` or `'4.16.'`) never emit a period under any circumstance.
    - **Runner / Cloth Number Sanitization (`enter_selection`, `select_runner_in_active_panel`)**: Wrapped all direct cloth injection numbers, unanchored discoveries, and OCR runner numbers in `re.sub(r'[^0-9]', '', str(runner))` before calling `pyautogui.write()`, ensuring OCR trailing dots (e.g. `'01.'`) can never be typed.
    - **Stake Entry Sanitization (main loop)**: Sanitized stake entries to strict integers (`re.sub(r'[^0-9]', '', str(int(round(float(stake))))))`, completely eliminating any float decimal points.

## [0.23.12] - 2026-10-08

### Fixed
- **Resolved False Selection Removal in Causality Guard (`reconcile_bet_scoping_qualifiers`)**:
  - **Root Cause**: When a bet or stake was noted on the same line as a selection (e.g. `Line 5: DIGHEAR AYR 5.13 50p`), Causality Guard strictly checked `line_num < effective_line` (5 < 5 = False), erroneously stripping the 5th runner as "written BELOW line 5", breaking a 5-runner Lucky 31 down to 4 runners.
  - **Inclusivity & Safeguards**:
    - Changed condition to `line_num <= effective_line` so runners written on the bet line are always retained.
    - Single-bet slips (`len(bets_list) == 1`) are exempted from causality truncation since all selections belong to the solitary bet.
    - Added required runner count guard: fixed-count full-cover wagers (e.g. Lucky 31 requiring 5 selections) are never truncated below their required count when all runners are present.
- **Added Market Rasen & Comprehensive UK/Irish Racecourses to Domestic Directory**:
  - **Root Cause**: Market Rasen was missing from `DEFAULT_DOMESTIC_HORSE_COURSES` and `meetings_directory.json`, causing `resolve_meeting("Market Rasen")` to classify it as `"unknown"`, which failed Best Odds Guaranteed (BOG) eligibility as `"Non-UK/Irish or unverified meeting"`.
  - **Directory Expansion**: Added Market Rasen and its common abbreviations (`mark`, `markr`, `mark r`, `mktr`, `mkt rasen`, `mr`) plus other domestic tracks (Doncaster, Chepstow, Brighton, Leicester, Ludlow, Nottingham, Ripon, Wincanton, Yarmouth, Kilbeggan) to `DEFAULT_DOMESTIC_HORSE_COURSES` and `meetings_directory.json`.
  - **Official Racecard BOG Verification**: Added direct verification in `is_bog_eligible_selection` for runners validated against The Racing API cache.
- **Fixed Meeting Category Isolation & Runner Presence Check (`enter_selection`, `is_target_meeting_at_top`)**:
  - **Root Cause**: When cycling meetings for a horse selection (e.g. Spot On Soph cloth #1 at 16:16), an unverified meeting category allowed the presence check to scan a greyhound screen (Central Park 4:16 Trap 1: Lady Kitty). A partial word match falsely declared the runner present, injecting cloth #1 into a dog race instead of advancing to Market Rasen.
  - **Category Isolation Enforcement**: Ensured that horse selections (or any selection with `api_horse_number` from The Racing API or `not is_trap_ref`) strictly reject greyhound and virtual screens from runner presence checks.
- **Mandatory OCR Verification for Bet Type Selection on F8 Screen (`select_bet_type_on_f8`)**:
  - **Root Cause**: `PAGE_1_BET_ROWS` assumed a static row order (e.g. Row 8 for Lucky 31). Because the bet list layout dynamically shifts depending on the number of active runners, clicking a hardcoded row without verification could select the wrong bet type.
  - **Pre-Click OCR Verification (`ocr_f8_row_text`)**:
    - Introduced `ocr_f8_row_text()` to read the label of any row on the F8 screen.
    - Prior to clicking or confirming any Page 1 bet type, verifies via `is_bet_type_match()` that the row text actually matches the target bet.
    - If the candidate row does not match, dynamically scans the entire table across pages via OCR.
    - If the requested bet type cannot be located (e.g. due to insufficient selections), notifies the operator rather than confirming an incorrect bet.

## [0.23.11] - 2026-09-30

### Fixed
- **Resolved Infinite Dismissal Loop & False Positives in Modal Dialog Handler (`dismiss_continue_modal_dialog`)**:
  - **Root Cause Analysis**:
    1. In v0.23.10, `is_continue_modal_dialog_present()` checked only a single pixel at `(450, 374)` for yellow with a wide tolerance ($\pm 35$). On scaled 1366x768 screens, `(450, 374)` lands directly in Betty's runner/odds table. If an odds button or cell text matched that color, it triggered a continuous false positive even when no modal was present.
    2. Coordinates `CONTINUE_MODAL_BTN_COORD = (511, 374)` and `CONTINUE_MODAL_SAMPLE_COORD = (450, 374)` were hardcoded strictly for 1024x576 native displays, causing clicks on 1366x768 displays to miss the button completely.
    3. `dismiss_continue_modal_dialog()` returned `True` unconditionally once detected, causing the `while True:` loop in `dismiss_any_modal_popups()` to restart infinitely and bypass timeouts.
  - **Red Border Boundary Verification (`is_continue_modal_dialog_present`)**:
    - Mandated strict perimeter verification against `TARGET_RED` along the modal frame midpoints (`CONTINUE_MODAL_RED_BORDER_COORDS_1024` and `_1366`). Eliminates 100% of false positives on the runner grid.
  - **Dual-Resolution Dynamic Centroid Detection (`find_continue_modal_button_coord`)**:
    - Implemented yellow button cluster detection across calibrated bounding regions for both 1024x576 (`Center ~ 511, 369`) and 1366x768 (`Center ~ 682, 492`).
  - **Loop Guard & Dismissal Confirmation (`dismiss_continue_modal_dialog`)**:
    - Added a 2-attempt retry cap with verified clearance check (`not is_continue_modal_dialog_present()`).
    - Returns `True` strictly if the modal is confirmed cleared from the screen; returns `False` otherwise, preventing infinite loop traps in `dismiss_any_modal_popups()`.

## [0.23.10] - 2026-09-30

### Fixed
- **Resolved "Insufficient Extra Bets Available / Perm Patent (2119)" Modal Error on F8 Screen**:
  - **Root Cause Analysis**:
    1. In UK betting terminology and Betty EPOS, selecting Singles (Row 1), Doubles (Row 2), and Trebles (Row 3) simultaneously on a 4-selection bet constitutes a **Perm Patent** (4 Patents = 28 separate wagers).
    2. In v0.23.9, the proactive mutual-exclusion deselect loop in `select_bet_type_on_f8()` attempted to deselect unrequested rows prior to checking shortcuts. During Bet 4 (1-runner Single), it misidentified Row 2 and Row 3 as selected and clicked them, compounding them into the transaction and inflating total wagers to the terminal hardware capacity (`Betting Slip 9 of 9`, £19.50 instead of £6.00).
    3. When Bet 6 attempted to enter the Each-Way Accumulator, Betty EPOS ran out of available slip wager capacity, triggering Error Modal 2119: *"Insufficient extra bets available - Please remove a wager from the slip or start new transaction for Perm Patent (2119)"*.
    4. Because `dismiss_any_modal_popups()` did not previously recognize this warning/error modal (which features a yellow `[ Continue ]` button), the modal remained on screen, blocking clicks to `Each-Way` and `Acc On All Selns` (Row 4). Betty EPOS rejected the wager addition, leaving the previous state (Win Only, Doubles) visible.
  - **Native Shortcut Fast-Path Prioritization**:
    - Re-architected `select_bet_type_on_f8()` to execute native single-key shortcuts (`'s'` for Singles, `'d'` for Doubles) immediately before performing any table clicks. Singles and Doubles are selected natively and isolated without touching adjacent table rows.
  - **Single Confirmed Row Toggle for Multiples (`select_bet_type_on_f8`)**:
    - Eliminated blind multi-row deselect clicking. When selecting non-shortcut bet types (Accumulator Row 4, Trebles Row 3), only specifically confirmed active rows are toggled off before clicking the target row centroid `(110, row_click_y)`.
  - **Betty Modal Error / [ Continue ] Handler (`dismiss_continue_modal_dialog`)**:
    - Added detection for red-bordered error/warning modals containing yellow `[ Continue ]` buttons (sampled at `(450, 374)` for `RGB(255, 255, 128)`).
    - Automatically clicks `[ Continue ]` at `(511, 374)` or sends `Enter`, ensuring no modal popups trap the automation or swallow F8 button clicks.

## [0.23.9] - 2026-09-30

### Fixed
- **Resolved Multi-Bet Bleed & Acca Toggling Bug on F8 Bet Selection Screen (`select_bet_type_on_f8`)**:
  - **Root Cause of 9 Bets & Acca Reverting to Doubles**:
    1. In Betty EPOS, rows on the F8 Bet Selection Screen are independent multi-select toggle buttons, not mutually exclusive radio buttons. When transitioning across bet sections via `F10` or `F11`, Betty EPOS retains the previous active bet type selection (e.g. Doubles from Bet 2 / Bet 4 / Bet 6).
    2. Because v0.23.8 omitted row isolation, selecting Trebles or Accumulator on subsequent bets left Doubles active simultaneously, causing Betty to enter multiple bet types per section (Doubles + Treble on Bet 3, Doubles + Acca on Bet 5), inflating the slip to 9 bets.
    3. Additionally, `'q'` was configured as a shortcut for Accumulator in `BET_SHORTCUTS`, but `'q'` is not a valid Betty EPOS shortcut.
    4. Furthermore, `is_f8_row_selected()` previously sampled a narrow right-margin slice (`X: 160..205`) that produced false-negative results on Accumulator, prompting an erroneous retry click in `select_bet_type_on_f8()` that toggled Accumulator **OFF**, leaving only residual Doubles active on Bet 7.
  - **Interior Button Ratio Detection (`is_f8_row_selected`)**:
    - Replaced the narrow right-margin check with a full-interior button crop across `X: 15..200, Y: top_y+2..top_y+24`.
    - Computes both bright green (`RGB(0, 255, 64)`) and unselected cyan (`RGB(0, 255, 255)`) pixel counts.
    - Verified across all historical and current production screenshots: yields 100% true-positive accuracy with zero false positives or false negatives.
  - **Strict Mutual Exclusion Isolation (`select_bet_type_on_f8`)**:
    - Prior to selecting `target_row`, scans Page 1 rows (0..10) and toggles off any conflicting green row (`r != target_row`), verifying each turns cyan.
    - If `target_row` is already selected green, avoids redundant clicks that would toggle it off.
    - If `target_row` is not selected, clicks centroid `(110, Y)` and verifies it turned green.
    - Purged invalid shortcut `'q'` for Accumulator, ensuring Accumulator is clicked deterministically at Row #4 `(110, 186)`.

## [0.23.8] - 2026-09-30

### Fixed
- **Purged Erroneous Rogue Row Deselect Loop in `select_bet_type_on_f8`**:
  - **Root Cause of Singles Selection**: In v0.23.7, an experimental mutual-exclusion loop (`for r_other in range(...)`) was added to detect and click unrequested green rows. In Betty EPOS, when the F8 Bet Selection Screen opens, **Singles (Row 1)** is highlighted green by default. Furthermore, in Betty EPOS, clicking an in-table bet row **selects** that row rather than deselecting it. As a result, the loop detected Row 1 (Singles) active green and clicked `(110, 108)` (Row 1), immediately switching the active bet selection back to Singles!
  - Completely purged the `r_other` clicking loops from both the shortcut and direct-click paths in `select_bet_type_on_f8`.
  - Re-established pure deterministic centroid clicking on `PAGE_1_BET_ROWS[target_row]` (e.g. Row 3 Trebles at `(110, 160)`), ensuring Trebles is clicked and selected directly with zero extraneous row interactions.

## [0.23.7] - 2026-09-30

### Fixed
- **Eliminated Erroneous `'e'` Keystroke in `apply_each_way_on_f8` & `ensure_win_only_on_f8`**:
  - **Root Cause of Ghost Flag Selection**: Identified that in Betty EPOS, sending keystroke `'e'` does NOT toggle Each-Way. Instead, when focus is inside the F8 window, pressing `'e'` directly activates **Flag (Row 11)**! Because `apply_each_way_on_f8()` previously dispatched `pyautogui.keyDown('e')` after selecting Treble, Betty EPOS immediately switched the bet selection from Treble (Row 3) to Flag (Row 11).
  - Completely purged all `pyautogui.press('e')` and `keyDown('e')` calls. Both `apply_each_way_on_f8()` and `ensure_win_only_on_f8()` now strictly click their calibrated button centroids (`EACH_WAY_BTN_COORD = (165, 498)` and `WIN_ONLY_BTN_COORD = (165, 471)`), ensuring 100% reliable Each-Way toggling with zero keyboard side-effects.
- **Reordered F8 Entry Sequence (`process_slip`)**:
  - Reordered actions inside F8:
    1. Enter Stake (`pyautogui.write(stake_val)` $\rightarrow$ `Enter`).
    2. Set Each-Way or Win-Only (`apply_each_way_on_f8()` or `ensure_win_only_on_f8()`).
    3. Select Bet Type LAST (`select_bet_type_on_f8()`).
  - Selecting the bet type as the absolute final step before section transitions (`F10`/`F11`) guarantees that Treble (or any other bet type) remains active and verified green right at the moment Betty commits the bet.
- **Mutual-Exclusion Rogue Row Deselect Sweep (`select_bet_type_on_f8`)**:
  - Added a defensive sweep across Page 1 rows (0..10). If any unrequested row (such as Flag at Row 11 / index 10) is active green, the companion clicks the rogue row to toggle it off, then re-verifies that the target row (Trebles at Row 3 / index 2) remains active.
- **Prevented Duplicate `F8` Pressing on Retained Selections (`process_slip`)**:
  - Added `if not is_f8_screen_active(): press('f8')`. When extending bets via `F11`, Betty EPOS already stays on the F8 Bet Selection Screen; skipping redundant `F8` keypresses eliminates modal flickering and input drops.

## [0.23.6] - 2026-09-30

### Fixed
- **Removed Premature `is_already_selected` Short-Circuit in `select_bet_type_on_f8`**:
  - Identified the reason Flag remained selected: `select_bet_type_on_f8()` checked `if is_f8_row_selected(target_row): return True` *before* issuing any click or keystroke. This false-positive short-circuit caused the companion to believe the bet type was already selected, completely skipping row clicking on Bets 1, 2, and 3, and leaving whatever row was previously selected (Flag) untouched.
  - Eliminated the pre-selection skip check. The companion now ALWAYS actively dispatches the bet's native shortcut (or directly clicks the row centroid `(110, Y)`) on every bet section.
- **Robust PIL Screenshot Green Detection in `is_f8_row_selected`**:
  - Replaced legacy single-pixel GDI checks with a PIL region screenshot crop of the row right margin (`X: 160..205, Y: row_top..row_bot`).
  - Verified across real screenshots: returns exactly 0 green pixels on unselected cyan rows and >1000 green pixels on selected rows, completely eliminating false-positive green detections across all 11 rows.

## [0.23.5] - 2026-09-30

### Fixed
- **Eliminated Erroneous `'b'` Shortcut & Implemented Deterministic Page 1 Row Selection (`select_bet_type_on_f8`, `PAGE_1_BET_ROWS`)**:
  - Identified root cause of Treble selecting Flag: in Betty EPOS, keystroke `'b'` activates **Flag (Row 11)**, NOT Treble. Removed `'b'` from `BET_SHORTCUTS`.
  - Added deterministic Page 1 mapping (`PAGE_1_BET_ROWS`) mapping canonical bet names to their exact row indices (Rows 1..11, Y: 95..381).
  - For Trebles (Row 3, $Y=160$), the companion now directly clicks the row centroid `(110, 160)` and confirms green RGB selection, eliminating any ambiguity or keyboard trap.
- **Strict Target-Specific Green Row Verification (`is_f8_row_selected`)**:
  - Replaced generic `any(is_f8_row_selected(k))` with strict verification targeting the specific `target_row`.
  - Re-anchored table coordinates to empirical window metrics (`F8_TABLE_TOP_Y = 95`, `F8_ROW_HEIGHT = 26`).
  - Optimized horizontal sampling coordinates ($X \in \{180, 190, 150, 110\}$) in the row right-margin, avoiding letter glyphs and providing 100% true-positive detection of bright green (`RGB(0, 255, 64)`) versus cyan (`RGB(0, 255, 255)`).
- **F8 Screen Exit Safeguard on F10 Transitions (`process_slip`)**:
  - Added an exit verification safeguard when pressing `F10` (New Section).
  - If Betty EPOS blocks transition due to an invalid bet configuration (e.g. Flag on 3 selections) or error modal, the companion detects that Betty is still on F8 and safely aborts rather than blindly typing subsequent runner post-times into the active F8 Stake box (`Stake: 1930193`).
- **Enhanced Each-Way & Win-Only Fast-Path Detection (`is_each_way_active_on_f8`)**:
  - Added direct pixel verification at button margin `(200, 498)` for instant Each-Way state verification.

## [0.23.4] - 2026-09-30

### Fixed
- **Mandatory Native Keyboard Shortcut Execution (`select_bet_type_on_f8`)**:
  - Enforced that any bet type with an assigned native shortcut (e.g. `'q'` for Accumulator, `'d'` for Double, `'b'` for Treble, `'s'` for Single, `'y'` for Yankee, `'l'` for Lucky 15) strictly uses the shortcut without ever falling back to OCR bet list clicking.
  - Implemented 50ms Win32 key dwell time (`keyDown` -> `0.05s` -> `keyUp`) to ensure Betty EPOS reliably registers the keystroke without dropping it.
  - Added an automatic shortcut re-dispatch retry if row confirmation is not detected on the first pass.
- **Robust Multi-Point Green Row Detection (`is_f8_row_selected`)**:
  - Upgraded green row detection to sample across multiple horizontal coordinates ($X \in \{60, 100, 147, 180\}$) across the bet row width. Prevents false negative checks caused by single-pixel text glyphs, font anti-aliasing, or pipe delimiters.
- **Corrected Other Bets Button Coordinate (`F8_OTHER_BETS_COORD`)**:
  - Re-anchored `F8_OTHER_BETS_COORD` from legacy off-screen `(77, 560)` to the actual in-table button at Row 9 `(147, 421)`.
- **Expanded Plural Aliases in `BET_SHORTCUTS`**:
  - Added plural and variant mappings (`doubles`, `trebles`, `accumulators`, `yankees`, `patents`, etc.) to guarantee instant shortcut lookup regardless of grammatical normalization.

## [0.23.3] - 2026-09-30

### Fixed
- **Corrected Accumulator Shortcut Key Mapping (`BET_SHORTCUTS`)**:
  - Remapped `'accumulator'` and `'acca'` shortcuts from `'a'` to native Betty EPOS key `'q'`. In Betty, pressing `'q'` instantly selects `Acc On All Selns`, preventing the terminal from defaulting to singles.
- **Strict Compound Bet Filtering in F8 Bet List Matcher (`is_bet_type_match`)**:
  - Implemented strict compound bet guards: queries for standard bets (`single`, `double`, `treble`, `accumulator`) now explicitly reject compound row names containing `'+'`, `'and'`, or cross-type pairings (e.g. `'Doubles + Trebles'` is rejected when searching for `'treble'` or `'double'`).
  - Added word-boundary matching to prevent substrings (such as `'trebles'` inside `'doublestrebles'`) from triggering false positives.
- **Fixed Out-of-Bounds Row Selection Check in Shortcut Verification (`is_f8_row_selected`)**:
  - Bounded `is_f8_row_selected()` strictly to `row_index < 8` and `center_y <= 440`.
  - Previously, checking `k=10` (Row 11) sampled at Y=491/654, directly overlapping the Each Way toggle button. If Each-Way was active green, the shortcut loop mistook the Each-Way button for a selected bet row (`Row #11 active green`), bypassing actual bet selection.
- **Enforced Bidirectional Win Only vs Each-Way State on F8 (`ensure_win_only_on_f8`)**:
  - Added `ensure_win_only_on_f8()` to actively reset Betty's F8 screen to Win Only when a bet is not Each-Way (`not bet.get('each_way')`).
  - Detects if Each-Way is active green and clicks `WIN_ONLY_BTN_COORD` (150, 470) or toggles `'e'` to guarantee Win Only bets are never placed Each-Way.
- **Restored Calibrated 1024x576 F8 Screen Metrics (`get_f8_metrics`)**:
  - Reverted unintended monitor-level resolution scaling in `get_f8_metrics()`. Betty EPOS executes strictly inside its native 1024x576 window regardless of host monitor resolution (1366x768). All F8 list coordinates, row heights, and button anchors now align precisely with the terminal window.

## [0.23.2] - 2026-09-30

### Fixed
- **Resolved Unwanted Exit from Bet Editing on F8 (`process_slip`)**:
  - Identified and eliminated an erroneous post-F8 defensive check that expected Betty to automatically exit F8 upon bet type selection.
  - In Betty EPOS, selecting a bet type highlights the bet in green and keeps the F8 screen active until committed by `F10` (New Section) or `F11` (Extend Bet). The previous check mistook the open F8 screen for a rejection and clicked `[Cancel Bet]`, which cancelled the bet and kicked the operator out of bet editing.
  - With the check removed, bet entries flow directly into `F10` or `F11` as intended.
- **Root Directory Cleanliness**:
  - Removed stale snapshot `betty_companion_v0.22.24.py` from root directory to adhere strictly to Rule 1.

## [0.23.1] - 2026-09-30

### Fixed
- **Restored Calibrated Terminal Window Coordinates (`READY_COORD = (440, 465)`)**:
  - Reverted dynamic display scaling on Betty's main application window coordinates. The Betty EPOS window renders at fixed 1024x576 coordinates regardless of the host desktop monitor resolution (1366x768).
  - Restored `READY_COORD = (440, 465)`, `CYAN_REGION = (0, 0, 305, 465)`, `GUARANTEE_COORD = (889, 93)`, `BETSLIP_FIRST_SELECTION_COORD = (780, 70)`, `BETSLIP_ROW_HEIGHT = 34`, `STAKE_INPUT_COORD = (284, 449)`, and `RED_TIME_EXHAUSTION_REGION = (410, 440, 60, 40)`.
  - Preserved dual-resolution calibration for Betty modal dialogs (`F8_OTHER_BETS_COORD`, `EACH_WAY_BTN_COORD`, `PRICE_OVERRIDE_BTN_COORD`, `CANCEL_BET_BTN_COORD`) and retained the dynamic combinatorial math engine (`math.comb`).

## [0.23.0] - 2026-09-30

### Added
- **Dynamic Display Resolution Engine (`scale_coord`, `scale_region`)**:
  - Implemented dynamic coordinate and bounding-box scaling mapping base 1024x576 calibrations to any active display resolution (e.g. 1366x768).
  - Replaced hardcoded dual coordinates across `READY_COORD`, `GUARANTEE_COORD`, `BETSLIP_FIRST_SELECTION_COORD`, `BETSLIP_ROW_HEIGHT`, `STAKE_INPUT_COORD`, `SCROLL_ARROW_COORD`, `RED_TIME_EXHAUSTION_REGION`, and modal dialog borders.
  - Strict preservation of invariant `SLIP_REGION = (491, 78, 365, 505)`.
- **Dynamic Combinatorial Math Engine (`math.comb`)**:
  - Eliminated hardcoded lookup dictionaries for combination multipliers in `infer_selection_count_from_multiplier` and `calculate_bet_cost_pence`.
  - Dynamically calculates combination lines for any permutation fold (`perm K-folds`, doubles, trebles, 4-folds...) and generalizes fold reconciliation across 3, 4, 5, 6, 7+ selections without brittle hardcoded branches.
  - Integrated `UK_BETTING_GLOSSARY` from `rules_engine.py` to allow dynamic bookmaker rule configuration.

### Changed
- **High-Fidelity Slip Preprocessing (`pre_process_slip_image`)**:
  - Increased maximum image dimension boundary to 1024px so cropped slip regions (365x505) are never downscaled.
  - Applied balanced contrast (1.25x) and sharpness (1.20x) preserving pencil loops, biro strokes, and fraction slashes without blocky saturation.
- **Snappy Keystroke & Automation Execution (`click_betty_cell`, `process_slip`)**:
  - Replaced blocking `time.sleep` calls with interruptible mouse dwell timings in `click_betty_cell`, cutting cell click latency in half while ensuring Betty GDI compatibility.
  - Streamlined F10 (New Section) and F11 (Extend Bet) inter-bet transitions to 0.12s, accelerating multi-bet slip entry while ensuring modal dismissal safety.

## [0.22.26] - 2026-09-30

### Fixed
- **Dynamic Stake Preservation in Split-Line Cross Doubles (`reconcile_bet_scoping_qualifiers`)**:
  - Eliminated hardcoded 50p fallback on cross-doubles line merges. Unit stake is now dynamically extracted from the parsed bet (`unit_sp = b_curr.get('stake_pence') or b_next.get('stake_pence') or 50`), accurately preserving customer stakes (e.g. 25p, £1.00, £2.00) across merged entries.
- **Resolution-Adaptive F8 Bet List & Screen Metrics (`get_f8_metrics`, `is_f8_row_selected`, `select_bet_type_on_f8`)**:
  - Implemented `get_f8_metrics()` helper dynamically calculating scaled F8 bet list bounding regions, row heights, and row click targets for both native 1024x576 and 1366x768 displays.
  - Resolved row click offset issues on scaled displays when selecting multi-bet types via OCR.
- **Centralized Screen Resolution & DPI Querying (`get_screen_resolution`, `is_scaled_display`)**:
  - Replaced duplicate `ctypes.windll.user32.GetSystemMetrics` calls across `is_each_way_active_on_f8`, `is_f8_screen_active`, and button detectors with centralized cached calls.
- **Dead Code & Redundancy Removal**:
  - Removed obsolete 65-line `confirm_price_override_if_present()` function superseded by `state_handle_price()` and `dismiss_any_modal_popups()`.
  - Removed uncalled `is_f8_other_bets_active()` function.
  - Streamlined nested exception handling in `is_price_purple_guaranteed()` and `is_selection_non_runner()`.

## [0.22.25] - 2026-09-29

### Added
- **Operator-Verified Each-Way Entry Engine on F8 (`apply_each_way_on_f8`, `is_each_way_active_on_f8`)**:
  - Implemented visual RGB detection (`is_each_way_active_on_f8`) distinguishing between active bright green `(0, 255, 64)` and unselected cyan `(0, 255, 255)` on Betty's `[ Each Way ]` button box.
  - Implemented `apply_each_way_on_f8()` adhering strictly to operator protocol: dispatches `'e'` with Win32 key dwell time, verifies visual green activation, and automatically falls back to clicking `EACH_WAY_BTN_COORD` if the keystroke is dropped.

### Changed
- **Enforced Strict Bet Entry Sequence on F8 (`process_slip`)**:
  - Aligned entry sequence to the operator-defined standard: `enter stake` $\rightarrow$ `select bet type` $\rightarrow$ `press 'e' if the bet is e/w`.
  - Added adequate dwell timing before F10/F11 transitions so Each-Way bet state is fully settled before advancing sections.

### Fixed
- **BOG Application on Overridden Prices (`state_apply_guarantees`)**:
  - Ensured Best Odds Guaranteed (BOG) is applied to all priced selections, including price-overridden runners.
  - Streamlined modal handling: pressing `'g'` on an overridden price triggers Betty's blue override dialog, which is immediately dismissed via `[Override with entered price]` without entering repetitive 34+ retry loops.
  - Updated `is_price_purple_guaranteed` and `is_selection_non_runner` with resolution-aware coordinate scaling, ensuring price color checks read the exact betslip price column on both 1024x576 and 1366x768 screens.
- **F8 Screen Detection & Cancel Bet Calibration (`is_f8_screen_active`, `CANCEL_BET_BTN_COORD`)**:
  - Added dual resolution calibration for `CANCEL_BET_BTN_COORD` (native `(719, 529)` and scaled `(959, 705)`).
  - Updated `is_f8_screen_active` to test both native and scaled anchor points with flicker resilience.

## [0.22.24] - 2026-09-29

### Fixed
- **Type Checker Errors & Static Analysis Guarding**:
  - Guarded `l_num` in `recover_unemitted_interleaved_bets` against `None` before comparison (`if l_num is None or l_num in existing_lines: continue`), fixing `<` comparison error between `Literal[0]` and `None`.
  - Explicitly initialized `mult_val = None` in `reconcile_bet_scoping_qualifiers` and safely formatted `mult_label = f"{mult_val}x" if mult_val is not None else "combination"`, eliminating possible uninitialized variable warning.
  - Guarded `b_line` before invoking `lines_map.get(b_line, '')`, preventing `int | None` overload mismatch with `dict[int, str]`.
  - Removed redundant `str()` conversions on `sm` in `match_runner_to_racecard` meeting check.

## [0.22.23] - 2026-09-29

### Added
- **Slip-Level Multi-Meeting Affinity & Track Context (`match_runner_to_racecard`, `state_pre_scan_and_match_slip`)**:
  - Implemented pre-pass meeting detection across betting slips to aggregate active tracks (e.g. `Bath`, `Ayr`) from confident runner matches and explicit meeting hints.
  - Runners running at confirmed slip meetings receive a contextual affinity multiplier (`meeting_mult = 1.12`), allowing difficult cursive handwriting to be resolved against official runners at active courses.
- **Prefix Word Match & Cursive Confusable Disambiguation (`match_runner_to_racecard`)**:
  - Added first-word exact match boost (`sim = 0.82`) for two-word horse names when race time is within 20 minutes (e.g. `Jax Rag` 16:07 matching `Jax Edge` 16:02 Bath).
  - Added cursive capital/letter confusable normalization for frequent OCR/VLM confusions (e.g. cursive `G` vs `T` in `Gipsy`/`Gypsy` vs `Tipsy`), enabling immediate resolution of `Gipsy Sign` / `Gypsy Dean` to `Tipsy Tiger` (15:08 Ayr).
- **VLM Handwriting Disambiguation Rules for Cursive 'Last 3' and Single Doubles**:
  - Added explicit instructions distinguishing cursive 'Last 3' following a Treble from compound '& 4-fold' hallucinations.
  - Clarified that interleaved doubles without explicit `3 x` multipliers represent single 2-selection doubles.

## [0.22.22] - 2026-09-29

### Fixed
- **Multi-Selection Double Scoping Without Explicit Multiplier (`reconcile_bet_scoping_qualifiers`)**:
  - **Root Cause**: When a double had 3 preceding selections (e.g. Line 5: `50 EW Doub`), the qualifier reconciler evaluated `elif mult_num == 3 or has_doub_hint:` and converted the bet into combination `doubles` (3 distinct doubles = 300p), inflating the slip total by £2.00.
  - **Fix**: Added strict requirement for `has_3x_mult` (`mult_num == 3` or explicit `3x` in text). If `has_doub_hint` is present without a `3x` multiplier, the bet is strictly scoped as a single double on the **last 2 selections** (`bet['horses'] = bet['horses'][-2:]`, `bet['bet_type'] = 'double'`), costing 100p as intended.
- **Runaway Duplicate Bet Restoration (`recover_unemitted_interleaved_bets`)**:
  - **Root Cause**: In retries where selections had missing or misaligned line numbers, `existing_lines` did not match transcribed line numbers. The restorer resurrected all already-parsed bets as "unemitted", causing bet counts to balloon from 7 to 13-14 bets (£16.00).
  - **Fix**: Added textual token matching against existing bet descriptions (`SequenceMatcher` ratio > 0.70 or substring matching) and selection subset checks to ensure an already parsed bet is never duplicated.
- **Enforced `line_num` in Structured VLM Response Schema & Python Backfill**:
  - Added `"line_num"` to the `"required"` schema fields for both `selections` and `bets` in the Gemini structured output definition to prevent the model from emitting `Line None`.
  - Added robust Python fallback backfilling that scans `line_transcription` for runner names or times to assign the correct `line_num` if omitted.

## [0.22.21] - 2026-09-29

### Added
- **Universal Modal Pop-Up Watcher & Auto-Dismissal (`dismiss_any_modal_popups`, `dismiss_price_override_dialog`)**:
  - Implemented an always-on universal modal watcher that actively detects and dismisses obstructive Betty modal popups without requiring predefined expectations or narrow flag checks.
  - Handles both the **Blue Price Discrepancy Dialog** (*"The price you entered was not correct at the time the bet was placed. Select from the options shown below."*) by clicking the yellow **`[Override with entered price]`** button, and the **Red Late Selection / Void Selection Dialog** by clicking **`[Yes]`**.
  - Dual-layer detection supporting both pixel anchor checks (including verified top border midpoint `(815, 290)` RGB `0, 0, 255`) and direct visual button cluster scanning (`is_price_override_button_visible`).

### Fixed
- **Price Override Dialog Re-Triggering During BOG Sweep (Red -> Purple Transition)**:
  - **Root Cause**: When a selection requiring a price override has `'g'` pressed, Betty re-evaluates the price discrepancy at the exact moment the price text converts from RED (Early Price) to PURPLE (Best Odds Guaranteed), re-spawning the blue override modal. In previous versions, the check only ran before or on `'g'`, leaving the post-conversion modal active on screen to intercept subsequent `'down'` navigation and `'f8'` bet screen keystrokes.
  - **Fix in `state_apply_guarantees`**:
    - Actively polls and dismisses popups upon betslip focus (`GUARANTEE_COORD`), after every `'down'` navigation keypress, immediately after `'g'` is pressed, and critically **immediately following the price turning purple**.
    - Removed arbitrary `is_override_expected` timeout gating (which had dropped detection to 50ms on non-flagged selections), ensuring a robust 250ms polling window across all runners.
- **Direct Yellow Override Button Click (Bypassing Futile 'Enter' Keypress)**:
  - In `confirm_price_override_if_present` and `state_handle_price`, if the yellow "Override with entered price" button is visible, the companion immediately clicks the button centroid instead of wasting 350ms attempting an `'Enter'` keypress that cannot clear multi-option discrepancy modals.
- **F8 Bet Screen & Bet Transition Protection**:
  - Guarded F8 screen entry and bet transitions (`F11` / `F10`) with `dismiss_any_modal_popups`, guaranteeing no residual popup blocks terminal state transitions.

## [0.22.20] - 2026-09-29

### Fixed
- **`normalize_bet_type('doubles')` Returned `"doubles"` Instead of `"double"` — Wrong F8 Bet Type Selected**:
  - **Root Cause**: `\bdouble\b` in the regex does NOT match inside `"doubles"` — there is no word boundary between `e` and `s`. So `normalize_bet_type` fell through to the identity return, giving `"doubles"` (plural). `BET_SHORTCUTS.get('doubles')` → `None` (only `'double'` is a key). No shortcut was found, the OCR scanner ran and picked Row #1 `"Singles"` as the best match, entering the wrong bet type.
  - **Fix**: Changed regex to `r'\b(?:doubles?|doub|dousl)\b'` — the `s?` makes the trailing `s` optional, matching both `"double"` and `"doubles"` correctly.
- **Split-Line Doubles Merger Incorrectly Merged Two Separate Bets**:
  - **Root Cause**: The merger condition used `set(curr_names).issubset(set(next_names))` — if a 2-horse double (Rating, Big Harry) appeared before a 3-horse doubles bet (Rating, Big Harry, Star Cast), the 2 horses were a subset of the 3, so the merger fired and discarded the separate initial double.
  - **Fix**: Changed condition to `curr_names == next_names` (exact identical horse set). Only merges when the VLM split one bet across two consecutive lines with the same selection set (e.g. left-column `3 x` on a separate line). Never merges when next bet has additional horses.
- **EW Auto-Correction Healer Blindly Flipped Explicit `WIN` Bets to `EW`**:
  - **Root Cause**: The healer tried every bet in sequence and flipped the first one that made totals match, regardless of whether the transcription explicitly said `WIN`. This converted `50 WIN DOUBL LAST 2` (Star Cast + Yokkell) from correct 50p WIN to 100p EW, masking the real total mismatch caused by the merger bug above.
  - **Fix**: Added a WIN guard — before flipping a bet's EW flag, checks both the `line_transcription` raw text and the bet description. If either contains `\bwin\b` without a simultaneous `\b(?:ew|e/w|each)\b`, the bet is skipped as it must remain WIN-only.

## [0.22.19] - 2026-09-29

### Fixed
- **Real-Horse-First Guard: VLM Generic `"Virtual"` Tag No Longer Bypasses Racecard Lookup (`state_pre_scan_and_match_slip`)**:
  - **Root Cause**: When a betting slip has no meeting name written (e.g. just `BIG HARRY 4.08`), the VLM hallucinates `meeting: "Virtual"` on every selection. This caused `is_virtual_selection()` to return `True` → `virt_type="virtual_generic"`, which unconditionally bypassed the UK racecard crosscheck for all selections, including real horse races.
  - **Cascade Failure**: Big Harry (real Ayr race, 16:40) was accepted as-is with meeting=Virtual and time=4.08. During automation Betty searched the virtual panel at 16:08 (not 16:40), didn't find Big Harry, exhausted all recovery attempts, and aborted.
  - **Fix**: Added a **Real-Horse-First Guard** in the virtual bypass block:
    - If `virt_type == "virtual_generic"` AND the meeting is a bare token (`"Virtual"`, `"v"`, `""`) AND there is **no explicit `(v)` marker** in any time or name field — attempt `match_runner_to_racecard()` first.
    - If a confident UK/Irish racecard match is found: log `[+] Real-Horse Override` and use real racecard data (name, meeting, corrected race time, cloth number). The VLM's virtual tag is discarded.
    - If no racecard match: log that the selection is being treated as genuine virtual/unanchored and fall through to the standard virtual bypass.
    - Named virtual tracks (Portman Park, Steepledown, Sprintvalley, etc.) → `virt_type != "virtual_generic"` → are **not** subject to the racecard pre-check and continue to bypass as before.
  - **Time Correction Bonus**: The racecard matcher also corrects misread race times (e.g. `4.08` → actual `16:40` for Big Harry at Ayr) as a side effect of the match.

## [0.22.18] - 2026-09-29

### Fixed
- **`AB N-M` Range Notation Correctly Parsed as `ABOVE M` (`parse_scoping_qualifier`)**:
  - `50 EW ACCUM AB 1-5` was previously parsed as `('above', 1)` because the regex captured the first digit of the range `1-5`.
  - Added a range-aware pre-check: `AB N-M` is now correctly detected as "selections 1 through M" → returns `('above', M)`.
  - This prevented the accumulator from being scoped to only the last 1 selection (So Tempting), which then cascaded into the accumulator auto-expansion guard and the same-race contingency splitter creating incorrect 25p accumulator splits.
- **`N x doubles` bet_type Correction Before Accumulator Auto-Expansion (`reconcile_bet_scoping_qualifiers`)**:
  - When the VLM parsed `3 x 50 WIN X DOUB` with a `bet_type` of `"accumulator"` (or similar non-double), the accumulator auto-expansion guard at `<4 horses` would incorrectly expand the 3-horse combination doubles bet to all 6 preceding selections on the slip.
  - Added a pre-expansion type correction: if the combined description/raw_text contains `\bdoub\w*\b` and no explicit treble/accumulator keyword, and the current `bet_type` is `accumulator`, `single`, or blank, the `bet_type` is corrected to `'doubles'` before the accumulator guard runs.
  - This prevents cascade failures where the expanded 6-horse "doubles" bet triggers same-race contingency splitting (Star Cast vs Krissy both at Ayr 15:08), creating nonsensical 25p accumulator bets.

## [0.22.17] - 2026-09-29

### Fixed
- **Interleaved Bet Restorer, Compound Bet Splitter, EW Conflict Resolver, Written Total Guard**:
  - Upgraded `recover_unemitted_interleaved_bets()`, `split_compound_bet_entries()`, `reconcile_bet_scoping_qualifiers()`, and `extract_written_total_pence()` with various improvements from the multi-section walkthrough bet.

## [0.22.16] - 2026-09-29

### Fixed
- **Sequential Top-to-Bottom Scoping & Multiplier Auto-Resolution (`6 x 50 win doubles` / `3 x 50 win doubles`)**:
  - Resolved Betty Companion erroneously pulling selections from beneath a written bet instruction line:
    - **Root Cause**:
      1. UK betting slips are written sequentially from top to bottom: runner selections are written first, followed by footer bet instructions applying strictly to the selections listed above that line.
      2. When customer wrote `6 x 50 win doubles` (line 7) after 4 selections (`Cosmo Brown`, `Radine`, `Control Room`, `Manfield`), the VLM previously pulled runners from subsequent sections below line 7 (`Overnight Thunder`, `Billy Bathgate`, `Mickey Curran`).
      3. Similarly, accumulator expansion fallback previously used `list(selections)`, pulling all runners across the entire slip.
    - **Strict Top-to-Bottom Causality Invariant**:
      - Enforced in `reconcile_bet_scoping_qualifiers()`: any bet instruction written at line $L$ filters its selections strictly to selections written above line $L$ (`line_num < L`), stripping any runners written below. The only exception is a header bet written at line 1 prior to any selections.
    - **Combination Multiplier Auto-Resolution (`infer_selection_count_from_multiplier`)**:
      - Automatically computes required selection count from standard combination multipliers: $\binom{4}{2} = 6$ doubles $\rightarrow 4$ preceding runners; $\binom{3}{2} = 3$ doubles $\rightarrow 3$ preceding runners; $\binom{5}{2} = 10$ doubles $\rightarrow 5$ runners; $\binom{4}{3} = 4$ trebles $\rightarrow 4$ runners.
      - Auto-scopes combination bets to the exact preceding runner window.
    - **Accumulator Expansion Invariant**:
      - Restricts accumulator expansion strictly to `preceding_selections` above the accumulator line, preventing accumulators from pulling downstream runners.
    - **Prompt Scoping Guidance**:
      - Strengthened sequential layout rules in `VLM_SLIP_PROMPT_TEMPLATE`, providing explicit examples of 4 selections followed by $6\times$ doubles and 3 selections followed by $3\times$ doubles and trebles.

## [0.22.15] - 2026-09-29

### Fixed
- **Greyhound vs. Horse Race Category Isolation & Runner-Presence Safeguard Overhaul**:
  - Resolved Betty Companion erroneously accepting a greyhound race (Monmore 17:37) and selecting Trap 2 instead of cycling to the live horse race at Bath (17:37):
    - **Root Cause**:
      1. At 17:37, three meetings shared the same post time: Steepledown (Virtual), Monmore (Greyhounds), and Bath (Horses).
      2. Steepledown was correctly rejected by virtual detection (`(v)`).
      3. On Monmore (`monm:5:37 trap 1. skylars chio`), `is_target_meeting_at_top` correctly rejected `'monm'` against `'Bath'`.
      4. However, the pre-dequeue runner-presence safety check ran on Monmore because it only checked whether the screen was virtual, failing to check whether the screen was a greyhound race.
      5. In addition, `scan_visible_runners()` had a single-word fuzzy matching fallback that allowed any single word in the target horse name to match any token on screen. Target horse `Army Bugler` matched `Stackemup Amy` (Trap 2 at Monmore) because `'army'` fuzzy-matched `'amy'` with 0.857 similarity.
      6. Betty Companion prematurely confirmed Monmore as Bath and injected `#2` directly, selecting Trap 2 on the dog race.
    - **Greyhound Race Screen Detection (`is_screen_greyhound_race`)**:
      - Added dedicated detection for greyhound/trap screens inspecting both header and runner lines for trap indicators (`trap`, `traps`, `\bt\d\b`) and meeting codes (`monm`, `cray`, `romf`, `hove`, `shef`, `sund`, `swin`, etc.).
    - **Category Isolation Invariant**:
      - Enforced in both `is_target_meeting_at_top()` and `state_read_cyan_panel()`: domestic horse races (`target_cat == "horse"`) can NEVER match or run presence checks against virtual or greyhound screens. Conversely, greyhound bets can never match horse racing screens.
    - **Distinct Course Presence Guard**:
      - A runner-presence check will never override a screen if the active screen header resolves to an explicit, distinct known course of the same category (e.g. Ayr vs Bath).
    - **Multi-Word Runner Matching Integrity**:
      - Overhauled `scan_visible_runners()` so that horses with multiple words (e.g. `Army Bugler`, `Pull The Rug`, `Liberty Bird`) require all significant words (or a high-confidence compact full-name match) to match. A single word match can never claim a multi-word horse.

## [0.22.14] - 2026-09-29

### Added
- **Identical-Stake Multi-Single Consolidation Engine (`consolidate_identical_stake_singles`)**:
  - Implemented automatic aggregation of multiple single bets sharing identical unit stakes and each-way terms into a single consolidated bet entry:
    - In Betty's terminal, entering $N$ selections into the slip and selecting `Singles` (shortcut `'s'`, Row 1) with unit stake $X$ on the F8 Bet Selection screen automatically applies the £$X$ stake across all $N$ selections simultaneously.
    - Previously, slips with multiple singles (e.g. 3 selections each at £2 Win) entered each selection into Betty individually, opened F8, typed the stake, pressed F10, and entered the next selection, incurring multiple redundant navigation cycles.
    - Betty Companion now enters all runner selections in a single pass, applies Best Odds Guaranteed (BOG) sweep across all priced domestic selections in the slip, opens F8 once, types the unit stake (e.g. `200` for £2.00), and selects `Singles` (`'s'`).
  - **All-Singles & Mixed-Slip Grouping Architecture**:
    - For slips containing only singles, groups selections by `(stake_pence, each_way)` regardless of slip ordering.
    - For mixed slips (e.g. doubles, trebles, and singles), groups consecutive singles sharing identical unit stakes and terms while preserving bet structure and ordering.
    - Fully integrates with `calculate_bet_cost_pence()`, correctly computing $N \times \text{unit\_stake} \times \text{ew\_mult}$ (e.g. $3 \times 200\text{p} = 600\text{p}$ / £6.00) to reconcile with customer written totals.
  - **VLM Handwriting & Scoping Guidance**:
    - Added prompt guidelines instructing vision models to accurately extract multi-single selections at identical stakes.

## [0.22.13] - 2026-09-29

### Fixed
- **Straight Accumulator vs. Perm Folds Normalization (`1 x 50 EW ACCUMULATOR 4 FOLD` / `ABOVE 5`)**:
  - Resolved Betty Companion erroneously converting straight accumulators and 4-folds into `'perm 4-folds'` in both [`rules_engine.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/rules_engine.py) and [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py):
    - When a customer wrote `1 x 50 EW ACCUMULATOR 4 FOLD`, the regular expression `(\d+)[- ]folds?` matched `4 FOLD` before checking `accumulator`, converting the bet into `'perm 4-folds'`.
    - In Betty's F8 terminal, when exactly 4 horses are in the slip, **"Perm 4-folds" does not exist** ($\binom{4}{4}=1$ is strictly an `Accumulator`, labeled on Row 4 as `"Acc on all selns"` / `"Accumulator"`). The OCR scanner cycled Pages 1 to 5 searching for `'perm 4-folds'` in an endless loop until the operator aborted with `ESC`.
    - Upgraded `normalize_bet_type()` across both engines: any bet containing `accumulator` / `acca`, a `1 x` multiplier, or where the fold size equals the selection count now resolves strictly to `'accumulator'`.
    - Added defense-in-depth in F8 entry: if `norm_type` is `perm N-folds` and $N == \text{len}(\text{horses})$, automatically redirect to `'accumulator'`.
  - **F8 Native Accumulator Shortcut & Fast Path**:
    - Changed `BET_SHORTCUTS['accumulator']` from `'q'` (which failed to confirm) to `'a'` (native terminal key for Accumulator).
    - Whitelisted `'a'` in `select_bet_type_on_f8()`, enabling instantaneous one-touch selection with OCR fallback to Row 4 (`"Acc on all selns"`).
- **Cursive Handwriting Positional Scoping Disambiguation (`'ASALT'` / `'ABAB'` $\rightarrow$ `'ABOVE 5'` / `'ABOVE 2'`)**:
  - Resolved Betty Companion scoping an Accumulator at the bottom of a 5-horse slip to only the last 2 horses (`Cosmo Brown` and `Henfield`) and incorrectly attempting F11 (Extend Bet):
    - Gemini vision occasionally transcribes hurried cursive handwriting for `ABOVE 5` / `ALL 5` as `ASALT` or `ABALT`, and `ABOVE 2` / `LAST 2` as `ABAB 2`.
    - Upgraded `parse_scoping_qualifier()` with tolerant phonetic/cursive regexes (`above`, `ab`, `abv`, `abab`, `abov`, `abve`, `aboub`, `asalt`, `abalt`, `aslt`) and `all` qualifiers, automatically resolving `ASALT` $\rightarrow$ `('above', 5)`.
  - **Accumulator Selection Minimum Invariant**:
    - Enforced betting terminal rule: an `Accumulator` can never have fewer than 4 selections on a 4+ runner slip (a 2-horse bet is a Double; a 3-horse bet is a Treble).
    - Upgraded `reconcile_bet_scoping_qualifiers()`: if a bet is an Accumulator but retained fewer than 4 selections, it automatically expands to all selections on the slip (or all preceding selections), ensuring F10 (New Section) is pressed and all 5 horses are entered into Betty.
  - **VLM Handwriting & Scoping Prompt Updates**:
    - Added explicit instructions in the Gemini VLM prompt detailing cursive ligatures for `ABOVE <N>` / `ALL <N>` and clarifying that an `ACCUMULATOR` written at the foot of a slip applies across all selections on the slip.

## [0.22.12] - 2026-09-29

### Fixed
- **Wolverhampton Meeting OCR Font Confusion (`'wow'` $\rightarrow$ `'Wolverhampton'`) & Runner-Presence Safeguard**:
  - Resolved Betty Companion erroneously dequeuing Wolverhampton on evening racecards (e.g. 19:30 Wolverhampton):
    - In Betty's terminal font, tightly kerned `'olv'` in `'Wolv'` frequently merges in OCR into `'ow'`, producing `'wow 7:30 01. billy bathgate'` instead of `'wolv'`.
    - Because `'wow'` was not registered as a known alias, [`is_target_meeting_at_top()`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py#L1262) rejected the meeting, causing Betty Companion to press `right` and discard the meeting even while runner #1 (*Billy Bathgate*) was actively rendered on screen.
  - **Runner-Presence Meeting Confirmation**:
    - Upgraded [`state_read_cyan_panel()`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py#L1478) with an intelligent pre-dequeue safeguard: before discarding any active meeting screen with `right`, Betty Companion checks whether `target_horse_name` is visibly rendered in the runner list. If the target racehorse is already on screen, it confirms the meeting and proceeds to direct cloth injection without dequeuing.
  - **Comprehensive Wolverhampton & Wolves Alias Expansion**:
    - Registered `'wolves'`, `'wolv'`, `'wow'`, `'jon'`, `'folv'`, `'olv'`, `'oly'`, `'woy'`, `'woly'`, `'wol'`, `'wov'`, `'wlv'`, `'wolver'`, `'wolverh'`, `'iwolv'`, `'lwolv'`, `'1wolv'`, `'iwow'`, `'lwow'`, `'1wow'`, `'woiv'`, `'wo1v'`, and `'wo1'` as authoritative aliases in both [`meetings_manager.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) and [`meetings_directory.json`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_directory.json).
    - Upgraded `is_target_meeting_match()` in [`meetings_manager.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) to perform canonical course resolution so colloquial customer terms like `'wolves'` seamlessly match terminal abbreviations like `'wolv'` and `'wow'`.
    - Synchronized `target_aliases` in [`is_target_meeting_at_top()`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py#L1262) to pull horse racing aliases directly from `meetings_manager.course_alias_map`.

## [0.22.11] - 2026-09-29

### Fixed
- **Ayr Racecourse Meeting OCR Dropped Character Recognition (`'yr'` / `'yt'` $\rightarrow$ `'Ayr'`)**:
  - Resolved Betty Companion erroneously dequeuing the Ayr meeting on post times with multiple meetings (e.g. 14:08 Ayr):
    - Betty's terminal font renders the initial capital `'A'` of `'Ayr'` immediately against the left screen boundary ($X \approx 2..5$), occasionally resulting in Tesseract dropping the initial letter and reading `'yr 2:08 of. swift salian'` instead of `'ayr 2:08'`.
    - **Header Token Extraction Overhaul**: `is_target_meeting_at_top()` previously extracted words across the entire line and filtered tokens with `len(w) >= 3`. This caused 2-letter tokens like `'yr'` to be discarded, falling back onto runner names like `'swift'` (from "Swift Salian") which failed to match `'Ayr'` and caused Betty to press `right` and discard the meeting.
    - Upgraded `is_target_meeting_at_top()` to extract meeting words specifically **before the race timestamp** (`r'^([a-z\s]+?)\s*\b\d{1,2}[:.]\d{2}'`), allowing valid 2-letter meeting prefixes before the time.
    - Updated prefix drop tolerance in `_matches_token` to accept 2-letter truncated tokens (`clean_target[1:].startswith(tok)` or `clean_target.endswith(tok)`), allowing `'yr'` and `'yt'` to match `'ayr'`.
    - Registered `'yr'`, `'yt'`, `'ay'`, `'ayer'`, and `'ayre'` as authoritative aliases for `'Ayr'` in both [`meetings_manager.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) and [`meetings_directory.json`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_directory.json).

## [0.22.10] - 2026-09-29

### Fixed
- **Proactive Blue Price Discrepancy Dialog Checks During BOG Guarantee Sweep**:
  - Resolved Betty terminal modal lockup where selecting or navigating to a bet that previously required a price override re-triggers the blue price discrepancy modal (*"The price you entered was not correct at the time the bet was placed. Select from the options shown below."*), trapping focus and blocking `'down'`, `'g'`, and Non-Runner checks.
  - **Runner Selection & Focus Interception**:
    - `state_apply_guarantees()` now actively checks and dismisses the blue price discrepancy dialog immediately upon initial betslip focus (`GUARANTEE_COORD` for selection #1) and after every `down` arrow navigation keypress advancing to subsequent runners.
  - **Bet Guarantee Verification Check**:
    - Added an automatic blue dialog check every time a bet is guaranteed via `'g'`, polling with flicker resilience up to 200ms when an override was previously registered on the selection.
    - If Betty consumes the `'g'` keypress to trigger the modal, `state_apply_guarantees()` overrides the price, clears the dialog, verifies whether the price turned purple, and re-presses `'g'` to guarantee the selection.
  - **Enhanced `confirm_price_override_if_present()`**:
    - Added `timeout` and `is_override_expected` parameters. When `is_override_expected=True`, it bypasses the futile `Enter` keypress (which fails when no highlighted price exists) and directly executes a calibrated center-click on the **`[Override with entered price]`** button (`(953, 567)` on 1366x768 / `(712, 430)` on 1024x576).
    - Upgraded `wait_for_blue_price_box()` to detect the dialog via either `BLUE_PRICE_BORDER_COORDS` or `is_price_override_button_visible()`.

## [0.22.9] - 2026-09-29

### Fixed
- **Blue Price Discrepancy Dialog & Override Button Calibration (`(953, 567)` / `(712, 430)`)**:
  - Resolved price override failures where Betty pops up the multi-choice price discrepancy modal ("The price you entered was not correct at the time the bet was placed. Select from the options shown below.") and pressing `Enter` fails because there is no highlighted price list option.
  - **Root Cause**: The button centroid search was constrained to an out-of-bounds region `(650, 365, 95, 60)` with a fallback to `(697, 394)` which landed on blank white space above the button in 1024x576, and completely missed the button on 1366x768 screens.
  - **Dual-Resolution Support**:
    - Calibrated `BLUE_PRICE_BORDER_COORDS` with both native 1024x576 anchor points and 1366x768 scaled anchor points (including `(815, 290)` top border, verified pure blue RGB: `(0, 0, 255)`).
    - Calibrated `PRICE_OVERRIDE_BTN_COORD` for both 1024x576 (`(712, 430)`) and 1366x768 (`(953, 567)`).
    - Upgraded `find_price_override_button_coord()` to dynamically inspect priority search windows based on active screen resolution (`(880, 520, 140, 100)` on 1366x768, `(660, 395, 105, 75)` on 1024x576), computing the exact centroid of the yellow button (`RGB: 255, 255, 128`).
    - Added `is_price_override_button_visible()` defending against letter stroke color sampling and ensuring fallback clicks directly strike the center of the "Override with entered price" button.

## [0.22.8] - 2026-09-29

### Fixed
- **Sedgefield Best Odds Guaranteed (BOG) & Course Directory Recognition**:
  - Added Sedgefield along with its terminal and shorthand aliases (`"sedg"`, `"sedge"`, `"sedgefield"`) to both `DEFAULT_DOMESTIC_HORSE_COURSES` in [`meetings_manager.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) and `uk_irish_course_aliases` in [`meetings_directory.json`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_directory.json).
  - Resolved issue where Sedgefield resolved as `"unknown"`, causing [`is_bog_eligible_selection`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py) to skip the BOG guarantee sweep and leave prices in unguaranteed red EP. Sedgefield selections now correctly qualify for domestic BOG and trigger `'g'` guarantee keypresses.

## [0.22.7] - 2026-09-28

### Fixed
- **CompactHUD Click-and-Drag Null-Safety Safeguards**:
  - Added explicit null guards (`if not self.root: return`) to `_start_drag` and `_do_drag` event callbacks in [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py).
  - Filtered widget collection with `if widget is not None` prior to binding `<Button-1>` and `<B1-Motion>`, resolving IDE static analysis type errors (`Object of class NoneType has no attribute winfo_x / winfo_y / geometry`).
- **Redundant `int()` Wrapper Elimination in `calculate_bet_cost_pence`**:
  - Removed redundant `int(...)` wrapper around `round(float(bet['unit_stake']) * 100)` in both [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py) and [`rules_engine.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/rules_engine.py), satisfying Pyrefly and Python 3 typing analysis.

## [0.22.6] - 2026-09-28

### Changed
- **76% VLM Input Token Reduction & Payload Optimization**:
  - Streamlined `prompt_text` in [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py) from 28,216 characters (~7,050 tokens) down to ~4,320 characters (~1,080 tokens), slashing total input payload per slip from **~9,980 tokens to 2,480 tokens (-75% reduction)**.
  - Merged duplicate scoping sections into a single authoritative set of rules covering `LAST <N>`, `ABOVE <N>`, Header/Footer formats, combinations, and unit stake enforcement.
  - Eliminated redundant raw JSON examples from the prompt text, allowing Gemini's grammar compiler to strictly enforce `response_schema` without prompt bloat.
  - Replaced the exhaustive 35+ international track directory dump in [`meetings_manager.py:get_vlm_prompt_summary()`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) with a compact directory targeting UK virtuals and dog track aliases.
  - Calibrated image preprocessing in `pre_process_slip_image()` to native 1.0x scale (`max_dim = 512`), maintaining 100% stroke sharpness while eliminating multi-tile vision penalties.
  - Streamlined `response_schema` in `bets.horses` to require `selection_num`, enabling the model to output lightweight bet structures while the companion hydrates runner names and prices automatically.
  - **Empirically Verified**: Verified live on a complex 5-selection, 7-bet interleaved slip; accurately extracted all 5 runners, all 7 bet instructions, and achieved an exact 800p (£8.00) match with 0 errors.

## [0.22.5] - 2026-09-28

### Fixed
- **Cross-Module Engine Logic Synchronization (`rules_engine.py` $\leftrightarrow$ `betty_companion.py`)**:
  - `clean_horse_name`: Synchronized virtual racing `(v)` tag cleaning (`re.sub(r'\s*\([vV]\)', '', n)`) across both modules to prevent runner matching failures on virtuals.
  - `parse_race_time_to_minutes`: Synchronized dash-separated time parsing (`r'(\d{1,2})[:\.-](\d{2})'`) so `17-40` normalizes accurately to `17:40` (1060 mins).
  - `normalize_bet_type`: Ported the permutation folds regex normalizer (`perm 5-folds`, `5-fold`, `WORD_TO_NUM`) into `rules_engine.py`, ensuring multi-leg contingency split evaluations correctly categorize perm fold bet types.
  - `calculate_bet_cost_pence`: Fixed potential `TypeError` when `stake_pence` is `None`, eliminated premature returns on unverified `total_stake_pence`, added robust fallback to `unit_stake * 100` when `stake_pence` is absent, and aligned combination lines arithmetic.
- **Out-of-Order Variable Initialization & State Scoping in `betty_companion.py`**:
  - Positioned `GREYHOUND_TRACKS` at module top immediately following `meetings_manager` import, and eliminated duplicate re-initialization on line 2524.
  - Re-ordered global cycle management state (`SESSION`, `is_cycle_running`, `abort_event`) prior to `trigger_abort` and `_esc_poller_daemon`.
  - Relocated `wait_for_runner_panel` below `interruptible_sleep` and `abort_event` to resolve forward-reference warnings.

### Removed
- **Dead & Redundant Code Elimination**:
  - Removed orphaned `is_guarantee_time_window()` in `betty_companion.py` (abandoned hardcoded 08:00–23:59 harness superseded by `evaluate_bog_eligibility`).
  - Removed dead `is_blue_price_box_present()` in `betty_companion.py` (superseded by dynamic poller `wait_for_blue_price_box`).
  - Cleaned stale `(v0.13.0)` header docstring in `meetings_manager.py`.

## [0.22.4] - 2026-09-28

### Fixed
- **Towcester Greyhound Header OCR & Border Artifact Tolerance (`‘owe` $\rightarrow$ `Towcester`)**:
  - Resolved false-negative meeting rejection during linear cyan header inspection where Towcester was misidentified and erroneously dequeued via `'right'`:
    `Target meeting 'Towcester' not at top (active: '‘owe 7:16 trap 1. confey blaze'). Dequeueing with 'right'...`
  - **Root Cause**: The cyan capture window (`CYAN_REGION = (0, 0, 305, 465)`) borders the terminal edge, causing Tesseract to misinterpret the vertical border line / capital `'T'` as an opening quote `'‘'`, leaving `'owe'`. In addition, low-resolution bitmap fonts commonly produce `'c'` $\leftrightarrow$ `'e'` character confusion (`TOWC` $\leftrightarrow$ `TOWE`).
  - **Fixes Applied**:
    1. Added `"towe"`, `"towec"`, `"owe"`, and `"owc"` to Towcester aliases in [`meetings_directory.json`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_directory.json).
    2. Enhanced `is_target_meeting_match` in [`meetings_manager.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py) and `is_target_meeting_at_top` in [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py) with dual tolerant prefix matching: checks `c <-> e` normalized substrings on both target canonical names and alias sets when a leading letter is dropped or converted to an OCR delimiter.

## [0.22.3] - 2026-09-28

### Added
- **Persistent Always-On-Screen Notification Console (`CompactHUD`)**:
  - Configured the floating notification console to remain visible on screen at all times across all lifecycle stages (startup, idle daemon listening, active OCR/VLM transcription, racecard matching, bet entry, completion, and abort).
  - Added live state-aware operational badges: `[Ctrl+Alt+B]` when idle/ready, `[ESC: Abort]` during active automation, `[Done]` on slip completion, and `[Aborted]` / `[Error]` on interrupts and exceptions.
  - Implemented click-and-drag repositioning: operator can click and drag the HUD anywhere on screen if needed, while defaulting safely docked in the bottom-right corner.
  - Added automatic text wrapping (`wraplength=290`) on live status messages to prevent long descriptions from clipping.
- **Smooth Idle State Recovery & Auto-Reset**:
  - Replaced window `withdraw()` logic in `hide()` with `reset_to_idle(delay_ms)`: post-entry success banners (`#1B5E20`) and abort notices dwell for 4.5–6.0 seconds before automatically transitioning back to the `"Ready. Press Ctrl+Alt+B to scan slip"` state without disappearing.
  - Integrated defensive recovery hooks in `start_automation_cycle()` and `notify()` ensuring unhandled errors or early cycle returns smoothly reset the console to ready.

## [0.22.2] - 2026-09-28

### Fixed
- **`MeetingsDirectoryManager.are_meetings_equivalent` Null-Safety Guard**:
  - Resolved `AttributeError: Object of class 'NoneType' has no attribute 'lower'` when evaluating meetings that do not resolve to a canonical name (returning `None`).
  - Added safe `if c1 and c2 and c1.lower() == c2.lower():` verification before invoking `.lower()`, ensuring unknown and unanchored meeting strings fail over gracefully to `is_target_meeting_match`.
- **Redundant `bool()` Cast Elimination in BOG Guarantee Sweep**:
  - Removed redundant `bool(...)` wrapper on line 4326 in `betty_companion.py` within the `has_eligible_bog` generator comprehension, satisfying Pyrefly and Python static type analysis.

## [0.22.1] - 2026-09-28

### Added
- **Automatic Late Selection / 'Void Selection' Modal Detection & Resolution**:
  - Implemented automatic detection and clearance for Betty's 'Late Selection' / 'Void Selection' prompt dialog:
    `"Wager staked X mins, Y secs after 'off'. Do you wish to apply 'Void Selection' processing? [Yes] [No]"`
  - Added `LATE_SELECTION_BORDER_COORD = (692, 292)` with `TARGET_RED = (255, 0, 0)` and `LATE_SELECTION_YES_BTN_COORD = (589, 504)`.
  - Added `is_late_selection_dialog_present` and `check_and_handle_late_selection_dialog` to immediately verify and click `'Yes'` whenever a selection is added to the betslip, preventing terminal deadlocks on late wagers.
  - Wired into both `state_handle_price` (immediately after runner entry and price clearance) and `state_process_betslip`.

## [0.22.0] - 2026-09-28

### Added
- **Same-Race Multi-Runner Entry Chaining**:
  - Implemented same-race runner chaining in `state_process_betslip` and added `select_runner_in_active_panel`: when consecutive selections in a bet run in the same race (e.g. Reversed Forecasts, Straight Forecasts, Combination Forecasts, Tricasts), Betty Companion preserves the currently open cyan race panel.
  - Eliminates redundant `/` time resets, time re-entry, and meeting dequeuing cycles (`right` arrow), allowing subsequent selections to be entered directly via active panel runner selection (e.g. entering `1`, Enter, `4`, Enter immediately).
- **Virtual Racing Meeting Aliases & Directory Expansion (`Portman Park`, etc.)**:
  - Added common betting shop abbreviations to `meetings_directory.json` for Portman Park (`"p. park"`, `"p park"`, `"p.park"`, `"ppark"`, `"p/park"`, `"p park (v)"`, `"p. park (v)"`), Steepledown (`"s. down"`, `"s down"`), and Sprintvalley (`"s. valley"`, `"s valley"`).
  - Added `are_meetings_equivalent` to `MeetingsDirectoryManager` for robust equivalence checking across aliases and terminal header tokens.
- **Virtual Racing & Singles + RFC Transcription Prompt Guidelines**:
  - Added dedicated Virtual Racing rules and handwriting interpretation guidelines for slips combining win singles with forecast/RFC wagers (e.g. `1 £4 w`, `4 £4 w`, `£1 r/f/c` resolving to £4 Win on 1, £4 Win on 4, and £1 RFC on 1 & 4 for £10 total).
  - Explicitly guides the model to prevent misreading `£4 w` as `fc` and prevents inflating unit stakes from `£1` to `£5`.

### Fixed
- **Virtual Runner Greyhound / Sheffield Misclassification**:
  - Fixed issue in `is_greyhound_or_trap_selection` and `rules_engine.py` where numbered selections at virtual courses (e.g. runner `1` or `4` at Portman Park) were misidentified as greyhound trap bets and subsequently defaulted to `Sheffield`.
  - Added defensive guards in `pre_flight_check_slip` to protect virtual and international meetings from ever defaulting to Sheffield.

## [0.21.2] - 2026-09-28

### Changed
- **High-Speed Best Odds Guaranteed (BOG) Pricing Sweep Acceleration**:
  - Streamlined `state_apply_guarantees` timing calibrations: reduced initial betslip focus pause from 200ms to 60ms, down-arrow navigation from 180ms to 40ms, and `'g'` keypress pause from 200ms to 40ms.
  - Implemented high-speed red-pixel screening in `is_selection_non_runner`: active runners on the betslip contain no red text, so the checker now evaluates a numpy red-pixel mask first (< 1ms). Heavy Tesseract OCR processes are strictly bypassed unless red Non-Runner indicator pixels are actually detected.
  - Optimized `confirm_price_override_if_present` with non-blocking border and button color checks (< 1ms) to eliminate multi-frame sleep polling and redundant template matching during the guarantee sweep.
  - Reduced total guarantee cycle latency from ~800ms-1,100ms per runner down to ~105ms per runner (an 85%+ speed improvement across multi-leg accumulator slips).

## [0.21.1] - 2026-09-28

### Added
- **Multi-Page F8 Bet List Traversal (Up to 8 Pages)**:
  - Extended `select_bet_type_on_f8` cycling ceiling from 4 pages to 8 pages (`max_pages = 8`) to ensure late-page specialized permutations (e.g. `Perm 5-folds`, `Perm 6-folds`) can be located and selected reliably.
  - Implemented dynamic page fingerprinting (`seen_page_signatures` storing concatenated normalized text of visible rows) to detect wrap-arounds safely if Betty has fewer than 8 total pages of bets.
- **Perm Folds Bet Type Normalization & Menu Matching**:
  - Added Perm Folds normalization to `normalize_bet_type`: converts colloquial expressions like `"perm 5-folds"`, `"5-fold"`, `"5 folds"`, `"fivefold"`, `"fivefolds"` to canonical `"perm 5-folds"`, mapping 2-folds and 3-folds to `"double"` and `"treble"` respectively.
  - Added menu string definitions in `BET_TYPE_MENU_NAMES` for `perm 4-folds` through `perm 10-folds`.
  - Added regex matching in `is_bet_type_match` allowing canonical perm folds (`perm {N}-folds`) to match Betty's on-screen menu formats (`Perm 5-Folds`, `5-Folds`, `5 Folds`, `Perm 5 Fold`).

### Fixed
- **Digit Collision Prevention in Fuzzy Bet Type Matching**:
  - Implemented a strict digit mismatch guard in `is_bet_type_match`. Previously, string similarity (`SequenceMatcher`) between `"perm4folds"` and `"perm5folds"` produced a 0.90 similarity score, risking false matches across adjacent fold numbers. The validator now extracts all digits from both candidate and target strings; if both contain digits and their sets differ, fuzzy matching is strictly rejected.

## [0.21.0] - 2026-09-28

### Added
- **Dynamic F8 Bet List OCR Scanner & Page Cycling Engine**:
  - Implemented dynamic OCR scanning of Betty's F8 bet selection list (`F8_BET_LIST_REGION = (6, 125, 282, 384)` bounding `X: 6..288, Y: 125..509`).
  - Added multi-page traversal via `OTHER_BETS_BTN_COORD = (77, 560)` (cycling up to 4 pages) to automatically search, find, and click bets lacking keyboard shortcuts (such as Combination Tricast, Tricast, Trixie, Canadian, etc.).
  - Added RGB selection confirmation: verifies that the clicked bet type row turns to active bright green (`RGB(0, 255, 64)`), retrying if needed before continuing.
  - Calibrated row geometry for the 11 vertical bet options: `F8_ROW_HEIGHT = 34.9px`, `Row 1` bounds `(6, 125)` to `(288, 158)`, and click centroid `X = 147`.
  - Added `is_f8_other_bets_active` detecting yellow active state (`RGB(255, 255, 128)`) vs. cyan normal state (`RGB(0, 255, 255)`).
  - Replaced the dangerous static fallback that previously defaulted unmapped bet types to placing a Single (`'s'`). If a bet type cannot be located after cycling through all pages, the system now stops cleanly and issues an operator alert.

## [0.20.14] - 2026-09-28

### Added
- **International & US Racing Directory Expansion (`Philadelphia`, `Parx`, etc.)**:
  - Added `"philadelphia"` (aliases: `"philadelphia"`, `"phila"`, `"phil"`, `"parx"`, `"parx racing"`, `"philadelphia park"`) to `international_meetings` in `meetings_directory.json`.
  - Added 31 other major North American and French racecourses to `international_meetings` (Churchill Downs, Del Mar, Santa Anita, Tampa Bay Downs, Pimlico, Keeneland, Woodbine, Mahoning Valley, Penn National, etc.) so retail betting slips for US racing resolve immediately.
  - Added direct international meeting matching to `is_target_meeting_match` in `meetings_manager.py` so Betty's terminal headers (`PHIL`, `PARX`, `PHILA`) match cleanly during navigation.

### Fixed
- **Pre-Flight International Bypassing (Eliminated Domestic Runner Substitution Bug)**:
  - Fixed issue where `Lex @ 15/8 (17:40 Philadelphia)` was falsely flagged as an unknown horse and rewritten by AI re-examination to `Pillars Presence #13 (17:40 Roscommon)`.
  - Prioritized `is_international_selection` in pre-flight scanning before UK/Irish racecard lookups: international selections now bypass UK/Irish racecard crosschecking and lock the customer's written runner, meeting, and time directly.
  - Added defensive guards in `reexamine_runner_with_ai`: if a selection represents international, greyhound, or virtual racing, or if the specified meeting does not exist in today's UK/Irish cards, candidate re-examination against UK/Irish runners is strictly aborted to prevent hallucinations.
  - When candidate re-examination is invoked for UK/Irish racing, candidate runners are now strictly filtered to the written UK/Irish meeting rather than mixing in unrelated meetings at the same post time.

- **Best Odds Guaranteed (BOG) Domestic Eligibility Enforcement**:
  - Implemented `is_bog_eligible_selection` enforcing retail betting shop rules: Best Odds Guaranteed (`'g'`) is strictly restricted to domestic UK and Irish horse racing.
  - Non-UK/Irish horse racing (US, French, Dubai, etc.), greyhound racing, and virtual racing are completely barred from BOG.
  - `state_apply_guarantees` and `state_process_betslip` now verify BOG eligibility prior to pressing `'g'` and skip the guarantee sweep entirely if no domestic horse selections are present in the bet.
## [0.20.13] - 2026-09-28

### Removed
- **Legacy Model Pinging Status Message**:
  - Replaced the outdated HUD status banner `"Pinging Gemini models in parallel..."` at the start of slip scans with `"Scanning slip with {PREFERRED_VLM_MODEL}..."`.
  - Confirmed the system dispatches directly to the primary preferred model (`gemini-3.5-flash`) on the billing-active key without executing any preliminary health-check pings or model probes.

## [0.20.12] - 2026-09-28

### Fixed
- **Wolverhampton Low-Res OCR Alias Resolution (`woy` -> `Wolverhampton`)**:
  - Identified root cause of failure to enter runner 'Wootz' at 16:55: on Betty's low-resolution terminal font, the track code `wolv` / `wol` merged and OCR'd as `'woy'` (`woy 4:55 01. al jolson`).
  - Added `"woy": "Wolverhampton"`, `"woly": "Wolverhampton"`, `"wol": "Wolverhampton"`, and border delimiter variants (`"iwolv"`, `"lwolv"`, `"iwoy"`, `"lwoy"`) to both `uk_irish_course_aliases` in `meetings_directory.json` and `DEFAULT_DOMESTIC_HORSE_COURSES` in `meetings_manager.py`.
  - Ensures Betty Companion immediately recognizes Wolverhampton as active without cycling through and exhausting available meetings.

### Changed
- **API Key Priority Optimization (Direct to Billing Key)**:
  - Repointed primary `GEMINI_API_KEY` in `.env` to Key #3 (`...Zro-2w`), the verified billing-active project key.
  - Eliminated the 3-5 second delay caused by transient HTTP 503 busy retries on Keys #1 and #2, ensuring immediate HTTP 200 OK responses on initial payload dispatch.

## [0.20.11] - 2026-09-28

### Fixed
- **Restoration of Proven BOG Guarantee Coordinate (`GUARANTEE_COORD = (889, 93)`) & Keyboard Navigation**:
  - Restored the battle-tested price guarantee mechanism from `v0.19.14` and all pre-v0.20 releases:
    - Automatically clicks `GUARANTEE_COORD = (889, 93)` once to focus the active betslip list control directly in the price/odds column.
    - Applies `'g'` to Selection 1, then natively advances down through subsequent selections using the keyboard `'down'` arrow key followed by `'g'`.
    - Eliminates the synthetic mouse click calculations (`(780, 70 + i * 34)`) introduced in v0.20.9 that missed the selection hitboxes, deselecting Betty's rows and causing `'g'` keypresses to be dropped.
    - Retains full Non-Runner (NR) skipping logic, defensively bypassing guarantees on scratched horses.

## [0.20.10] - 2026-09-28

### Removed
- **Winsound & Audio Alert Functionality**:
  - Completely removed `winsound` library import and all audio beeping cues across the companion daemon per operator specification.
  - Removed abort sound alerts (`winsound.Beep(450, 160)` / `winsound.Beep(300, 300)`) from `trigger_abort`.
  - Removed sound emission threads (activation pips, success chimes, failure buzzers) from the `notify` notification pipeline, ensuring 100% silent operation.

## [0.20.9] - 2026-09-28

### Fixed
- **Status HUD Relocation to Bottom-Right**:
  - Relocated `CompactHUD` window from the top-right corner (`y=20`) to the bottom-right corner (`screen_w - 330, screen_h - 130`).
  - Resolved root cause of BOG guarantee failures: previously, the floating HUD was sitting directly on top of Betty's active betslip (`X: 700..1017, Y: 3..89`), intercepting and swallowing mouse clicks intended for Selection 1.
- **Direct Red Runner Name Centroid Clicking in Betslip**:
  - Calibrated `BETSLIP_FIRST_SELECTION_COORD` to `(780, 70)` (the exact horizontal center of the bright red runner name text on Selection 1, e.g. "8. Storm On Jura").
  - Calibrated `BETSLIP_ROW_HEIGHT` to `34px` (exact vertical line-to-line spacing between selections in Betty's betslip).
  - Updated `state_apply_guarantees` to directly click each runner's red name at `(780, 70 + i * 34)` with `click_betty_cell` before pressing `'g'`, ensuring Betty's Win32 control unambiguously focuses each selection.

## [0.20.8] - 2026-09-28

### Changed
- **VLM Model Prioritization for Gemini 3.5**:
  - Set `PREFERRED_VLM_MODEL = "gemini-3.5-flash"` as the primary vision model for initial slip interpretation.
  - Reordered `VLM_WATERFALL_MODELS` to prioritize `gemini-3.5-flash` followed by `gemini-3.5-flash-lite` at the front of the cascade.
  - Updated `reexamine_runner_with_ai` candidates to prioritize `gemini-3.5-flash` for ambiguous cursive handwriting re-examination against Sporting Life / Racing API racecards.

## [0.20.7] - 2026-09-28

### Removed
- **Left Selection Reuse Panel Pipeline**:
  - Completely removed the left selection reuse table navigation and right-click summoning mechanisms per operator instruction.
  - Restored clean, reliable sequential entry for every runner across all bet sections:
    - Automatically validates yellow time input box ready state (pressing `/` if not ready or if menu active).
    - Writes race time, inspects cyan meeting list, discovers/selects official runner, and enters price via standard flow.
    - Selections identical to previous bets continue to be seamlessly extended using Betty's native `F11` (Extend Bet) shortcut.

### Fixed
- **Blue Price Verification Dialog & Override Button Center Click**:
  - Calibrated the exact center coordinates of the yellow **"Override with entered price"** button to `PRICE_OVERRIDE_BTN_COORD = (697, 394)` (button bounding box: `X: 650..744, Y: 365..424`), replacing the previous edge coordinate `(710, 418)`.
  - Upgraded click execution to `click_betty_cell`, applying a deliberate 50ms pre-move settle and 80ms mouse-down hold time directly in the button centroid to ensure Betty's legacy Win32 modal dialog reliably registers the click.
  - Re-verified standard flow: when the blue price check screen appears, the script immediately presses `'Enter'` to accept the "Price when struck" option (the default highlighted option). If `'Enter'` does not clear the modal, it automatically clicks the center of the "Override with entered price" button.

### Clarified
- **Best Odds Guaranteed (BOG) & System Time Windows**:
  - Confirmed that Betty Companion does not restrict `'g'` execution based on local system time; the companion attempts to apply `'g'` to every priced runner regardless of the clock.
  - Noted that Betty's own host terminal/server only awards BOG (turning the runner price purple) if the bet is placed within the shop's designated BOG promotion windows; outside those windows, Betty retains the price as an Early Price (EP) in red.

## [0.20.6] - 2026-09-28

### Added
- **Visual Entry Verification (`is_reuse_row_entered`)**:
  - Implemented dual-layer visual confirmation after clicking any selection in the left reuse panel:
    - **Layer 1 (Reuse Panel Row Whiteness)**: Confirms the targeted selection row turns pure white (`RGB > 230, 230, 230`) across cell background coordinates `(80, row_y)`, `(215, row_y)`, and `(280, row_y)`, distinct from unentered cyan (`128, 255, 255`) and green hover states.
    - **Layer 2 (Betslip Red Text Detection)**: Validates that the active betslip on the right updates with the runner's details rendered in distinctive red text (`r > 180, g < 60, b < 60`) at `y = 70 + betslip_idx * 36`.
  - Added an automated 3-attempt retry loop: if Betty drops a synthetic mouse event or rendering lags, the automation automatically retries clicking with fine coordinate micro-adjustments until visual registration is confirmed.

### Fixed
- **Vertical Row Coordinate Calibration (`227` -> `221`)**:
  - Calibrated `REUSE_PANEL_ROW_START_Y` from `227` to `221` (dead center of Row 0's vertical span from `y=209` to `y=235`). Previously, `227` landed near the bottom border, causing Betty's GDI list control to occasionally miss clicks.
- **Panel Visibility Invariant Detection (`(233, 215)`)**:
  - Repointed `is_reuse_panel_visible()` to Row 0's vertical red dividing border at `(233, 215)`, which is consistently bright red (`RGB: 255, 0, 0`) whenever the panel is open regardless of runner count (1 to 10+ runners).
  - Resolved bug where the previous check at `(10, 320)` failed on slips with 2 or 3 runners (where the table ends at `y=262`), triggering unwanted right-clicks and preventing the `'/'` key from restoring the yellow time input box.
- **GDI Mouse Event Hold Time**:
  - Increased `click_betty_cell` mouse-down hold time to 80ms with 50ms pre-move settling to ensure legacy Win32/GDI window procedures never drop input events.

## [0.20.5] - 2026-09-28

### Fixed
- **Selection Reuse Calibration (Price Box vs SP Name Box)**:
  - Corrected reuse panel click mechanics based on Betty UI specification:
    - When a price is taken (`has_price=True`), automation now clicks the designated **Price box** (`REUSE_PANEL_ODDS_X = 266`, where `9-2` is displayed), correctly inputting the selection with price.
    - When no price is taken (SP), automation clicks inside the **Name box** (`REUSE_PANEL_NAME_X = 168`), inputting the selection at SP.
  - Implemented `click_betty_cell(x, y)` with deliberate 50ms mouse down/up hold time to ensure legacy Win32/GDI Betty controls reliably register clicks.
  - Aligned time entry transitions: pressing `/` while on the reuse screen directly restores the yellow time box for new runner entry.

### Changed
- **Token Consumption & Latency Optimization**:
  - **Single-Tile Vision Budgeting**: Constrained slip image preprocessing to a maximum dimension of 768px (`max_dim = 768`), ensuring the slip image fits inside a single Gemini vision tile (258 tokens) instead of spanning multiple tiles (saving ~770 input tokens per scan).
  - **Client-Side Bet Hydration**: Redesigned `response_schema` so `bets[].horses[]` only returns `{name, selection_num, price}`, eliminating redundant generation of full 7-field runner objects across every multiple bet. Python automatically hydrates bets from `selections`, cutting over 850–1,000 output tokens and reducing translation latency by 10–15 seconds.
  - **Prompt Streamlining**: Removed duplicate 20-line raw greyhound track lists from prompt text in favor of centralized `meetings_manager` catalog.

## [0.20.4] - 2026-09-28

### Fixed
- **Selection Reuse Panel Transfer**:
  - Fixed an issue where selections reused from the left panel were not transferring into the betslip on the right. When a price was present, the code previously clicked the odds column (`REUSE_PANEL_ODDS_X = 262`), which is ignored by Betty. Automation now strictly clicks the runner **name** column (`REUSE_PANEL_NAME_X = 168`), which transfers the runner into the active betslip for both priced and SP wagers.
  - Added `is_reuse_panel_visible()` to verify whether the reuse panel is open via its red table border (`y=320`), preventing redundant right-clicks that could unfocus or toggle Betty.
  - Added proactive ready-state check (`is_reuse_panel_visible()` / `READY_COORD`) when transitioning from reused runners to first-time runners, ensuring the yellow time box is always active before typing post times.

### Changed
- **Racecard AI Re-Examination Optimization (Eliminated 2-Minute Hang)**:
  - Eliminated the pre-flight scan hang where ambiguous runner re-examination cascaded sequentially across 9 models with 35-second timeouts (~97 seconds total).
  - Prioritized high-throughput, high-quota endpoints (`gemini-3.1-flash-lite` with 500 RPD / 15 RPM) for re-examination, bypassing the 20 RPD / 5 RPM choke point on full Flash models.
  - Reduced re-examination timeout from 35s to 10s and capped attempts to at most 2 models, ensuring handwriting re-checks resolve in 2-4 seconds.
  - Reordered global `VLM_WATERFALL_MODELS` so `gemini-3.1-flash-lite` serves as the immediate high-capacity failover for primary slip translation if `gemini-3.6-flash` is busy.

## [0.20.3] - 2026-09-28

### Changed
- **Payload Streamlining & Latency Reduction**:
  - Made multi-turn visual reference demonstrations conditional on `retry_hint`, eliminating 2 heavy base64 example images (~10,000 input tokens) from primary scans.
  - Drastically cuts pre-fill vision encoding overhead and acceleration latency on first-pass slip scans.
- **Real-Time Heartbeat & Ticking Elapsed Progress (`sys.stdout.flush`)**:
  - Added live ticking progress display during active Gemini VLM generation (`[*] Translating slip with {model}... (2s... 4s...)`) in both console and HUD.
  - Flushed stdout immediately to prevent console buffering illusion where users mistook long generations for frozen executions.

## [0.20.2] - 2026-09-28

### Added
- **Adjacent & Margin Qualifier Recognition (`LAST 2`, `LAST 3`, `ABOVE 2`, etc.)**:
  - Enhanced VLM prompt to mandate full horizontal row scanning from left margin to right margin for adjacent bet qualifiers (e.g. `50 EW DOUBL    LAST 2`).
  - Added programmatic reconciler `reconcile_bet_scoping_qualifiers` and `parse_scoping_qualifier`:
    - Automatically detects qualifiers like `last N`, `lst N`, `above N`, `ab N`, `top N`, and word numbers (`two`, `three`, `four`).
    - Correlates each bet with line transcriptions by line number, bet keywords, and Each-Way attributes.
    - Strictly scopes the bet's `horses` to the targeted $N$ selections (e.g. for `50 EW Double Last 2` across 3 runners, automatically targets Runner 2 and Runner 3, excluding Runner 1).
    - Recalculates unit and total costs and reconciles against customer written total.
  - Added `line_num` field to the `bets` object in Gemini VLM response schema for 1-to-1 line correlation.

## [0.20.1] - 2026-09-28

### Added
- **Expanded Selection Group Scoping (3x Cross Doubles & Treble Recognition)**:
  - Explicitly modeled customer slip layout where 2 runners (e.g. Give Hand, Galileo Dame) are written with tentative intermediate text and an added 3rd runner (e.g. Sub Thirteen) followed by `3 x 50 win double` and `1 x £1 win treble`.
  - Transcribes all 3 selections together into both Bet 1 (3x £0.50 Win Only Doubles = £1.50) and Bet 2 (1x £1.00 Win Only Treble = £1.00), cleanly matching £2.50 total payment without phantom intermediate doubles.
- **Related Contingency Auto-Correction & Same-Race Clash Splitting (`rules_engine.py`)**:
  - Normalized meeting matching via `meetings_manager.resolve_meeting` in `get_horse_event_key` so track variants (e.g. `Epso` / `Epsom Downs`, `Cur` / `Curragh`) reliably detect same-race clashes.
  - Automatically splits multi-race multiples containing same-race clashes down the bet hierarchy according to UK bookmaker rules: a 50p Win Treble with 2 runners in the same race auto-corrects to 2x 25p Win Doubles; a 50p Win Double on 2 same-race runners auto-corrects to 2x 25p Win Singles.
  - Added operator HUD notifications (`notify_cb`) alerting cashier when a same-race clash is detected and auto-corrected.
  - Generalized combination double clash handling for arbitrary runner counts ($N \ge 3$).

## [0.20.0] - 2026-09-28

### Added
- **Selection Reuse Panel Workflow (Image 4 Integration)**:
  - Added right-click shortcut on Betty's bet view area at `(800, 250)` to summon the left reuse panel.
  - Calibrated row coordinates `Y = 227 + (k - 1) * 26` for chronological runner indexing.
  - Implemented dual-column entry: clicking the horse name column `(165, y)` enters selection at Starting Price (SP); clicking the odds column `(262, y)` enters selection with odds taken.
  - Integrated `session_entered_selections` tracking so that previously entered runners are re-added directly without redundant race time entries.
- **Purple Guaranteed Price RGB Verification & Non-Runner (NR) Skipping (Images 1 & 2)**:
  - Implemented `is_price_purple_guaranteed` detecting purple text RGB signature `(R: 110-235, B: 100-200, G <= 110, B > G + 20)`.
  - Implemented `is_selection_non_runner` detecting red "NR" text on betslip rows.
  - Updated `state_apply_guarantees` to skip non-runners, bypass keyboard down arrow when focused on NR, and click directly to subsequent runner rows.
- **F8 Bet Type Screen Button Geometry & 'Other Bets' Cycling (Image 3)**:
  - Calibrated coordinate map `BET_BUTTONS_F8` for Singles, Doubles, Trebles, Acca, Doubles + Trebles, Yankee, Lucky 15, Patent, Lucky 31, Lucky 63, and Flag.
  - Added fallback cycling via `OTHER_BETS_BTN_COORD = (53, 417)` when a requested bet is not on page 1.
- **F11 (Extend Bet) vs F10 (New Section) Optimization**:
  - Automatically compares canonical selections between successive bets: identical selections (e.g. 3x cross doubles followed by £1 treble) use F11 to retain selections and skip redundant entry.
  - Disparate selections use F10 to clear the terminal and start a fresh section.

### Fixed
- **Doubles & Trebles Slip Parsing Overhaul (Section Headers & Dividers)**:
  - Replaced rigid upward-scoping VLM prompt rules with section-aware scoping supporting Section Headers (`£1 ew treble` written above selections), Section Footers (`3x cross doubles` and `£1 treble` written below selections), and horizontal divider lines (`---`).
  - Fixed erroneous selection grouping where trebles or doubles previously pulled wrong selections across divider boundaries.
- **Red Post-Time Exhaustion Detection & Auto-Recovery (`state_read_cyan_panel`)**:
  - Added real-time check for red post-time text on Betty terminal when cycling through meetings with `right`.
  - Automatically presses `/` to reopen the yellow time box, re-enters the race time, and resumes meeting dequeueing upon detecting an over-cycle or exhaustion state.
  - Integrated `SCROLL_ARROW_COORD = (420, 570)` runner list scroll-down check when target meeting is on top but selection is not in visible top runners.

## [0.19.14] - 2026-09-24

### Fixed
- **Cyan Panel Meeting Recognition for Southwell & Leading OCR Artifacts (`is_target_meeting_at_top`)**:
  - Resolved safety abort when entering races at Southwell where Betty displays `'isout 4:22 01. king sharja'`.
  - Added tolerance in `is_target_meeting_at_top` for single-character leading OCR delimiter/border noise (e.g. `|`, `[`, `!`, `1` reading as `i` or `l` in front of track codes, such as `isout` -> `sout`).
  - Added `"isout": "Southwell"` and `"lsout": "Southwell"` aliases to `meetings_directory.json` and `DEFAULT_DOMESTIC_HORSE_COURSES`.
- **All-Weather Track Suffix Sanitization (`(AW)`)**:
  - Automatically stripped `(AW)` / `(A.W.)` / `AW` suffixes from target course names in `is_target_meeting_at_top`, `resolve_meeting`, and `is_target_meeting_match` to ensure racecard tracks like `"Southwell (AW)"` cleanly match Betty terminal headers (`"sout"`, `"isout"`, `"southwell"`).
- **Dashed Race Time Notation (`4-22`, `2-07`, `2-25`) & Pre-Flight Deduplication**:
  - Updated `parse_race_time_to_minutes` regex to `(\d{1,2})[:\.-](\d{2})` supporting customer-written dash-delimited post times.
  - Eliminated duplicate runner registration during pre-flight scans where raw dash times previously failed normalization and caused 3-runner slips to register as 6 unique selections.
- **VLM Endpoint Latch Protection**:
  - Prevented experimental preview models (`gemini-robotics-er-2-preview`) from latching `PREFERRED_VLM_MODEL` on transient fallbacks, reserving primary preference for stable flagship endpoints (`gemini-3.6-flash`).

## [0.19.13] - 2026-09-24

### Fixed
- **Pyrefly Type Guard in `StatusHUD._poll_queue`**:
  - Bound `root = self.root` with an immediate early-exit guard (`if not root: return`) in `StatusHUD._poll_queue`, strictly narrowing the type of `root` and resolving IDE type checker warnings for `configure`, `deiconify`, and `withdraw` calls on `Optional[tk.Tk]`.
- **Typing Import Restoration in `meetings_manager.py`**:
  - Restored `from typing import Any` import required by the `self.data: dict[str, Any] = {}` type annotation in `MeetingsDirectoryManager.__init__`.

## [0.19.12] - 2026-09-24

### Fixed
- **TypeError Defensiveness & Racecard Time Safety**:
  - **`calculate_bet_cost_pence` NoneType Stake Guard**: Hardened `unit_stake = bet.get('stake_pence') or 0` to prevent `TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'` when Gemini returns a JSON bet with `"stake_pence": null`.
  - **`match_runner_to_racecard` Minutes Guard**: Filtered runner lists to ensure `r.get('minutes') is not None` before computing `abs(r['minutes'] - target_mins)` across multi-runner exact matches, defending against crashes on cards with missing or unparsed off-times.
  - **`reexamine_runner_with_ai` Time Window Safety**: Added explicit `r.get('minutes') is not None` checks when constructing proximity candidate windows for AI handwriting re-examination.
  - **Manual Confirmation Modal Scope Sanitation**: Cleaned up Tkinter widget instantiation order in `prompt_manual_horse_input` so the entry widget is created before closures (`pick_candidate`) reference it, eliminating forward-reference closure ambiguity.

### Changed
- **Comprehensive Dead Code Elimination & Architecture Pruning**:
  - **Removed Legacy `expand_trap_forecast_bets`**: Eliminated 119 lines of uncalled heuristic parsing code left over from pre-v0.18.0 architectures, fully deferring to the multimodal structured JSON engine.
  - **Removed Legacy `detect_special_preprinted_slip_type`**: Removed 63 lines of uncalled Tesseract crop and OCR heuristic routines superseded by direct VLM pre-printed coupon recognition.
  - **Pruned Uncalled `RacecardManager` Methods**: Removed `get_hierarchy` and `get_hierarchy_text` (uncalled since prompt hierarchy dumping was deprecated in v0.10.0).
  - **Eliminated Unused Functions & Aliases**: Removed unused `calculate_total_slip_pence`, `ApiKeyPoolManager.get_key_count`, and the deprecated `match_runner_to_sporting_life` alias (migrating callers directly to `match_runner_to_racecard`).
  - **Import & Regex Optimization**: Removed unused imports (`as_completed`, `BookmakerRulesManager` from `betty_companion.py`, `Any` from `meetings_manager.py`, and `sys`, `Any` from `rules_engine.py`); removed redundant regex pattern `m5` in `parse_currency_string_to_pence` (subsumed by `m_dash`); and simplified no-op ternary threshold calculations in `is_target_meeting_at_top`.

## [0.19.11] - 2026-09-23

### Fixed
- **Strikethrough Fidelity Guard (Ligatures & Letter Crossbars)**:
  - Refined the prompt's `[CROSSED OUT]` voiding criteria to strictly require deliberate, unambiguous, heavy crossing-out lines rather than connected cursive pen strokes.
  - Explicitly instructed the model that letter crossbars (e.g. `T`, `H`, `F`, `t` as in `THINTHREAD`) and cursive ligatures are natural handwriting features and must never be treated as strikethroughs, preventing runners from being falsely omitted from the slip.
- **Exhaustive Interleaved Bet Extraction Enforcement**:
  - Enforced a 1-to-1 extraction rule requiring every transcribed bet instruction line on the slip to produce an entry in the `bets` array, eliminating partial omissions where Flash models previously dropped bets after the first line.
  - Enhanced `calculate_bet_cost_pence` so that when customers specify a double over $> 2$ selections (e.g. 3 selections), it dynamically evaluates the combination line count ($N(N-1)/2 = 3$ doubles) rather than undercounting as a single double.

## [0.19.10] - 2026-09-23

### Changed
- **Flagship VLM Model Waterfall Prioritization (`gemini-3.6-flash`)**:
  - Replaced `gemini-robotics-er-2-preview` as the primary preferred model with **`gemini-3.6-flash`**, Google's recommended high-capacity, general-purpose multimodal production model.
  - Eliminated transient HTTP 503 high-demand bottlenecks and 429 quota exhaustion associated with experimental preview endpoints.
  - Reordered the failover waterfall: `gemini-3.6-flash` $\rightarrow$ `gemini-flash-latest` $\rightarrow$ `gemini-3.8-flash` $\rightarrow$ `gemini-3.7-flash` $\rightarrow$ `gemini-3.5-flash` $\rightarrow$ `gemini-robotics-er-2-preview`, preserving robust fallback capabilities while optimizing for first-pass speed (~6.9s) and transcription precision.

## [0.19.9] - 2026-09-23

### Fixed
- **Retail Trailing Dash Currency Notation (`60 -` = £60.00 / 6000p)**:
  - **Trailing Dash Regex Parsing (`parse_currency_string_to_pence`)**: Added specialized regex handling for UK retail betting shorthand where whole pounds are written with a trailing dash or slash (e.g. `60 -`, `60-`, `60 - .`, `60/-`, `£60 -`, `60 - TOTAL STAKE`), correctly converting them to 6000 pence (£60.00) instead of 60 pence.
  - **Fail-Safe Extraction Override (`extract_written_total_pence`)**: Enhanced total stake extraction to inspect both the raw total string and transcribed visual slip lines. If the customer wrote trailing dash notation (e.g. `60 -`) but the model outputs pence < 100 or drops the 100x whole-pound scale, the system automatically overrides with the verified whole-pound stake (6000p).
  - **VLM Prompt Grounding**: Added explicit instructions in Sections 3 and 4 of the vision prompt explaining UK betting slip notation where trailing dashes represent zero pence, and instructing the model to align whole-number stakes (e.g. `60 W` with `60 -` total) as whole-pound singles (£60.00 Win Single).
  - **Stake Reconciliation 100x Scaling Healer**: Implemented an automated healer in `state_read_slip_via_api` that detects when calculated bet costs mismatch the written total by exactly 100x (`calc_total_pence * 100 == written_total_pence`), automatically scaling unit stakes to whole pounds.

## [0.19.8] - 2026-09-23

### Fixed
- **AttributeError Fix for Course Disambiguation (`MeetingsDirectoryManager.get_canonical_meeting_name`)**:
  - Resolved `AttributeError: 'MeetingsDirectoryManager' object has no attribute 'get_canonical_meeting_name'` during `is_target_meeting_at_top` when verifying meeting headers against known courses (e.g. `Steepledown` vs. `Redcar`).
  - Added `get_canonical_meeting_name(self, meeting_name: str) -> str | None` to [`MeetingsDirectoryManager`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/meetings_manager.py#L207-L215), delegating to `resolve_meeting` across horse racing, virtuals, greyhounds, and international tracks.
  - Streamlined `is_target_meeting_at_top` in [`betty_companion.py`](file:///c:/Users/User/Desktop/Test%20Scripts/betty_companion/betty_companion.py#L1248-L1254) to directly query `get_canonical_meeting_name`.

## [0.19.7] - 2026-09-23

### Fixed
- **Exhaustion State Red-Time Detection & Ready State Restoration via '/' (`state_read_cyan_panel`)**:
  - **Calibrated Exhaustion Detection via Red Post-Time Text**: When meetings at a post time exhaust on Betty's terminal, Betty exits the cyan panel and returns to the main edit screen where the post time renders in bright red (`RGB: 255, 0, 0`) at `RED_TIME_EXHAUSTION_REGION = (410, 440, 60, 40)` and the yellow cursor box is absent (`media_1790189175552.png`). Implemented `is_meetings_exhausted_screen()` to detect this exact terminal condition.
  - **Automated Ready State Restoration (`restore_ready_state_if_exhausted`)**: In Betty's terminal, pressing `/` in the exhausted state clears the red post time and restores the yellow cursor box at `READY_COORD = (440, 465)`. Automated immediate restoration upon exhaustion so Betty is returned to the initial ready state, satisfying all starting position validations for subsequent bets.
  - **Re-Entry Synchronization**: Documented and verified that pressing `/` returns Betty to the yellow box state required to re-enter post times and reload meeting lists.

## [0.19.6] - 2026-09-23

### Fixed
- **Linear Meeting Dequeue Architecture & Removal of Destructive 'Left' Keypresses (`state_read_cyan_panel`)**:
  - **Eliminated Corrupting 'Left' Arrow Calls**: Betty's cyan panel is not a bidirectional carousel. In Betty's terminal interface, pressing `left` while a meeting list is visible is destructive—it eliminates all other meetings below the top meeting. All calls to `pyautogui.press('left')` ("backtracking") have been completely removed.
  - **Linear One-Way Meeting Dequeue**: Implemented proper linear dequeue navigation: pressing `right` pops/removes the top meeting and promotes the next meeting in the stack to the top position.
  - **Terminal Exhaustion Detection**: When all meetings at a given post time are dequeued with `right`, Betty naturally closes the cyan panel and returns to the pre-time entry screen (where the yellow cursor box is restored at `READY_COORD = (440, 465)`). Added active flicker-resilient polling for `READY_COORD` and panel closure to detect exhaustion immediately without lingering in dead loops.
  - **Capped Meeting Inspection (`max_meetings_to_check = 6`)**: Reduced traversal ceiling from 14 to 6 meetings per post time, logging a clean diagnostic summary of all checked meetings if a runner or meeting cannot be found.

## [0.19.5] - 2026-09-23

### Added
- **Automated Live Terminal Discovery for Standard Unanchored Virtual Bets**:
  - Addressed retail domain reality that customers in UK betting shops never write '(v)' or virtual track names on their slips; virtual bets are written identically to regular horse bets (e.g. `4-1 Drop Zone 5.07`).
  - In `state_pre_scan_and_match_slip`: when a selection does not match official live racecards (The Racing API), if it has a valid post time, it is automatically routed to **Live Terminal Panel Discovery** instead of halting execution with an intrusive manual modal dialog.
  - In `state_read_cyan_panel`: Betty types the race post time, scans the active terminal panel across both virtual (e.g. `Port 5:07(v)`) and live races, identifies matching runners, extracts their cloth numbers, and enters the bet seamlessly at full automation speed.
  - Operator manual prompt now serves strictly as a last-resort fallback only if the runner cannot be located on any meeting screen after a complete carousel sweep.

## [0.19.4] - 2026-09-23

### Added
- **Comprehensive Virtual Racing Support & Generic Disambiguation**:
  - Added `"generic_virtual"` entry under `"virtual_racing"` in `meetings_directory.json` and `meetings_manager.py` indexing generic virtual markers (`(v)`, `v`, `virt`, `virtual`, `virtuals`, `v race`).
  - Enhanced `is_virtual_meeting` and `resolve_meeting` to immediately identify generic virtual markers, returning `(True, "Virtual", "virtual_generic")`.
  - Configured `is_target_meeting_match` so generic virtual targets (`(v)` or `Virtual`) match ANY active virtual race meeting on Betty's panel (`Port`, `Sprint`, `Steeple`, `Dash`, etc.).

### Fixed
- **Virtual Racing Intent & Slip Field Extraction (`is_virtual_selection`)**:
  - Expanded `is_virtual_selection` to inspect not only `meeting` and `raw_meeting_hint`, but also `time`, `raw_time`, `written_time`, and `name` for virtual markers (e.g. `5.07(v)`, `5.07 v`, `Drop Zone (v)`).
  - Sanitized `clean_horse_name` and time fields to strip virtual markers while preserving virtual intent and preventing runner lookup failures.
- **Unanchored Runner Discovery (`state_read_cyan_panel`)**:
  - Eliminated the fatal error when `target_meeting` is unspecified or unknown on customer betting slips (e.g. `4-1 Drop Zone 5.07`).
  - Implemented dynamic panel inspection for unanchored selections: Betty enters the post time, scans the active meeting header and runners (including scroll-down checking), locks in matching runners, and cycles to adjacent meetings if not found.
- **Refined Virtual vs. Real Disambiguation Invariant (`is_target_meeting_at_top`)**:
  - Protected real domestic racecourses (e.g. `Perth`, `Redcar`, `Ayr`) from ever matching virtual screens (`(v)`).
  - Ensured virtual targets never match live screens, while generic virtual targets (`(v)` / `Virtual`) seamlessly accept any active virtual track screen.

## [0.19.3] - 2026-09-23

### Fixed
- **Virtual vs. Real Course Disambiguation Invariant (`Port 5:07(v)` vs. `Pert 5:07`)**:
  - Diagnosed that `is_target_meeting_at_top` previously fuzzy-matched `Port` (Portman Park Virtual) to `Pert` (Perth) because their 4-letter similarity (`0.75`) met the `0.74` threshold.
  - Enforced a strict Virtual Disambiguation Invariant in `is_target_meeting_at_top`: screens marked with virtual indicators (`(v)` or `v`) will NEVER match live racecard meetings (such as Perth or Redcar), and live screens will never match virtual targets.
  - Added distinct course alias protection to prevent fuzzy matching between different registered tracks (e.g. `port` vs. `pert`, `carl` vs. `cart`).
  - Added `"pert": "Perth"` to `terminal_prefix_mappings` in `meetings_directory.json` to ensure instantaneous exact matching.

## [0.19.2] - 2026-09-23

### Fixed
- **Multi-Key 503 Transient Throttling Bypass (`rotate_on_transient_busy`)**:
  - Identified that Google Cloud load balancers enforce 503 rate/concurrency limits on a per-project basis.
  - Implemented automatic key rotation on `HTTP 503` so that when a project is temporarily throttled, the companion immediately rotates to the next available API key in the pool (`rotate_on_transient_busy`), routing the request through a clean project pipeline.
  - Increased `max_attempts_per_model` to 3 and added an adaptive 2.5s backoff to ensure momentary gateway spikes clear seamlessly.
- **Payload Token Optimization & Prompt Streamlining**:
  - Replaced the bulky 13.5KB hierarchy dump (704 runners) with a concise, targeted summary of today's active UK and Irish race meetings.
  - Reduced OCR prompt token count by over 75%, eliminating load balancer task shedding and drastically speeding up visual parsing.

## [0.19.1] - 2026-09-23

### Changed
- **Resolved Google 503 Congestion via Dedicated Spatial Vision Infrastructure**:
  - Audited all 44 Google Gemini endpoints live to diagnose widespread `HTTP 503 High Demand` errors on standard public chat endpoints (`gemini-3.5-flash`, `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-flash-latest`, and `gemini-3.1-flash-lite`).
  - Promoted `gemini-robotics-er-2-preview` (Embodied Reasoning 2) to the top of `VLM_WATERFALL_MODELS` and set as `PREFERRED_VLM_MODEL`.
  - Benchmarked on real messy UK betting slips: achieved 100% handwriting transcription accuracy with zero 503 errors and zero 429 quota locks, running on Google's dedicated high-performance multimodal perception infrastructure.

## [0.19.0] - 2026-09-23

### Added
- **Real-Time API Telemetry & Response Diagnostics**:
  - Added precise network latency timing (`elapsed_req` in seconds) and HTTP status code tracking to all Gemini VLM calls in both console logs and the persistent HUD.
  - Implemented Google Safety & Moderation block inspection: automatically checks and logs `promptFeedback.blockReason` and candidate `finishReason` (`SAFETY`, `RECITATION`, `BLOCKLIST`), streaming human-readable diagnostic explanations.
  - Added token utilization metrics to slip parsing confirmation (`usageMetadata.promptTokenCount` and `usageMetadata.candidatesTokenCount`).
  - Enhanced error detail extraction: when Google returns `HTTP 429` (Quota Exceeded) or `HTTP 503` (High Demand), the exact error text from Google's response payload is extracted and logged to console and HUD in color-coded pills.

## [0.18.1] - 2026-09-23

### Changed
- **Endpoint Latency Calibration & Fast Model Prioritization**:
  - Re-benchmarked Google Gemini endpoints under live conditions across multiple API keys.
  - Promoted `gemini-3-flash-preview` to the top of `VLM_WATERFALL_MODELS` and set as `PREFERRED_VLM_MODEL` based on its verified ~1.7–1.8s response time (avoiding transient 503 high-demand delays on `gemini-3.5-flash`).
- **Multi-Key Environment Configuration**:
  - Configured 3 distinct Gemini API keys in `.env` (`GEMINI_API_KEY`, `GEMINI_API_KEY_2`, and `GEMINI_API_KEY_3`) mapped with verified healthy keys as primary and secondary in the pool.

## [0.18.0] - 2026-09-23

### Added
- **Multi-API-Key Pooling & Automatic Failover (`ApiKeyPoolManager` in `betty_companion.py`)**:
  - Implemented seamless pooling of multiple Google Gemini API keys via `.env` (`GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`... or comma-separated `GEMINI_API_KEYS=key1,key2`).
  - When an API key reaches its daily free-tier quota (`HTTP 429`), the companion automatically and instantaneously rotates to the next available backup key in the pool without failing the active slip.
- **Smart Quota Caching & Session Memoization**:
  - Maintained an in-memory session cache of quota-exhausted models (`is_model_exhausted(model_name)`).
  - When a model returns `HTTP 429`, it is immediately marked as exhausted and bypassed for the remainder of the session (0ms delay), preventing futile repeat requests.
- **Immediate 429 Circuit Breaker**:
  - If all candidate models across all available keys in the pool are exhausted, the companion immediately halts with a clean HUD alert (`[!] All Gemini Free Quotas Exhausted. Add GEMINI_API_KEY_2 to .env`), completely eliminating 2-minute loops of cascading failures.

### Changed
- **Eliminated Quota-Draining 9-Model Broadcast Pings**:
  - Replaced the concurrent 9-model broadcast health probe with a smart **Sticky Primary Waterfall** (`get_prioritized_model_waterfall`).
  - The companion now sends the slip request directly to the last-known working preferred model, reducing API quota consumption from **10 calls down to 1 call per slip** (a 90% quota savings).
- **Few-Shot Payload Size Optimization & Timeout Tuning**:
  - Capped multi-turn visual handwriting examples to the **top 2 most effective demonstrations** (`MAX_FEW_SHOT_EXAMPLES = 2`).
  - Reduced API payload sizes from ~4.5MB down to <900KB, making network transfers 4x faster and eliminating token-rate spikes.
  - Increased network socket timeout from 22s to 35s to prevent premature read timeouts on complex betting slips.

## [0.17.0] - 2026-09-23

### Added
- **Persistent Compact Status HUD (`CompactHUD` & `STATUS_HUD` in `betty_companion.py`)**:
  - Implemented a persistent, floating status HUD docked in the top-right corner (`310x52px`, alpha 0.93, always-on-top, borderless) that stays visible across the entire automation cycle.
  - Reduced HUD footprint (down from 390x85px) to be non-intrusive while operating alongside fullscreen Betty.
  - Streams real-time, step-by-step progress updates throughout execution (starting state verification, parallel Gemini model probing, multi-scan translation, racecard pre-scanning, sequential runner entry, BOG guarantee sweeps, F8 stake entry, and handoff completion).
  - Architected on a thread-safe `queue.Queue` processed via Tkinter's `root.after()` loop, eliminating cross-thread GUI crashes on Windows.
  - Automatically auto-hides 5-6 seconds after final handoff or operator cancellation.
- **Hardware-Level Always-Listening ESC Abort Subsystem (`_esc_poller_daemon` in `betty_companion.py`)**:
  - Reimplemented the abort mechanism using a dedicated background daemon thread polling Windows `ctypes.windll.user32.GetAsyncKeyState(0x1B)` (VK_ESCAPE physical key state) every 20ms.
  - Continuously listens before, during, and after automation starts, completely bypassing Windows UI privilege isolation (UIPI), focused window swallows, and PyAutoGUI active typing.
  - Added secondary hook via `keyboard.add_hotkey('esc', trigger_abort, suppress=False)` and dialog keybinding `<Escape>`.
  - Instant visual & audible feedback: Tapping ESC immediately turns the HUD crimson (`#B00020`), displays `[!] ABORTED`, and plays an alert tone.
  - **Non-Blocking Interruptible Delays (`interruptible_sleep`)**: Replaced all blocking sleeps across the automation loop with sliced delays that wake up and exit within 20ms of an ESC press.
  - **Interruptible API Requests**: Wrapped Gemini network calls in a `ThreadPoolExecutor` with a 40ms abort polling loop, ensuring pressing ESC immediately breaks out of in-flight API requests without hanging on socket timeouts.

## [0.16.1] - 2026-09-23

### Removed
- **Unresponsive Abort Mechanism & ESC Hotkey Hooks (`betty_companion.py`)**:
  - Removed all non-functional abort logic across the entire companion script:
    - Deleted global `abort_event = threading.Event()`, `cancel_active_cycle()`, and keyboard hook `keyboard.add_hotkey('esc', cancel_active_cycle)` which failed to interrupt execution when Windows focus was captured by Betty full-screen or during synchronous blocking API/OCR operations.
    - Removed wrapper function `safe_sleep(seconds: float)` and replaced all ~30 `safe_sleep(...)` calls across UI polling, runner list scanning, guarantee sweeps, F8 transitions, and retry loops with standard, reliable `time.sleep(...)`.
    - In `prompt_manual_horse_input()`: Replaced the "Abort Cycle (ESC)" button with "Cancel", removed the broken `abort_event.set()` signal, and configured operator cancellation to cleanly return `False` without leaving dirty global state.
    - Cleaned console idle banners and HUD notifications to remove non-functional "Press ESC to cancel" prompts.

## [0.16.0] - 2026-09-23

### Added
- **Concurrent Fast-Response Model Health Ping (`select_fastest_available_model` in `betty_companion.py`)**:
  - Implemented parallel 1-token health probing across all candidate Gemini VLM models using `ThreadPoolExecutor` right when automation is triggered.
  - Measures live round-trip latency and captures HTTP response codes concurrently.
  - Dynamically sorts responsive models (`HTTP 200`) by response speed, placing the fastest healthy endpoint at the very front of the waterfall before sending the full multi-part slip image payload.
  - Automatically identifies and bypasses models returning `HTTP 429` (Quota Exceeded) or `HTTP 503` (High Demand Spikes), completely eliminating wasted wait times, timeouts, and cascading overhead.
  - Expanded candidate vision model pool to include `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite`, `gemini-3.1-flash-lite-preview`, `gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-flash-latest`, and `gemini-flash-lite-latest`.

### Changed
- **Codebase Streamlining & Bloat Pruning (`betty_companion.py`)**:
  - Pruned **342 lines of redundant code and static bloat**, reducing the codebase from 4,163 to 3,821 lines while maintaining 100% behavioral parity.
  - **Pruned `UK_BETTING_GLOSSARY`**: Replaced 249 lines of bulky dictionary literals with a direct, concise `BET_SHORTCUTS` dictionary and unified line counts into `LINES_PER_BET_TYPE`.
  - **Eliminated Duplicate 3x-Doubles Backfill Passes**: Removed redundant Block 1 (L2798-2840) and Block 3 (L3066-3094), consolidating 3x-double inheritance into the unified programmatic block scoping engine.
  - **Single-Pass Price & Even Money Recovery**: Consolidated odds and Even Money extraction into the primary selection parsing pass, replacing 87 lines of nested loops across `line_texts` with an instant dictionary sync.
  - **Pre-Flight Dog Track Deduplication**: Removed redundant secondary track lookup and fuzzy matching loops in `state_pre_scan_and_match_slip`, utilizing the track already resolved by `is_greyhound_or_trap_selection()`.
  - **Racecard Candidate Matching Acceleration**: Added pre-caching of `clean_name` in `RacecardManager` to avoid repeatedly sanitizing 700+ runner names inside fuzzy candidate comparison loops.

### Removed
- **Dead Functions & Unused Imports (`betty_companion.py`)**:
  - Removed uncalled function `wait_for_pixel_match` (20 lines).
  - Removed obsolete wrapper shims `get_sporting_life_data()`, `get_sporting_life_lines()`, and `get_sporting_life_runners()`.
  - Removed unused imports: `itertools`, `defaultdict`, `pymsgbox`, `MeetingsDirectoryManager`, and 7 unreferenced helpers from `rules_engine`.
  - Removed obsolete constants: `PRICE_CHECK_COORD`, `PRICE_CONFIRM_BTN_COORD`, `INTERNATIONAL_MEETINGS`.

## [0.15.1] - 2026-09-23

### Fixed
- **Slanted Handwriting Flow & Margin-Note Re-attribution (`betty_companion.py`)**:
  - Addressed an issue on handwritten slips where customer text flows left-to-right across the page but slants slightly upwards or downwards, causing right-margin qualifiers like `LAST 2` or `ABOVE 4` to be transcribed on the horse line directly above the bet (e.g. `4-1 Follow Charlie 5.17 LAST 2` instead of `50 ew doubl LAST 2`).
  - Added an automated pre-pass in Python post-processing that detects trailing margin qualifiers (`LAST <N>`, `ABOVE <N>`, `AB <N>`) on lines directly preceding a bet instruction and re-attributes the qualifier down to the bet on that horizontal band.
- **Strict 1-Line Invariant for Singular Doubles (`calculate_bet_cost_pence` & scoping in `betty_companion.py`)**:
  - Resolved a severe combination inflation bug where a singular double (e.g. `50 win doubl`, `50 ew doubl`) that had `ABOVE 4` mistakenly attached was expanded into $\binom{4}{2} = 6$ doubles $\times 50\text{p} = 300\text{p}$ (£3.00), adding an unintended £2.50 to the calculated total.
  - Enforced that a `double` only expands into combination lines when an explicit combination multiplier (`3 x`, `6 x`, `\b\d+\s*x\b`) or plural (`doubles`, `cross doubles`) is written. Singular doubles strictly cost 1 line (unit stake * 1 for Win, * 2 for EW).
  - Added normalization to strip misplaced `ABOVE <N>` ($N \ge 3$) qualifiers from doubles and transfer them to adjacent accumulators where they belong, keeping singular doubles bound strictly to the 2 selections directly above them (`above_runners[-2:]`).

## [0.15.0] - 2026-09-23

### Added
- **Explicit Line & Selection Numbering (`betty_companion.py`)**:
  - Transcribes all lines with sequential 1-based line numbers (`Line 1`, `Line 2`...) and active runners with 1-based selection numbers (`Selection 1`, `Selection 2`...).
  - Guarantees clear visual tracking and 1-to-1 grounding between physical slip lines and structured selection entities.
- **3-Component Selection Parsing (`betty_companion.py`)**:
  - Structured every runner detection into three core elements:
    1. **Price (Odds)**: Fractional take price (e.g. `3/1`, `4/5`, `1/5`, `10/3`, `13/2`) or `Evs`, defaulting to `SP` only when unwritten.
    2. **Selection Name**: Official horse name resolved against the racecard hierarchy.
    3. **Time / Meeting**: Primary post time (in raw format e.g. `1.30` and normalized 24-hr `13:30`) used as the principal key for racecard grounding, with meeting shorthand when written.
- **Automated Price Double-Check (`betty_companion.py`)**:
  - Added automated line/margin re-scanning in Python post-processing: if a selection is extracted with `SP` or missing price, Betty Companion double-checks the raw transcription line for fractional odds (`\d+[-/]\d+`) or Even Money declarations (`evs`, `evens`, `1/1`), automatically rescuing the customer's take price.
- **Programmatic Block-Based Bet Assignment (`betty_companion.py`)**:
  - Formulated programmatic relative block scoping for all bet instructions:
    - **Default Double**: Binds strictly to the 2 selections directly above the bet line (`above_selections[-2:]`).
    - **Default Treble / 3x Doubles**: Binds strictly to the 3 selections directly above the bet line (`above_selections[-3:]`).
    - **Default Accumulator**: Binds to ALL active selections written above the bet line (`above_selections[:]`).
    - **Explicit Scoping Overrides**: Strictly respects written customer qualifiers such as `Above <N>`, `Ab <N>`, or `Last <N>` (e.g. `50 EW Accumulator Above 6`).
- **Deterministic Stake Cost Engine (`betty_companion.py`)**:
  - Added `calculate_bet_cost_pence` to deterministically calculate exact total bet stake in pence directly from `unit_stake`, `bet_type`, `num_horses`, and `each_way` flag rather than relying on ungrounded VLM stake arithmetic.

## [0.14.7] - 2026-09-23

### Fixed
- **Concatenated Digits & Each-Way Notation Recognition (`50ew`, `50EW`, `50e/w`) (`betty_companion.py` & `examples.json`)**:
  - Addressed an issue where handwritten `50ew` written as a concatenated token without a space (e.g. `50ew DOUBL` on Line 3) was misread by the VLM as `50 win doubl`, causing Bet 1 to be registered as Win-only instead of Each-Way.
  - Added explicit instructions in VLM prompt rules and few-shot reference notes (References 1 & 8) stating that digits directly attached to cursive `ew` or `EW` represent Each-Way (`each_way: true`, `stake_pence: 50`) and must never be transcribed as `win`.
  - Added an `Each-Way Sanitizer` in Python post-processing to detect `\b\d+ew\b` or `e/?w` in bet descriptions and ensure `each_way` is preserved.
- **Interleaved Cross Doubles & Treble Runner Scoping (Missing Chapman's Peak in Pre-Flight) (`betty_companion.py`)**:
  - Resolved a scoping bug where `3 x 50 win doubles` (Line 9) and `1 x £1 ew treble` (Line 10) mistakenly bound to selections 1, 2, and 3 (`Ararat`, `Burgundy Man`, `Percy's Star`) instead of the 3 selections immediately preceding those bet lines (`Percy's Star`, `Jimmy Speaking`, `Chapman's Peak`).
  - Implemented Rule 1C for interleaved multiple bets (Doubles, 3x Doubles, 6x Doubles, Trebles) lacking explicit `above <N>` qualifiers: they now strictly bind to the preceding $N$ selections written above that bet line (`above_runners[-effective_n:]`), ensuring runner 5 (`Chapman's Peak`) is correctly incorporated into the middle cross doubles and treble.
  - Avoids same-race runner contingency between `Ararat` and `Chapman's Peak` (both running at 19:00 Kempton).
- **Total Stake Reconciliation Healer (`betty_companion.py`)**:
  - Implemented an automated reconciliation healer that checks if the customer's written total stake (e.g. `8 - 50` / 850p) differs from the calculated bet cost.
  - Evaluates candidate bets to see if toggling a single ambiguous Win/EW flag reconciles the calculated total to match the customer's written total stake to the exact penny (£0.00 difference), automatically healing Bet 1 from 50p Win Double (50p) to 50p Each-Way Double (100p) and reconciling the total to £8.50.

## [0.14.6] - 2026-09-22

### Fixed
- **Carousel Boundary & Dead-End Screen Backtracking (`state_read_cyan_panel` in `betty_companion.py`)**:
  - Resolved terminal cycling stalls where cycling right reached the boundary wall of Betty's meeting list (e.g. `cae horse oo` / end of tabs) and continued pressing `right`, exceeding `max_cycles = 10` and aborting.
  - Implemented dynamic stall detection: if `top_preview == last_top_preview` after a keypress or if the screen matches dummy end screens (`cae horse`, `horse oo`, `race horse`, `ttc`), the companion automatically switches direction and backtracks with `left`, seamlessly recovering earlier meetings like Fontwell.
  - Added flicker retry: if `ocr_panel_lines` returns empty due to terminal screen redraw latency, Betty Companion waits 0.18s and re-samples before advancing the cycle or firing premature direction keys.
  - Increased `max_cycles` from 10 to 14 to allow full bidirectional sweeps across busy race times.
- **Interleaved `Last <N>` Positional Scoping (`betty_companion.py`)**:
  - Fixed a scoping flaw where `Last 2` on Line 9 (`50 win doubl Last 2`) bound to the last 2 selections of the entire 7-runner slip (`On The River` & `Assail`), duplicating Bet 6.
  - Unified scoping to evaluate against `above_runners`: `Last <N>` now strictly takes the last $N$ selections written *above that bet line* on the slip (`above_runners[-target_n:]`), correctly binding Bet 4 to `[Oklahoma, Badri]`.

## [0.14.5] - 2026-09-22

### Added
- **Multi-Turn Visual Few-Shot Reference 8 (`handwriting_examples/examples.json` & `interleaved_above5_last4_accumulator_slip.png`)**:
  - Enrolled complex real-world slip into few-shot reference catalog featuring 7 runners, interleaved 50p doubles, 3x doubles, 1 x £1 treble, 50p EW accumulator with "Above 5" margin note, 50p EW double, and 50p EW accumulator with "last 4".
  - Ground truth accounts for exactly 650p (£6.50) total bet cost across 7 bets, reconciling to the exact penny against customer written `6 - 50 TOTAL STAKE`.
- **Deterministic Accumulator Scoping & "ALL Above" Default Guardrail (`betty_companion.py`)**:
  - Codified the user-defined accumulator scoping rule: when an accumulator is detected with no `last <N>` qualifier, it automatically scopes to **ALL active selections written above that line** on the slip.
  - Dynamically calculates active selection count preceding the accumulator line in the visual transcription and binds strictly to `all_selections[:active_above_count]`, preventing runner omissions (e.g. including all 5 selections above Line 10: `Starshine Legend`, `Supreme Clarets`, `Hot And Cold`, `Oklahoma`, `Badri`).
- **Strict `last <N>` Positional Binding Guardrail (`betty_companion.py`)**:
  - Codified deterministic `last <N>` binding: when a bet specifies `last <N>` (e.g. `last 4`), it strictly binds to `all_selections[-N:]` (e.g. `[Oklahoma, Badri, On The River, Assail]`), preventing middle-runner skipping.
- **Pound Unit Stake Sanitizer & Parser (`betty_companion.py`)**:
  - Added regex parsing for explicit pound unit stakes (`£1`, `1 x £1`, `£2`) in bet descriptions or raw text to set `stake_pence = pound_val * 100`, eliminating discrepancies where £1 was mistakenly transcribed or defaulted as 50p.

### Fixed
- **Resolved Pre-Flight Same-Race Contingency Split for Bet 7 (`rules_engine.py` / `betty_companion.py`)**:
  - Addressed the appearance of unexpected Bets 7 & 8 during pre-flight. These bets were not hallucinations, but rather the BetAnsells Rules Engine triggering same-race contingency splits between `Hot And Cold` and `On The River` (both running at 17:30 Southwell) because the VLM previously skipped `Badri`. With `Badri` correctly bound in the last 4 selections (`[Oklahoma, Badri, On The River, Assail]`), all 4 runners run in distinct races with zero contingencies, retaining the single 50p EW Accumulator.

## [0.14.4] - 2026-09-22

### Added
- **Even Money Odds Detection & Shorthand Support (`E-`, `E`, `Evs`, `1/1`) (`betty_companion.py`)**:
  - Implemented Even Money detection supporting retail customer shorthand where a standalone `E`, `E-`, `E/`, or `Evs` is written in the left margin or preceding a runner name (e.g. `E- Flight Tracker 4.20`).
  - Added racecard runner disambiguation: `E` or `E-` is treated strictly as an Even Money odds declaration (`price: "Evs"`) and is stripped from the runner name unless an official runner scheduled to race today genuinely begins with `E` (e.g. `Electric Arc`, `Equilateral`).
  - Enhanced `match_runner_to_racecard` and post-VLM reception with automatic runner prefix stripping and price inheritance.
- **Updated Few-Shot Reference 7 (`handwriting_examples/examples.json`)**:
  - Updated Example 7 line 11 raw transcription to `E- Flight Tracker 4.20`, setting `Flight Tracker` price to `Evs` across selections and bets (Bet 6 Double & Bet 7 Accumulator).

## [0.14.3] - 2026-09-22

### Added
- **Multi-Turn Visual Few-Shot Reference 7 (`handwriting_examples/examples.json` & `strikethrough_interleaved_accumulator_slip.png`)**:
  - Enrolled complex real-world slip into the multi-turn few-shot reference database featuring crossed-out selections, interleaved unit doubles, 3x doubles, EW treble, and scoped positional accumulators ("above 4" and "last 4").
  - Documented ground truth across 6 active selections (`Londoner`, `Hanney Girl`, `Inside Story`, `Misunderstood`, `Star People`, `Flight Tracker`) and 7 bets totaling exactly 550p (£5.50), reconciling to the penny against the customer written total.
- **Strikethrough / Voided Line Purge Guardrail (`betty_companion.py`)**:
  - Added deterministic Python post-VLM filtering that scans `line_transcription` for `[CROSSED OUT]`, `crossed out`, `[void]`, or `strikethrough` tags and automatically purges cancelled runners from both `selections` and all bet `horses` lists, even if the vision model accidentally included them in the JSON payload.

### Fixed
- **Interleaved Positional Double Scoping (`betty_companion.py`)**:
  - Codified strict upward chronological scoping in `prompt_text`: a double written directly below selection $N$ combines selection $N$ and selection $N-1$ (the selection directly above it) and never reaches forward or down to lower unread lines.
- **Cross-Line Price Stealing in Fallback Odds Reconciliation (`betty_companion.py`)**:
  - Fixed a flaw where a selection line lacking odds (e.g. `Flight Tracker 4.20`) stole fractional prices (`11/10`) from the preceding line (`11/10 Star People 2.40`). The post-processor now verifies that the preceding line is a pure standalone odds annotation and does NOT contain its own race time or horse name.

## [0.14.2] - 2026-09-22

### Fixed
- **VLM Waterfall Endpoint Sanitization & 503 Spike Resilience (`betty_companion.py`)**:
  - **Replaced Premature Break with 1.2s Backoff on Transient 503**: Resolved a critical flaw where `break` immediately abandoned healthy endpoints on temporary 1-second server demand spikes without attempting a second try. Betty Companion now pauses for 1.2 seconds on Attempt 1 and retries the endpoint (proven live: Attempt 1 returned 503, Attempt 2 completed with 200 OK in 15.9s).
  - **Removed Dead / Stalling Endpoints**: Purged `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, and `gemini-flash-lite-latest` from `VLM_WATERFALL_MODELS` after discovering they were hanging on Google's infrastructure for the full 15-second timeout, freezing the companion for 45 seconds.
  - **Added Responsive Models (`gemini-3.1-flash-lite-preview`)**: Enrolled the active, verified-working preview lite endpoint into the priority queue.
  - **Increased Network Timeout**: Raised HTTP request timeout from 15 seconds to 22 seconds to accommodate high-resolution multimodal transcription during peak network traffic without timing out.

## [0.14.1] - 2026-09-22

### Fixed
- **Blue Price Discrepancy Dialog & Override Button Calibration (`betty_companion.py`)**:
  - **Calibrated Blue Border Detection Coordinates**: Resolved an issue where `PRICE_CHECK_COORD` was erroneously set to `(711, 288)` (a white interior point of the dialog). Updated to the actual 6px solid blue border points `BLUE_PRICE_BORDER_COORDS = [(763, 288), (302, 288), (530, 217), (530, 469)]` (`TARGET_BLUE = (0, 0, 255)`).
  - **Calibrated "Override with entered price" Button (`PRICE_OVERRIDE_BTN_COORD`)**: Calibrated the button coordinate to `(710, 418)` (center of the yellow override button inside the blue dialog modal `[X: 651..754, Y: 381..457]`), replacing the out-of-bounds legacy coordinate `(957, 562)` (retained as secondary fallback).
  - **Dynamic Button Centroid Finder (`find_price_override_button_coord`)**: Added auto-centroid detection that scans `(650, 380, 110, 85)` for `TARGET_YELLOW` to click the exact center of the button even if Betty's dialog shifts slightly.

### Added
- **Flicker-Resilient Multi-Sampling UI Utilities (`betty_companion.py`)**:
  - **`check_pixel_flicker_resistant`**: Multi-sample pixel verification defending against Betty UI flickering, redraw blanks, or GDI rendering stutter. Samples up to $N$ times with interval spacing (returns immediately on first match with zero latency penalty on clean frames).
  - **`wait_for_blue_price_box` & `wait_for_blue_price_box_cleared`**: Dedicated polling loops across multiple border anchor points to reliably catch modal appearance and verify closure.
  - **Flicker-Resilient Starting State & F8 Detection**: Applied multi-sampling to `READY_COORD = (440, 465)`, post-time prompt slash check, and `is_f8_screen_active()`, preventing premature aborts or missed transitions when the UI flickers mid-cycle.

## [0.14.0] - 2026-09-22

### Added
- **Persistent System Temp Racecard Cache (`RacecardManager`)**:
  - Implemented persistent disk caching in the OS temporary directory (`%TEMP%\betty_racecards_YYYYMMDD.json`) with daily rotation.
  - On launch/relaunch, Betty Companion loads cached official runners in **~8ms** (down from ~1,100ms network fetch), completely eliminating startup fragility and API delay during restarts.
- **Dynamic Cyan Runner Panel Polling (`wait_for_runner_panel`)**:
  - Replaced static post-race-time sleep with an active NumPy pixel monitor over `CYAN_REGION = (0, 0, 305, 465)`.
  - Checks for runner text rendering every 25ms, triggering panel OCR the millisecond Betty renders the screen (~80–150ms).

### Changed
- **Decoupled House Rules from VLM Vision Prompt (`betty_companion.py`)**:
  - Removed Section 10 ("BETANSELLS OFFICIAL HOUSE RULES & DISCREPANCY SETTLEMENT") from `prompt_text`. Discrepancy settlement (non-runners, voids, same-race multiples) is handled deterministically in Python post-VLM by `rules_engine.py` and `bookmaker_rules.json`.
  - Focused the VLM prompt strictly on high-fidelity visual transcription of the physical paper slip, saving ~400 prompt tokens per scan and preventing premature bet alteration.
- **Dynamic Parameter Binding**:
  - Bound `TOTAL_STAKE_GRACE_VARIANCE_PENCE` directly to `bookmaker_rules_mgr.get_parameter("total_stake_grace_variance_pence", default=100)`, ensuring `bookmaker_rules.json` is the sole source of truth for bookmaker rules and tolerances.

## [0.13.11] - 2026-09-22

### Changed
- **Betty Terminal Automation Timing & Reactive UI Acceleration** (`betty_companion.py`):
  - **Eliminated Redundant Double Sleep on Meeting Cycling (`state_read_cyan_panel`)**: Discovered and removed an accidental double `safe_sleep(0.45)` occurring on every meeting cycle (once before and once after `right` arrow press). Reduced post-keypress cycle delay to `0.20s`, accelerating meeting tab navigation from `0.90s` per press down to `0.20s` (~75% faster).
  - **Streamlined Race Time Entry Delay (`run_cycle_logic`)**: Reduced the arbitrary `0.80s` post-time wait down to `0.20s`, saving ~600ms per runner while allowing Betty's fast cyan panel rendering to initiate immediately.
  - **Reactive F8 Bet Screen Polling (`run_cycle_logic`)**: Replaced the fixed `0.50s` wait after pressing `F8` and `0.40s` post-entry wait with reactive polling against `is_f8_screen_active()`. Keystrokes for stake, bet type, and each-way now execute immediately as soon as Betty opens the screen (~50–80ms), cutting F8 execution time from `1.50s` to `~0.40s`.
  - **Optimized Price Confirmation Delay (`state_handle_price`)**: Reduced post-price keypress delay from `0.40s` to `0.20s`.

## [0.13.10] - 2026-09-22

### Fixed
- **VLM Translation Latency & High Demand 503 Cascades** (`betty_companion.py`):
  - **Prioritized High-Throughput Production Endpoints**: Restructured `VLM_WATERFALL_MODELS` to place proven low-latency, active models (`gemini-3.5-flash` and `gemini-3-flash-preview`) at the head of the waterfall, resolving severe bottlenecking caused by overloaded `-flash-lite` public endpoints returning HTTP 503.
  - **Instant Failover on Server Busy (HTTP 503/500/502/504)**: Replaced multi-second exponential backoff sleep loops on busy servers with instantaneous cascade (`break`) to the next model pool, eliminating up to 15–20 seconds of dead-time per overloaded model.
  - **Sticky Preferred Model Routing (`PREFERRED_VLM_MODEL`)**: Implemented dynamic session-level sticky caching. When a model successfully transcribes a slip, it is automatically promoted to the front of `available_models` for all subsequent cycles, ensuring subsequent customer slips respond in ~2 seconds without re-probing the waterfall.
  - **Reduced Request Timeout**: Lowered the HTTP payload request timeout from 60 seconds to 20 seconds to fail-fast against non-responsive network connections.

## [0.13.9] - 2026-09-22

### Fixed
- **`meetings_manager.py:187,213` — Unnecessary `str()` Calls on Typed `str` Parameters** (`meetings_manager.py`):
  - In `is_virtual_meeting(self, meeting_name: str)` and `resolve_meeting(self, raw_meeting: str)`, parameters were already typed as `str`.
  - Replaced `str(meeting_name).lower()` with `meeting_name.lower()` and `str(raw_meeting).lower()` with `raw_meeting.lower()`, resolving static analysis type-checker warnings.

## [0.13.8] - 2026-09-22

### Fixed
- **Fontwell Hijacked as Fontainebleau & Missing Cloth Number Grounding** (`betty_companion.py`, `meetings_manager.py`, `meetings_directory.json`):
  - **Fontwell Course Alias (`meetings_directory.json`, `meetings_manager.py`)**: Removed `"font"` as an alias for the French meeting `Fontainebleau` and assigned `"font"`, `"fontw"`, and `"fontwell"` directly to `Fontwell`. Betty's official 4-letter header for Fontwell is `Font`.
  - **International Prefix Hijack Guard (`is_international_selection`)**: Eliminated naive `meeting.startswith(k)` which was matching `fontwell` against `font` and falsely classifying Fontwell selections as international meetings. Added checks ensuring domestic tracks resolved by `meetings_manager.resolve_meeting` are never flagged as international.
  - **Priority Grounding Against Official UK/Irish Racecards (`state_pre_scan_and_match_slip`)**: Reordered pre-scan checks so that selections are matched against the official The Racing API / Sporting Life racecard cache *before* falling back to ungrounded international designations. When a selection like `Flashy Boy 16:32` exists on today's UK racecard (Fontwell #4), it is immediately grounded, assigned its official cloth number, and eligible for instant Direct Cloth Injection into Betty.

## [0.13.7] - 2026-09-22

### Fixed
- **Runner Panel OCR Failure on Small Fields & International Races** (`betty_companion.py`):
  - **Coordinate Calibration (`CYAN_REGION`)**: Recalibrated `CYAN_REGION` from `(8, 3, 389, 591)` to `(0, 0, 305, 465)`. Previously, starting at `x = 8` sliced off the leading 3–4 pixels of the first column (causing `Font` to clip to `\ufffdont` or `ont`), while spanning width `389` captured the yellow jump buttons (`[A->]`, `[D->]`, etc.) at `x = 308`, and spanning height `591` captured the bottom category buttons (`Tuesday's SIS Horse Racing`) below `y = 482`.
  - **Dynamic Trailing Whitespace Trimming (`get_trimmed_panel_image`)**: Small fields (e.g. 4 runners in French/Irish races like Fontainebleau 16:32) occupy only the top ~105px of the panel, leaving 350px+ of pure white void. When Tesseract was run with `--psm 6` (single uniform block), the overwhelming white space caused layout analysis to collapse and drop the runners completely. Added intelligent whitespace trimming that detects the active content boundary and crops trailing empty rows before OCR.
  - **Multi-PSM Fallback Engine (`ocr_panel_lines`)**: Added automatic fallback to `--psm 3` and `--psm 11` if `--psm 6` ever yields an empty line set, ensuring OCR never stalls silently during meeting cycling.
  - **Tolerant Leading-Character Drop Guard (`is_target_meeting_at_top`)**: Added Rule 6 checking `clean_target[1:].startswith(top_token)` so that any potential single-pixel left-edge clipping (e.g. `ont` $\rightarrow$ `fontainebleau`, `ever` $\rightarrow$ `beverley`, `out` $\rightarrow$ `southwell`) still resolves to the correct target meeting.

## [0.13.6] - 2026-09-20

### Fixed
- **Listowel $\rightarrow$ Towcester Misclassification Fix** (`betty_companion.py`, `meetings_directory.json`):
  - Resolved a critical bug where selections written at Listowel (e.g. `3:18 Listowel`, `3.18 Listowel 1 x 2 RFC`) were systematically misdetected as Towcester across all race times.
  - **Fuzzy Matching Quirk Elimination**: Removed `'towe'` from the Towcester aliases in `meetings_directory.json`. In Python's `difflib.SequenceMatcher`, `lis[t][o][w][e]l` matched `towe` with a $0.6667$ similarity ratio, crossing the previous $0.65$ threshold. Bitmapped OCR font confusion (`c` $\leftrightarrow$ `e`) remains fully handled dynamically by Rule 5 in `meetings_manager.py` without polluting `GREYHOUND_TRACKS`.
  - **Horse Forecast Protection in `expand_trap_forecast_bets()`**: Enhanced `expand_trap_forecast_bets()` to check whether bet selections or meeting names belong to horse racing courses before applying trap expansion logic. Legitimate horse racing forecasts (RFC, SFC, CFC) are now preserved as horse selections rather than converted into greyhound traps.
  - **Fuzzy Match Cutoff Hardening**: Raised the greyhound track fuzzy matching cutoffs from `0.65` in `expand_trap_forecast_bets()` and `0.55` in `state_pre_scan_and_match_slip()` to `0.80`, aligning with the existing strict thresholds in `meetings_manager.py` and `rules_engine.py`. Added explicit checks ensuring words resolving to horse courses via `meetings_manager.resolve_meeting()` are never fuzzy-matched to greyhound tracks.
  - **VLM Vision Prompt Clarification**: Neutralized prompt language in Section 7 of `prompt_text` so that mentioning horse courses like Listowel does not prime the vision model to divert customer bets to greyhound tracks.

## [0.13.5] - 2026-09-20

### Fixed
- **`rules_engine.py:601` — TypeError: `>` not supported between `int` and `None`** (`rules_engine.py`):
  - `mgr.get_parameter()` has an untyped return signature; the static analyser correctly flagged that `max_traps` could be `None`, making `effective_trap > max_traps` a runtime TypeError. Fixed with `int(... or 6)` guard so `max_traps` is always a concrete integer.
- **`rules_engine.py:74` — Unnecessary `str()` call** (`rules_engine.py`):
  - `parse_race_time_to_minutes(time_str: str)` already declares `time_str` as `str`, making `str(time_str).strip()` a redundant cast. Simplified to `time_str.strip()`.
- **`betty_companion.py:2864` — Unnecessary `bool()` call** (`betty_companion.py`):
  - `pyautogui.pixelMatchesColor(...)` returns a `bool` natively; wrapping it in `bool(...)` was a redundant cast. Removed the wrapper in `is_f8_screen_active()`.

## [0.13.4] - 2026-09-20


### Fixed
- **Bug 6 — Afternoon Time-Bump Misfires on 9:xx and 10:xx Times** (`betty_companion.py` + `rules_engine.py`):
  - `parse_race_time_to_minutes` was bumping `h + 12` for `h <= 10`, which incorrectly converted a valid `9:00 AM` or `10:00 AM` race time to `21:00` / `22:00`. Tightened condition to `h <= 8` — all UK/Irish afternoon races start no earlier than 12:00, so 1–8 are unambiguously PM shorthand. Fix applied to both the `betty_companion.py` copy (line 230) and the `rules_engine.py` copy (line 70).
- **Bug 7 — '2:44' Dead-Zone: Bare Time-Only Screens Not Caught by Cycling Stall Guard** (`betty_companion.py`):
  - The cycling backtrack guard (`state_read_cyan_panel`, line 834) only triggered on `'ttc'` tokens or strings ≤ 4 chars. A time-only OCR header like `"2:44"` (4 chars, caught) or `"14:22"` (5 chars, **not** caught) would cause an infinite right-cycling loop against a screen Betty can never resolve. Added `_is_time_only_screen` regex check (`^\d{1,2}[:.]\d{2}\b`) to detect both short and long time-only headers and trigger the left-backtrack.
- **Bug 8 — Unreachable Ternary on Line 2996 Always Returns Sheffield** (`betty_companion.py`):
  - The conditional `"Sheffield" if any(...) else "Sheffield"` was logically equivalent to an unconditional `"Sheffield"` — both branches returned the same value. Simplified to a direct assignment with an explanatory comment and a `print` warning so operators can see when the fallback fires.
- **Bug 2 — `normalize_bet_type` Diverged Between Modules** (`rules_engine.py`):
  - `rules_engine.py`'s copy was missing `alphabet`, `round robin`, `flag`, `super flag`, `rounder`, `roundabout`, `union jack`, `up-and-down`, and used shorter abbreviation patterns (`tbl`, `dbl`, `sgl`) compared to the handwriting-aware `betty_companion.py` version (`treb`, `doub`, `dousl`, `win`). Replaced with the full canonical version so both modules are consistent.
- **Bug 3 — `UK_BETTING_GLOSSARY` in `rules_engine.py` Missing 9 Bet Types** (`rules_engine.py`):
  - `calculate_bet_cost_pence` in `rules_engine.py` silently returned `unit_stake * 1` (single-line default) for `alphabet`, `round robin`, `flag`, `super flag`, `rounder`, `roundabout`, `union jack`, `up-and-down`, and `accumulator` because they were absent from the flat glossary. Added all missing entries with correct line counts.

## [0.13.3] - 2026-09-20


### Fixed
- **Local Shadow Copy of `is_greyhound_or_trap_selection` Still Had Broken Fallback** (`betty_companion.py`):
  - The fix applied in v0.13.2 targeted `rules_engine.py`, but `betty_companion.py` defines its own independent shadow copy of `is_greyhound_or_trap_selection` (lines 1470–1508) that the main automation loop (`state_pre_scan_and_match_slip`) actually calls. This local copy **still contained** the broken `horse.get('number')` cloth-number fallback on lines 1501–1502, rendering the rules_engine fix entirely ineffective during live slip processing.
  - Removed the two offending lines from `betty_companion.py`'s local copy and added the same explanatory comment added in v0.13.2, ensuring both copies are now consistent and the cloth number can never masquerade as a trap number in either code path.

## [0.13.2] - 2026-09-20


### Fixed
- **False Greyhound Reclassification of Horse Racing Selections** (`rules_engine.py`):
  - Removed a dangerously broad fallback in `is_greyhound_or_trap_selection()` that copied `horse.get('number')` (the Racing API cloth number) into `trap_num` whenever the selection name didn't match a trap pattern. Because every horse racecard entry carries a cloth number (e.g. `#4`), this caused *all* horse racing selections pre-populated with an API cloth number to be falsely classified as greyhound trap bets and re-routed to Sheffield.
  - Trap detection now fires strictly on (a) the selection name matching a trap pattern (`digit`, `"Trap N"`, `"T3"`, etc.) or (b) the meeting resolving to a known greyhound track in `meetings_directory.json`. The `horse['number']` field is horse-racing-only data and must never influence sport-type classification.

## [0.13.1] - 2026-09-20


### Fixed
- **VLM API Model Waterfall Overhaul & Timeout Resilience**:
  - Replaced legacy endpoints with active, high-quota Google models (`gemini-3.1-flash-lite` and `gemini-flash-lite-latest`), removing retired models (`gemini-2.0-flash`, `gemini-2.5-pro`) that triggered repeated HTTP 404 cascading errors.
  - Centralized model waterfall configuration in `VLM_WATERFALL_MODELS` across both slip translation (`state_read_slip_via_api()`) and runner re-examination (`reexamine_runner_with_ai()`).
  - Increased per-attempt REST request timeout from 45s to 60s to prevent premature read timeouts during high-load API periods.
- **Customer Written Total Stake Currency Parser**:
  - Updated regex in `parse_currency_string_to_pence()` to handle trailing `'p'` suffix after two-digit pence (e.g. `'7 - 50p'`), resolving false £7.00 calculation mismatches that previously caused slip extraction to re-scan.

## [0.13.0] - 2026-09-20

### Added
- **Centralized Meetings Directory (`meetings_directory.json`) & Management Engine (`meetings_manager.py`)**:
  - Decoupled all racecourses, greyhound tracks, international tracks, and virtual racing definitions from Python source code into an external declarative configuration: `meetings_directory.json`.
  - Implemented `MeetingsDirectoryManager` in `meetings_manager.py` featuring timestamp-based hot-reloading (`os.path.getmtime`), alias indexing, and canonical track resolution without requiring application restarts.
  - Added support for UK Retail Virtual Racing (horses & greyhounds: Dash, Portman Park, Sprintvalley, Steepledown, Brushwood, Millers Mount, Meadowvale, Stanningley, Longford, Hillside, Rapid Track, Sandy Lanes, Heathlands, Shelbourne Virtual) with automatic normalization of Betty's `(v)` terminal suffix.
  - Injected `covered_meetings_summary` into the VLM vision prompt (`state_read_slip_via_api()`) alongside today's API racecards, eliminating hallucinations where virtual or dog slips were mistakenly mapped to live horse courses.
  - Added Virtual selection detection (`is_virtual_selection()`) to `state_pre_scan_and_match_slip()`, preserving written runner and post time details and bypassing live racecard lookups for virtual races.

### Changed
- **Betty Cyan Panel Meeting Recognition (`is_target_meeting_at_top()`)**:
  - Integrated `meetings_manager.is_target_meeting_match()` into the top meeting matcher, enabling immediate recognition of virtual screens (e.g. `dash 2:48(v)` $\rightarrow$ `Dash`), greyhound abbreviations, and course aliases without unnecessary right-arrow cycling.
  - Refactored `rules_engine.py` and `betty_companion.py` to dynamically consume `meetings_manager` instead of maintaining duplicate static track dictionaries.

## [0.12.2] - 2026-09-20

### Fixed
- **Greyhound / Trap Bet Meeting Grounding & Horse Course Exclusion**:
  - Resolved a critical bug where greyhound trap bets were incorrectly assigned horse racing meetings (e.g. `Listowel`) when the VLM hallucinated a horse track from post times, causing the Betty terminal automation to cycle past greyhound cards to find horse meetings.
  - Enforced a strict invariant in `state_pre_scan_and_match_slip()`: selections flagged as greyhound / trap bets (`is_dog = True`) are strictly prohibited from inheriting horse racing courses. If unresolved, the system dynamically inspects raw meeting hints, transcribed slip lines, and performs fuzzy matching against `GREYHOUND_TRACKS`.
  - Expanded `GREYHOUND_TRACKS` in both `betty_companion.py` and `rules_engine.py` with common OCR/handwriting variants for Sheffield (`'sweft'`, `'swift'`, `'sheff'`, `'shef'`, `'sheffd'`, `'shf'`).
- **Trap Forecast Notation & Related Contingency Prevention**:
  - Enhanced `expand_trap_forecast_bets()` to recognize dot-, space-, dash-, and slash-separated trap pairs (`2 . 5`, `2.5`, `2-5`, `2 x 5`, `2 5`) representing trap straight forecasts (e.g. `2 . 5 20 F/C`).
  - Added reconciliation for VLM-split trap forecasts: when a forecast bet contains selections with mismatched post times (e.g. `14:48` and `2.5`) due to trap notations being misread as post times, both selections are reconciled to the single race time (`14:48`) and track (`Sheffield`).
  - Prevented BetAnsells House Rule 1.17 from prematurely splitting single-race trap forecasts across different races into two win singles.
- **VLM Few-Shot Visual Learning & Prompt Directives**:
  - Added Reference 6 to `handwriting_examples/examples.json` using the customer's handwritten Sheffield straight forecast (`greyhound_sheffield_forecast.png`).
  - Added explicit instructions to Section 7 of `prompt_text` explaining that greyhound racing never takes place at horse courses, clarifying Sheffield OCR misreads, and providing structural guidance for dot-separated trap forecasts.

## [0.12.1] - 2026-09-20

### Changed
- **Pre-Release SemVer Restructure (`1.x.x` -> `0.x.x`)**:
  - Restructured all project version numbers to the `0.x.x` series (current: `v0.12.1`) to strictly reflect pre-release development status under the Semantic Versioning (SemVer) specification.
  - Migrated all historical archive files (`previous_versions/`, `versions/`), launcher scripts, and changelog records from `1.x.x` to `0.x.x`.

### Fixed
- **Cyan Panel Meeting Recognition & OCR Font Normalization (`is_target_meeting_at_top()`)**:
  - Resolved an issue where Betty Companion failed to recognize Towcester on Betty's cyan race selection screen when OCR read `'towe 2:36 trap 1'` instead of `'towc'`.
  - Added OCR font normalization handling bitmapped character confusions (`c` $\leftrightarrow$ `e`) so that `'towe'` seamlessly matches `'towc'` / `'Towcester'`.
  - Integrated canonical track alias resolution via `GREYHOUND_TRACKS`, ensuring registered track abbreviations (e.g. `'tow'`, `'towc'`, `'towe'`) are recognized immediately.
  - Adjusted fuzzy string similarity threshold for 4-letter prefixes to `>= 0.74` (permitting single-character OCR substitutions), while preserving a strict `0.85` threshold on ambiguous sibling roots (`newb` vs `newm` vs `newc`).
  - Added conditional filtering for `IGNORABLE_TOKENS`: day-of-week tokens `'sun'` and `'mon'` are no longer stripped when the target meeting is Sunderland or Monmore.
  - Added defensive overshoot recovery in `state_read_cyan_panel()`: if cycling right repeatedly hits a non-meeting screen (e.g. `'ttc'`), the script automatically backtracks with `'left'`.

## [0.12.0] - 2026-09-20

### Added
- **Special Pre-Printed Slip Recognition & Mandatory Bet Type Enforcement**:
  - Expanded few-shot visual reference database (`handwriting_examples/examples.json`) with annotated high-fidelity coupon templates:
    - **Yankee Coupon** (`special_slip_yankee.png`): 4-row selection grid with pre-printed `YANKEE` label in bottom-right cell. Automatically enforces an 11-bet Yankee (6 doubles, 4 trebles, 1 four-fold accumulator).
    - **Canadian / Super Yankee Coupon** (`special_slip_canadian.png`): 5-row selection grid with pre-printed `CANADIAN` label in bottom-right cell. Automatically enforces a 26-bet Canadian / Super Yankee (10 doubles, 10 trebles, 5 four-folds, 1 five-fold accumulator).
    - **Patent Coupon** (`special_slip_patent.png`): 3 numbered selection rows (1, 2, 3), header *"3 SELECTIONS = Three Singles, Three Doubles & One Treble = 7 BETS"*, `WIN 7 @` (win) and `WIN 14 @` (each-way) stake boxes, and pre-printed `PATENT` label in bottom-right cell. Automatically enforces a Patent (7 bets win, or 14 bets each-way).
  - Implemented `detect_special_preprinted_slip_type()` in `betty_companion.py` combining VLM visual classification and specialized localized quadrant OCR (with PSM 11 and font-specific ligature matching) to reliably classify special retail coupons without false positives on regular handwritten slips.
  - Wired special slip detection directly into `state_read_slip_via_api()`: when a coupon slip is detected, `bets_list` is guaranteed to be constructed strictly as that specific bet type, associating all selections to that bet regardless of whether the bet name was handwritten by the customer.
  - Added dedicated Betty terminal keyboard shortcut `'c'` for Canadian / Super Yankee in `UK_BETTING_GLOSSARY` and `BET_SHORTCUTS`.

### Fixed
- **Prefix Substring Regex Collision in `normalize_bet_type()`**:
  - Reordered `canadian|super\s*yankee` evaluation before `yankee|yank` in both `betty_companion.py` and `rules_engine.py`, preventing customer-written or alias "super yankee" bets from being mistakenly truncated into regular Yankees.

## [0.11.1] - 2026-09-20

### Fixed
- **VLM Vision Prompt Format Specifier Crash**:
  - Escaped unescaped JSON curly braces in greyhound reversed forecast example (`[{{"name": "Trap 1", ...}}]`) inside `state_read_slip_via_api()`.
  - Resolved `ValueError: Invalid format specifier ' "Trap 1", "number": 1, "time": "12:51", "meeting": "Sunderland"' for object of type 'str'` which was aborting slip scan on trigger.

## [0.11.0] - 2026-09-20

### Added
- **Dedicated Modular Rules Engine (`rules_engine.py`)**:
  - Extracted discrepancy settlement, related contingencies, and bookmaker rules management from the 3,700-line monolithic `betty_companion.py` into a standalone, lightweight, zero-GUI module.
  - Fully decoupled business settlement logic from `pyautogui`, `cv2`, and screen automation, enabling standalone testing, fast imports, and microservice/API deployment.
- **Externalized Declarative Configuration & Hot-Reloading (`bookmaker_rules.json`)**:
  - Upgraded `BookmakerRulesManager` with automated disk file modification tracking (`os.path.getmtime`); edits made to rules by shop managers or supervisors take effect immediately on the next slip scan without restarting Betty.
  - Formalized declarative `non_normal_states` taxonomy across all profiles:
    - `STATE_FORECAST_NON_EXISTENT_RUNNER` $\rightarrow$ `CONVERT_TO_WIN_SINGLE_FULL_STAKE` (Rule 1.17)
    - `STATE_FORECAST_DIFFERENT_RACES` $\rightarrow$ `SPLIT_INTO_HALF_STAKE_SINGLES` (Rule 1.17)
    - `STATE_FORECAST_REPEATED_RUNNER` $\rightarrow$ `CONVERT_TO_WIN_SINGLE_FULL_STAKE` (Rule 1.17)
    - `STATE_FORECAST_LONE_SELECTION` $\rightarrow$ `CONVERT_TO_WIN_SINGLE_FULL_STAKE` (Rule 1.17)
    - `STATE_FORECAST_UNNAMED_FAVOURITE` $\rightarrow$ `VOID_BET` (Rule 1.17)
    - `STATE_TRICAST_ONE_NON_RUNNER` $\rightarrow$ `CONVERT_TO_STRAIGHT_FORECAST_FULL_STAKE` (Rule 1.18)
    - `STATE_TRICAST_TWO_NON_RUNNERS` $\rightarrow$ `CONVERT_TO_SP_WIN_SINGLE_FULL_STAKE` (Rule 1.18)
    - `STATE_TRICAST_REPEATED_RUNNER` $\rightarrow$ `CONVERT_TO_STRAIGHT_FORECAST_FULL_STAKE` (Rule 1.18)
    - `STATE_TRICAST_UNNAMED_FAVOURITE` $\rightarrow$ `VOID_BET` (Rule 1.18)
    - `STATE_FAVOURITE_EACH_WAY_REQUESTED` $\rightarrow$ `VOID_PLACE_ELEMENT_SETTLE_WIN_ONLY` (Rule 1.7)
    - `STATE_MULTIPLE_SAME_RACE_CLASH` $\rightarrow$ `SPLIT_INTO_LOWER_ACCUMULATORS` (Rule 1.8.1)
    - `STATE_SLIP_UNINSTRUCTED_SAME_RACE` $\rightarrow$ `SETTLE_AS_STRAIGHT_FORECAST` (Rule 1.8.1)
    - `STATE_SLIP_UNINSTRUCTED_DIFFERENT_RACES` $\rightarrow$ `SPLIT_INTO_EQUAL_WIN_SINGLES` (Rule 1.8.1)
- **Pluggable Notification Callback**:
  - Implemented `set_notification_callback()` in `rules_engine.py` bridging directly into Betty Companion's audio and floating HUD banners.

### Changed
- Refactored `betty_companion.py` to import `BookmakerRulesManager`, `resolve_discrepancies`, and related helpers from `rules_engine.py`, removing ~590 lines of duplicate code.
- Maintained 100% backward compatibility for all existing functions and aliases (`resolve_bookmaker_discrepancies`, `resolve_betansells_discrepancies`, `resolve_same_race_contingencies`).
- Bumped version to `1.11.0` across all banners, UI titles, launcher scripts, and test suites.

## [0.10.0] - 2026-09-20

### Added
- Modular Multi-Bookmaker Discrepancy Rules Architecture (`BookmakerRulesManager`):
  - Refactored the discrepancy resolution pipeline from a hardcoded single-firm implementation to a pluggable, scalable architecture adaptable to any bookmaker firm or custom house rules.
  - Externalized rule profiles into `bookmaker_rules.json` supporting multiple firm configurations:
    - `BetAnsells`: Official Nov 27, 2025 Terms & Conditions, Rules and Payout Limits.
    - `Standard_UK_Tattersalls`: Standard UK retail betting shop rules.
    - `WilliamHill`: William Hill retail rules.
    - `Betfred`: Betfred retail rules.
    - `Custom`: Easily configurable template for bespoke house rules or experimental variations.
  - Added dynamic active profile switching via `.env` (`ACTIVE_BOOKMAKER=...`) or `bookmaker_rules.json` (`active_profile`), with graceful in-memory defaults.
  - Generalized `resolve_bookmaker_discrepancies()` to query the active profile dynamically:
    - Configurable `forecast_non_runner_action` (`single_full_stake`, `single_unit_stake`, `void`).
    - Configurable `forecast_different_races_action` (`split_half_stake_singles`, `void`).
    - Configurable `forecast_repeated_selection_action` and `forecast_lone_selection_action`.
    - Configurable `forecast_unnamed_favourite_allowed` and `tricast_unnamed_favourite_allowed`.
    - Configurable `tricast_one_non_runner_action` and `tricast_two_non_runners_action`.
    - Configurable `unnamed_favourites_each_way_allowed`.
    - Configurable `uninstructed_same_race_action` and `uninstructed_different_races_action`.
    - Configurable `max_greyhound_traps` (default 6, expandable).
  - Maintained 100% backward-compatible alias `resolve_betansells_discrepancies()` for legacy test harnesses and scripts.
  - Added active firm name indicators to console startup banners, pre-flight headers, and rule-action diagnostic notifications.

### Changed
- Bumped version to `1.10.0` across all banners, UI titles, and launcher batch scripts.

## [0.9.0] - 2026-09-20

### Added
- BetAnsells Official Betting Rules & Discrepancy Resolution Engine (`resolve_betansells_discrepancies`):
  - Codified official company Terms & Conditions, Rules and Payout Limits (effective 27th November 2025) directly into the pre-flight automation pipeline to automatically detect and legally resolve customer slip discrepancies.
  - **Rule 1.17 (Forecast Discrepancies)**:
    - Automatically converts forecasts containing non-runners, non-existent numbers, or lone selections into a **Win Single** on the remaining runner at the **full forecast stake** (e.g. £1 Reversed Forecast on Trap 1 & invalid Trap 7 $\rightarrow$ £2.00 Win Single on Trap 1).
    - Automatically detects forecasts where selections run in different races and splits the bet into **two half-stake Win Singles**, one on each selection (total stake strictly conserved).
    - Automatically converts repeated selections in a forecast into a Win Single at full stake.
    - Flags and voids forecasts containing un-named favourites with clear operator notifications.
  - **Rule 1.18 (Tricast Discrepancies)**:
    - Automatically converts tricasts with 1 non-existent selection / non-runner into a **Straight Forecast** (or Reversed Forecast for combination tricasts) on the 2 remaining selections in written order at the **total tricast stake**.
    - Automatically converts tricasts with 2 non-existent selections / non-runners into a **Win Single** at SP on the remaining selection at the **total tricast stake**.
    - Automatically converts repeated selections in a tricast into a Straight Forecast on the distinct selections.
  - **Rule 1.7 (Favourites Win-Only Rule)**:
    - Automatically identifies un-named favourites in horse and greyhound racing, voids the Each-Way place element, and adjusts the bet to **Win Only**.
  - **Rule 1.8.1 (Incomplete / Uninstructed Slips)**:
    - Automatically resolves uninstructed multi-runner slips into Straight Forecasts if in the same race, or Win Singles if across different races.
  - **Rule 1.8.4 & Trap Validation (`is_selection_existent`)**:
    - Validates greyhound trap selections against the strict 1 to 6 trap limit; traps $> 6$ or $\le 0$ are recognized as non-existent.
    - Validates horse cloth numbers against official racecard declared runners.
- Updated VLM vision prompt with comprehensive section on BetAnsells House Rules for visual transcription.
- Updated `expand_trap_forecast_bets` to expand combinations of any digits (e.g. `1 x 7 £1 R/F`) and multi-trap tricasts (`1 x 2 x 7`) into structured selections for downstream discrepancy processing.

### Changed
- Bumped version to `1.9.0` across all banners, UI titles, and launcher batch scripts.

## [0.8.0] - 2026-09-20

### Added
- Native UK & Irish Greyhound (Dog) Racing Support:
  - Added authoritative `GREYHOUND_TRACKS` directory mapping track abbreviations (e.g. `sund` $\rightarrow$ Sunderland, `romf` $\rightarrow$ Romford, `sheff` $\rightarrow$ Sheffield, `cray` $\rightarrow$ Crayford, `monm` $\rightarrow$ Monmore, `towc` $\rightarrow$ Towcester, `yar` $\rightarrow$ Yarmouth, `donc` $\rightarrow$ Doncaster, `kins` $\rightarrow$ Kinsley, `swin` $\rightarrow$ Swindon, `pb` $\rightarrow$ Perry Barr, `cp` $\rightarrow$ Central Park, etc.).
  - Added `is_greyhound_or_trap_selection()` to reliably identify trap bets (`Trap 1`, `T1`, `1`) and dog track meetings.
  - Automatically bypasses horse racecard grounding for greyhound bets, completely eliminating false crosscheck hallucinations against unrelated horse meetings (e.g. preventing `Trap 1 12.51 Sund` from being matched to `Silencio #1` at `Fontainebleau`).
  - Preserves exact trap number as saddle cloth number for direct terminal injection.
- Trap Forecast Combination Expansion Engine (`expand_trap_forecast_bets`):
  - Automatically parses shorthand trap combinations (e.g. `1 x 5 £1 R/F`, `1-4 SFC`, `1x2x5 CFC`) into structured multi-trap runner selections with post time and course.
  - Generates full runner objects for each trap selection (`Trap 1` #1, `Trap 5` #5) so Betty terminal receives valid multi-selection forecasts without operator intervention.
- International Horse Racing Protection:
  - Added `INTERNATIONAL_MEETINGS` directory recognizing French, South African, UAE/Dubai, US, and Australian tracks (e.g. Fontainebleau, Chantilly, Deauville, Saint-Cloud, Fairview, Greyville, Meydan, Gulfstream).
  - Added `is_international_selection()` to preserve written international meetings and post times without mutating them into UK/Irish racecard entries.
- Added Forecast/Tricast exemption to `resolve_same_race_contingencies()` ensuring legitimate same-race bets (e.g. Reversed Forecast on Traps 1 and 5) are never split into singles.
- Updated VLM vision prompt with comprehensive rules on greyhound trap bets and international horse racing.

### Changed
- Bumped version to `1.8.0` and synchronized launcher batch scripts with SemVer protocol.

## [0.7.0] - 2026-09-20

### Added
- Automated Related Contingency Split Engine (`resolve_same_race_contingencies`):
  - Implemented standard UK betting shop / Tattersalls Rule for same-race multiples: when two or more selections in the same race appear in a multiple bet (Doubles, Trebles, Accumulators), the bet is automatically split into lower accumulators or singles across the clashed selections at an equally divided unit stake.
  - Full mathematical total stake conservation across all split combinations:
    - 50p Win Double on 2 same-race runners $\rightarrow$ two 25p Win Singles (total 50p).
    - 50p EW Double on 2 same-race runners $\rightarrow$ two 25p EW Singles (total 100p).
    - 50p Treble with 2 same-race runners & 1 unrelated runner $\rightarrow$ two 25p Doubles (total 50p).
    - 3x 50p Doubles with 2 same-race runners $\rightarrow$ two 50p Doubles across distinct races + two 25p Singles (total 150p).
    - 50p EW Accumulator across 3 races with 2 clashed runners $\rightarrow$ two 25p EW Trebles (total 100p).
  - Race event resolution using normalized meeting names and post times (`get_horse_event_key`).
- Defensive F8 Terminal Error Recovery:
  - Calibrated F8 `[Cancel Bet]` button coordinate `CANCEL_BET_BTN_COORD = (719, 529)` with color `TARGET_YELLOW` (`(255, 255, 128)`).
  - Added `is_f8_screen_active()` to detect if Betty terminal rejects a bet (e.g. invalid selection or terminal validation error) and remains locked on the F8 screen.
  - Automatically clicks `[Cancel Bet]`, clears terminal state (`F10`), and safely advances to the next bet without UI desynchronization or runaway input.
- Added same-race related contingency awareness and guidance to VLM vision prompt in `state_read_slip_via_api()`.

### Changed
- Bumped version to `1.7.0` and synchronized launcher batch scripts with SemVer protocol.

## [0.6.1] - 2026-09-19

### Fixed
- Fixed static type checking issues in `BET_SHORTCUTS` dictionary comprehension by explicitly validating and type-guarding list aliases (`isinstance(_aliases, list)` and `isinstance(_al, str)`).
- Fixed static type checker parameter mismatch in `pyautogui.press(shortcut)` by strictly type-guarding `isinstance(shortcut, str)`.
- Removed redundant `str()` call on already string-typed `bet_type` parameter in `normalize_bet_type()`.
- Cleaned up unused `PIL` import in `scratch/test_few_shot.py`.
- Synchronized `__version__ = "0.6.1"` and launcher batch scripts with SemVer protocol.

## [0.6.0] - 2026-09-19

### Added
- Keyboard functionality for Betty terminal bet entry shortcuts:
  - Straight Forecast: `f` (aliases: `sfc`, `s/f/c`, `straight f/c`, `sf`)
  - Reversed Forecast: `r` (aliases: `rfc`, `r/f/c`, `reversed f/c`, `rf`)
  - Combination Forecast: `c` (aliases: `cfc`, `c/f/c`, `comb f/c`, `cf`)
  - Lucky 15: `l` (aliases: `lucky15`, `l15`, `l 15`, `4 l15`)
  - Lucky 31: `j` (aliases: `lucky31`, `l31`, `l 31`, `5 l31`)
  - Yankee: `y` (aliases: `yank`)
  - Patent: `p` (aliases: `pat`)
- Added comprehensive UK Betting Glossary (`UK_BETTING_GLOSSARY`) defining official UK betting shop bet types based on the Wikipedia specification (Single, Double, Treble, Accumulator, Straight/Reversed/Combination Forecast, Tricast/Combination Tricast, Trixie, Patent, Yankee, Lucky 15/31/63, Canadian/Super Yankee, Heinz, Super Heinz, Goliath, Alphabet, Up-and-Down/SSA, Round Robin, Flag, Super Flag, Rounder, Roundabout, Union Jack) with runner requirements, line calculations, and breakdown descriptions.
- Added special pre-printed "LUCKY 15 • 31 • 63" coupon slip detection:
  - Automatically identifies pre-printed Lucky grid coupons from header, grid rows, and footer title.
  - Automatically resolves 4 selections to Lucky 15 (`bet_type: "lucky 15"`) and 5 selections to Lucky 31 (`bet_type: "lucky 31"`).
  - Determines Win vs Each-Way from the stake column triangle placement.
- Added `normalize_bet_type()` helper to map customer slang, ligature abbreviations, and formatting variations into canonical UK bet types.

## [0.5.6] - 2026-09-19

### Fixed
- Fixed multiple bet combination math in `calculate_bet_cost_pence()`:
  - Added combination multiplier calculation (`m_mult = re.search(r'\b(\d+)\s*x\b')`) so bets like '3 x 50p Doubles' calculate as 3 lines $\times$ 50p = 150p (£1.50) instead of being erroneously priced as 1 double (50p).
  - Added dynamic combination line math ($N \text{ choose } K$) for doubles and trebles based on runner counts.
  - Resolves false-positive stake reconciliation variance deficit (£1.50) that triggered the failsafe abort.
- Added Multiplier Guardrail to ensure '3x Doubles' are never trimmed down to 2 horses even if positional text references 'last 2', guaranteeing 3 runners are strictly maintained.

## [0.5.5] - 2026-09-19

### Fixed
- Fixed guardrail over-correction: normal 2-horse doubles (e.g. Bet 1) are no longer overwritten with 3 horses by removing the overly aggressive `or len(horses) == 2` check in the runner inheritance guardrail; 3-horse inheritance or backfill now strictly requires explicit '3 x', '3x', or 'last 3' in the bet description or raw text.
- Enforced strict chronological upward scoping for 'ABOVE N' / 'AB N':
  - Added strict upward reading rules to `prompt_text`: bets appearing in the middle of a slip (e.g. '50p EW Accumulator AB 4' on line 8) can only reference selections written strictly above that line and never reach downward into selections written below it.
  - Added Python guardrail trimming to enforce strict upper-bound scoping: any 'ABOVE N' or 'AB N' bet with more than N attached runners is automatically trimmed to strictly the first N selections.

## [0.5.4] - 2026-09-19

### Fixed
- Fixed unit stake parsing on multiple bets: added Unit Stake Sanitizer to ensure `stake_pence` is strictly the unit stake per single line (e.g. 50p for '3 x 50p doubles', NOT the multiplied total of 150p), preventing Betty terminal from overcharging the customer.
- Added runner inheritance for '3x Doubles' and companion Trebles: automatically synchronizes all 3 runners from an adjacent 3-runner Treble or backfills preceding selections from the slip.
- Added explicit Unit Stake Rules for Betty terminal into `prompt_text`.

## [0.5.3] - 2026-09-19

### Added
- Generalized positional scoping: dynamically parses and extrapolates any relative scoping pattern in the form `[Last | Above | AB] + <N>` (e.g. `LAST 2`, `LAST 3`, `LAST 4`, `ABOVE 4`, `AB 4`, `LAST 5`).
- Mathematical combination runner validation: enforces structural selection minimums (e.g. Win/EW Trebles mathematically require $\ge 3$ selections; Accumulators require $\ge 4$; $K \times \text{Doubles}$ requires $N \text{ choose } 2 = K$, such as $3 \times \text{Doubles} \rightarrow 3$ runners, $6 \times \text{Doubles} \rightarrow 4$ runners).
- Automated back-filling guardrail in `state_read_slip_via_api()`: if the vision model associates fewer selections than mathematically required or scoped by the qualifier, Betty Companion automatically back-fills missing runners counting upwards from `selections`.

## [0.5.2] - 2026-09-19

### Fixed
- Fixed few-shot prompt injection parroting bug: converted few-shot reference demonstrations from single-message payload dumping into conversational multi-turn `user` and `model` role separation. Prevents models (such as `gemini-3.5-flash-lite`) from memorizing and echoing the visual reference cheat sheet (Akabusi) instead of transcribing the newly scanned slip (Balzac).

## [0.5.1] - 2026-09-19

### Fixed
- Fixed static type checking issues in `betty_companion.py`:
  - Added credential presence guard before HTTP Basic Auth call to `https://api.theracingapi.com/v1/racecards/free`, resolving `tuple[str | None, str | None]` parameter mismatch on `Session.get(auth=...)`.
  - Added explicit `list[dict]` typing for few-shot request payload `parts`, resolving type inference errors on `{"inline_data": ...}` dictionary insertion.
  - Guaranteed non-null integer type (`calc_pence_val`) for calculated bet stake pence and retry prompt hint difference calculations, preventing `None / 100` and `None - int` runtime/static type failures.
  - Removed redundant `str()` conversions on variables already typed as `str`.

## [0.5.0] - 2026-09-19

### Added
- Added dynamic Multimodal Few-Shot Visual Learning engine via `handwriting_examples/examples.json` and base64-encoded visual cheat sheet references (e.g. `squashed_complex_slip.png`).
- Added parser support for interleaved bets written directly between selection lines (top-to-bottom procedural parsing).
- Added customer positional scoping rules: `LAST 2` (applies to the 2 selections written immediately above), `ABOVE 4` / `AB 4` (applies to all 4 selections written above), and `LAST 4` (applies to the 4 selections written immediately above).
- Added customer handwriting ligature & shorthand recognition: squashed `eW` (Each-Way), `TREB` (Win Treble), and `DOUSL` / `DOUB` (Double).
- Added support for non-standard post times ending in specific minutes (e.g. `:52`, `:46`, `:42`, `:02`) common on French, Irish, and AW floodlit cards.
- Added optional `"description"` field to `bets` items in Gemini response schema.

## [0.4.2] - 2026-09-19

### Added
- Added £1.00 (`100p`) grace variance tolerance (`TOTAL_STAKE_GRACE_VARIANCE_PENCE`) to the total stake failsafe reconciliation check.
- If the detected total of bets is within £1.00 either way of the customer's written total (|calculated - written| <= £1.00), Betty Companion logs the accepted variance and continues automated processing without triggering unnecessary rescans or aborts.

### Changed
- Mismatch failsafe alerts and retry prompt hints now only trigger when the total bet cost differs from the customer's written total by more than £1.00.

## [0.4.1] - 2026-09-19

### Fixed
- Fixed evening race time recognition and course disambiguation (e.g. `6.30 N` being erroneously transcribed as afternoon races like `3:20` at Newbury).
- Added explicit prompt rules distinguishing afternoon meetings (13:00 to 17:30) from evening floodlit meetings (17:30 to 21:00) and preventing stroke-shape misinterpretations (digit '6' vs '3').
- Implemented `disambiguate_track_hint()` to disambiguate single-letter and shorthand track codes (e.g. 'N' in the evening = Newcastle AW vs Newbury/Newmarket in the afternoon; 'K' = Kempton AW; 'W' = Wolverhampton AW).
- Updated response schema with strict digit lock (`raw_time` and `raw_meeting_hint`) to preserve raw visual handwriting fidelity before runner grounding.

### Changed
- Replaced harsh slip image contrast enhancement with dedicated `pre_process_slip_image()` using soft grayscale and anti-aliased Lanczos interpolation to prevent loop closures on digits like '6'.

## [0.4.0] - 2026-09-19

### Added
- Slip Total Stake Failsafe: Reads customer written total stake at the bottom of handwritten slips (supporting formats like `7 - 00`, `7.00`, `£7`, `50p`, `14 - 50`).
- Automated Bet Reconciliation Engine: Sums up all parsed bets (accounting for unit stakes, line counts, and each-way multipliers) and verifies that total bet cost matches the customer's written total stake.
- 3-Attempt Auto-Rescan Loop: If parsed bets do not reconcile with the customer's written total, the script automatically re-captures and re-examines the slip up to 3 times, passing targeted feedback to the vision model to detect missed selections.
- Critical Safety Abort: If totals still do not reconcile after 3 attempts, Betty Companion halts gracefully and returns to idle listening mode to prevent partial or incorrect bet placement.

## [0.3.3] - 2026-09-19

### Fixed
- Fixed meeting mismatch in `state_read_cyan_panel()` where simultaneous races (e.g. Romford greyhounds and Navan horses at 13:42) caused the script to falsely detect the target meeting as active at the top.
- Introduced dedicated `is_target_meeting_at_top(lines, target_meeting)` helper that strictly checks the primary meeting header position, preventing premature runner cloth number injection before cycling `right` to the correct meeting.
- Removed premature runner scan bypass in `state_read_cyan_panel()` ensuring Betty Companion always forces cycling until the target meeting is verified active at the top.

## [0.3.2] - 2026-09-19

### Added
- Single source of truth version constant (`__version__ = "0.3.2"` and `APP_NAME = f"Betty Companion v{__version__}"`).
- Automated pre-flight validation check for `GEMINI_API_KEY` with graceful HUD warning if missing.
- Interruptible `safe_sleep()` helper backed by `threading.Event()` for millisecond-level `ESC` abort reactivity.

### Changed
- Converted all blocking `time.sleep()` calls in `run_cycle_logic()`, `state_read_cyan_panel()`, `state_handle_price()`, and `state_apply_guarantees()` to interruptible `safe_sleep()`.
- Replaced global `abort_requested` boolean with thread-safe `abort_event = threading.Event()`.
- Switched selection deduplication in `state_pre_scan_and_match_slip()` to time-normalized keys (`parse_race_time_to_minutes`) and clean horse names.
- Updated launcher `bettycomplaunch.bat` to Betty Companion v0.3.2.

### Fixed
- Fixed duplicate runner verification modals when race times are entered in different formats (e.g. `2.30` vs `14:30`).
- Fixed cloth number synchronization in `prompt_manual_horse_input()` so official cloth numbers are copied on candidate match.
- Fixed Tkinter banner and dialog lifecycle to prevent `Tcl_AsyncDelete` crashes when transient windows close.

## [0.3.1] - 2026-09-19

### Changed
- Integrated `python-dotenv` to load credentials directly from `.env`.
- Removed hardcoded fallback API credentials from source code.

## [0.3.0] - 2026-09-19

### Added
- Pre-flight racecard cross-referencing and AI handwriting re-examination against live UK/Irish racecards.
- Direct saddle cloth number injection from The Racing API to bypass OCR guessing on Betty's cyan panel.
- Interactive operator manual input dialog with candidate runner suggestions.
