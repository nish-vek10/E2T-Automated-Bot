# -*- mode: python ; coding: utf-8 -*-

import numpy
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['closePartial.py'],
    pathex=['.'],
    binaries=[],
    datas=collect_data_files('numpy') + collect_data_files('MetaTrader5'),
    hiddenimports=[
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core._dtype_ctypes',
        'numpy.linalg',
        'numpy.lib.format',
        'MetaTrader5',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='closePartial_exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='closePartial_exe',
)
