# 🎙️ EchoText

AI-powered desktop audio transcription application with real-time audio-text synchronization.

---

## ✨ Features

- 🎙️ **Audio Transcription**  
  Powered by OpenAI's Whisper using the optimized `faster-whisper` implementation.

- 🎵 **Audio–Text Synchronization**  
  Click any word or segment to instantly jump to that timestamp in the audio playback.

- 💾 **Persistent History & Reports**  
  All transcriptions and generated summaries are saved locally using SQLite.

- 🤖 **AI-Generated Minutes of Meeting (MoM)**  
  Summarize meetings automatically using `Qwen2.5-0.5B-Instruct` locally, with a robust TF-IDF keyword-extraction fallback if the neural network is unavailable.

- 📤 **Export Support**  
  Download transcripts as plain text `.txt` files or copy Markdown MoM reports.

- 🖥️ **Desktop Application**  
  Native Electron-based wrapper for Windows integration.

---

## 🛠️ Tech Stack

### 🔙 Backend
- Python + FastAPI
- faster-whisper (optimized CTranslate2 Whisper implementation)
- SQLite (local database persistence)
- Hugging Face Transformers (`Qwen/Qwen2.5-0.5B-Instruct` for summarization)

### 🎨 Frontend
- React + Vite
- Tailwind CSS
- Axios (API communication)

### 🖥️ Desktop Wrapper
- Electron

---

## 📦 Prerequisites

Ensure you have the following installed on your system:
- **Node.js** (v18+)
- **Python** (v3.8+)
- **FFmpeg** (automatically configured on first startup via `imageio-ffmpeg`)

---

## 🔧 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/advait-vikas/EchoText.git
cd text_to_voice
```

### 2️⃣ Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3️⃣ Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 4️⃣ Install Electron Dependencies
```bash
npm install
```

---

## 🚀 Running the Application

### 🖥️ Desktop Mode (Recommended)
Run the entire stack with a single command from the project root:
```bash
npm run electron:dev
```
This will automatically:
1. Start the Python FastAPI backend
2. Start the Vite React development server
3. Launch the Electron desktop window

### 🌐 Web Mode (Development)

**Option 1: Using PowerShell Startup Script**
```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

**Option 2: Manual Start**

1. **Terminal 1 – Backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --port 8000
   ```

2. **Terminal 2 – Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

Open [http://localhost:5173](http://localhost:5173) in your web browser.

---

## 📁 Project Structure

```
text_to_voice/
├── backend/              # Python FastAPI backend
│   ├── main.py           # API endpoints & application startup
│   ├── database.py       # SQLite connection & database operations
│   ├── summarizer.py     # Qwen-2.5 MoM & TF-IDF fallback summarizer
│   ├── requirements.txt  # Python package list
│   └── uploads/          # Local audio files storage (gitignored)
│
├── frontend/             # React frontend
│   ├── src/
│   │   ├── App.jsx       # Main application view & logic
│   │   └── index.css     # Global styles & design system
│   └── package.json      # React project scripts & dependencies
│
├── electron/             # Electron desktop configuration
│   ├── main.js           # Desktop main process
│   └── preload.js        # Security context bridge
│
├── package.json          # Root Electron configuration
└── start.ps1             # PowerShell developer startup script
```

---

## ⚙️ How It Works

1. **Upload**: Drag & drop or select an audio file (`.mp3`, `.wav`, `.m4a`, `.mp4`).
2. **Transcription**: `faster-whisper` processes the audio and returns timestamped word segments.
3. **Synchronization**: In the editor, click any word to seek the audio player to that exact timestamp.
4. **Minutes of Meeting (MoM)**: Click **Summarize | MOM** to generate detailed structured notes and actionable items from the transcription.
5. **History & Export**: Access previous transcriptions from the sidebar or export them to `.txt`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
