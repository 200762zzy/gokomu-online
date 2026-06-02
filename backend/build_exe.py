"""Build GomokuOnline.exe via PyInstaller spec file.
Override dist path with PYINSTALLER_DISTPATH env var (for CI)."""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "GomokuOnline.spec"
DISTPATH = Path(os.getenv("PYINSTALLER_DISTPATH", str(ROOT)))
WORKPATH = ROOT / "build"

spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'{ROOT / "backend" / "run.py"}'],
    pathex=[r'{ROOT / "backend"}'],
    binaries=[],
    datas=[
        (r'{ROOT / "frontend" / "dist"}', 'frontend_dist'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'httpx',
        'aiosqlite',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GomokuOnline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

SPEC.write_text(spec_content, encoding="utf-8")
print(f"Spec file created: {SPEC}")

subprocess.run(
    [sys.executable, "-m", "PyInstaller", str(SPEC), "--distpath", str(DISTPATH), "--workpath", str(WORKPATH), "--clean"],
    cwd=str(ROOT),
    check=True,
)
print(f"Build complete: {DISTPATH / 'GomokuOnline.exe'}")
