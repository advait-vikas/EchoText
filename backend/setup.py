import sys
sys.setrecursionlimit(10000)
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": [
        "fastapi", 
        "uvicorn", 
        "faster_whisper", 
        "ctranslate2", 
        "sqlite3", 
        "starlette", 
        "pydantic",
        "torch",
        "transformers",
        "sentencepiece",
        "huggingface_hub"
    ],
    "excludes": [
        "torchvision", "torchaudio", "nvidia", "matplotlib", 
        "PIL", "IPython", "notebook", "tkinter", "pandas", "scipy", 
        "cv2", "PyQt5", "PyQt6", "PySide2", "PySide6"
    ],
    "include_files": []
}

setup(
    name="echotext-backend",
    version="1.0",
    description="EchoText Backend API",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", target_name="echotext-backend.exe")]
)
