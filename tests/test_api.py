"""Tests for the FastAPI team formation API."""

import json
import pytest
from fastapi.testclient import TestClient

from team_formation.api.main import app
from team_formation.api.models import (
    TeamAssignmentRequest,
    ConstraintInput,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_request_data():
    """Sample request data for testing."""
    return {
        "participants": [
            {"id": 8, "gender": "Male", "job_function": "Manager", "years_experience": 10},
            {"id": 9, "gender": "Male", "job_function": "Executive", "years_experience": 10},
            {"id": 10, "gender": "Female", "job_function": "Executive", "years_experience": 15},
            {"id": 16, "gender": "Male", "job_function": "Manager", "years_experience": 7},
            {"id": 18, "gender": "Female", "job_function": "Contributor", "years_experience": 3},
            {"id": 20, "gender": "Female", "job_function": "Manager", "years_experience": 5},
            {"id": 21, "gender": "Male", "job_function": "Executive", "years_experience": 13},
            {"id": 29, "gender": "Male", "job_function": "Contributor", "years_experience": 4},
            {"id": 31, "gender": "Female", "job_function": "Contributor", "years_experience": 1},
        ],
        "constraints": [
            {"attribute": "gender", "type": "diversify", "weight": 1},
            {"attribute": "job_function", "type": "cluster", "weight": 1},
            {"attribute": "years_experience", "type": "cluster_numeric", "weight": 1},
        ],
        "target_team_size": 3,
        "less_than_target": False,
        "max_time": 10,
    }


def test_root_endpoint(client):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Team Formation API"


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_assign_teams_valid_request(client, sample_request_data):
    """Test team assignment with a valid request."""
    # Make request to SSE endpoint
    with client.stream("POST", "/api/assign_teams", json=sample_request_data) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                events.append({"type": event_type, "data": json.loads(data)})

        # Should have at least one event (could be progress or complete)
        assert len(events) > 0

        # Last event should be complete
        last_event = events[-1]
        assert last_event["type"] == "complete"

        # Check the completion data
        result = last_event["data"]
        assert "participants" in result
        assert "stats" in result

        # All participants should have team_number
        for participant in result["participants"]:
            assert "team_number" in participant
            assert isinstance(participant["team_number"], int)
            assert participant["team_number"] >= 0

        # Check stats
        assert result["stats"]["num_participants"] == 9
        assert result["stats"]["num_teams"] == 3  # 9 participants / 3 team size


def test_pydantic_model_validation():
    """Test Pydantic model validation."""
    # Valid constraint
    constraint = ConstraintInput(
        attribute="gender",
        type="diversify",
        weight=1
    )
    assert constraint.attribute == "gender"
    assert constraint.type == "diversify"
    assert constraint.weight == 1

    # Invalid constraint type
    with pytest.raises(ValueError, match="Invalid constraint type"):
        ConstraintInput(
            attribute="gender",
            type="invalid_type",
            weight=1
        )

    # Invalid weight (must be > 0)
    with pytest.raises(ValueError):
        ConstraintInput(
            attribute="gender",
            type="diversify",
            weight=0
        )


def test_assign_teams_invalid_constraint_type(client, sample_request_data):
    """Test that invalid constraint types are rejected."""
    sample_request_data["constraints"] = [
        {"attribute": "gender", "type": "invalid_type", "weight": 1}
    ]

    response = client.post("/api/assign_teams", json=sample_request_data)
    assert response.status_code == 422  # Unprocessable Entity


def test_assign_teams_invalid_target_size(client, sample_request_data):
    """Test that invalid target team sizes are rejected."""
    sample_request_data["target_team_size"] = 2  # Must be > 2

    response = client.post("/api/assign_teams", json=sample_request_data)
    assert response.status_code == 422  # Unprocessable Entity


def test_assign_teams_nonexistent_constraint_attribute(client, sample_request_data):
    """Test that constraints referencing nonexistent attributes are rejected."""
    sample_request_data["constraints"] = [
        {"attribute": "nonexistent_attribute", "type": "diversify", "weight": 1}
    ]

    response = client.post("/api/assign_teams", json=sample_request_data)
    assert response.status_code == 422  # Unprocessable Entity


def test_assign_teams_empty_participants(client):
    """Test that empty participants list is rejected."""
    request_data = {
        "participants": [],
        "constraints": [],
        "target_team_size": 3,
        "max_time": 10,
    }

    response = client.post("/api/assign_teams", json=request_data)
    assert response.status_code == 422  # Unprocessable Entity


def test_assign_teams_with_time_limit(client, sample_request_data):
    """Test that the solver respects the time limit."""
    # Set a very short time limit
    sample_request_data["max_time"] = 2

    with client.stream("POST", "/api/assign_teams", json=sample_request_data) as response:
        assert response.status_code == 200

        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                events.append({"type": event_type, "data": json.loads(data)})

        # Should complete (successfully or with error)
        assert len(events) > 0


def test_assign_teams_progress_events(client, sample_request_data):
    """Test that progress events are sent during optimization."""
    with client.stream("POST", "/api/assign_teams", json=sample_request_data) as response:
        assert response.status_code == 200

        progress_events = []
        complete_events = []

        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                event_data = json.loads(data)

                if event_type == "progress":
                    progress_events.append(event_data)
                    # Check progress event structure
                    assert "solution_count" in event_data
                    assert "objective_value" in event_data
                    assert "wall_time" in event_data
                    assert "message" in event_data
                elif event_type == "complete":
                    complete_events.append(event_data)

        # Should have at least one complete event
        assert len(complete_events) >= 1

        # Progress events should have increasing solution counts
        if len(progress_events) > 1:
            for i in range(len(progress_events) - 1):
                assert progress_events[i]["solution_count"] <= progress_events[i + 1]["solution_count"]


def test_assign_teams_with_list_attributes(client):
    """Test team assignment with list-valued attributes."""
    request_data = {
        "participants": [
            {"id": 1, "name": "Alice", "skills": ["Python", "JavaScript"]},
            {"id": 2, "name": "Bob", "skills": ["Python", "Go"]},
            {"id": 3, "name": "Charlie", "skills": ["JavaScript", "Rust"]},
            {"id": 4, "name": "David", "skills": ["Python"]},
            {"id": 5, "name": "Eve", "skills": ["Go", "Rust"]},
            {"id": 6, "name": "Frank", "skills": ["JavaScript"]},
        ],
        "constraints": [
            {"attribute": "skills", "type": "cluster", "weight": 1},
        ],
        "target_team_size": 3,
        "less_than_target": False,
        "max_time": 10,
    }

    with client.stream("POST", "/api/assign_teams", json=request_data) as response:
        assert response.status_code == 200

        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                events.append({"type": event_type, "data": json.loads(data)})

        # Should complete successfully
        last_event = events[-1]
        assert last_event["type"] == "complete"

        # All participants should have team assignments
        result = last_event["data"]
        assert len(result["participants"]) == 6


def test_request_model_validation():
    """Test the TeamAssignmentRequest model validation."""
    # Valid request
    request = TeamAssignmentRequest(
        participants=[
            {"id": 1, "name": "Alice", "gender": "Female"},
            {"id": 2, "name": "Bob", "gender": "Male"},
            {"id": 3, "name": "Charlie", "gender": "Male"},
        ],
        constraints=[
            {"attribute": "gender", "type": "diversify", "weight": 1}
        ],
        target_team_size=3,
        less_than_target=False,
        max_time=60,
    )

    assert len(request.participants) == 3
    assert len(request.constraints) == 1
    assert request.target_team_size == 3
    assert request.max_time == 60

    # Test constraint attribute validation
    with pytest.raises(ValueError, match="does not exist in any participant"):
        TeamAssignmentRequest(
            participants=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            constraints=[
                {"attribute": "nonexistent", "type": "diversify", "weight": 1}
            ],
            target_team_size=3,
        )
