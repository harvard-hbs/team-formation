import { app, BrowserWindow, dialog } from "electron";
import { ChildProcess, spawn } from "child_process";
import * as path from "path";
import * as http from "http";

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;
let backendPort: number = 0;

/**
 * Find a free port by binding to port 0 and reading the assigned port.
 */
function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = require("net").createServer();
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on("error", reject);
  });
}

/**
 * Get the path to the PyInstaller-bundled backend executable.
 */
function getBackendPath(): string {
  const isPackaged = app.isPackaged;
  const resourcesPath = isPackaged
    ? process.resourcesPath
    : path.join(__dirname, "..");

  const platform = process.platform;
  const execName =
    platform === "win32" ? "team_formation_api.exe" : "team_formation_api";

  return path.join(resourcesPath, "python-dist", execName);
}

/**
 * Get the path to the frontend dist directory.
 */
function getFrontendPath(): string {
  const isPackaged = app.isPackaged;

  if (isPackaged) {
    return path.join(process.resourcesPath, "ui-dist");
  }

  // Development: use the ui/dist directory from the project root
  return path.join(__dirname, "..", "..", "ui", "dist");
}

/**
 * Spawn the Python backend subprocess.
 */
function startBackend(port: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const backendPath = getBackendPath();

    console.log(`Starting backend: ${backendPath} on port ${port}`);

    backendProcess = spawn(backendPath, [], {
      env: {
        ...process.env,
        PORT: String(port),
        CORS_ORIGINS: "*",
        PRODUCTION: "false",
        LOG_LEVEL: "WARNING",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });

    backendProcess.stdout?.on("data", (data: Buffer) => {
      console.log(`[backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr?.on("data", (data: Buffer) => {
      console.error(`[backend] ${data.toString().trim()}`);
    });

    backendProcess.on("error", (err: Error) => {
      console.error("Failed to start backend:", err);
      reject(err);
    });

    backendProcess.on("exit", (code: number | null, signal: string | null) => {
      console.log(`Backend exited with code=${code} signal=${signal}`);
      backendProcess = null;
    });

    // Poll the health endpoint until the backend is ready
    pollHealth(port, 30000, 200)
      .then(() => {
        console.log("Backend is ready");
        resolve();
      })
      .catch((err) => {
        console.error("Backend failed to start:", err);
        reject(err);
      });
  });
}

/**
 * Poll the /health endpoint until it responds OK.
 */
function pollHealth(
  port: number,
  timeoutMs: number,
  intervalMs: number
): Promise<void> {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      if (Date.now() - start > timeoutMs) {
        reject(new Error("Backend did not start within timeout"));
        return;
      }

      const req = http.get(
        `http://127.0.0.1:${port}/health`,
        (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            setTimeout(check, intervalMs);
          }
        }
      );

      req.on("error", () => {
        setTimeout(check, intervalMs);
      });

      req.setTimeout(1000, () => {
        req.destroy();
        setTimeout(check, intervalMs);
      });
    };

    check();
  });
}

/**
 * Create the main application window.
 */
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: "Team Formation",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const frontendPath = getFrontendPath();
  const indexPath = path.join(frontendPath, "index.html");

  console.log(`Loading frontend from: ${indexPath}`);
  mainWindow.loadFile(indexPath);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

/**
 * Gracefully shut down the backend subprocess.
 */
function stopBackend(): Promise<void> {
  return new Promise((resolve) => {
    if (!backendProcess) {
      resolve();
      return;
    }

    const proc = backendProcess;
    const killTimeout = setTimeout(() => {
      console.log("Backend did not exit gracefully, sending SIGKILL");
      proc.kill("SIGKILL");
      resolve();
    }, 5000);

    proc.on("exit", () => {
      clearTimeout(killTimeout);
      resolve();
    });

    console.log("Sending SIGTERM to backend");
    proc.kill("SIGTERM");
  });
}

// Application lifecycle

app.whenReady().then(async () => {
  try {
    backendPort = await findFreePort();
    // Set env var so the preload script can read it
    process.env.BACKEND_PORT = String(backendPort);
    await startBackend(backendPort);
    createWindow();
  } catch (err) {
    console.error("Failed to initialize:", err);
    dialog.showErrorBox(
      "Startup Error",
      `Failed to start the Team Formation backend.\n\n${err}`
    );
    app.quit();
  }
});

// macOS: re-create window when dock icon is clicked
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0 && backendPort > 0) {
    createWindow();
  }
});

// macOS: keep app alive when all windows close
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", async () => {
  await stopBackend();
});

app.on("will-quit", async (event) => {
  if (backendProcess) {
    event.preventDefault();
    await stopBackend();
    app.quit();
  }
});
