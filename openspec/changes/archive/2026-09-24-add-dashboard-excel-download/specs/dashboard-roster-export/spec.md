# Spec Delta

## Purpose

Lets HBS Online Program Services turn a solved team-formation roster into the
exact spreadsheet the Learner Dashboard accepts for upload, without renaming
columns or deriving team labels by hand.

## ADDED Requirements

### Requirement: Dashboard export action availability

The system SHALL offer a Dashboard Download action wherever the roster's other
export actions are offered. The action SHALL be available only when team
assignment results exist, because the exported team label is derived from the
assigned team number.

#### Scenario: No roster loaded

- **WHEN** no participant roster has been loaded
- **THEN** the Dashboard Download action is not offered

#### Scenario: Roster loaded but not yet solved

- **WHEN** a roster is loaded and no team assignment has completed
- **THEN** the Dashboard Download action is not offered

#### Scenario: Assignment results available

- **WHEN** a team assignment has completed and results are present
- **THEN** the Dashboard Download action is offered alongside the existing
  roster export actions

### Requirement: Required column validation

The system SHALL verify, before generating any file, that every required source
column is present in the assignment results. The required source columns are
`first_name`, `last_name`, `email_id`, `hbx_id`, `wave_code`,
`profile_image_url`, and `team_number`.

Source columns SHALL be matched without regard to header case, because rosters
arrive with differing conventions. When one or more required columns are
absent, the system SHALL report an error that names every missing column using
its canonical lower-case name, and SHALL NOT produce a file. A column that is
present but empty for some participants is not a missing column.

#### Scenario: All required columns present

- **WHEN** the user triggers the Dashboard Download and the results contain all
  seven required columns
- **THEN** no error is reported and the export file is produced

#### Scenario: One required column missing

- **WHEN** the user triggers the Dashboard Download and the results lack
  `hbx_id`
- **THEN** an error is shown identifying `hbx_id` as missing
- **AND** no file is downloaded

#### Scenario: Several required columns missing

- **WHEN** the user triggers the Dashboard Download and the results lack both
  `wave_code` and `profile_image_url`
- **THEN** the error names both `wave_code` and `profile_image_url`
- **AND** no file is downloaded

#### Scenario: Required column present but blank for a participant

- **WHEN** every required column exists but one participant has an empty
  `profile_image_url`
- **THEN** the export succeeds and that participant's Profile Photo URL cell is
  empty

#### Scenario: Roster uses upper-case headers

- **WHEN** the roster carries `FIRST_NAME`, `LAST_NAME`, `EMAIL_ID`, `HBX_ID`,
  `WAVE_CODE`, and `PROFILE_IMAGE_URL`
- **THEN** no column is reported missing and the export is produced

#### Scenario: Missing column reported canonically from an upper-case roster

- **WHEN** the roster uses upper-case headers and has no `HBX_ID` column
- **THEN** the error names the missing column as `hbx_id`

### Requirement: Dashboard column selection and naming

The exported file SHALL contain exactly seven columns, in this order, with
these header names, and SHALL exclude every other column present in the roster.
The roster's source columns are matched without regard to case; the exported
header names are fixed and do not vary with the roster's casing:

| Position | Source column | Header in exported file |
| --- | --- | --- |
| 1 | `first_name` | `First Name` |
| 2 | `last_name` | `Last Name` |
| 3 | `email_id` | `Business Email Address` |
| 4 | `hbx_id` | `HBS Online ID` |
| 5 | `wave_code` | `Bodhi Wave Code` |
| 6 | `profile_image_url` | `Profile Photo URL` |
| 7 | `team_number` | `Team Name` |

#### Scenario: Roster carries extra columns

- **WHEN** the roster also contains columns used only as solver constraints,
  such as `time_zone` or `skills_list`
- **THEN** those columns do not appear in the exported file

#### Scenario: Header row

- **WHEN** the exported file is opened
- **THEN** its first row is the seven header names above, in the order above

#### Scenario: Header names do not follow roster casing

- **WHEN** the roster supplies its columns as `FIRST_NAME` and `LAST_NAME`
- **THEN** the exported headers are still `First Name` and `Last Name`

#### Scenario: One roster mixes header casing

- **WHEN** different source columns in the same roster use different casing,
  such as `FIRST_NAME` beside `last_name`
- **THEN** every column is resolved and the exported file is complete

#### Scenario: A column appears in two casings

- **WHEN** a roster carries both `first_name` and `FIRST_NAME`
- **THEN** the value under the exact contract name `first_name` is exported

### Requirement: Team label transform

The system SHALL write the `Team Name` value as the text `Team N`, where N is
the participant's zero-indexed assigned team number plus one. No other exported
value is transformed.

#### Scenario: First team

- **WHEN** a participant is assigned `team_number` 0
- **THEN** their `Team Name` value is the text `Team 1`

#### Scenario: Later team

- **WHEN** a participant is assigned `team_number` 11
- **THEN** their `Team Name` value is the text `Team 12`

#### Scenario: Other values pass through

- **WHEN** a participant's `email_id` is `jdoe@example.com`
- **THEN** their `Business Email Address` value is `jdoe@example.com`,
  unchanged

### Requirement: Export file format and contents

The system SHALL deliver the export as a single-sheet Office Open XML workbook
(`.xlsx`) that opens without a repair prompt in Microsoft Excel. The file SHALL
contain one row per assigned participant, ordered by team number ascending and,
within a team, in the order the participants appear in the results. The
downloaded file name SHALL identify it as a dashboard roster and SHALL be
unique enough that repeated downloads do not silently overwrite one another.

#### Scenario: Row count

- **WHEN** the results contain 84 assigned participants
- **THEN** the exported sheet has 84 data rows plus one header row

#### Scenario: Row ordering

- **WHEN** the results contain participants across teams 0, 1, and 2 in mixed
  order
- **THEN** the exported rows are grouped `Team 1`, then `Team 2`, then `Team 3`

#### Scenario: Opens cleanly in Excel

- **WHEN** the downloaded file is opened in Microsoft Excel
- **THEN** it opens as a normal workbook with no repair or format warning

### Requirement: Identical behavior in the desktop application

The Dashboard Download SHALL behave the same in the packaged desktop
application as in the browser, producing an equivalent `.xlsx` file and letting
the user choose where it is saved.

#### Scenario: Download from the desktop app

- **WHEN** the user triggers the Dashboard Download in the packaged desktop
  application
- **THEN** the same seven-column `.xlsx` file is produced and written to a
  location the user can choose
