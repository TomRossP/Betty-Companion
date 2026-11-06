# Betty Companion

Works through Betty's unedited wagers on a shop till. It reads each slip, checks it against Betty's racecards and
enters it. In LIVE mode it places the wager; in TEST mode it stops just before placing. Anything it can't do is left
for staff, with the reason.

## On a till

1. Download `BettyCompanion-<version>.zip` from **Releases** and unzip it somewhere the till can write to, for example
   `C:\BettyCompanion`.
2. Double-click `BettyCompanion.exe`. Nothing is installed.
3. Pair the till with the relay once: **System** tab, **Settings**, **Pair this till**, then approve the code on the relay's
   `/admin` page.

The staff guide is [release/README.txt](release/README.txt). The relay is set up as in
[relay/RELAY_SETUP.md](relay/RELAY_SETUP.md).

## For development

- `betty_companion.py`: the program. `python betty_companion.py` runs it on its own.
- `launcher.py`: the control window (`BettyCompanion.exe`). It runs the program with `--backend`.
- `master_index.py`: Betty's Master Index, how sports selections are entered: which row fits, whether a list can be believed.
  `sports_markets.json` has the market names, `index_price_glyphs.json` the price column's exact shapes.
- `relay_link.py`: pairing with the relay. `error_guide.py`: the explanations shown in the Errors tab.
- `python build_release.py`: builds `dist\BettyCompanion\` and the release zip. Needs PyInstaller and Tesseract
  installed on the build PC.
- Per-PC settings and keys go in `.env`, which is never committed. See [CHANGELOG.md](CHANGELOG.md) for every release.
