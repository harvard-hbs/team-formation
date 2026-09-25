# Tasks

## 1. Dependency setup

- [x] 1.1 Check the current `exceljs` version and open advisories before adding it; if it is unmaintained or carries an unfixed advisory, stop and raise the backend-endpoint alternative from design.md rather than proceeding
- [x] 1.2 Add `exceljs` to `dependencies` in `ui/package.json` and verify `cd ui && npm install` completes and `npm audit` reports no new high or critical findings
- [x] 1.3 Record the production bundle size from `cd ui && npm run build` before and after the dependency is imported, and verify the increase is acceptable to the reviewer

## 2. Export service

- [x] 2.1 Create `ui/src/services/dashboardExport.ts` with the column mapping as a single exported constant listing the seven source columns, their Dashboard headers, and their order; verify the constant matches the table in `specs/dashboard-roster-export/spec.md` exactly
- [x] 2.2 Implement a pure `findMissingColumns(participants)` returning the names of required source columns absent from the results; verify by hand against three fixtures - all columns present, `hbx_id` missing, and both `wave_code` and `profile_image_url` missing - that it returns `[]`, `["hbx_id"]`, and both names respectively
- [x] 2.3 Implement a pure `buildDashboardRows(participants)` that selects and renames the seven columns, writes `Team Name` as `Team <team_number + 1>`, passes all other values through unchanged, emits an empty value for a blank or absent cell, and sorts by `team_number` ascending preserving input order within a team; verify a fixture with teams 0, 1, 11 in mixed order produces rows labelled `Team 1`, `Team 2`, `Team 12` in that group order
- [x] 2.4 Implement `exportToDashboardXlsx(participants, filename)` building a single-sheet workbook from those rows with the header row first, then downloading it with the `Blob` plus hidden-anchor pattern already used by `exportToCSV` in `ui/src/services/csvParser.ts`; verify the downloaded file opens in Microsoft Excel with no repair prompt
- [x] 2.5 Add a short JSDoc block to each exported function stating the Dashboard contract it implements, matching the comment density of `csvParser.ts`; verify `cd ui && npm run build` still type-checks

## 3. Roster toolbar button

- [x] 3.1 Add a "Dashboard Download" button to the card title of `ui/src/components/RosterTable.vue`, beside Export CSV and Export JSON, rendered only when `store.results` is set; verify the button is absent with no roster loaded, absent with a roster loaded but unsolved, and present after a solve completes
- [x] 3.2 Implement its handler to call `findMissingColumns` against `store.results` first, and on any missing column call `store.setError` with a message naming every missing column and return without producing a file; verify with a roster lacking `hbx_id` that the message names it and no download starts
- [x] 3.3 On success, call `exportToDashboardXlsx` with a file name identifying it as a dashboard roster and carrying a timestamp, following the `team-assignments-${Date.now()}` convention in the same component; verify two consecutive downloads produce differently named files
- [x] 3.4 Confirm the missing-column error is actually visible to a user standing at the roster toolbar; `store.errorMessage` renders in `TeamSettings.vue`, a different card, so if it is easy to miss, replace it with a local `v-alert` or snackbar in `RosterTable.vue` as design.md anticipates

## 4. End-to-end verification

- [x] 4.1 Run the full flow in the browser against a fixture roster carrying all seven columns plus extra constraint columns such as a `_list` column, and verify the downloaded workbook has exactly the seven Dashboard headers in order, one row per participant, and no extra columns
- [x] 4.2 Build the desktop app per `desktop/README.md` (frontend build, `./scripts/build-python.sh`, then `npm run dist:mac` or the local platform target) and verify the Dashboard Download in the packaged app produces an equivalent file and lets the user choose where it is saved; if the download silently fails or saves without prompting, add a `will-download` handler in `desktop/electron/main.ts`
- [x] 4.3 Replace the Enhancements section in `desktop/README.md` with a pointer to the shipped feature, and document the button and its required columns in `ui/README.md`; verify the required-column list in the docs matches the constant from task 2.1
- [x] 4.4 Add a CHANGELOG.md entry under a new Unreleased Added heading describing the Dashboard Download; verify it names the output format and the required columns

## 5. Case-insensitive source columns

- [x] 5.1 Match contract source columns without regard to header case in `findMissingColumns` and `buildDashboardRows`, preferring an exact match when a roster carries two casings of the same column; verify fixtures in all-caps, mixed case, and lower case all validate clean and export identically
- [x] 5.2 Report missing columns under their canonical lower-case contract names regardless of roster casing; verify an upper-case roster with no `HBX_ID` reports `hbx_id`
- [x] 5.3 Keep the exported header names fixed regardless of roster casing; verify a `FIRST_NAME` roster still exports the header `First Name`
- [x] 5.4 Run the browser flow with an all-caps roster and verify the downloaded workbook matches the lower-case roster's output
- [x] 5.5 Note the case-insensitive matching in the Dashboard Download section of `ui/README.md`; verify the wording matches the implemented rule
