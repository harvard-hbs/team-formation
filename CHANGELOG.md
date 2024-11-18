# Change Log


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
  
