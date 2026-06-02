import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Aggressively exclude large unnecessary libraries
excluded_modules = [
    'torch', 'torchvision', 'torchaudio', 'nvidia', 'matplotlib', 
    'PIL', 'jedi', 'nbformat', 'IPython', 'notebook', 
    'black', 'pydoc', 'tkinter', 'unittest', 'test',
    'win32com', 'pyarrow', 'pandas', 'scipy', 'sklearn',
    'jax', 'jaxlib', 'nltk', 'cv2', 'opencv-python'
]

# Specifically ensure SSL and other critical libraries are included
# We search for these in the current Python environment
python_dir = os.path.dirname(sys.executable)
site_packages = os.path.join(python_dir, 'Lib', 'site-packages')
binaries = []

# Common names for SSL DLLs in Python 3.12+
ssl_dlls = ['libcrypto-3-x64.dll', 'libssl-3-x64.dll', 'libcrypto-3.dll', 'libssl-3.dll']
for dll in ssl_dlls:
    dll_path = os.path.join(python_dir, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))
    else:
        # Check DLLs folder too
        dll_path = os.path.join(python_dir, 'DLLs', dll)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))

# ctranslate2 DLLs MUST be at the bundle root (not _internal) for CPU dispatcher to work.
ct2_dir = os.path.join(site_packages, 'ctranslate2')
ct2_dlls = ['ctranslate2.dll', 'libiomp5md.dll', 'cudnn64_9.dll']
for dll in ct2_dlls:
    dll_path = os.path.join(ct2_dir, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries + collect_dynamic_libs('ctranslate2') + collect_dynamic_libs('faster_whisper'),
    datas=collect_data_files('faster_whisper') + collect_data_files('ctranslate2'),
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'faster_whisper',
        'ctranslate2',
    ] + collect_submodules('uvicorn'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
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
    name='echotext-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='echotext-backend',
)
