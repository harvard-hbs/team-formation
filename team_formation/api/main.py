"""FastAPI application for team formation with SSE progress streaming."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from team_formation.team_assignment import TeamAssignment
from team_formation.api.callbacks import SSESolutionCallback
from team_formation.api.models import (
    TeamAssignmentRequest,
    TeamAssignmentResponse,
    ErrorResponse,
    ProgressEvent,
)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.WARNING),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if running in production mode
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

# Create FastAPI app
app = FastAPI(
    title="Team Formation API",
    description="API for constraint-based team formation with real-time progress updates",
    version="1.0.0",
)

# Configure CORS based on environment
if IS_PRODUCTION:
    # In production, use specific origins from environment variable
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

    if not allowed_origins:
        # If no CORS_ORIGINS set, allow same-origin only (container serving static files)
        allowed_origins = ["*"]
        logger.warning("No CORS_ORIGINS set, allowing all origins. Set CORS_ORIGINS for production.")
else:
    # Development: allow localhost
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_request_to_dataframes(
    request: TeamAssignmentRequest,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert API request to pandas DataFrames for TeamAssignment.

    Args:
        request: The validated team assignment request

    Returns:
        Tuple of (participants_df, constraints_df)
    """
    # Convert participants list to DataFrame
    participants_df = pd.DataFrame(request.participants)

    # Convert constraints list to DataFrame
    constraints_data = [
        {
            "attribute": c.attribute,
            "type": c.type,
            "weight": c.weight,
        }
        for c in request.constraints
    ]
    constraints_df = pd.DataFrame(constraints_data) if constraints_data else pd.DataFrame(
        columns=["attribute", "type", "weight"]
    )

    return participants_df, constraints_df


def convert_result_to_response(
    participants_df: pd.DataFrame,
    solution_count: int,
    wall_time: float,
) -> Dict[str, Any]:
    """Convert TeamAssignment result to API response format.

    Args:
        participants_df: DataFrame with team assignments in team_num column
        solution_count: Number of solutions found during optimization
        wall_time: Total wall clock time in seconds

    Returns:
        Dictionary with participants and stats
    """
    # Replace NaN values with None (which becomes null in JSON)
    participants_df = participants_df.replace({pd.NA: None, pd.NaT: None, np.nan: None})

    # Convert DataFrame to list of dicts
    result_data = participants_df.to_dict(orient="records")

    # Rename team_num to team_number for API consistency
    for participant in result_data:
        if "team_num" in participant:
            participant["team_number"] = int(participant.pop("team_num"))

    # Build stats
    stats = {
        "solution_count": solution_count,
        "wall_time": wall_time,
        "num_teams": int(participants_df["team_num"].nunique()) if "team_num" in participants_df else 0,
        "num_participants": len(participants_df),
    }

    return {
        "participants": result_data,
        "stats": stats,
    }


async def run_team_assignment_async(
    request: TeamAssignmentRequest,
    event_queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
) -> Dict[str, Any]:
    """Run team assignment in a background thread with progress updates.

    Args:
        request: The validated team assignment request
        event_queue: Queue to send progress events to
        loop: Event loop for async operations

    Returns:
        Dictionary with team assignment results

    Raises:
        Exception: If team assignment fails
    """
    logger.info(
        f"Starting team assignment: {len(request.participants)} participants, "
        f"{len(request.constraints)} constraints, max_time={request.max_time}s"
    )

    # Convert request to DataFrames
    participants_df, constraints_df = convert_request_to_dataframes(request)
    logger.debug(f"Converted to DataFrames: participants shape={participants_df.shape}, "
                 f"constraints shape={constraints_df.shape}")

    # Create TeamAssignment instance
    ta = TeamAssignment(
        participants=participants_df,
        constraints=constraints_df,
        target_team_size=request.target_team_size,
        less_than_target=request.less_than_target,
    )
    logger.info(f"Created TeamAssignment instance, target_team_size={request.target_team_size}")

    # Create SSE callback
    callback = SSESolutionCallback(
        event_queue=event_queue,
        loop=loop,
        stop_after_seconds=request.max_time,
    )
    logger.info(f"Created SSE callback with {request.max_time}s timeout")

    # Run solver in thread pool to avoid blocking
    def run_solver():
        """Run the solver synchronously."""
        logger.info("Starting CP-SAT solver...")
        ta.solve(
            solution_callback=callback,
            max_time_in_seconds=request.max_time,
            log_progress=log_level == "DEBUG"
        )
        logger.info("Solver completed")
        return ta

    # Execute solver in thread pool
    logger.info("Launching solver in thread pool...")
    ta_result = await asyncio.to_thread(run_solver)
    logger.info(f"Solver thread completed, solution_found={ta_result.solution_found}")

    # Check if solution was found
    if not ta_result.solution_found:
        raise Exception(
            f"No solution found within {request.max_time} seconds. "
            "Try increasing max_time or relaxing constraints."
        )

    # Convert result to response format
    result = convert_result_to_response(
        participants_df=ta_result.participants,
        solution_count=callback.solution_count,
        wall_time=callback.wall_time,
    )

    return result


async def event_generator(request: TeamAssignmentRequest):
    """Generate SSE events for team assignment progress.

    Args:
        request: The validated team assignment request

    Yields:
        Server-sent events with progress updates and final result
    """
    # Create queue for events
    event_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    # Start team assignment in background
    assignment_task = asyncio.create_task(
        run_team_assignment_async(request, event_queue, loop)
    )

    try:
        # Stream progress events
        while not assignment_task.done():
            try:
                # Wait for event with shorter timeout for more responsive streaming
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)

                # Send progress event
                yield {
                    "event": event.event_type,
                    "data": event.model_dump_json(),
                }

            except asyncio.TimeoutError:
                # No event received, continue waiting
                continue

        # Drain any remaining events in queue
        while not event_queue.empty():
            event = await event_queue.get()
            yield {
                "event": event.event_type,
                "data": event.model_dump_json(),
            }

        # Get the final result
        result = await assignment_task

        # Send completion event with results
        yield {
            "event": "complete",
            "data": json.dumps(result),
        }

    except Exception as e:
        logger.error(f"Error during team assignment: {str(e)}", exc_info=True)

        # Send error event
        error_event = ProgressEvent(
            event_type="error",
            message=str(e),
        )

        yield {
            "event": "error",
            "data": error_event.model_dump_json(),
        }


@app.post(
    "/api/assign_teams",
    response_class=EventSourceResponse,
    responses={
        200: {
            "description": "Server-sent events stream with progress and results",
            "content": {
                "text/event-stream": {
                    "example": "event: progress\ndata: {...}\n\nevent: complete\ndata: {...}\n\n"
                }
            },
        },
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def assign_teams(request: TeamAssignmentRequest) -> EventSourceResponse:
    """Assign participants to teams based on weighted constraints.

    This endpoint accepts a team formation configuration and returns a stream
    of server-sent events (SSE) with progress updates and the final team assignments.

    ## Event Types

    - **progress**: Intermediate solutions during optimization
      - Contains: solution_count, objective_value, wall_time, num_conflicts, message

    - **complete**: Final team assignments (sent once at the end)
      - Contains: participants with team_number field, stats

    - **error**: Error occurred during optimization
      - Contains: error message

    ## Example Usage

    ```javascript
    const eventSource = new EventSource('/api/assign_teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            participants: [...],
            constraints: [...],
            target_team_size: 7,
            less_than_target: false,
            max_time: 60
        })
    });

    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data.message);
    });

    eventSource.addEventListener('complete', (event) => {
        const result = JSON.parse(event.data);
        console.log('Teams assigned:', result.participants);
        eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
        const error = JSON.parse(event.data);
        console.error('Error:', error.message);
        eventSource.close();
    });
    ```
    """
    logger.info(
        f"Received team assignment request: {len(request.participants)} participants, "
        f"{len(request.constraints)} constraints, target_team_size={request.target_team_size}"
    )

    return EventSourceResponse(event_generator(request))


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Team Formation API",
        "version": "1.0.0",
        "endpoints": {
            "assign_teams": "/api/assign_teams (POST)",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Static file serving for Vue.js frontend (production mode)
# Determine static files directory
STATIC_DIR = Path(__file__).parent.parent.parent / "ui" / "dist"

if IS_PRODUCTION and STATIC_DIR.exists():
    # Mount static assets (CSS, JS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the Vue.js frontend."""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found. Build the UI first: cd ui && npm run build"}

    # Catch-all route for Vue.js client-side routing
    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """Serve Vue.js routes (for client-side routing)."""
        # Don't catch API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("health"):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the requested file
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html for client-side routing
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        return {"message": "Frontend not found. Build the UI first: cd ui && npm run build"}
else:
    @app.get("/")
    async def root():
        """Root endpoint with API information (development mode)."""
        return {
            "name": "Team Formation API",
            "version": "1.0.0",
            "mode": "development",
            "message": "Frontend should be served separately in development mode (npm run dev)",
            "endpoints": {
                "assign_teams": "/api/assign_teams (POST)",
                "health": "/health",
                "docs": "/docs",
            },
        }


def run():
    """Run the FastAPI server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "team_formation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning",
    )


if __name__ == "__main__":
    run()
