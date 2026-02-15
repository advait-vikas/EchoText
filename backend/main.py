import os
import shutil
import tempfile
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
import imageio_ffmpeg
from database import init_db, add_transcription, get_transcriptions, delete_transcription, get_transcription

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Ensure ffmpeg is in path
if not shutil.which("ffmpeg"):
    print("ffmpeg not found in PATH. Attempting to configure imageio-ffmpeg.")
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        print(f"Added {ffmpeg_dir} to PATH")
    except Exception as e:
        print(f"Error configuring ffmpeg from imageio-ffmpeg: {e}")

import torch
from contextlib import asynccontextmanager

model = None
device = "cuda" if torch.cuda.is_available() else "cpu"
# float16 is fast on GPU, float32 or int8 is better for CPU
compute_type = "float16" if device == "cuda" else "float32"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, device, compute_type
    print("Initializing database...")
    init_db()
    
    try:
        print(f"Loading Faster-Whisper model on {device} ({compute_type})...")
        model = WhisperModel("base", device=device, compute_type=compute_type)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load on {device}: {e}. Falling back to CPU...")
        device = "cpu"
        compute_type = "int8"
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("Model loaded on CPU.")
            
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

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    global model, device, compute_type
    if model is None:
        raise HTTPException(status_code=503, detail="Model is loading...")

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
        # Transcribe
        segments_generator, info = model.transcribe(temp_path, beam_size=5)
        
        segments_list = []
        full_text = []
        for s in segments_generator:
            segments_list.append({
                "start": s.start,
                "end": s.end,
                "text": s.text.strip()
            })
            full_text.append(s.text.strip())
        
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
        # Robust fallback: Try initializing a fresh CPU model if CUDA failed
        if "CUDA" in str(e) or "cudnn" in str(e):
            try:
                print("CUDA failed. Retrying with a fresh CPU model...")
                cpu_model = WhisperModel("base", device="cpu", compute_type="int8")
                segs, _ = cpu_model.transcribe(temp_path)
                
                res_segs = []
                res_text = []
                for s in segs:
                    res_segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
                    res_text.append(s.text.strip())
                
                transcript = " ".join(res_text)
                audio_url = f"http://127.0.0.1:8000/audio/{unique_filename}"
                db_id = add_transcription(file.filename, transcript, audio_path=audio_url, segments=res_segs)
                
                return JSONResponse(content={
                    "transcript": transcript, 
                    "filename": file.filename, 
                    "id": db_id,
                    "audio_url": audio_url,
                    "segments": res_segs
                })
            except Exception as cpu_e:
                raise HTTPException(status_code=500, detail=f"CPU fallback also failed: {cpu_e}")
        
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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "EchoText API is ready"}
