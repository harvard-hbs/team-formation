# Team Formation Desktop

Electron shell that packages the Team Formation FastAPI backend and Vue.js
frontend into a standalone desktop application for macOS, Windows, and Linux.
No Docker, Python, or Node.js installation is required by the end user.

## How It Works

On launch, the Electron main process ([electron/main.ts](electron/main.ts)):

1. Binds to port 0 to find a free loopback port.
2. Spawns the PyInstaller-bundled backend on that port with `PORT`,
   `PRODUCTION=true`, `CORS_ORIGINS=*`, `LOG_LEVEL=WARNING`, and `STATIC_DIR`
   pointing at the built frontend.
3. Polls `http://127.0.0.1:<port>/health` until it returns 200 (30 second
   timeout, 200 ms interval), then opens the `BrowserWindow`.
4. Loads `http://127.0.0.1:<port>` rather than a `file://` URL, so the backend
   serves the frontend's absolute Vite asset paths correctly.
5. On quit, sends `SIGTERM` to the backend and escalates to `SIGKILL` after
   5 seconds.

[electron/preload.ts](electron/preload.ts) exposes `window.__API_BASE_URL__`
with the chosen port. The frontend reads it in
[ui/src/services/api.ts](../ui/src/services/api.ts), falling back to
`VITE_API_BASE_URL` and then `http://localhost:8000` when running in a browser.

The window uses `contextIsolation: true` and `nodeIntegration: false`; the
preload script is the only bridge into the renderer.

## Layout

```
electron/                 TypeScript source (main.ts, preload.ts)
resources/                Icons and macOS entitlements
scripts/build-python.sh   PyInstaller build wrapper (build-python.ps1 on Windows)
team_formation_api.spec   PyInstaller spec for the backend bundle
electron-builder.yml      Packaging configuration
dist-electron/            Compiled Electron JavaScript (generated)
python-dist/              Bundled backend (generated)
release/                  Installers (generated)
```

Everything marked generated is gitignored.

## Prerequisites

- Node.js 22 and npm
- Python 3.12 with the project installed (`pip install -e ..`) and
  `pip install pyinstaller`

## Local Development

Build the two bundled payloads first, then run the shell:

```bash
# 1. Build the Vue.js frontend
cd ../ui && npm ci && npm run build && cd ../desktop

# 2. Bundle the backend into desktop/python-dist/
./scripts/build-python.sh

# 3. Compile the Electron TypeScript and launch
npm ci
npm run dev
```

`npm run dev` runs `tsc && electron .`. Steps 1 and 2 only need to be repeated
when the frontend or Python code changes. `build-python.sh` cleans previous
output, runs PyInstaller, moves `dist/team_formation_api` to `python-dist/`,
and smoke tests `/health` on port 8000.

The backend is bundled one-directory rather than one-file because OR-Tools
loads many dynamic shared libraries that do not resolve reliably in one-file
mode. When adding a Python dependency that is imported dynamically, add it to
`hiddenimports` in [team_formation_api.spec](team_formation_api.spec).

## Building Installers

```bash
npm run dist:mac      # macOS DMG (arm64)
npm run dist:win      # Windows NSIS installer (x64)
npm run dist:linux    # Linux AppImage (x64)
npm run dist          # All configured targets
npm run pack          # Unpacked directory, for debugging packaging issues
```

Installers are written to `release/`. Cross-compiling is not supported for
macOS; build each platform on that platform or use CI.

`electron-builder.yml` copies `python-dist/` and `../ui/dist/` into the app's
resources directory as `python-dist` and `ui-dist`, which is where
`getBackendPath()` and `getFrontendPath()` look when `app.isPackaged` is true.

## CI and Releases

[.github/workflows/desktop-build.yml](../.github/workflows/desktop-build.yml)
builds all three platforms in a matrix on `workflow_dispatch` or on pushing a
`v*` tag. Each job installs Python and Node, builds the frontend, bundles the
backend, smoke tests `/health` on port 9300, syncs `package.json` version from
the tag, and packages with electron-builder. On a tag, a `release` job
publishes a GitHub Release with the installers attached.

To cut a release:

```bash
git tag v2.0.4 && git push --tags
```

Installers are built in CI and attached to the release; they are never checked
into the repository.

## Code Signing

macOS and Windows signing is scaffolded but disabled. The commented blocks in
[electron-builder.yml](electron-builder.yml) (`mac.identity`,
`win.certificateFile`) and the commented `CSC_LINK`, `APPLE_ID`, and related
environment variables in the workflow mark what needs to be filled in once
certificates are available as repository secrets. Until then, users must
bypass Gatekeeper and SmartScreen warnings on first launch.
