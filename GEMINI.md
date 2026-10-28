# Project Rules & Working Protocol: Betty Companion

## 1. Strict Semantic Versioning (SemVer) Protocol
Before making ANY code modifications or generating replacement scripts, you MUST strictly adhere to this versioning lifecycle:

1. **Inspect Current Version**:
   - Check the existing `__version__` constant at the top of the working script.
2. **Determine the Increment**:
   - **PATCH** (`x.y.Z` $\rightarrow$ `x.y.Z+1`): For bug fixes, timing tweaks, coordinate calibrations, or typo fixes.
   - **MINOR** (`x.Y.z` $\rightarrow$ `x.Y+1.0`): For new features (e.g. new bet types, new API feeds, UI enhancements).
   - **MAJOR** (`X.y.z` $\rightarrow$ `X+1.0.0`): For breaking changes, terminal workflow overhauls, or architecture rewrites.
3. **Backup / Archive Snapshot Before Changing Code**:
   - Before applying modifications, copy the current working file into the `previous_versions/` folder named with its version:
     `previous_versions/betty_companion_v{OLD_VERSION}.py`
   - When completing and releasing a new version, save a copy of the release snapshot into `previous_versions/` (`previous_versions/betty_companion_v{NEW_VERSION}.py`).
   - **Root Directory Cleanliness**: Version-tagged script files (e.g. `betty_companion_v*.py`) MUST NOT remain in the root directory. The root folder should strictly contain only the single active script `betty_companion.py`. If a version snapshot is generated, it must reside strictly in `previous_versions/` or be removed from the root immediately after copying.
4. **Apply Changes to New Working Copy**:
   - Apply edits to the main script (`betty_companion.py`).
   - Immediately update `__version__ = "{NEW_VERSION}"` and `APP_NAME = f"Betty Companion v{__version__}"`.
   - Ensure all dialogs, console banners, and HUD titles dynamically display the new version.
5. **Update CHANGELOG.md**:
   - Append an entry to `CHANGELOG.md` detailing the version number, date, and a bulleted summary of changes under `### Added`, `### Changed`, or `### Fixed`.

## 2. Layout since 1.0.0 (the exe)
- `betty_companion.py` is still the program: bug fixes and features go there, versioned as above. `python betty_companion.py` still runs it on its own.
- `launcher.py` is the control window (`BettyCompanion.exe`). It runs the program as `--backend` and talks to it through pipes (section 7 of `betty_companion.py`). `relay_link.py` handles pairing with the relay; `error_guide.py` holds the plain-English explanations in the Errors tab. Add an entry there when a new staff reason or error message is added.
- A fix reaches the tills only in a new build: `python build_release.py` makes `dist\BettyCompanion-<version>.zip` from the current files.

## 3. Invariant Project Constraints
- Never modify `SLIP_REGION = (491, 78, 365, 505)`.
- Never store raw API keys or passwords in the source code; always load via `python-dotenv`.
- Console logs are saved as text to `logs/` and kept for 30 days.