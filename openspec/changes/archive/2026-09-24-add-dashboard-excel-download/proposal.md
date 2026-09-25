# Proposal

## Why

HBS Online Program Services currently takes the team-formation roster export and
reshapes it by hand -- renaming columns and deriving a team label -- before it can
be uploaded into the Learner Dashboard. That manual step is repeated for every
cohort and is an easy place to introduce transcription errors. The tool already
holds every value the Dashboard needs; it should emit the upload file directly.

## What Changes

- Add a "Dashboard Download" button to the roster toolbar in the Vue.js UI,
  alongside the existing Export CSV and Export JSON buttons. It renders only once
  team assignments exist, because the export derives a team label from
  `team_number`.
- Pressing the button produces an `.xlsx` workbook containing only the seven
  Dashboard columns, in the order given below, with headers renamed from the
  roster's source columns:

  | Source column | Output column |
  | --- | --- |
  | `first_name` | `First Name` |
  | `last_name` | `Last Name` |
  | `email_id` | `Business Email Address` |
  | `hbx_id` | `HBS Online ID` |
  | `wave_code` | `Bodhi Wave Code` |
  | `profile_image_url` | `Profile Photo URL` |
  | `team_number` | `Team Name` |

- Transform `team_number` (0-indexed, assigned by the solver) into the string
  `Team <team_number + 1>`, so team 0 exports as `Team 1`.
- Validate before generating: if any required source column is missing from the
  roster, show an error naming the missing columns and produce no file.
- Generate the workbook client-side, so the same code path serves the browser
  and the Electron desktop app with no API or PyInstaller bundle change.

No existing behavior changes. The current CSV and JSON exports are untouched.

## Capabilities

### New Capabilities

- `dashboard-roster-export`: Exporting an assigned roster as an HBS Online
  Learner Dashboard upload file -- required-column validation, column selection
  and renaming, the team label transform, and the `.xlsx` download itself.

### Modified Capabilities

None. This change adds a capability without altering requirements of any
existing one.

## Impact

- **Frontend (`ui/`)**: new export service module; new button and handler in
  `ui/src/components/RosterTable.vue`; new dependency `exceljs` in
  `ui/package.json`.
- **Desktop app (`desktop/`)**: no code change. The Electron shell loads the
  same built frontend, so the button ships with it once `ui/dist` is rebuilt.
  Only the download-to-disk behavior in the packaged app needs verification.
- **Backend (`team_formation/`)**: none. No new endpoint and no new Python
  dependency, so `desktop/team_formation_api.spec` and the bundle size are
  unaffected.
- **Documentation**: the enhancement section in `desktop/README.md` is replaced
  by a pointer once this ships; user-facing notes belong in `ui/README.md`.
