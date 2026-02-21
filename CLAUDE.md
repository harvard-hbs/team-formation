# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package for constraint-based team formation that uses Google OR-Tools CP-SAT solver to optimally assign participants to teams based on weighted constraints. The tool provides:

- **Programmatic Python API** for direct solver integration
- **FastAPI REST API** with Server-Sent Events for real-time progress streaming
- **Vue.js Web Application** with Vuetify Material Design UI
- **Streamlit UI** for quick interactive use
- **Electron Desktop App** for macOS, Windows, and Linux
- **Docker deployment** combining frontend and backend in a single container

## Common Development Commands

### Testing
```bash
# Run all tests
make test
# or
pytest

# Run tests with info-level logging
make test-info
# or
pytest --log-cli-level=INFO

# Run specific test
pytest tests/test_small.py
```

### Building and Distribution
```bash
# Build package
make build
# or
python -m build

# Clean distribution files
make dist-clean

# Check distribution
make check-dist

# Upload to PyPI
make upload
```

### Running the Application
```bash
# Start Streamlit UI
python -m team_formation

# Start FastAPI REST API server
team-formation-api
# or
python -m team_formation.api.main

# Start Vue.js frontend (development)
cd ui && npm run dev

# Build Vue.js frontend for production
cd ui && npm run build

# Run with Docker (production, combined frontend + backend)
docker build -t team-formation .
docker run -p 8000:8000 team-formation

# Use programmatically
python -c "from team_formation.team_assignment import TeamAssignment; print('API ready')"
```

### Development Setup
```bash
# Install development dependencies
make install
# or
pip install -r requirements-dev.txt
```

## Architecture Overview

### Core Components

- **`team_assignment.py`** - Main `TeamAssignment` class implementing the CP-SAT constraint solver logic
- **`team_assignment_ui.py`** - Streamlit web interface for interactive team formation
- **`working_time.py`** - Utilities for handling time zone and working hour constraints
- **`__main__.py`** - Entry point that launches the Streamlit UI

### Key Classes and Methods

- `TeamAssignment(participants, constraints, target_team_size, less_than_target=False)`
  - `solve(solution_callback=None)` - Run the constraint solver
  - `evaluate_teams()` - Evaluate how well teams meet constraints
  - `participants` - DataFrame with team assignments in `team_num` column

### Constraint Types

The solver supports four constraint types:
- `cluster` - Group participants with shared discrete attribute values
- `cluster_numeric` - Minimize numeric attribute ranges within teams
- `different` - Ensure teams don't share specific attribute values
- `diversify` - Match team attribute distributions to overall population

### Data Format

**Participants DataFrame** requires:
- Unique identifier column (typically `id`)
- Attribute columns for constraints
- List columns should end with `_list` suffix and contain semicolon-separated values

**Constraints DataFrame** requires:
- `attribute` - Column name from participants data
- `type` - One of: cluster, cluster_numeric, different, diversify
- `weight` - Numeric priority weight for the constraint

### Streamlit UI Architecture

The UI (`team_assignment_ui.py`) provides:
- File upload for participants (CSV/JSON) and constraints (CSV/JSON)
- Interactive constraint editing
- Team generation with progress tracking
- Team evaluation and export functionality
- Session state management for multi-step workflow

### FastAPI REST API Architecture

The API (`team_formation/api/`) provides:
- **`main.py`** - FastAPI application with endpoints and SSE streaming
- **`models.py`** - Pydantic models for request/response validation
- **`callbacks.py`** - SSE solution callback for real-time progress updates
- POST `/assign_teams` endpoint with Server-Sent Events for progress streaming
- Async constraint solving with threading
- OpenAPI/Swagger documentation at `/docs`

### Vue.js Web Application Architecture

The project includes a modern Vue.js single-page application (`ui/`) that provides a rich interface for team formation.

**Tech Stack:**
- **Vue 3** with Composition API and `<script setup>` syntax
- **TypeScript** for type safety throughout the codebase
- **Vuetify 3** for Material Design UI components
- **Pinia** for reactive state management
- **Vite** for fast development and production builds
- **PapaParser** for client-side CSV parsing
- **Chart.js/vue-chartjs** for team visualizations
- **@microsoft/fetch-event-source** for SSE streaming

**Key Frontend Components (`ui/src/`):**
- `App.vue` - Main layout with app bar and three-section design
- `components/RosterSection.vue` - Participant upload and roster display
- `components/TeamSettings.vue` - Team size and solver configuration
- `components/ConstraintManager.vue` - Constraint definition table UI
- `components/TeamsSection.vue` - Run solver and display results
- `components/ProgressStream.vue` - Real-time solver progress display
- `components/TeamVisualization.vue` - Chart-based team analysis

**State Management (`ui/src/stores/teamFormation.ts`):**
- Centralized Pinia store managing participants, constraints, results
- Computed properties for validation and team grouping
- Preset system using localStorage for constraint configurations

**API Service Layer (`ui/src/services/api.ts`):**
- `assignTeams()` - POST to `/api/assign_teams` with SSE streaming
- Callbacks for progress, complete, and error events
- Request cancellation via AbortController
- Health check and API info endpoints

### Frontend-Backend Communication

The Vue.js frontend communicates with the FastAPI backend via Server-Sent Events (SSE) for real-time progress updates:

1. **Request Flow:**
   - Frontend collects participants (CSV upload) and constraints (UI form)
   - Pinia store validates configuration and builds request payload
   - API service POSTs to `/api/assign_teams` with JSON body

2. **SSE Streaming:**
   - Backend creates async event generator
   - Solver runs in thread pool (`asyncio.to_thread`) to avoid blocking
   - `SSESolutionCallback` pushes progress events to async queue
   - Events stream back: `progress` (intermediate solutions), `complete` (final result), `error`

3. **Event Handling:**
   - Frontend uses `@microsoft/fetch-event-source` library
   - Each `progress` event updates the UI progress display
   - `complete` event triggers results display and team visualization
   - Store updates trigger reactive UI changes

**API Endpoints Used:**
- `POST /api/assign_teams` - Main solver endpoint with SSE response
- `GET /health` - Health check
- `GET /api` - API information

### Desktop Application (Electron)

The project includes an Electron-based desktop application (`desktop/`) that bundles the FastAPI backend and Vue.js frontend into native installers for macOS, Windows, and Linux.

**Tech Stack:**
- **Electron** with TypeScript for the native shell
- **PyInstaller** to bundle the Python/FastAPI backend as a standalone executable
- **electron-builder** for packaging platform-specific installers

**Directory Structure:**
```
desktop/
  electron/               # TypeScript source (main.ts, preload.ts)
  dist-electron/          # Compiled Electron JavaScript
  resources/              # Icons and macOS entitlements
  python-dist/            # PyInstaller-bundled backend (generated)
  release/                # Final installers (generated)
  electron-builder.yml    # electron-builder configuration
  package.json            # npm dependencies and scripts
  tsconfig.json           # TypeScript compiler config
  team_formation_api.spec # PyInstaller spec file
```

**How It Works:**
1. Electron main process finds a free local port and spawns the PyInstaller-bundled backend
2. Backend serves the Vue.js frontend as static files and exposes the API
3. Electron loads `http://127.0.0.1:<port>` in a BrowserWindow
4. On quit, Electron sends SIGTERM to the backend for graceful shutdown

**Local Development:**
```bash
# Build the Vue.js frontend first
cd ui && npm ci && npm run build && cd ..

# Bundle the backend with PyInstaller
cd desktop && pip install pyinstaller && pyinstaller team_formation_api.spec --noconfirm && cd ..

# Run the Electron app in dev mode
cd desktop && npm ci && npm run dev
```

**Build Commands:**
```bash
cd desktop
npm run dist:mac     # Build macOS DMG (arm64)
npm run dist:win     # Build Windows NSIS installer (x64)
npm run dist:linux   # Build Linux AppImage (x64)
npm run dist         # Build all platforms
```

**Build Artifacts:**
- macOS: `Team Formation-<version>-arm64.dmg`
- Windows: `Team Formation Setup <version>.exe`
- Linux: `team-formation-<version>.AppImage`

#### CI/CD and GitHub Releases

Desktop builds are automated via GitHub Actions (`.github/workflows/desktop-build.yml`):

**Triggers:**
- Pushing a git tag matching `v*` (e.g., `git tag v2.0.1 && git push --tags`)
- Manual trigger via `workflow_dispatch` in the GitHub Actions UI

**Build Pipeline:**
1. Three parallel jobs build for macOS (arm64), Windows (x64), and Linux (x64)
2. Each job: installs Python + Node.js, builds the Vue.js frontend, bundles the backend with PyInstaller, runs a smoke test against `/health`, then packages with electron-builder
3. Platform installers are uploaded as workflow artifacts
4. A release job creates a **published GitHub Release** with all installers attached

**Downloading Desktop Builds:**
- Users download installers from the repository's [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github) page
- Releases are automatically published when triggered by a version tag
- Built binaries are **not** checked into the repository — they are built in CI and attached to releases as downloadable assets

**Code Signing:**
- macOS and Windows code signing is configured in `electron-builder.yml` but currently commented out, pending certificate setup in GitHub Actions secrets

### Docker Deployment Architecture

The application uses a multi-stage Docker build for production deployment:

**Build Process (`Dockerfile`):**
1. **Stage 1 (frontend-builder):** Node 20 Alpine builds Vue.js app
2. **Stage 2:** Python 3.11 slim with FastAPI and built frontend

**Production Mode:**
- Single container serves both API (`/api/*`) and frontend (`/*`)
- FastAPI mounts Vue.js `dist/` as static files
- Catch-all route serves `index.html` for client-side routing
- Environment variables: `PRODUCTION=true`, `LOG_LEVEL`, `CORS_ORIGINS`

**Development Mode:**
- Frontend: `cd ui && npm run dev` (Vite dev server on port 3000)
- Backend: `team-formation-api` (FastAPI on port 8000)
- CORS configured to allow localhost cross-origin requests

**Cloud Deployment:**
- Ready for GCP Cloud Run, AWS ECS, Azure Container Apps
- Health check endpoint at `/health`
- Non-root user for security

### Testing Structure

Tests are organized by functionality:
- `test_small.py` - Basic functionality tests
- `test_diversify.py` - Diversification constraint tests
- `test_num_cluster.py` - Numeric clustering tests
- `test_working_time.py` - Time-based constraint tests
- `test_api.py` - FastAPI endpoint tests with async/httpx
- Large test datasets in `tests/data/`

## Important Implementation Details

### Constraint Solver Integration
- Uses Google OR-Tools CP-SAT solver with custom solution callbacks
- Supports both optimal and time-bounded solving
- Threading used for non-blocking UI solver execution

### Multi-valued Attributes
- Attributes ending in `_list` are automatically parsed as semicolon-separated lists
- Cluster constraints work with multi-valued participant attributes
- Working time constraints support multiple acceptable time ranges

### Package Structure
- Built using hatchling (not setuptools)
- Console script entry points:
  - `team-formation = "team_formation.__main__:main"` (Streamlit UI)
  - `team-formation-api = "team_formation.api.main:run"` (FastAPI server)
- Version managed in `pyproject.toml`