# Team Formation API

FastAPI server for constraint-based team formation with real-time progress streaming via Server-Sent Events (SSE).

## Installation

The API is included with the `team-formation` package. Install with:

```bash
pip install -e .
```

## Starting the Server

Start the API server using the command-line entry point:

```bash
team-formation-api
```

The server will start on `http://localhost:8000` by default.

For development with auto-reload:

```bash
uvicorn team_formation.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### `GET /api`
Root endpoint with API information.

### `GET /health`
Health check endpoint.

### `POST /api/assign_teams`
Assign participants to teams based on weighted constraints. Returns a stream of Server-Sent Events (SSE) with progress updates and final results.

## Usage Example

### Request Format

```json
{
  "participants": [
    {
      "id": 1,
      "name": "Alice",
      "gender": "Female",
      "job_function": "Manager",
      "years_experience": 10
    },
    {
      "id": 2,
      "name": "Bob",
      "gender": "Male",
      "job_function": "Executive",
      "years_experience": 15
    }
    // ... more participants
  ],
  "constraints": [
    {
      "attribute": "gender",
      "type": "diversify",
      "weight": 1
    },
    {
      "attribute": "job_function",
      "type": "cluster",
      "weight": 1
    },
    {
      "attribute": "years_experience",
      "type": "cluster_numeric",
      "weight": 1
    }
  ],
  "target_team_size": 5,
  "less_than_target": false,
  "max_time": 60
}
```

### Constraint Types

- **`diversify`** - Match team attribute distributions to overall population
- **`cluster`** - Group participants with shared discrete values
- **`cluster_numeric`** - Minimize numeric ranges within teams
- **`different`** - Ensure team members don't share specific values

### Using with JavaScript/TypeScript

```javascript
const response = await fetch('http://localhost:8000/api/assign_teams', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    participants: [...],
    constraints: [...],
    target_team_size: 5,
    less_than_target: false,
    max_time: 60
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('event:')) {
      const eventType = line.substring(7).trim();
    } else if (line.startsWith('data:')) {
      const data = JSON.parse(line.substring(6));

      if (eventType === 'progress') {
        console.log(`Progress: ${data.message}`);
        console.log(`  Solutions: ${data.solution_count}`);
        console.log(`  Time: ${data.wall_time.toFixed(2)}s`);
      } else if (eventType === 'complete') {
        console.log('Team assignment complete!');
        console.log(`Created ${data.stats.num_teams} teams`);
        console.log('Team assignments:', data.participants);
      } else if (eventType === 'error') {
        console.error('Error:', data.message);
      }
    }
  }
}
```

### Using with Python

```python
import requests
import json

url = "http://localhost:8000/api/assign_teams"
payload = {
    "participants": [...],
    "constraints": [...],
    "target_team_size": 5,
    "less_than_target": False,
    "max_time": 60
}

with requests.post(url, json=payload, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')

            if line.startswith('event:'):
                event_type = line[7:].strip()
            elif line.startswith('data:'):
                data = json.loads(line[6:])

                if event_type == 'progress':
                    print(f"Progress: {data['message']}")
                elif event_type == 'complete':
                    print(f"Complete! Created {data['stats']['num_teams']} teams")
                    for participant in data['participants']:
                        print(f"  {participant['name']} -> Team {participant['team_number']}")
                elif event_type == 'error':
                    print(f"Error: {data['message']}")
```

### Using with curl

```bash
curl -N -X POST http://localhost:8000/api/assign_teams \
  -H "Content-Type: application/json" \
  -d '{
    "participants": [
      {"id": 1, "name": "Alice", "gender": "Female"},
      {"id": 2, "name": "Bob", "gender": "Male"},
      {"id": 3, "name": "Charlie", "gender": "Male"}
    ],
    "constraints": [
      {"attribute": "gender", "type": "diversify", "weight": 1}
    ],
    "target_team_size": 3,
    "max_time": 10
  }'
```

## Response Format

The endpoint returns Server-Sent Events (SSE) with the following event types:

### Progress Event (`event: progress`)

```json
{
  "event_type": "progress",
  "solution_count": 5,
  "objective_value": 42.5,
  "wall_time": 2.34,
  "num_conflicts": 120,
  "message": "Solution 5: objective=42.50, time=2.34s, conflicts=120"
}
```

### Complete Event (`event: complete`)

```json
{
  "participants": [
    {
      "id": 1,
      "name": "Alice",
      "gender": "Female",
      "team_number": 0
    },
    {
      "id": 2,
      "name": "Bob",
      "gender": "Male",
      "team_number": 1
    }
    // ... more participants
  ],
  "stats": {
    "solution_count": 10,
    "wall_time": 5.67,
    "num_teams": 3,
    "num_participants": 9
  }
}
```

### Error Event (`event: error`)

```json
{
  "event_type": "error",
  "message": "No solution found within 60 seconds. Try increasing max_time or relaxing constraints."
}
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

Run the API tests:

```bash
uv run pytest tests/test_api.py -v
```

## Architecture

The API implementation consists of:

- **`main.py`** - FastAPI application and `/api/assign_teams` endpoint with static file serving
- **`models.py`** - Pydantic request/response models with validation
- **`callbacks.py`** - SSE solution callback for progress streaming

The implementation uses:
- `asyncio` for async/await patterns
- `sse-starlette` for Server-Sent Events streaming
- `asyncio.Queue` for thread-safe event communication between the solver thread and FastAPI
- `asyncio.to_thread()` to run the CP-SAT solver without blocking the event loop

### Production Mode

When `PRODUCTION=true` environment variable is set, the API serves:
- API endpoints at `/api/*`
- Static Vue.js frontend files at `/*`

In development mode (`PRODUCTION=false` or unset), only the API endpoints are served.

## Deployment

### Docker (Recommended)

See the main [README.md](../../README.md#docker-deployment) for Docker deployment instructions.

### Manual Deployment

For production deployment, use a production ASGI server:

```bash
# Set production mode
export PRODUCTION=true

# Run with uvicorn
uvicorn team_formation.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with gunicorn:

```bash
export PRODUCTION=true
gunicorn team_formation.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Note**: Configure CORS origins using the `CORS_ORIGINS` environment variable (comma-separated list) for production use.
