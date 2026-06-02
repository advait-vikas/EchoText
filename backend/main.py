import os
import shutil
import tempfile
import uuid
import sys

# --- Packaging Hack: Patch transformers to prevent KeyError: frozenset() under cx_Freeze/PyInstaller ---
try:
    from importlib.abc import MetaPathFinder
    from importlib.util import find_spec

    class PatchTransformersFinder(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == 'transformers.utils.import_utils':
                sys.meta_path.remove(self)
                try:
                    spec = find_spec(fullname, path)
                    if spec is not None:
                        orig_exec = spec.loader.exec_module
                        def new_exec(module):
                            orig_exec(module)
                            orig = module.define_import_structure
                            module.define_import_structure = lambda *a, **k: {frozenset(): {}, **orig(*a, **k)}
                        spec.loader.exec_module = new_exec
                    return spec
                finally:
                    sys.meta_path.insert(0, self)
            return None

    sys.meta_path.insert(0, PatchTransformersFinder())
except Exception as e:
    print(f"Failed to install transformers packaging patch: {e}")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
import imageio_ffmpeg
from database import init_db, add_transcription, get_transcriptions, delete_transcription, get_transcription, update_summary, set_db_path
from summarizer import extract_mom
from contextlib import asynccontextmanager

# --- Path Configuration ---
if getattr(sys, 'frozen', False) or os.environ.get('RUNNING_IN_DOCKER') == 'true':
    # Set OpenMP vars to prevent ctranslate2 access violation
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["OMP_NUM_THREADS"] = "1"
    
    if getattr(sys, 'frozen', False):
        # cx_Freeze stores the executable in the base directory
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
    # Use AppData for writable files in production or Docker
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'EchoText')
else:
    # If running normally during development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BASE_DIR

# Ensure necessary directories exist
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configure Database Path
DB_PATH = os.path.join(DATA_DIR, "transcriptions.db")
set_db_path(DB_PATH)

# Configure Whisper Cache inside Data Dir
os.environ["HF_HOME"] = os.path.join(DATA_DIR, "models")
os.environ["WHISPER_HOME"] = os.path.join(DATA_DIR, "models")

# --- Startup Verification ---
print(f"EchoText Backend starting up...")
print(f"Base Directory: {BASE_DIR}")
print(f"Data Directory: {DATA_DIR}")
print(f"Database Path: {DB_PATH}")

# Ensure ffmpeg is in path
if not shutil.which("ffmpeg"):
    print("ffmpeg not found in PATH. Checking imageio-ffmpeg...")
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        print(f"Added {ffmpeg_dir} to PATH")
    except Exception as e:
        print(f"Error configuring ffmpeg: {e}")

# Using CPU by default for maximum portability and smaller app size
device = "cpu"
compute_type = "int8"
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("EchoText starting up...")
    init_db()
    print("Database initialized.")
    # Model is loaded lazily on first transcription request
    print("Startup complete. Model will load on first transcription.")
    yield
    model = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=UPLOAD_DIR), name="audio")

def log_debug(msg):
    log_path = os.path.join(DATA_DIR, "transcribe_debug.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    global model, device, compute_type
    log_debug("--- NEW TRANSCRIPTION REQUEST ---")
    
    # Lazy model loading - load on first request
    if model is None:
        log_debug(f"Loading Faster-Whisper model on {device} ({compute_type})...")
        try:
            model = WhisperModel("base", device=device, compute_type=compute_type)
            log_debug("Model loaded successfully.")
        except Exception as e:
            log_debug(f"Failed to load model: {e}")
            raise HTTPException(status_code=503, detail=f"Model failed to load: {str(e)}")


    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.mp4')):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    permanent_path = os.path.join(UPLOAD_DIR, unique_filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    with open(permanent_path, "wb") as f:
        f.write(content)

    try:
        log_debug(f"Starting model.transcribe on {temp_path}...")
        # Transcribe
        segments_generator, info = model.transcribe(temp_path, beam_size=5)
        
        log_debug("Transcription started, iterating segments...")
        segments_list = []
        full_text = []
        for s in segments_generator:
            segments_list.append({
                "start": s.start,
                "end": s.end,
                "text": s.text.strip()
            })
            full_text.append(s.text.strip())
        
        log_debug("Transcription loop complete.")
        transcript = " ".join(full_text)
        audio_url = f"http://127.0.0.1:8000/audio/{unique_filename}"
        
        db_id = add_transcription(file.filename, transcript, audio_path=audio_url, segments=segments_list)
        
        return JSONResponse(content={
            "transcript": transcript, 
            "filename": file.filename, 
            "id": db_id,
            "audio_url": audio_url,
            "segments": segments_list
        })

    except Exception as e:
        print(f"Transcription error: {e}")
        log_debug(f"EXCEPTION ENCOUNTERED: {str(e)}")
        import traceback
        log_debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.get("/history")
def get_history():
    return get_transcriptions()

@app.delete("/history/{id}")
def delete_history_item(id: int):
    delete_transcription(id)
    return {"status": "ok", "deleted": id}

@app.post("/summarize/{id}")
async def summarize_transcription(id: int):
    print(f"Summarize requested for ID: {id}")
    item = get_transcription(id)
    if not item:
        print(f"Item not found: {id}")
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    transcript = item.get('transcript', '')
    if not transcript:
        print(f"No transcript found for ID: {id}")
        raise HTTPException(status_code=400, detail="No transcript available to summarize")
    
    try:
        print(f"Running extraction for transcript length: {len(transcript)}")
        summary_data = extract_mom(transcript)
        print("Summary generated successfully, updating database...")
        update_summary(id, summary_data)
        return summary_data
    except Exception as e:
        print(f"Summarization error for ID {id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "ok", "message": "EchoText API is ready"}

if __name__ == "__main__":
    import uvicorn
    # Use a fixed port to match Electron's expectation
    uvicorn.run(app, host="127.0.0.1", port=8000)
