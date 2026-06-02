const electron = require('electron');
const fs = require('fs');
const path = require('path');

// FAILSAFE: If ELECTRON_RUN_AS_NODE is set, Electron runs as Node.js and require('electron') returns a string path.
// We must detect this, unset the variable, and respawn the application.
if (typeof electron === 'string') {
    const { spawn } = require('child_process');
    const env = { ...process.env };
    delete env.ELECTRON_RUN_AS_NODE;

    // Respawn the same executable with the cleaned environment
    const child = spawn(process.execPath, process.argv.slice(1), {
        env,
        detached: true,
        stdio: 'ignore'
    });
    child.unref();

    process.exit(0);
}

const { app, BrowserWindow, Menu, dialog } = electron;
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess = null;
let frontendProcess = null;
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

// Check if running in development or production
const isDev = !app.isPackaged;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        title: 'EchoText',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    Menu.setApplicationMenu(null);

    if (isDev) {
        mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
        // mainWindow.webContents.openDevTools();
    } else {
        // Path resolution for different packaging structures
        let indexPath = path.join(__dirname, '../frontend/dist/index.html');
        if (!fs.existsSync(indexPath)) {
            // Fallback for electron-builder structure if different
            indexPath = path.join(process.resourcesPath, 'app/frontend/dist/index.html');
        }
        if (!fs.existsSync(indexPath)) {
            // Another common structure
            indexPath = path.join(process.resourcesPath, 'dist/index.html');
        }

        console.log('Loading index from:', indexPath);
        mainWindow.loadFile(indexPath).catch(err => {
            console.error('Failed to load file:', err);
            dialog.showErrorBox('Load Error', `Could not load index.html at ${indexPath}`);
        });
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function checkServiceRunning(port) {
    return new Promise((resolve) => {
        const options = {
            host: 'localhost',
            port: port,
            path: '/',
            timeout: 1000
        };

        const req = http.request(options, () => {
            resolve(true); // Service is running
        });

        req.on('error', () => {
            resolve(false); // Service is not running
        });

        req.end();
    });
}

async function startBackend() {
    const isRunning = await checkServiceRunning(BACKEND_PORT);

    if (isRunning) {
        console.log('Backend already running');
        return;
    }

    console.log('Starting Python backend...');

    let backendExec;
    let backendCwd;

    if (isDev) {
        backendExec = 'python';
        const backendArgs = ['-m', 'uvicorn', 'main:app', '--port', BACKEND_PORT.toString()];
        backendCwd = path.join(__dirname, '../backend');

        backendProcess = spawn(backendExec, backendArgs, {
            cwd: backendCwd,
            shell: true,
            stdio: 'pipe'
        });
    } else {
        // In production, use the frozen executable
        // Try multiple locations to be robust
        const possibleExecs = [
            path.join(process.resourcesPath, 'echotext-backend/echotext-backend.exe'),
            path.join(process.resourcesPath, 'backend/echotext-backend/echotext-backend.exe'),
            path.join(__dirname, '../backend/build/exe.win-amd64-3.12/echotext-backend.exe')
        ];

        for (const execPath of possibleExecs) {
            if (fs.existsSync(execPath)) {
                backendExec = execPath;
                backendCwd = path.dirname(execPath);
                break;
            }
        }

        if (!backendExec) {
            throw new Error('Could not find backend executable');
        }

        console.log(`Executing: ${backendExec} in ${backendCwd}`);

        backendProcess = spawn(backendExec, [], {
            cwd: backendCwd,
            shell: false,
            stdio: 'pipe',
            windowsHide: true
        });
    }

    servicesWeStarted.backend = true;

    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.on('exit', (code) => {
        console.log(`Backend exited with code ${code}`);
        if (code !== 0 && code !== null) {
            // Only show error if the app is still running
            if (mainWindow) {
                dialog.showErrorBox('Backend Error', `Backend process crashed with code ${code}`);
            }
        }
    });
}

async function startFrontend() {
    // Only start frontend dev server in dev mode
    if (!isDev) return;

    const isRunning = await checkServiceRunning(FRONTEND_PORT);

    if (isRunning) {
        console.log('Frontend already running');
        return;
    }

    console.log('Starting Vite dev server...');
    const frontendDir = path.join(__dirname, '../frontend');

    frontendProcess = spawn('npm.cmd', ['run', 'dev'], {
        cwd: frontendDir,
        shell: true,
        stdio: 'pipe',
        env: { ...process.env, BROWSER: 'none' }
    });

    servicesWeStarted.frontend = true;

    frontendProcess.stdout.on('data', (data) => {
        console.log(`[Frontend] ${data.toString().trim()}`);
    });

    frontendProcess.stderr.on('data', (data) => {
        console.log(`[Frontend] ${data.toString().trim()}`);
    });

    frontendProcess.on('exit', (code) => {
        console.log(`Frontend exited with code ${code}`);
    });
}

function waitForService(port, name, maxRetries = 60) {
    return new Promise((resolve, reject) => {
        let retries = 0;

        const check = () => {
            checkServiceRunning(port).then((running) => {
                if (running) {
                    console.log(`${name} is ready!`);
                    resolve();
                } else if (retries < maxRetries) {
                    retries++;
                    console.log(`Waiting for ${name}... (${retries}/${maxRetries})`);
                    setTimeout(check, 1000);
                } else {
                    reject(new Error(`${name} failed to start after ${maxRetries} seconds`));
                }
            });
        };

        check();
    });
}

let servicesWeStarted = { backend: false, frontend: false };

function stopServices() {
    if (servicesWeStarted.backend && backendProcess) {
        backendProcess.kill();
    }
    if (servicesWeStarted.frontend && frontendProcess) {
        frontendProcess.kill();
    }
}

app.whenReady().then(async () => {
    try {
        console.log('Starting EchoText...');

        // Start backend
        await startBackend();
        await waitForService(BACKEND_PORT, 'Backend');

        // Start frontend (only if in dev)
        if (isDev) {
            await startFrontend();
            await waitForService(FRONTEND_PORT, 'Frontend');
        }

        // Create window
        createWindow();

    } catch (error) {
        console.error('Startup error:', error);
        dialog.showErrorBox('Startup Failed', error.message);
        app.quit();
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopServices();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    stopServices();
});
