"""FastAPI application for team formation with SSE progress streaming."""

import asyncio
import json
import logging
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Team Formation API",
    description="API for constraint-based team formation with real-time progress updates",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
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
    # Convert request to DataFrames
    participants_df, constraints_df = convert_request_to_dataframes(request)

    # Create TeamAssignment instance
    ta = TeamAssignment(
        participants=participants_df,
        constraints=constraints_df,
        target_team_size=request.target_team_size,
        less_than_target=request.less_than_target,
    )

    # Create SSE callback
    callback = SSESolutionCallback(
        event_queue=event_queue,
        loop=loop,
        stop_after_seconds=request.max_time,
    )

    # Run solver in thread pool to avoid blocking
    def run_solver():
        """Run the solver synchronously."""
        ta.solve(solution_callback=callback)
        return ta

    # Execute solver in thread pool
    ta_result = await asyncio.to_thread(run_solver)

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
                # Wait for event with timeout to check task status
                event = await asyncio.wait_for(event_queue.get(), timeout=0.5)

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
        completion_event = ProgressEvent(
            event_type="complete",
            solution_count=result["stats"]["solution_count"],
            objective_value=0.0,  # Final objective included in progress events
            wall_time=result["stats"]["wall_time"],
            num_conflicts=0,
            message=f"Team assignment complete! Created {result['stats']['num_teams']} teams.",
        )

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
    "/assign_teams",
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
    const eventSource = new EventSource('/assign_teams', {
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Team Formation API",
        "version": "1.0.0",
        "endpoints": {
            "assign_teams": "/assign_teams (POST)",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def run():
    """Run the FastAPI server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "team_formation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    run()
