# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para TLDRDC
# Generado para PyInstaller 6.x
# Modo: onedir (recomendado para playtest - arranca al instante)
#
# Para compilar: pyinstaller TLDRDC.spec
# Output en: dist/TLDRDC_Prueba1/

import os
from pathlib import Path

project_root = Path(SPECPATH)
code_dir = project_root / "code"
modules_dir = project_root / "modules"

a = Analysis(
    [str(code_dir / "TLDRDC_Prueba1.py")],
    pathex=[str(project_root), str(code_dir)],
    binaries=[],
    datas=[
        # Imágenes incluidas en el bundle, destino relativo dentro del exe
        (str(code_dir / "images"), "images"),
        # Módulos del proyecto (events, ui_config, etc.)
        (str(modules_dir), "modules"),
    ],
    hiddenimports=[
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "tkinter",
        "tkinter.font",
        "modules.ui_config",
        "modules.ui_imagen_manager",
        "modules.ui_estructura",
        "modules.reactive",
        "modules.events",
        "modules.logging_manager",
        "modules.performance_monitor",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TLDRDC_Prueba1",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sin ventana de consola negra al abrir
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TLDRDC_Prueba1",
)
