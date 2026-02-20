import { contextBridge } from "electron";

// The main process sets BACKEND_PORT in process.env before creating the window.
// The preload script has access to process.env in Electron.
const port = process.env.BACKEND_PORT || "8000";

// Expose the API base URL to the renderer via window.__API_BASE_URL__
contextBridge.exposeInMainWorld("__API_BASE_URL__", `http://127.0.0.1:${port}`);
