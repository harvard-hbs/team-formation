import numpy as np
import pandas as pd
import pytest

from team_formation.team_assignment import (
    PROBLEM_INVALID_NUMBER,
    PROBLEM_MISSING,
    ParticipantDataError,
    TeamAssignment,
    validate_participants,
)


def make_participants(num=9):
    return pd.DataFrame(
        {
            "id": [1000 + i for i in range(num)],
            "gender": ["Female" if i % 2 else "Male" for i in range(num)],
            "age": [20 + i for i in range(num)],
            "working_time_list": [["05-10", "10-15"] for _ in range(num)],
            "notes": ["" for _ in range(num)],
        }
    )


def make_constraints(*specs):
    return pd.DataFrame(
        [{"attribute": attr, "type": ct, "weight": 1} for attr, ct in specs]
    )


@pytest.mark.parametrize(
    "missing_value", [None, np.nan, pd.NA, "", "   "], ids=repr
)
def test_missing_categorical_values(missing_value):
    participants = make_participants()
    participants["gender"] = participants["gender"].astype(object)
    participants.at[2, "gender"] = missing_value
    issues = validate_participants(
        participants, make_constraints(("gender", "diversify"))
    )
    assert len(issues) == 1
    assert issues[0].attribute == "gender"
    assert issues[0].problem == PROBLEM_MISSING
    assert issues[0].rows == [{"row": 4, "id": 1002}]


def test_empty_list_is_missing():
    participants = make_participants()
    participants.at[0, "working_time_list"] = []
    issues = validate_participants(
        participants, make_constraints(("working_time_list", "cluster"))
    )
    assert [issue.rows for issue in issues] == [[{"row": 2, "id": 1000}]]


def test_absent_key_is_missing():
    records = make_participants().to_dict(orient="records")
    del records[5]["gender"]
    issues = validate_participants(
        pd.DataFrame(records), make_constraints(("gender", "diversify"))
    )
    assert issues[0].rows == [{"row": 7, "id": 1005}]


def test_zero_and_false_are_not_missing():
    participants = make_participants()
    participants["flag"] = [False] * len(participants)
    participants.at[0, "age"] = 0
    issues = validate_participants(
        participants,
        make_constraints(("age", "cluster_numeric"), ("flag", "diversify")),
    )
    assert issues == []


def test_unconstrained_blank_column_ignored():
    issues = validate_participants(
        make_participants(), make_constraints(("gender", "diversify"))
    )
    assert issues == []


def test_non_numeric_value_is_invalid():
    participants = make_participants()
    participants["age"] = participants["age"].astype(object)
    participants.at[3, "age"] = "unknown"
    issues = validate_participants(
        participants, make_constraints(("age", "cluster_numeric"))
    )
    assert len(issues) == 1
    assert issues[0].problem == PROBLEM_INVALID_NUMBER
    assert issues[0].rows == [{"row": 5, "id": 1003, "value": "unknown"}]


def test_numeric_string_is_valid():
    participants = make_participants()
    participants["age"] = [str(age) for age in participants["age"]]
    issues = validate_participants(
        participants, make_constraints(("age", "cluster_numeric"))
    )
    assert issues == []


def test_missing_and_invalid_reported_separately():
    participants = make_participants()
    participants["age"] = participants["age"].astype(object)
    participants.at[1, "age"] = None
    participants.at[2, "age"] = "n/a"
    issues = validate_participants(
        participants, make_constraints(("age", "cluster_numeric"))
    )
    assert [issue.problem for issue in issues] == [
        PROBLEM_MISSING,
        PROBLEM_INVALID_NUMBER,
    ]


def test_all_problem_attributes_reported():
    participants = make_participants()
    participants["gender"] = participants["gender"].astype(object)
    participants.at[1, "gender"] = None
    participants.at[4, "gender"] = None
    participants.at[6, "age"] = np.nan
    issues = validate_participants(
        participants,
        make_constraints(("gender", "diversify"), ("age", "cluster_numeric")),
    )
    assert [(issue.attribute, issue.count) for issue in issues] == [
        ("gender", 2),
        ("age", 1),
    ]


def test_row_numbers_are_positional():
    participants = make_participants()
    participants.index = [50 + i for i in range(len(participants))]
    participants.at[51, "gender"] = None
    issues = validate_participants(
        participants, make_constraints(("gender", "diversify"))
    )
    assert issues[0].rows == [{"row": 3, "id": 1001}]


def test_identifier_column_precedence():
    participants = make_participants().drop(columns=["id"])
    participants["email"] = [f"p{i}@example.com" for i in range(len(participants))]
    participants["participant_id"] = [f"P{i}" for i in range(len(participants))]
    participants.at[0, "gender"] = None
    issues = validate_participants(
        participants, make_constraints(("gender", "diversify"))
    )
    assert issues[0].rows == [{"row": 2, "id": "P0"}]


def test_no_identifier_column():
    participants = make_participants().drop(columns=["id"])
    participants.at[0, "gender"] = None
    issues = validate_participants(
        participants, make_constraints(("gender", "diversify"))
    )
    assert issues[0].rows == [{"row": 2, "id": None}]


def test_blank_identifier():
    participants = make_participants()
    participants["id"] = participants["id"].astype(object)
    participants.at[0, "id"] = None
    participants.at[0, "gender"] = None
    issues = validate_participants(
        participants, make_constraints(("gender", "diversify"))
    )
    assert issues[0].rows == [{"row": 2, "id": None}]


def test_error_message_format():
    participants = make_participants(30)
    participants["gender"] = participants["gender"].astype(object)
    participants.loc[0:24, "gender"] = None
    participants["age"] = participants["age"].astype(object)
    participants.at[27, "age"] = "unknown"
    constraints = make_constraints(
        ("gender", "diversify"), ("age", "cluster_numeric")
    )
    with pytest.raises(ParticipantDataError) as exc_info:
        TeamAssignment(participants, constraints, 3)
    message = str(exc_info.value)
    lines = message.split("\n")
    assert len(lines) == 3
    assert lines[1].startswith(
        "- gender (diversify): 25 rows missing a value: row 2 (id 1000), "
    )
    assert "row 11 (id 1009), and 15 more" in lines[1]
    assert "row 12" not in lines[1]
    assert lines[2] == (
        '- age (cluster_numeric): 1 row with a non-numeric value: '
        'row 29 (id 1027) "unknown"'
    )
    assert len(exc_info.value.issues[0].rows) == 25


def test_missing_numeric_no_longer_nan_error():
    participants = make_participants()
    participants.at[3, "age"] = np.nan
    with pytest.raises(ParticipantDataError, match=r"age \(cluster_numeric\)"):
        TeamAssignment(participants, make_constraints(("age", "cluster_numeric")), 3)


def test_participant_data_error_is_value_error():
    participants = make_participants()
    participants.at[0, "age"] = np.nan
    with pytest.raises(ValueError):
        TeamAssignment(participants, make_constraints(("age", "cluster_numeric")), 3)


def test_numeric_strings_solve():
    participants = make_participants()
    participants["age"] = [str(age) for age in participants["age"]]
    ta = TeamAssignment(participants, make_constraints(("age", "cluster_numeric")), 3)
    ta.solve(max_time_in_seconds=10)
    assert ta.solution_found
    assert pd.api.types.is_numeric_dtype(ta.participants["age"])
