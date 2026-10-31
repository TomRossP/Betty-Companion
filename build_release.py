"""
Builds the Betty Companion release: python build_release.py

  1. PyInstaller (BettyCompanion.spec): dist\\BettyCompanion\\, one folder, windowed, no UPX
  2. Tesseract copied in from this PC (C:\\Program Files\\Tesseract-OCR): the program and English only
  3. README.txt next to the exe
  4. dist\\BettyCompanion-<version>.zip, with its SHA-256 (to check a download, or for a false-positive report)

The tills need nothing installed: unzip, double-click BettyCompanion.exe.

This PC runs the built exe too, so the build stops while BettyCompanion.exe is running (a build over the running
program on 31 Oct deleted its Tesseract mid-wager), and the per-PC files next to the exe (logs\\, .env,
betty_paths.json: anything the build doesn't make) are set aside and put back, never zipped (the logs hold slips).
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
APP = os.path.join(DIST, "BettyCompanion")
TESSERACT_SRC = os.environ.get("TESSERACT_SRC", r"C:\Program Files\Tesseract-OCR")
TESSDATA = ["eng.traineddata", "configs", "tessconfigs"]  # English only; the program never asks for osd
BUILT = {"BettyCompanion.exe", "_internal", "README.txt"}  # what the build makes in APP; anything else is the PC's
KEPT = os.path.join(DIST, "BettyCompanion.kept")             # the PC's files while the build runs
EXE_NAME = "BettyCompanion.exe"


def running_copies() -> list[str]:
    """PIDs of BettyCompanion.exe running on this PC (tasklist; [] when it can't be asked)."""
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {EXE_NAME}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, check=False).stdout
    except OSError:
        return []
    return [line.split('","')[1] for line in out.splitlines() if line.startswith(f'"{EXE_NAME}"')]


def set_aside_pc_files() -> list[str]:
    """Moves the PC's own files out of APP into KEPT (a rename: same drive); their names."""
    if os.path.exists(KEPT):
        sys.exit(f"An earlier build was interrupted: this PC's files (logs, settings) are in {KEPT}. "
                 f"Move them back into {APP}, delete the empty {KEPT}, then build again.")
    names = sorted(n for n in os.listdir(APP) if n not in BUILT) if os.path.isdir(APP) else []
    if names:
        os.makedirs(KEPT)
        for name in names:
            os.replace(os.path.join(APP, name), os.path.join(KEPT, name))
        print(f"Set aside this PC's files: {', '.join(names)}")
    return names


def put_back_pc_files(names: list[str]):
    """The PC's files back into APP (made if the build failed before it), then KEPT removed once empty."""
    if not names:
        return
    os.makedirs(APP, exist_ok=True)
    for name in names:
        os.replace(os.path.join(KEPT, name), os.path.join(APP, name))
    os.rmdir(KEPT)
    print(f"Put back this PC's files: {', '.join(names)}")


def dlls_needed(folder: str, exe: str) -> set[str]:
    """The DLLs in `folder` that `exe` loads, directly or through each other (the rest are for Tesseract's training
    tools: ICU, Pango, Cairo, ~45 MB). pefile comes with PyInstaller."""
    import pefile
    local = {f.lower(): f for f in os.listdir(folder) if f.lower().endswith(".dll")}
    need, todo = set(), [exe]
    while todo:
        pe = pefile.PE(os.path.join(folder, todo.pop()), fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                                               pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"]])
        for attr in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
            for entry in getattr(pe, attr, []):
                dll = entry.dll.decode().lower()
                if dll in local and local[dll] not in need:
                    need.add(local[dll])
                    todo.append(local[dll])
    return need


def version() -> str:
    with open(os.path.join(ROOT, "betty_companion.py"), encoding="utf-8") as f:
        return re.search(r'^__version__\s*=\s*"([^"]+)"', f.read(), re.MULTILINE).group(1)


def copy_tesseract(dest: str):
    """tesseract.exe, the DLLs it loads, and English (the training tools, docs and other languages stay out)."""
    if not os.path.isfile(os.path.join(TESSERACT_SRC, "tesseract.exe")):
        sys.exit(f"Tesseract not found in {TESSERACT_SRC} (set TESSERACT_SRC)")
    os.makedirs(os.path.join(dest, "tessdata"), exist_ok=True)
    shutil.copy2(os.path.join(TESSERACT_SRC, "tesseract.exe"), dest)
    for dll in dlls_needed(TESSERACT_SRC, "tesseract.exe"):
        shutil.copy2(os.path.join(TESSERACT_SRC, dll), dest)
    for name in TESSDATA:
        src = os.path.join(TESSERACT_SRC, "tessdata", name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dest, "tessdata", name), dirs_exist_ok=True)
        elif os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest, "tessdata"))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def folder_size(path: str) -> int:
    return sum(os.path.getsize(os.path.join(d, f)) for d, _, files in os.walk(path) for f in files)


def main():
    ver = version()
    running = running_copies()
    if running:
        sys.exit(f"{EXE_NAME} is running (PID {', '.join(running)}): close Betty Companion (Stop, then close its "
                 "window) and build again. Nothing was changed.")
    print(f"Building Betty Companion {ver}")
    kept = set_aside_pc_files()
    try:
        if os.path.isdir(APP):
            # Moved aside whole, then deleted: a file in use (the program, or the antivirus reading the exe) stops the
            # move before anything is gone. Deleted file by file, a lock on the exe left the folder half deleted (31 Oct)
            old = APP + ".old"
            shutil.rmtree(old, ignore_errors=True)
            try:
                os.replace(APP, old)
            except OSError as e:
                sys.exit(f"{APP} is in use ({e.strerror}): nothing was changed. Close Betty Companion (or wait for "
                         "the antivirus to finish with it) and build again.")
            shutil.rmtree(old, ignore_errors=True)
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
                        os.path.join(ROOT, "BettyCompanion.spec")], cwd=ROOT, check=True)
        copy_tesseract(os.path.join(APP, "_internal", "tesseract"))
        shutil.copy2(os.path.join(ROOT, "release", "README.txt"), APP)
        zip_path = os.path.join(DIST, f"BettyCompanion-{ver}.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for d, _, files in os.walk(APP):
                for f in files:
                    full = os.path.join(d, f)
                    z.write(full, os.path.join("BettyCompanion", os.path.relpath(full, APP)))
        digest = sha256(zip_path)
        with open(zip_path + ".sha256", "w", encoding="utf-8") as f:
            f.write(f"{digest}  {os.path.basename(zip_path)}\n")
    finally:
        put_back_pc_files(kept)  # after the zip: the PC's logs never go in it
    print(f"\nFolder: {APP} ({folder_size(APP) / 1e6:.0f} MB)")
    print(f"Zip:    {zip_path} ({os.path.getsize(zip_path) / 1e6:.0f} MB)")
    print(f"SHA-256 {digest}")
    print(f"Exe SHA-256 {sha256(os.path.join(APP, 'BettyCompanion.exe'))}")


if __name__ == "__main__":
    main()
