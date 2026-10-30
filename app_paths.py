"""
Where Betty Companion's files are, run as a script or as the packaged exe (PyInstaller, one folder).

Per-PC files (.env, logs/) sit next to the exe, where staff can see them. Files shipped with the program sit inside
the build (PyInstaller's _internal folder). Every answer is worked out when asked, never fixed at import, so a test
that pretends to be the exe (sys.frozen, sys.executable) gets the exe's folders.
"""
import os
import shutil
import sys

INSTALLED_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def is_frozen() -> bool:
    """Running as the packaged exe."""
    return bool(getattr(sys, 'frozen', False))


def app_dir() -> str:
    """The folder staff see: the exe's when packaged, else the project folder. .env and logs/ live here."""
    return os.path.dirname(sys.executable) if is_frozen() else os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    """The files shipped inside the build; the project folder when run as a script."""
    return getattr(sys, '_MEIPASS', None) or app_dir()


def log_dir() -> str:
    return os.path.join(app_dir(), "logs")


def env_file() -> str:
    return os.path.join(app_dir(), ".env")


def betty_paths_file() -> str:
    """Where Betty's drive was found on this till (betty_feed.save_betty_root), kept with this build."""
    return os.path.join(app_dir(), "betty_paths.json")


def find_tesseract() -> str | None:
    """
    The Tesseract to run: TESSERACT_CMD from .env, else the copy shipped with the program (tesseract/ next to the exe
    or inside the build), else the usual install, else one on PATH. None when there is none at all.
    """
    for path in (os.environ.get("TESSERACT_CMD", "").strip(),
                 os.path.join(app_dir(), "tesseract", "tesseract.exe"),
                 os.path.join(bundle_dir(), "tesseract", "tesseract.exe"),
                 INSTALLED_TESSERACT):
        if path and os.path.isfile(path):
            return path
    return shutil.which("tesseract")
