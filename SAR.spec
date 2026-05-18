# -*- mode: python ; coding: utf-8 -*-

import os

RAIZ = os.path.abspath(".")

block_cipher = None

a = Analysis(
    [os.path.join(RAIZ, "backend", "servidor.py")],
    pathex=[os.path.join(RAIZ, "backend")],
    binaries=[],
    datas=[
        (os.path.join(RAIZ, "frontend"),              "frontend"),
        (os.path.join(RAIZ, "integracao"),            "integracao"),
        (os.path.join(RAIZ, "certificado", "publico"), os.path.join("certificado", "publico")),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "pdfplumber",
        "docx",
        "google.generativeai",
        "openai",
        "bcrypt",
        "dotenv",
        "rotinas.genericas",
        "rotinas.importacao",
        "rotinas.autenticacao",
        "rotinas.sincronizacao",
        "rotinas.ia",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SAR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
