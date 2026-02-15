const { app, BrowserWindow, Menu, dialog } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

let mainWindow;
let backendProcess = null;
let frontendProcess = null;
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

let servicesWeStarted = { backend: false, frontend: false };

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

    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
    mainWindow.webContents.openDevTools();

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
    const backendDir = path.join(__dirname, '../backend');

    backendProcess = spawn('python', ['-m', 'uvicorn', 'main:app', '--port', BACKEND_PORT.toString()], {
        cwd: backendDir,
        shell: true,
        stdio: 'pipe'
    });

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
            dialog.showErrorBox('Backend Error', `Backend process crashed with code ${code}`);
        }
    });
}

async function startFrontend() {
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

function waitForService(port, name, maxRetries = 40) {
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

function stopServices() {
    // Only stop services we started
    if (servicesWeStarted.backend && backendProcess) {
        console.log('Stopping backend...');
        backendProcess.kill();
    }
    if (servicesWeStarted.frontend && frontendProcess) {
        console.log('Stopping frontend...');
        frontendProcess.kill();
    }
}

app.whenReady().then(async () => {
    try {
        console.log('Starting EchoText...');

        // Start backend
        await startBackend();
        await waitForService(BACKEND_PORT, 'Backend');

        // Start frontend
        await startFrontend();
        await waitForService(FRONTEND_PORT, 'Frontend');

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
    app.quit();
});

app.on('before-quit', () => {
    stopServices();
});
