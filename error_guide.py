"""
Plain-English explanations for the launcher's Errors tab: what each message from the program means and what staff
should do. explain(text) finds the first entry whose pattern matches. Add an entry here when a new message appears.
"""
import re

CHECK_BY_HAND = "Open the wager in Betty and enter it by hand, checking every line against the slip."

# (pattern, title, what it means, what to do). First match wins, so the specific ones come first.
GUIDE: list[tuple[str, str, str, str]] = [
    # --- Placing ---
    (r"after F12, wager .* still in the unedited list",
     "Placed? Not confirmed",
     "F12 (Place Bet) was pressed, but the wager is still in the unedited list afterwards. It may or may not have "
     "been placed.",
     "Check the wager in Betty BEFORE doing anything else. Only enter it if it was not placed, or the customer is "
     "paid twice."),
    (r"questioned the payment after F12",
     "Betty asked about the payment",
     "After F12, Betty showed a question about the payment. The program never answers payment questions.",
     "Look at Betty's question and finish the wager by hand."),
    (r"F12 \(Place Bet\) refused|commit_wager\(.*\) called in test mode",
     "Placing blocked (safety check)",
     "Something tried to press F12 when only the final placing step may, or in test mode. The program blocked it "
     "and switched the watcher off. Nothing was placed.",
     "Note the time and send the log (System, then Log) for checking. Press Start to carry on."),
    (r"slip totals .* (?:but|paid)|Betty's slip totals",
     "Betty's total doesn't match the payment",
     "The bets entered in Betty add up to a different amount from what the customer paid, so nothing was placed.",
     "Check each stake and bet type against the slip, then " + CHECK_BY_HAND[0].lower() + CHECK_BY_HAND[1:]),
    (r"after house rules the bets cost .* was paid|Money mismatch",
     "The stakes don't add up to the payment",
     "The stakes as read from the slip don't add up to the amount paid, even after the house rules. Usually a stake "
     "was misread, or the customer's sums are wrong.",
     "Read the stakes on the slip yourself and enter the wager by hand. If the reader got a stake wrong, it's "
     "worth noting the wager number."),
    (r"Rule 1\.8\.4: .* can't be divided",
     "Stake can't be split evenly",
     "A selection without a name matches several races at the written time. House rule 1.8.4 splits the stake "
     "equally between them, but this stake doesn't divide evenly.",
     "Settle the split by the house rules and enter it by hand."),
    # --- The slip ---
    (r"no reader answered|Slip scan failed: no reader|the slip could not be read",
     "The slip couldn't be read (Gemini)",
     "No slip reader answered: no internet, the relay is down or refused this till, or Gemini is out of quota or "
     "credit. Look at the Gemini light at the bottom of the window.",
     "Enter the wager by hand. If the Gemini light is red, check the internet. If it says the till isn't paired, "
     "pair it again under System, Settings."),
    (r"no bets could be read after",
     "No bets found on the slip",
     "The reader looked at the slip several times and found no bets it could use (blank, unclear or unusual "
     "slip).",
     CHECK_BY_HAND),
    (r"staff cancelled the slip|Slip processing cancelled by operator|cancelled by operator",
     "Cancelled at the selection check",
     "A selection couldn't be read, the entry box was shown, and it was cancelled (Cancel or Esc).",
     CHECK_BY_HAND),
    (r"Betty did not show the slip|no slip image|broken state",
     "Betty didn't show the slip",
     "Betty opened the wager without its slip picture (a known Betty glitch), several times in a row.",
     "Close and reopen the wager in Betty. If the slip shows, enter it by hand."),
    (r"View Wagers could not be read",
     "View Wagers couldn't be read",
     "The struck time or payment on View Wagers couldn't be read clearly twice in a row, so the wager wasn't "
     "started.",
     CHECK_BY_HAND),
    (r"racecard feed can't be read|racecard feed not found|Betty racecard feed unavailable",
     "Racecards missing",
     "Betty's racecard files for today (its Events folder) can't be read, so no selection can be checked.",
     "Look at the Data tab. Betty normally writes these files itself: check Betty is running and has today's "
     "cards. Enter wagers by hand until it's fixed."),
    (r"bet type\(s\) the program can't enter yet",
     "Bet type not supported yet",
     "The slip has a bet type the program can't enter yet.",
     CHECK_BY_HAND),
    (r"a bet has no stake",
     "A bet has no stake",
     "A bet on the slip has no stake that could be read.",
     CHECK_BY_HAND),
    (r"has no meeting / time / cloth number",
     "Not enough to find the selection",
     "A selection was read without the meeting, the time or the number needed to find it in Betty.",
     CHECK_BY_HAND),
    # --- Entering selections ---
    (r"Betty has no price for it yet",
     "No price in Betty yet",
     "The customer took a price, but Betty shows no price for that runner yet (early prices not up), so it can't "
     "be entered at the price.",
     "Enter it by hand at the price taken, as the shop does."),
    (r"is not in Betty's runner list",
     "Race not in Betty's runner list",
     "Betty's runner list has no race at that meeting and time. The time may be written wrong, the race may have "
     "been abandoned, or it isn't on Betty's card.",
     "Check the time and meeting on the slip against Betty's card, then enter it by hand."),
    (r"can't be found under .* runner list|could not bring .* to the top of Betty's runner list",
     "Runner not found in Betty's list",
     "The race was found, but the runner couldn't be picked from Betty's runner list.",
     CHECK_BY_HAND),
    (r"meeting at the top of Betty's .* runner list could not be read",
     "Runner list couldn't be read",
     "Betty's runner list for that time came up, but the meeting at its top couldn't be read, so the program didn't "
     "press on to another meeting blind.",
     CHECK_BY_HAND),
    (r"can't read whether Betty's .* list is the horses or",
     "Horses and dogs at the same name and time",
     "Horses and greyhounds share the meeting name at that time, and the screen didn't show which list was open.",
     CHECK_BY_HAND),
    (r"Betty's (?:'.*' )?folder|'The Favourite' isn't showing|in Betty's folder|folder '.*' wasn't found",
     "Favourite couldn't be picked",
     "The favourite is entered from Betty's race folders, and that folder or race couldn't be opened or found.",
     "Enter the favourite by hand from the race folder."),
    (r"betslip shows \d+ selection\(s\)",
     "Betslip has the wrong number of lines",
     "After adding a selection, Betty's betslip didn't show the expected number of lines. Something didn't go in, "
     "or went in twice.",
     "Open the wager in Betty and check each betslip line against the slip."),
    (r"guarantee|not guaranteed|guaranteed but should not be",
     "Price guarantee (BOG) not right",
     "A betslip line wasn't guaranteed when it should be (UK and Irish horses), or was when it shouldn't be.",
     "Check the G marks on the betslip, then place it by hand."),
    (r"betslip shows .* for |before F8, line",
     "A betslip line looks wrong",
     "A line in Betty's betslip doesn't match the selection: the wrong race, SP instead of a price, or the other "
     "way round.",
     "Check that line against the slip and correct it by hand."),
    (r"Betty left Choose Bet and Stake",
     "Betty left the bet screen",
     "All the selections were in and Choose Bet and Stake (F8) opened, then Betty went to another screen by itself "
     "before the bet type was chosen.",
     "Enter the wager by hand. The log line before it lists the keys sent on that screen; the first marked "
     "'(screen gone)' is where Betty left."),
    (r"bet list|for extended bet",
     "Bet type couldn't be chosen",
     "On Choose Bet and Stake, the bet type couldn't be found or selected in Betty's bet list.",
     "Choose the bet type and stake by hand."),
    (r"asked about the payment while entering",
     "Betty asked about the payment",
     "Betty showed a payment question while selections were being entered. The program never answers these.",
     "Look at Betty's question and finish the wager by hand."),
    # --- The watcher ---
    (r"Staff detector didn't start",
     "Staff detector not working",
     "Windows didn't let the program watch the keyboard and mouse, so it can't tell when staff use the till. It "
     "could type into Betty while someone else is using it.",
     "Stop the watcher, close Betty Companion and open it again. Until then, don't use the till while it runs."),
    (r"screens went wrong twice while entering it",
     "Betty's screens kept going wrong",
     "Twice in a row, Betty didn't show what the program expected while it was entering this wager, so it was left "
     "for staff (marked FAO in live mode).",
     CHECK_BY_HAND),
    (r"price check box stayed open",
     "Betty's price check box wouldn't close",
     "Betty asked about the price (\"The price you entered was not correct...\"). Enter didn't close the box, and nor "
     "did 'Override with entered price' (or that button wasn't there).",
     "Open the wager in Betty, choose the price by hand, and finish the bet."),
    (r"left unedited part-way",
     "Wager stopped part-way",
     "The watcher was stopped (Esc) or hit a problem while this wager was open, so it was left unedited and not "
     "marked FAO.",
     "Open the wager in Betty and check it: finish it by hand, or back out without saving."),
    (r"no longer in the unedited list",
     "Wager already taken",
     "The wager left the unedited list before the program opened it: someone else is dealing with it.",
     "Nothing to do. The watcher moves on to the next wager."),
    (r"Could not get Betty back to Home|could not get back to Home",
     "Betty is stuck on a screen",
     "The watcher couldn't get Betty back to the Home screen, so it switched itself off.",
     "Put Betty back on Home, then press Start."),
    (r"expected .*, Betty shows|did not load|left the unedited list while reopening",
     "Betty showed an unexpected screen",
     "Betty didn't show the screen the program expected (a popup, a slow screen, or someone using the till).",
     "If it keeps happening, put Betty back on Home and press Start."),
    (r"Screen is \d+x\d+",
     "Wrong screen size",
     "The program only works with the screen set to 1366 x 768.",
     "Set the display to 1366 x 768 (Windows Settings, Display), then press Start."),
    (r"^Watcher stopped",
     "The watcher stopped itself",
     "Betty showed something the program didn't expect, so the watcher switched itself off rather than guess. The "
     "rest of the message says what it saw.",
     "Check the wager on Betty and finish it by hand if needed. Put Betty back on Home, then press Start."),
    (r"Watcher error",
     "Unexpected program error",
     "Something unexpected went wrong inside the program, so the watcher switched itself off.",
     "Note the time, press Start to carry on, and send the log (System, then Log) for fixing."),
    (r"stopped unexpectedly|Traceback|exit code",
     "The program closed unexpectedly",
     "The program behind this window stopped by itself.",
     "Press Start to run it again. If it keeps happening, send the log for fixing."),
    (r"house rules changed total",
     "House rules changed the total",
     "Applying the house rules changed the total cost of the slip, which shouldn't happen.",
     "Check the bets in Betty before placing."),
    (r"not paired|pass was revoked",
     "This till isn't paired with the relay",
     "The relay doesn't recognise this till's pass (never paired, or revoked on /admin), so slips can't be read.",
     "Pair the till again: System, Settings, then Pair this till."),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), title, meaning, action) for p, title, meaning, action in GUIDE]

UNKNOWN = ("Not in the guide yet",
           "This message isn't explained in the guide yet.",
           "Check the wager in Betty and finish it by hand. If it keeps happening, send the log (System, then Log).")


def explain(text: str) -> dict:
    """{'title', 'meaning', 'action'} for a message from the program."""
    for pattern, title, meaning, action in _COMPILED:
        if pattern.search(text or ""):
            return {"title": title, "meaning": meaning, "action": action}
    return dict(zip(("title", "meaning", "action"), UNKNOWN))
