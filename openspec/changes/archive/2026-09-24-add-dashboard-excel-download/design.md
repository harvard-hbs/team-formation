# Design

## Context

See proposal.md - Why. The relevant existing state:

- `ui/src/services/csvParser.ts` already holds both roster exports. `exportToCSV`
  and `exportToJSON` build a `Blob`, create an object URL, click a hidden anchor,
  and revoke the URL. This change follows that pattern rather than inventing a
  second download mechanism.
- `ui/src/components/RosterTable.vue` renders the export buttons in its card
  title and calls those helpers from `handleExportCSV` / `handleExportJSON`,
  choosing `store.results || store.participants` as the data source.
- Assignment results live in `store.results` as `Participant[]`. The solver's
  `team_num` is renamed to `team_number` by the API before it reaches the client
  (`team_formation/api/main.py:124`), and it is zero-indexed
  (`team_formation/api/models.py:95`).
- `Participant` is `{ [key: string]: any }`, so required columns cannot be
  enforced by the type system and must be checked at runtime.
- The desktop app loads the built frontend over HTTP from the bundled backend
  (`desktop/electron/main.ts:167`), so frontend-only work reaches it through
  `ui/dist` with no Electron change.
- `ui/` has no test runner. `package.json` defines only `dev`, `build`, and
  `preview`, and there are no test files anywhere under `ui/`.

## Goals / Non-Goals

**Goals:**

- Keep column mapping, validation, and the team label transform in pure
  functions that do not touch the DOM, so they can be unit tested when a runner
  exists and reviewed easily now.
- One code path for browser and desktop.
- Make the required-column contract a single declared constant, so a future
  Dashboard schema change is a one-line edit.

**Non-Goals:**

- Generalizing this into a user-configurable column mapper. The mapping is
  fixed by the Learner Dashboard.
- Introducing a frontend test runner. Worth doing, but it is its own change.
- Styling or formatting inside the workbook (column widths, freeze panes, cell
  types). The Dashboard consumes values, not presentation.

## Decisions

### Generate the workbook in the browser, not the backend

Chosen: build the `.xlsx` client-side and download it via `Blob`.

The data is already in the store, so a server round trip would only re-send it.
More importantly, the desktop build bundles the backend with PyInstaller; a
Python Excel writer means a new dependency plus new `hiddenimports` in
`desktop/team_formation_api.spec` and a larger installer, for a transformation
that is a rename and a string concatenation.

Alternative considered: `POST /api/export/dashboard` returning an xlsx stream.
It would put the logic in Python next to the solver and make it testable with
the existing pytest suite -- a genuine advantage given `ui/` has no test runner.
Rejected on bundle cost and because it adds an API surface for a pure
client-side reshape. If the mapping ever needs to consult server-side data, this
is the decision to revisit.

### Use `exceljs`, not `xlsx` (SheetJS)

Chosen: `exceljs` (4.4.0 on npm at the time of writing).

The `xlsx` package on npm is frozen at 0.18.5; SheetJS moved distribution to
their own CDN, so the npm artifact no longer receives fixes. This repository
actively pins dependencies for advisories -- see the security entries in
`CHANGELOG.md` -- and depending on an unmaintained npm artifact works against
that. `exceljs` is published and maintained on npm, so Dependabot and `npm
audit` behave normally.

Alternatives considered: `xlsx` from the vendor CDN (breaks `npm ci`
reproducibility in CI and the desktop build); writing the OOXML zip by hand
(no dependency, but far too much surface for one export).

Confirm the current `exceljs` version and advisory status at implementation
time rather than trusting this note.

### Put the logic in a new service module, not in the component

Chosen: a new `ui/src/services/dashboardExport.ts` exporting three things -- the
column mapping constant, a pure validation function returning the missing
column names, and a pure row-building function -- plus the thin download
wrapper.

`csvParser.ts` is already a grab bag of parsing, exporting, and validation;
adding a third export format to it makes it worse. A separate module also keeps
the pure parts importable by a future test without pulling in Papa Parse.

### Surface the error through the existing store error channel

Chosen: on missing columns, call `store.setError(...)` with a message naming
them.

`store.errorMessage` already exists and is rendered by `TeamSettings.vue:105`.
A local snackbar in `RosterTable.vue` (the pattern `PresetManager.vue` uses)
would be more visually local to the button.

This is the weakest of the four decisions: the store error renders in a
different card from the button that triggered it, which is easy to miss. Flagged
for review at implementation -- if the error is not obviously visible next to
the roster toolbar, switch to a local `v-alert` or snackbar in `RosterTable.vue`.

## Risks / Trade-offs

- **`exceljs` pulls a nontrivial dependency tree into the bundle** -> Import only
  the browser build and check the production bundle size before and after; if
  the increase is unacceptable, revisit the backend-endpoint alternative rather
  than hand-rolling OOXML.
- **No frontend test runner, so the transform is verified by hand** -> Keep the
  validation and row-building functions pure and side-effect free so they are
  trivially testable the moment a runner lands; verify this change manually
  against a fixture roster with a known team count.
- **Electron's save behavior is assumed, not verified** -> The existing CSV and
  JSON exports use the same anchor-click mechanism, so the behavior should
  already be whatever the packaged app does today. Verify in a packaged build,
  not just `npm run dev`, and add an explicit `will-download` handler in
  `desktop/electron/main.ts` only if the download silently fails or saves
  without prompting.
- **Blank required values export as empty cells** -> Deliberate, per the spec:
  the tool cannot invent a missing `hbx_id`, and a hard failure would block an
  otherwise usable roster. Program Services sees the gap in the file.
- **Dashboard schema drift** -> The mapping is one constant; a column rename is
  a one-line change. It is not detectable from this side, so a bad upload is the
  first signal.

## Migration Plan

Additive and frontend-only. No data migration, no API version change. Rollback
is reverting the commit and rebuilding `ui/dist`; the desktop app needs a new
build to pick the feature up or drop it, since the frontend is baked into the
installer.

## Open Questions

- Should the exported file name include the cohort identifier rather than a
  timestamp? `store.cohortInfo` carries a `cohort_id`, which would be more
  useful to Program Services than epoch milliseconds, but it is optional and may
  be absent. Deferrable: the spec requires only that the name identify the file
  as a dashboard roster and not collide.
