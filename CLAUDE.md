# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package for constraint-based team formation that uses Google OR-Tools CP-SAT solver to optimally assign participants to teams based on weighted constraints. The tool provides both a programmatic API and a Streamlit web interface.

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

### Testing Structure

Tests are organized by functionality:
- `test_small.py` - Basic functionality tests
- `test_diversify.py` - Diversification constraint tests
- `test_num_cluster.py` - Numeric clustering tests
- `test_working_time.py` - Time-based constraint tests
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
- Console script entry point: `team-formation = "team_formation.__main__:main"`
- Version managed in `_version.txt`