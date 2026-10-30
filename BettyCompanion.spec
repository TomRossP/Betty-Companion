# PyInstaller recipe for Betty Companion: one folder, windowed, no UPX (UPX-packed exes upset antivirus).
# Build with:  python build_release.py   (it runs this, adds Tesseract and makes the release zip)
#
# dist\BettyCompanion\BettyCompanion.exe   the window (double-click); run with --backend it is the program itself
# dist\BettyCompanion\_internal\           Python, the libraries, the rules and meetings files, Tesseract
import os
import re

from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable,
                                                 VarFileInfo, VarStruct, VSVersionInfo)

ROOT = os.path.abspath(SPECPATH)  # noqa: F821 (PyInstaller provides SPECPATH)
with open(os.path.join(ROOT, "betty_companion.py"), encoding="utf-8") as f:
    VERSION = re.search(r'^__version__\s*=\s*"([^"]+)"', f.read(), re.MULTILINE).group(1)
NUMS = tuple(([int(n) for n in re.findall(r"\d+", VERSION)] + [0, 0, 0, 0])[:4])

STAGE = os.path.join(ROOT, "build", "stage")
os.makedirs(STAGE, exist_ok=True)
with open(os.path.join(STAGE, "VERSION"), "w", encoding="utf-8") as f:
    f.write(VERSION)
version_file = os.path.join(STAGE, "version_info.txt")
with open(version_file, "w", encoding="utf-8") as f:
    f.write(str(VSVersionInfo(
        ffi=FixedFileInfo(filevers=NUMS, prodvers=NUMS, mask=0x3F, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0,
                          date=(0, 0)),
        kids=[StringFileInfo([StringTable("080904B0", [
                  StringStruct("CompanyName", "Betty Companion"),
                  StringStruct("FileDescription", "Betty Companion: works through Betty's unedited wagers"),
                  StringStruct("FileVersion", VERSION),
                  StringStruct("InternalName", "BettyCompanion"),
                  StringStruct("OriginalFilename", "BettyCompanion.exe"),
                  StringStruct("ProductName", "Betty Companion"),
                  StringStruct("ProductVersion", VERSION)])]),
              VarFileInfo([VarStruct("Translation", [0x0809, 1200])])])))

a = Analysis(  # noqa: F821
    [os.path.join(ROOT, "launcher.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "bookmaker_rules.json"), "."),
           (os.path.join(ROOT, "meetings_directory.json"), "."),
           (os.path.join(STAGE, "VERSION"), "."),
           (os.path.join(ROOT, "assets", "betty.ico"), "assets")],
    # Imported inside functions (the window loads the program only with --backend)
    hiddenimports=["betty_companion", "rules_engine", "meetings_manager", "betty_feed", "relay_link", "error_guide"],
    # Installed on the build PC but never used: kept out (OpenCV alone is ~70 MB). Also pulled in but never used:
    # setuptools (PyInstaller's hook), numpy's test tools (loaded only when asked for; they bring win32pdh), and
    # Pillow's AVIF, WebP and colour-profile support (Pillow skips a missing format plugin). ~10 MB.
    excludes=["cv2", "pandas", "matplotlib", "scipy", "IPython", "PyQt5", "PyQt6", "PySide2", "PySide6",
              "pywinauto", "pytest", "setuptools", "_distutils_hack", "pkg_resources", "numpy.testing", "win32pdh",
              "PIL.AvifImagePlugin", "PIL._avif", "PIL.WebPImagePlugin", "PIL._webp", "PIL.ImageCms",
              "PIL._imagingcms"],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="BettyCompanion",
    console=False,
    upx=False,
    icon=os.path.join(ROOT, "assets", "betty.ico"),
    version=version_file,
)
coll = COLLECT(exe, a.binaries, a.datas, upx=False, name="BettyCompanion")  # noqa: F821
