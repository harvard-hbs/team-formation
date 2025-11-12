"""Pydantic models for the team formation API."""

from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class ConstraintInput(BaseModel):
    """A constraint for team formation."""

    attribute: str = Field(..., description="The attribute name from participants to constrain")
    type: str = Field(..., description="Constraint type: diversify, cluster, cluster_numeric, or different")
    weight: Union[int, float] = Field(..., description="Weight/priority for this constraint", gt=0)

    @field_validator("type")
    @classmethod
    def validate_constraint_type(cls, v: str) -> str:
        """Validate that the constraint type is one of the supported types."""
        valid_types = {"diversify", "cluster", "cluster_numeric", "different"}
        if v not in valid_types:
            raise ValueError(
                f"Invalid constraint type '{v}'. Must be one of: {', '.join(sorted(valid_types))}"
            )
        return v


class ParticipantInput(BaseModel):
    """A participant with arbitrary attributes.

    Participants can have any attributes, which will be validated
    against the constraints provided in the request.
    """

    model_config = {"extra": "allow"}  # Allow arbitrary fields

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override to include extra fields in serialization."""
        return super().model_dump(**kwargs)


class TeamAssignmentRequest(BaseModel):
    """Request payload for team assignment."""

    participants: List[Dict[str, Any]] = Field(
        ...,
        description="List of participants with arbitrary attributes",
        min_length=1
    )
    constraints: List[ConstraintInput] = Field(
        ...,
        description="List of constraints to apply",
        min_length=0
    )
    target_team_size: int = Field(
        ...,
        description="Target size for each team",
        gt=2
    )
    less_than_target: bool = Field(
        default=False,
        description="If True, non-target teams will be size-1; if False, size+1"
    )
    max_time: int = Field(
        default=60,
        description="Maximum time in seconds for optimization",
        gt=0
    )

    @model_validator(mode="after")
    def validate_constraints_match_participants(self) -> "TeamAssignmentRequest":
        """Validate that all constraint attributes exist in at least one participant."""
        if not self.participants:
            return self

        # Get all attribute names from all participants
        all_attributes = set()
        for participant in self.participants:
            all_attributes.update(participant.keys())

        # Check each constraint references an existing attribute
        for constraint in self.constraints:
            if constraint.attribute not in all_attributes:
                raise ValueError(
                    f"Constraint attribute '{constraint.attribute}' does not exist in any participant. "
                    f"Available attributes: {', '.join(sorted(all_attributes))}"
                )

        return self


class ParticipantOutput(BaseModel):
    """A participant with team assignment."""

    model_config = {"extra": "allow"}  # Allow arbitrary fields

    team_number: int = Field(..., description="Assigned team number (0-indexed)")


class TeamAssignmentResponse(BaseModel):
    """Response payload with team assignments."""

    participants: List[Dict[str, Any]] = Field(
        ...,
        description="Participants with team_number field added"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistics about the team assignment"
    )


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: str = Field(default="", description="Detailed error information")


class ProgressEvent(BaseModel):
    """Progress update event."""

    event_type: str = Field(..., description="Event type: progress, complete, or error")
    solution_count: int = Field(default=0, description="Number of solutions found")
    objective_value: float = Field(default=0.0, description="Current best objective value")
    wall_time: float = Field(default=0.0, description="Wall clock time in seconds")
    num_conflicts: int = Field(default=0, description="Number of conflicts in search")
    message: str = Field(default="", description="Human-readable progress message")
