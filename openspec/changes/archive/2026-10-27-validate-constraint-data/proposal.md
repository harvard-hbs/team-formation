# Proposal

## Why

When a participant is missing a value for an attribute used by a constraint, the solver fails with a low-level message, or it does not fail at all. A blank `cluster_numeric` value produces `cannot convert float NaN to integer`. A blank categorical value produces `('Missing values for attribute', 'gender')`, which does not say which rows are affected. Empty strings and empty `_list` values pass without any error and are treated as real values. Users of the desktop app cannot work out from these messages what to fix in their roster, so we want this fixed before the next tagged desktop release.

## What Changes

- Add a validation step that runs before the solver model is built. It checks every participant column referenced by a constraint for missing values.
- These values count as missing: `null`/`None`, `NaN`, an absent key, an empty or whitespace-only string, and, for `_list` columns, an empty list. For `cluster_numeric` constraints, a value that cannot be read as a number is reported as invalid.
- When problems are found, raise one error that lists every column with missing or invalid values. Each column shows a count of affected rows and identifies them by file row number and, when the data has an identifier column, by identifier value. Long lists are truncated with an "and N more" suffix.
- The FastAPI `/api/assign_teams` endpoint reports this validation failure through the existing SSE `error` event, using the readable message plus a structured `details` payload. The current uncaught `NaN` exceptions no longer reach the user.
- The Vue.js UI (and therefore the desktop app) shows the multi-line validation message readably in the existing error alert.
- The Streamlit UI shows the same message, since it calls the same `TeamAssignment` constructor.
- **BREAKING (behavioral)**: rosters with empty strings or empty `_list` values in constrained columns are now rejected. They currently solve silently, treating "blank" as its own category.

## Capabilities

### New Capabilities
- `participant-data-validation`: Pre-solve validation of participant data against the configured constraints, and how validation failures are reported to callers (Python API, REST API, and UIs).

### Modified Capabilities
<!-- None: no existing spec covers solver input validation. -->

## Impact

- `team_formation/team_assignment.py`: new validation function and exception type, called at the start of `TeamAssignment.__init__`. The ad hoc check in `categories_to_bool_vars` is superseded.
- `team_formation/api/main.py`, `team_formation/api/models.py`: map the validation exception to a structured SSE `error` event (optional `details` field on `ProgressEvent`).
- `ui/src/components/TeamSettings.vue` (error alert rendering), `ui/src/services/api.ts` and `ui/src/types` (optional `details` on the error event).
- `team_formation/team_assignment_ui.py`: display the validation message.
- Tests: new unit tests for validation, plus API tests for the error event.
- No new dependencies.
