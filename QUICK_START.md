# FastAPI Quick Start Guide

## Installation

Install the package with the new FastAPI dependencies:

```bash
uv pip install -e .
```

Or for development:

```bash
uv pip install -e ".[dev]"
```

## Start the API Server

```bash
team-formation-api
```

The server will start on `http://localhost:8000`

## Test the API

### 1. View Interactive Documentation

Open your browser to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Run the Example Script

In a new terminal:
```bash
uv run python examples/api_example.py
```

You should see real-time progress updates followed by team assignments.

### 3. Run the Tests

```bash
uv run pytest tests/test_api.py -v
```

All 12 tests should pass.

## Simple cURL Example

```bash
curl -N -X POST http://localhost:8000/assign_teams \
  -H "Content-Type: application/json" \
  -d '{
    "participants": [
      {"id": 1, "name": "Alice", "gender": "Female", "role": "Engineer"},
      {"id": 2, "name": "Bob", "gender": "Male", "role": "Designer"},
      {"id": 3, "name": "Charlie", "gender": "Male", "role": "Engineer"},
      {"id": 4, "name": "Diana", "gender": "Female", "role": "Designer"},
      {"id": 5, "name": "Eve", "gender": "Female", "role": "Manager"},
      {"id": 6, "name": "Frank", "gender": "Male", "role": "Manager"}
    ],
    "constraints": [
      {"attribute": "gender", "type": "diversify", "weight": 1},
      {"attribute": "role", "type": "cluster", "weight": 1}
    ],
    "target_team_size": 3,
    "less_than_target": false,
    "max_time": 10
  }'
```

## What to Expect

1. **Progress Events**: Real-time updates as the solver finds better solutions
   ```
   event: progress
   data: {"solution_count": 1, "objective_value": 42.0, ...}
   ```

2. **Complete Event**: Final team assignments
   ```
   event: complete
   data: {"participants": [...], "stats": {...}}
   ```

Each participant will have a `team_number` field (0-indexed).

## Key Features

✅ **Real-time progress** via Server-Sent Events (SSE)
✅ **Full validation** of constraints and participants
✅ **Flexible attributes** - participants can have any attributes
✅ **Four constraint types**: diversify, cluster, cluster_numeric, different
✅ **Time limits** - control optimization duration with `max_time`
✅ **Interactive docs** - automatic API documentation at `/docs`

## API Endpoint

**POST** `/assign_teams`

**Request Body:**
```typescript
{
  participants: Array<{[key: string]: any}>,  // List with arbitrary attributes
  constraints: Array<{
    attribute: string,    // Attribute name from participants
    type: string,        // diversify | cluster | cluster_numeric | different
    weight: number       // Priority weight (> 0)
  }>,
  target_team_size: number,     // Must be > 2
  less_than_target?: boolean,   // Default: false
  max_time?: number             // Seconds, default: 60
}
```

**Response:** Server-Sent Events stream

## More Information

- Full API documentation: `team_formation/api/README.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- API specification: `team-formation/API.md`

## Troubleshooting

**Server won't start?**
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Use a different port
uvicorn team_formation.api.main:app --port 8001
```

**Tests failing?**
```bash
# Reinstall dependencies
uv pip install -e ".[dev]"

# Run with verbose output
uv run pytest tests/test_api.py -vv
```

**Can't connect to API?**
```bash
# Check server is running
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}
```
