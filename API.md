# Server-Side API

In addition to the Python API in `team_assignment.TeamAssignment` we
are introducing a FastAPI endpoint called `assign_teams` that takes a
team-formation configuration payload (describedq below) and returns a set of
server-sent events (SSEs) describing progress and finally returns
either an error that a solution cannot be found, or payload that
contains the roster with a new `team_number` field on each roster row.

The configuration payload is a JSON document containing the following 

- `participants` - A list of participants. Each participant has an
  arbitrary set of attributes that identify the participant and that
  can be used in the constraints.
- `constraints` - A list of constraints that refer to the attributes.
- `target_team_size` - An integer greater than 2
- `less_than_target` - A boolean that is `true` if teams not
  `target_team_size` should be `target_team_size - 1`. If it is
  `false` the other teams will be `target_team_size + 1`.
- `max_time` - An integer with the maximum number of seconds that
  should be spent optimizing the constraints.

