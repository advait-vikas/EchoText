# EchoText - Desktop Application Setup

## Running the Electron Desktop App

### Development Mode:

1. **Start the backend** (in one terminal):
   ```powershell
   cd backend
   python -m uvicorn main:app --port 8000
   ```

2. **Start the frontend** (in another terminal):
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Start Electron** (in a third terminal):
   ```powershell
   npm run electron:dev
   ```

### Quick Start (Automated):

The Electron app will automatically start both the backend and frontend for you:

```powershell
# From the project root
npm run electron:dev
```

Wait for the backend to initialize (~10 seconds), then the Electron window will open.

## Project Structure

```
text_to_voice/
├── backend/              # Python FastAPI backend
│   ├── main.py
│   ├── database.py
│   └── uploads/         # Audio files storage
├── frontend/            # React frontend
│   ├── src/
│   └── dist/           # Production build
├── electron/            # Electron wrapper
│   ├── main.js         # Main process
│   └── preload.js      # Security bridge
└── package.json        # Electron configuration
```

## How It Works

1. **Electron Main Process** (`electron/main.js`):
   - Spawns the Python backend as a child process
   - Creates a browser window
   - Loads the frontend from Vite dev server (dev) or built files (production)
   - Manages application lifecycle

2. **Backend**: Runs on `http://localhost:8000`
3. **Frontend**: Runs on `http://localhost:5173` (dev) or loads from `dist/` (production)

## Next Steps

- [ ] Test transcription in Electron window
- [ ] Build production executable (Phase 2)
- [ ] Create app icon
- [ ] Add auto-updater (optional)
