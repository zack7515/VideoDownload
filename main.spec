# main.spec

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 這裡我們用自動化的方式處理 PyQt6
pyqt6_hiddenimports = collect_submodules('PyQt6')

# --- 第一階段：分析與備料 (Analysis) ---
a = Analysis(
    ['main.py', 'downloader.py'],
    pathex=['C:\\Users\\zack\\Desktop\\VideoDownload'],  # 寫入你需要的路徑
    binaries=[],
    datas=[
        ('icon', 'icon'),  # icon可以放入你所需要的
        ('ffmpeg.exe', '.')  # 解碼影音合併必須要的
    ],
    hiddenimports=pyqt6_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- 第二階段：組裝核心 Python 程式碼 (PYZ) ---
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- 第三階段：建立 .exe 啟動器 (EXE) ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon/ghibli_downloader.ico',  # icon可以放入你所需要的
)

# --- 第四階段：收集所有檔案到最終的輸出資料夾 (COLLECT) ---
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoDownloader', # 最終輸出的資料夾名稱
)