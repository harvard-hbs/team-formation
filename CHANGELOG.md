# Change Log

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
  

