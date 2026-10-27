# Spec Delta

## Purpose

Ensures participant data is complete for every attribute the configured constraints depend on before team formation runs, and reports any gaps in terms a person can act on: which columns are affected and which roster rows need fixing.

## ADDED Requirements

### Requirement: Validate constrained attributes before solving

Before team formation starts, the system SHALL check every participant for a usable value in each attribute referenced by a constraint. If any check fails, the system SHALL NOT run the solver and SHALL report a validation error. Attributes not referenced by any constraint SHALL NOT be checked.

#### Scenario: All constrained values present

- **WHEN** every participant has a value for every constrained attribute
- **THEN** validation passes and team formation proceeds as before

#### Scenario: Unconstrained column has blanks

- **WHEN** a participant column has blank values but no constraint references that column
- **THEN** validation passes and team formation proceeds

#### Scenario: Constrained column has a blank

- **WHEN** a constraint references `gender` and one participant has no `gender` value
- **THEN** the solver is not run and a validation error is reported

### Requirement: Definition of a missing value

The system SHALL treat a constrained attribute value as missing when it is null, not-a-number, absent from the participant record, or a string that is empty or only whitespace. For multi-valued attributes (column names ending in `_list`), an empty list SHALL also be treated as missing.

#### Scenario: Empty string

- **WHEN** a participant's value for a constrained attribute is `""` or `"   "`
- **THEN** that value is reported as missing

#### Scenario: Absent key

- **WHEN** a participant record has no key for a constrained attribute that other participants have
- **THEN** that value is reported as missing

#### Scenario: Empty multi-valued attribute

- **WHEN** a constraint references `working_time_list` and a participant's value is an empty list
- **THEN** that value is reported as missing

#### Scenario: Zero and false are not missing

- **WHEN** a participant's constrained value is the number `0` or the boolean `false`
- **THEN** that value is not reported as missing

### Requirement: Numeric constraint values must be numbers

For attributes referenced by a `cluster_numeric` constraint, the system SHALL report a present value that cannot be interpreted as a finite number as invalid. Invalid values SHALL be reported separately from missing values.

#### Scenario: Non-numeric text in a numeric column

- **WHEN** a `cluster_numeric` constraint references `age` and a participant's `age` is `"unknown"`
- **THEN** the solver is not run and the error reports `age` as having an invalid (non-numeric) value for that participant

#### Scenario: Numeric strings are accepted

- **WHEN** a `cluster_numeric` attribute value is the string `"42"`
- **THEN** the value is accepted as valid

### Requirement: Validation error describes all problems at once

A validation error SHALL list every constrained attribute that has missing or invalid values, not only the first one found. For each attribute it SHALL state the attribute name, the constraint type, the kind of problem (missing or invalid), and the number of affected participants.

#### Scenario: Multiple columns with problems

- **WHEN** `gender` has 2 missing values and `age` has 1 missing value, both constrained
- **THEN** a single validation error names both `gender` and `age` with their counts

### Requirement: Validation error identifies affected rows

For each attribute with problems, the error SHALL identify the affected participants by row number, counting the header row of an uploaded file as row 1 so the first participant is row 2. When the data has an identifier column (`id`, `ID`, `participant_id`, `student_id`, or `email`, first match wins), the error SHALL also include each affected participant's identifier value.

#### Scenario: Rows identified with ids

- **WHEN** the participant data has an `id` column and the 3rd participant (with `id` 1047) is missing `gender`
- **THEN** the error identifies that participant as row 4 with id 1047

#### Scenario: Rows identified without ids

- **WHEN** the participant data has no recognized identifier column and the 1st participant is missing `gender`
- **THEN** the error identifies that participant as row 2

### Requirement: Long row lists are truncated

When more than 10 participants are affected for one attribute, the human-readable message SHALL list the first 10 and summarize the remainder as "and N more". The structured error details SHALL still include every affected row.

#### Scenario: Many missing values

- **WHEN** 25 participants are missing `gender`
- **THEN** the message lists 10 rows followed by "and 15 more", and the structured details contain all 25 rows

### Requirement: Validation errors over the REST API

When a team assignment request fails validation, the `/api/assign_teams` stream SHALL emit an `error` event whose `message` is the human-readable validation message, and whose `details` contain, for each problem attribute, the attribute name, constraint type, problem kind, and the affected rows with row numbers and identifiers. Such an error SHALL NOT surface an internal message such as "cannot convert float NaN to integer".

#### Scenario: API request with missing numeric value

- **WHEN** a request has a `cluster_numeric` constraint on `age` and one participant has `age` set to null
- **THEN** the stream emits an `error` event whose message names `age` and the affected row, and no `complete` event is emitted

#### Scenario: Error event details are structured

- **WHEN** a request fails validation
- **THEN** the `error` event data includes a `details` list with one entry per problem attribute

### Requirement: Validation errors in the user interfaces

The web and desktop application and the Streamlit interface SHALL display the validation message in full, with each problem attribute on its own line, so the user can see which columns and rows to correct.

#### Scenario: Desktop app shows missing data

- **WHEN** a user uploads a roster with a blank cell in a constrained column and clicks create teams
- **THEN** the error alert lists the column name and the affected row numbers and identifiers, each attribute on a separate line
