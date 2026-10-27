# Tasks

## 1. Core validation (Python)

- [x] 1.1 Add `ID_COLUMN_CANDIDATES`, an `AttributeIssue` record, and `ParticipantDataError(ValueError)` (with `.issues` and a formatted `__str__` per design.md "Message format") to `team_formation/team_assignment.py`; verify with a unit test that `str(err)` lists one line per attribute and truncates after 10 rows with "and N more"
- [x] 1.2 Implement `validate_participants(participants, constraints)` covering missing values (None, NaN, absent key, blank/whitespace string, empty list) and invalid `cluster_numeric` values; verify with new `tests/test_validation.py` cases for each missing-value kind, `0`/`False` not missing, `"unknown"` invalid, `"42"` valid, unconstrained blank columns ignored
- [x] 1.3 Verify row numbering and identifiers in `tests/test_validation.py`: positional row + 2 with a non-default DataFrame index, identifier taken from the first matching candidate column, row-only output when no identifier column exists or the identifier is blank
- [x] 1.4 Call `validate_participants` in `TeamAssignment.__init__` after the duplicate-constraint check, raise `ParticipantDataError` on issues, then coerce `cluster_numeric` columns with `pd.to_numeric`; remove the old `isnull` check in `categories_to_bool_vars`; verify a test that previously produced "cannot convert float NaN to integer" now raises `ParticipantDataError` naming the column and row, and that `"42"`-string numeric data solves
- [x] 1.5 Run `uv run pytest --ignore=tests/test_big.py` and verify the existing tests still pass (no previously valid fixture contains blanks in constrained columns)

## 2. REST API error reporting

- [x] 2.1 Add optional `details: list[dict] | None` to `ProgressEvent` in `team_formation/api/models.py`, and in `event_generator` populate it from `ParticipantDataError.issues`; verify with a `tests/test_api.py` test that a request with a null `cluster_numeric` value yields an `error` event whose message names the column and row, whose `details` has one entry per problem attribute, and that no `complete` event is sent
- [x] 2.2 Add an API test that a blank string in a `diversify` column (from a CSV-style payload) produces a validation `error` event; verify it passes

## 3. Vue.js / desktop UI

- [x] 3.1 Add optional `details` to `ErrorEvent` in `ui/src/types` and apply `white-space: pre-line` to the error `v-alert` in `ui/src/components/TeamSettings.vue`; verify `npm run build` succeeds in `ui/`
- [x] 3.2 Manually verify in the dev app (`team-formation-api` plus `cd ui && npm run dev`): upload a CSV with a blank cell in a constrained column and a non-numeric value in a `cluster_numeric` column, click create teams, and confirm the alert shows each column on its own line with row numbers and ids

## 4. Streamlit UI

- [x] 4.1 In `generate_teams_callback` (`team_formation/team_assignment_ui.py`), catch `ParticipantDataError` around `TeamAssignment(...)` and show it with `st.error` instead of raising; verify manually with `python -m team_formation` using the same bad CSV that the error is displayed and no traceback appears

## 5. Documentation and release notes

- [x] 5.1 Document the missing-value rules and error format in `README.md` (data format section) and add a `CHANGELOG.md` entry noting the behavioral change for blank strings and empty `_list` values; verify the entries are present and accurate against the spec
- [x] 5.2 Bump the version to 2.2.0 in `pyproject.toml` and `desktop/package.json`; verify `uv build` succeeds

## 6. Integration check

- [x] 6.1 Build the desktop app locally (frontend build, PyInstaller bundle, `npm run dev` in `desktop/`) and verify the missing-data error from task 3.2 appears identically in the Electron window
- [x] 6.2 Run `openspec validate validate-constraint-data --strict` and verify it passes

## Workflow follow-up

- Archive the change with `/opsx:archive` after review and merge.
- Tag and release the desktop app (`v2.2.0`) once merged.
