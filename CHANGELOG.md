# Change Log

## [2.0.1] - 2026-02-20

### Fixed

- Fix API test paths to use `/api/assign_teams` endpoint
- Remove retired macOS Intel (macos-13) CI build target

### Security

- Update axios to ≥1.13.5 (DoS via `__proto__` key)
- Update electron to ≥35.7.5 (ASAR integrity bypass)
- Update electron-builder to ≥26.8.1 (tar path traversal vulnerabilities)
- Pin starlette ≥0.49.1 (O(n²) DoS and multipart DoS)
- Pin urllib3 ≥2.6.3 (decompression bomb and redirect vulnerabilities)
- Pin protobuf ≥6.33.5 (JSON recursion depth bypass)
- Pin cryptography ≥46.0.5 (subgroup attack on SECT curves)
- Update ortools to ≥9.15

## [2.0.0] - 2026-02-20

### Added

- **Electron desktop application** for standalone distribution without Docker or Python
  - PyInstaller-bundled FastAPI backend with Google OR-Tools
  - Electron shell with automatic backend lifecycle management (spawn, health check, shutdown)
  - Platform installers: macOS DMG, Windows NSIS installer, Linux AppImage
- **GitHub Actions CI pipeline** for cross-platform desktop builds
  - Matrix builds for macOS (ARM), Windows (x64), and Linux (x64)
  - Automated smoke testing of bundled backend in CI
  - Draft GitHub Releases with installer artifacts on version tags

### Modified

- FastAPI server now reads `PORT` from environment variable (defaults to 8000)
- CORS configuration supports `CORS_ORIGINS=*` for desktop app's `file://` origin
- Server detects PyInstaller bundle mode for correct uvicorn startup
- Frontend API URL can be injected via `window.__API_BASE_URL__` for Electron

## [1.6.1] - 2026-01-07

- Small code fix

## [1.6.0] - 2025-11-13

### Added

- **FastAPI REST API endpoint** with Server-Sent Events (SSE) for real-time progress streaming
  - POST `/assign_teams` endpoint for team formation via HTTP API
  - Real-time progress updates during constraint solving
  - Comprehensive request validation with Pydantic models
  - New console script: `team-formation-api` to run the API server
  - Full test coverage with 12 API tests
  - API documentation and examples in `team_formation/api/README.md`

### Dependencies

- Added `fastapi>=0.104.0` for REST API functionality
- Added `uvicorn[standard]>=0.24.0` for ASGI server
- Added `sse-starlette>=1.6.5` for Server-Sent Events support
- Added `pytest-asyncio` and `httpx` for async API testing (dev dependencies)

## [1.5.7] - 2025-11-09

### Modified

- Upgraded and tested with Google-OR Tools 9.14

## [1.5.6] - 2025-10-28

### Added

- Constraint validation for required columns and attributes present in roster

## [1.5.5] - 2025-09-29

### Modified

- Fixed bug with width in evaluation printout.
- Verified that editing constraint weight values works via logging.

### Added

- Documentation on deploying and developing using uv.
- Added another API use case in README.md

## [1.5.4] - 2025-09-29

### Added

- Added display of means of evaluation statistics.

## [1.5.2] - 2025-09-26

### Modified

- Modified UI to provide a wide layout and column-based formatting of
  settings and upload area.

### Added

- About box with version 
- Page title

## [1.5.1] - 2025-09-26

### Modified

- Modified UI to use the new `max_time_in_seconds` parameter for
  stopping the solver more promptly.

### Added

- Added a `max_time_in_seconds` parameter to `solve` method.

## [1.5.0] - 2025-09-26

### Modified

- Breaking change to pass column names to
  `team_assignment.working_time.working_times_hours`.

### Added

- Streamlit UI additions
  - Allow setting of working time column names.
  - UI updates during constraint solving.

## [1.5.0] - 2025-09-26

### Modified

- Breaking change to pass column names to
  `team_assignment.working_time.working_times_hours`.

### Added

- Streamlit UI additions
  - Allow setting of working time column names.
  - UI updates during constraint solving.

## [1.4.0] - 2025-04-27

### Modified

- Breaking change to format of `TeamAssignment.evaluate_teams().

### Added

- Streamlit UI additions
  - Make constraints editable in UI
  - Add team evaluations to UI

- Added evaluation for new constraint types

## [1.3.0] - 2025-04-12

### Modified

- Changed use of `add_abs_equality(target, expr)` constraints to
  `add_max_equality(target, [expr, -expr])` to get work around bug.

### Added
	
- Added new `different` constraint type.
- Added [`tests/test_abs_eq_bug.py`](tests/test_abs_eq_bug.py) to exhibit or-tools
  9.12.4544 bug with `add_abs_equality` constraint.
- Added a new version of numeric clustering based on min/max range.
	
## [1.2.0] - 2024-12-19

- Added new `cluster_numeric` constraint type.

## [1.1.0] - 2024-11-19

### Added

- Ability to convert working time and time zone into a set of hours from the Streamlit UI.
- Expose the Streamlit UI to be called as the main function.

## [1.0.3] - 2024-11-18

### Modified

- Reworked packaging, build, and upload to use
  [hatchling](https://pypi.org/project/hatchling/) rather than
  setuptools.

### Added

- Added [`CHANGELOG.md`](CHANGELOG.md)

## [1.0.2] - 2024-09-16

### Fixed

- Fixed `less_than_target=True` initialization parameter. The
  parameter could be passed to the initializer, but it was overridden
  by a line setting `less_than_target` to `False` in the
  initialization code. This was a vestige of a modification made
  during testing.
  

