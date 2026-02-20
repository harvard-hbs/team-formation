# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for bundling the Team Formation FastAPI backend.

Usage:
    pyinstaller desktop/team_formation_api.spec

This creates a one-directory bundle (not one-file) because ortools has
many dynamic shared libraries that don't work reliably in one-file mode.
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# Collect all ortools submodules (the solver has many internal modules)
ortools_hiddenimports = collect_submodules("ortools")
ortools_binaries = collect_dynamic_libs("ortools")
ortools_datas = collect_data_files("ortools")

# Collect uvicorn internals (uses dynamic imports for lifespan, loops, etc.)
uvicorn_hiddenimports = collect_submodules("uvicorn")

block_cipher = None

a = Analysis(
    ["../team_formation/api/main.py"],
    pathex=[os.path.abspath("..")],
    binaries=ortools_binaries,
    datas=ortools_datas,
    hiddenimports=[
        # ortools and its native extensions
        *ortools_hiddenimports,
        # uvicorn internals
        *uvicorn_hiddenimports,
        # ASGI server components
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.wsproto_impl",
        # FastAPI and Starlette
        "fastapi",
        "starlette",
        "starlette.middleware",
        "starlette.middleware.cors",
        "starlette.routing",
        "sse_starlette",
        "sse_starlette.sse",
        # Data processing
        "pandas",
        "numpy",
        "pandas._libs",
        "pandas._libs.tslibs",
        # Pydantic (used by FastAPI for models)
        "pydantic",
        "pydantic_core",
        # HTTP libraries
        "httptools",
        "h11",
        "anyio",
        "anyio._backends",
        "anyio._backends._asyncio",
        # Team formation package
        "team_formation",
        "team_formation.team_assignment",
        "team_formation.working_time",
        "team_formation.api",
        "team_formation.api.main",
        "team_formation.api.models",
        "team_formation.api.callbacks",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude packages not needed for the API server
        "streamlit",
        "watchdog",
        "tkinter",
        "matplotlib",
        "PIL",
        "IPython",
        "jupyter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="team_formation_api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for logging; Electron hides the window anyway
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="team_formation_api",
)
