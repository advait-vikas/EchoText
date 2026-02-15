// Preload script for Electron
// This runs in a sandboxed context before the renderer loads
// Use it to safely expose APIs from Node.js to the renderer process

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// some Node.js functionality without exposing sensitive APIs
contextBridge.exposeInMainWorld('electronAPI', {
    // Add any APIs you need to expose to the frontend here
    // For now, we don't need any as the frontend communicates with the backend via HTTP
});
