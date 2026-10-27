# Design

## Context

There are three entry points to the solver, and all of them build a `TeamAssignment` (in `team_formation/team_assignment.py`):

- the FastAPI `/api/assign_teams` endpoint, used by the Vue.js UI and the Electron desktop app, which turns the JSON request into DataFrames in `convert_request_to_dataframes`
- the Streamlit UI (`generate_teams_callback`)
- direct Python use

The constructor itself does no data validation. What happens today with missing values (reproduced against the current code):

| Input | Current behavior |
|---|---|
| `null` in a `cluster_numeric` column | `ValueError: cannot convert float NaN to integer` (raised from `int(...)` in `create_numeric_clustering_costs_*`) |
| `null` or absent key in a categorical column | `ValueError: ('Missing values for attribute', 'gender')` from `categories_to_bool_vars`, with no row information |
| `""` in a categorical column | Solves silently, with `""` treated as its own category |
| `[]` in a `_list` column | Solves silently, so the participant matches no cluster value |

The Vue CSV parser (`ui/src/services/csvParser.ts`) uses Papa Parse with `dynamicTyping`, so empty cells reach the API as `null`, and empty `_list` cells become `[]`. The API request validator already rejects a constraint attribute that no participant has at all, so that case stays as it is.

## Goals / Non-Goals

**Goals:**
- One validation implementation in the Python core, so every entry point gets the same behavior and wording.
- Errors that can be read in a single alert, plus structured details for programmatic callers.

**Non-Goals:**
- Client-side (TypeScript) duplication of the check. The desktop app always runs the bundled backend, so a second implementation would only drift.
- Validating unconstrained columns, checking for duplicate identifiers, or flagging categories that are too rare to diversify.
- Imputing or dropping rows automatically.

## Decisions

### Validate in `TeamAssignment.__init__` via a standalone function

Add a module-level `validate_participants(participants, constraints) -> list[AttributeIssue]` and an exception `ParticipantDataError(ValueError)` that carries `.issues` and formats the readable message in `__str__`. `TeamAssignment.__init__` calls the function right after its existing duplicate-constraint check and raises when issues come back.

- *Why the constructor:* it is the one choke point shared by all three entry points, and it runs before any CP-SAT variables are built.
- *Why a standalone function too:* callers such as a future "check data" button or tests can validate without constructing a model.
- *Why subclass `ValueError`:* existing `except ValueError` handlers and tests keep working.
- *Alternative considered:* validating only in the API layer. Rejected because Streamlit and Python callers would keep the `NaN` errors.

The now-redundant `isnull` check in `categories_to_bool_vars` is removed.

### Missing-value and numeric rules

Values are evaluated per cell, so list-valued cells work:

- Missing: `None`; float `NaN`/`pd.NA` (via `pd.isna` on scalars only); `str` that is empty after `.strip()`; and for `_list` columns (or any cell that is a `list`), `len == 0`.
- Numeric (only `cluster_numeric`): a non-missing value is valid if `pd.to_numeric(value)` succeeds and the result is finite. Booleans are not counted as numbers.
- Numeric strings are accepted by validation, and the solver uses `int(...)` on them. To guarantee the solver can consume whatever validation accepts, `__init__` converts validated `cluster_numeric` columns with `pd.to_numeric` before building the model. Otherwise `"42.5"` would pass validation and then fail at `int("42.5")`.

### Row identification

- The row number is the positional index plus 2 (header = row 1), independent of the DataFrame's index labels, which callers may have reset or filtered.
- The identifier column is the first of `id`, `ID`, `participant_id`, `student_id`, `email` that exists. This matches the list in `validateParticipantData` in `csvParser.ts`, minus ordering differences, and is defined once as a module constant. When the identifier value itself is missing, only the row number is shown.

### Message format

The message has one line per attribute, grouped by problem kind, for example:

```
Participant data is missing values required by the constraints:
- gender (diversify): 3 rows missing a value: row 4 (id 1047), row 9 (id 1052), row 30 (id 1073)
- age (cluster_numeric): 1 row with a non-numeric value: row 12 (id 1055) "unknown"
```

Each line lists up to 10 rows, then "and N more". Invalid numeric entries include the offending value (quoted and truncated to 30 characters) so the user can find it.

### API transport

- Add an optional `details: list[dict] | None = None` to the `ProgressEvent` model. In `event_generator`, when the exception is a `ParticipantDataError`, populate `details` from `.issues` (attribute, constraint_type, problem, count, rows[{row, id}]).
- The error stays on the existing SSE `error` event rather than becoming an HTTP 4xx, because the frontend already handles that path and validation runs inside the solver task. Other errors are unchanged.
- *Alternative considered:* run validation in the request handler and return HTTP 422 before opening the stream. That would be cleaner REST, but it adds a second error-delivery path the UI would have to handle, and the request handler would have to build the DataFrames twice.

### UI rendering

- `TeamSettings.vue`: give the error `v-alert` text `white-space: pre-line` so the newline-separated message renders one attribute per line.
- `ui/src/types`: add optional `details` to `ErrorEvent`. No UI behavior depends on it yet; it is typed for future use.
- Streamlit: wrap the `TeamAssignment(...)` construction in `generate_teams_callback` so a `ParticipantDataError` is shown with `st.error` (markdown list) instead of a traceback.

## Risks / Trade-offs

- [Rosters that solve today with blanks or empty `_list` cells will now be rejected] → This is intended; the proposal marks it as a behavioral breaking change. The message tells the user exactly which cells to fill. Note it in `CHANGELOG.md`.
- [Per-cell Python iteration over constrained columns is slower than vectorized checks] → Rosters are hundreds to low thousands of rows and a handful of constraints, which is negligible next to model construction. `test_big.py` covers the large case.
- [Converting `cluster_numeric` columns changes their dtype in the returned participants] → Only numeric-looking strings change, to numbers. JSON and CSV output stay equivalent.
- [The identifier column heuristic may pick the wrong column] → The row number is always present and is the primary locator. The identifier is supplementary.

## Migration Plan

No data migration is needed. Ship it in the next minor version (2.2.0) ahead of the desktop tag. To roll back, revert the commit; there are no persisted state changes.
