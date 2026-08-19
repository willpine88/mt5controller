# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mt5control.py'],
    pathex=[],
    binaries=[('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-console-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-console-l1-2-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-datetime-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-debug-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-errorhandling-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-fibers-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-fibers-l1-1-1.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-file-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-file-l1-2-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-file-l2-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-handle-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-heap-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-interlocked-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-kernel32-legacy-l1-1-1.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-libraryloader-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-localization-l1-2-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-memory-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-namedpipe-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-processenvironment-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-processthreads-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-processthreads-l1-1-1.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-profile-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-rtlsupport-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-string-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-synch-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-synch-l1-2-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-sysinfo-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-sysinfo-l1-2-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-timezone-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-core-util-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-conio-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-convert-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-environment-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-filesystem-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-heap-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-locale-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-math-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-multibyte-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-private-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-process-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-runtime-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-stdio-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-string-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-time-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/api-ms-win-crt-utility-l1-1-0.dll', '.'), ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.26100.0/ucrt/DLLs/x64/ucrtbase.dll', '.'), ('C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0/vcruntime140.dll', '.'), ('C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0/vcruntime140_1.dll', '.')],
    datas=[],
    hiddenimports=['win32gui', 'win32con', 'win32api', 'win32process'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # AVIF codec is never used (tray icon is drawn in-memory) but ships a 7.8 MB
    # _avif.pyd — the largest payload in the onefile archive. Dropping it shrinks
    # the exe and removes the entry that fails to extract on damaged copies.
    excludes=['PIL._avif', 'PIL.AvifImagePlugin'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MT5Controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['icon.ico'],
)
