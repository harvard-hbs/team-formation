# Constraint-Based Team Formation

A constraint-based team formation tools providing an API and a simple
user interface for dividing a roster of participants into a set of
smaller teams based on settings (e.g., team size), participant
attributes as defined in the input data set, and a set of constraints
defining ideal team composition.

The tool uses the Google OR-Tools [CP-SAT constraint
solver](https://developers.google.com/optimization/reference/python/sat/python/cp_model)
to find feasible team assignments.

## Deployment from PyPi

The Streamlit team formation UI can be run directly from the PyPi
[team-formation]() package using `uv` (how to install `uv`)[].

```
uv run --with team-formation python -m team_formation
```

## REST API Server

The package also provides a FastAPI-based REST API server with Server-Sent Events (SSE) for real-time progress updates during team formation.

### Running the API Server

```bash
# Run directly from PyPi using uv
uv run --with team-formation team-formation-api

# Or in development
uv run team-formation-api
```

The API server will start on `http://localhost:8000` by default.

### API Endpoints

- `POST /api/assign_teams` - Create team assignments with real-time progress streaming via SSE
- `GET /api` - API information
- `GET /health` - Health check

### Features

- Real-time progress updates via Server-Sent Events (SSE)
- Comprehensive request validation with Pydantic models
- Async constraint solving with progress callbacks
- Full OpenAPI/Swagger documentation at `/docs`

For detailed API documentation, examples, and usage instructions, see [team_formation/api/README.md](team_formation/api/README.md).

## Docker Deployment

The application can be deployed as a single Docker container that includes both the FastAPI backend and the Vue.js frontend. This is the recommended approach for production deployments.

### Quick Start

Build and run the containerized application:

```bash
# Build the Docker image
docker build -t team-formation:latest .

# Run the container
docker run -p 8000:8000 -e PRODUCTION=true team-formation:latest
```

The application will be available at `http://localhost:8000`

### Using Docker Compose

For easier management, use Docker Compose:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Environment Variables

Configure the container using environment variables:

- `PRODUCTION` - Set to `true` to enable production mode (required for static file serving)
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins (optional)
- `PORT` - Port to run the server on (default: 8000)
- `LOG_LEVEL` - Logging level (default: warning)

Example with custom configuration:

```bash
docker run -p 8000:8000 \
  -e PRODUCTION=true \
  -e CORS_ORIGINS="https://example.com,https://app.example.com" \
  team-formation:latest
```

### Cloud Platform Deployment

The Docker image can be deployed to various cloud platforms:

#### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/team-formation

# Deploy to Cloud Run
gcloud run deploy team-formation \
  --image gcr.io/YOUR_PROJECT_ID/team-formation \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PRODUCTION=true
```

#### AWS ECS/Fargate

```bash
# Build and push to Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t team-formation .
docker tag team-formation:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/team-formation:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/team-formation:latest

# Deploy using ECS task definition with PRODUCTION=true environment variable
```

#### Azure Container Instances

```bash
# Build and push to Azure Container Registry
az acr build --registry YOUR_REGISTRY --image team-formation:latest .

# Deploy to Azure Container Instances
az container create \
  --resource-group YOUR_RESOURCE_GROUP \
  --name team-formation \
  --image YOUR_REGISTRY.azurecr.io/team-formation:latest \
  --dns-name-label team-formation \
  --ports 8000 \
  --environment-variables PRODUCTION=true
```

### Container Architecture

The Docker image uses a multi-stage build process:

1. **Frontend Build Stage**: Builds the Vue.js frontend using Node.js
2. **Python Stage**: Installs Python dependencies and the team-formation package
3. **Final Image**: Combines the built frontend with the Python backend in a slim production image

The FastAPI application serves both:
- API endpoints at `/api/*` (including SSE streaming at `/api/assign_teams`)
- Static frontend files at `/*` (Vue.js SPA)

### Health Checks

The container includes a health check endpoint at `/health` that can be used for:
- Docker health checks
- Kubernetes liveness/readiness probes
- Load balancer health checks

```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

## Development

After cloning the repository the Makefile contains the following
development operations:

```
uv sync --extra dev         # install 
uv run pytest               # test 
uv build                    # build as package
uv run twine check dist/*   # check the distribution 
uv run twine upload dist/*  # upload to PyPi
```

Here is an example session for creating teams using the API:

```
uv run python
from team_formation.team_assignment import TeamAssignment, SolutionCallback
import pandas as pd
roster = pd.read_csv("climb_roster_1.csv")
constraints = pd.read_csv("climb_constraints.csv")
ta = TeamAssignment(roster, constraints, 7, less_than_target=False)
ta.solve(solution_callback=SolutionCallback(), max_time_in_seconds=60)
ta.evaluate_teams()
ta.participants.to_csv("climb_roster_w_teams.csv")
```

## Constraint Types

- `cluster` - Used for discrete categories or lists of discrete
  categories and attempts to find category overlaps in team members.
  One example would be to find overlapping time availability on
  discrete time blocks.
- `cluster_numeric` - Used on numeric attributes. This constraint
  tries to minimize the range (min to max) of the attribute's value
  in each the team.
- `different` - Used on discrete categories. Attempt to create teams
  that do not sure the value of this attribute.
- `diversify` - Used on discrete categories. This constraint tries to
  match the distribution of the category assignments with those in the
  full participant population.

## Constraint Specification and Weight

A constraint consists of the name of an attribute/column name in the
input dataset, the type of constraint (one of `cluster`,
`cluster_numeric`, `different`, or `diversify`), and a constraint
weight. The constraint solving is done by trying to minimize the
difference of the teams from ideal configuration, multiplying that
difference by the weight of the constraint. In this way you can
prioritize the most important constraints over less important ones.

## Search for Solutions

Once the data has been loaded, the settings made, and the constraints
defined you can search for solutions using the constraint
solver. Depending on the size of the problem and the particular
constraints it may not be feasible to find an optimal solution. An
upper bound in seconds can be provided before generation has
started. Once that number of seconds has been reached, the best
solution will be returned at the next opportunity.

## Evaluating a Solution

Once the solver has been stopped and a feasible solution has been
found it will store a new `team_num` attribute on each of the
participants in the dataset. In addition, a team evaluation can be
viewed where all of the constrained attributes will be rated for each
team. If the constraint has been fully satisfied, its value will be
zero. Positive values can be interpreted as the number of team members
for which the constraint is not valid, or the range of the value in
the team for a `cluster_numeric` constraint.

## Additional Information

Dividing a large learning cohort into smaller teams for group work,
discussion, or other activity is a common requirement in many learning
contexts. It is easy to automate the formation of randomly assigned
teams, but there can be rules, guidelines, and goals guiding the
desired team composition to support learning objectives and other
goals which can complicate manual and automated team creation.

The approach described in this document provides a technical framework
and implementation to support specifying team formation objectives in
a declarative fashion and can automatically generate teams based on
those objectives. There is also a description of how to measure and
evaluate the created teams with respect to the specified objectives.

The team formation objectives currently supported are team size and
*diversification* and *clustering* around participant
attributes. *Diversification* in this context is defined as the goal
of having the distribution of a particular attribute value on each
team reflect the distribution of that attribute value in the overall
learning cohort. For example, if the overall learning cohort has 60%
women and 40% men, a diversification goal on gender would attempt to
achieve 60/40 female/male percentages on each team or, more
specifically, to achieve the female/male participant counts that are
closest to 60%/40% for the particular team size.

*Clustering* is defined as the goal of having all team members share a
particular attribute value. For example, if there is a `job_function`
attribute with values of `Contributor`, `Manager`, and `Executive` a
clustering goal would be to have each team contain participants with a
single value of the `job_function` attribute to facilitate sharing
of common experiences.

Cluster variables can also be multi-valued indicated by a list of
acceptable values for the participant. For example, if there is a
`working_time` variable with hour ranges `00-05`, `05-10`, `10-15`,
`15-20`, and `20-24`. A participant might have the values `["00-05",
"20-24"]` indicating that both those time ranges are acceptable.

In order to balance possibly conflicting objectives and goals of the
team formation process we allow a weight to specified for each
constraint to indicate the priority of the objective in relation
to the others.

## Team Formation as Constraint Satisfaction using CP-SAT

The problem of dividing participants into specified team sizes guided
by diversity and clustering constraints can be stated as a [Constraint
Satisfaction
Problem](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem)
(CSP) with a set of variables with integer domains and constraints on
the allowed combinations.

There is a very efficient constraint solver that uses a variety of
constraint solving techniques from the Google Operational Research
team called [Google OR-Tools
CP-SAT](https://developers.google.com/optimization/cp/cp_solver) that
we are using for this team assignment problem.

The remainder of the document describes how to frame the team
formation problem in the CP-SAT constraint model to be solved by the
CP-SAT solver.

## Input Data

The input to the team formation process is a set of participants with
category-valued attributes, a target team size, and a set of
constraints. The specification of the constraints is done with a
dictionary with keys attribute names from the `participants` data frame as
keys, a type of `diversify` or `cluster`, and a numeric `weight`.

## API

- [API Documentation](https://harvard-hbs.github.io/team-formation)


```
    >>> from team_assignment import TeamAssignment
    >>> import pandas as pd
    >>> participants = pd.DataFrame(
            columns=["id", "gender", "job_function", "working_time"],
            data=[[8, "Male", "Manager", ["00-05", "20-24"]],
                  [9, "Male", "Executive", ["10-15", "15-20"]],
                  [10, "Female", "Executive", ["15-20"]],
                  [16, "Male", "Manager", ["15-20", "20-24"]],
                  [18, "Female", "Contributor", ["05-10", "10-15"]],
                  [20, "Female", "Manager", ["15-20", "20-24"]],
                  [21, "Male", "Executive", ["15-20"]],
                  [29, "Male", "Contributor", ["05-10", "10-15"]],
                  [31, "Female", "Contributor", ["05-10"]]]
        )
    >>> constraints = pd.DataFrame(
            columns=["attribute", "type", "weight"],
            data=[["gender", "diversify", 1],
                  ["job_function", "cluster", 1],
                  ["working_time", "cluster", 1]]
        )
    >>> target_team_size = 3
    >>> ta = TeamAssignment(participants, constraints, target_team_size)
    >>> ta.solve()
    >>> ta.participants.sort_values("team_num")
       id  gender job_function    working_time  team_num
    4  18  Female  Contributor  [05-10, 10-15]         0
    7  29    Male  Contributor  [05-10, 10-15]         0
    8  31  Female  Contributor         [05-10]         0
    0   8    Male      Manager  [00-05, 20-24]         1
    3  16    Male      Manager  [15-20, 20-24]         1
    5  20  Female      Manager  [15-20, 20-24]         1
    1   9    Male    Executive  [10-15, 15-20]         2
    2  10  Female    Executive         [15-20]         2
    6  21    Male    Executive         [15-20]         2
    >>> ta.evaluate_teams()
       team_num  team_size     attr_name       type  missed
    0         0          3        gender  diversify       1
    1         0          3  job_function    cluster       0
    2         0          3  working_time    cluster       0
    3         1          3        gender  diversify       0
    4         1          3  job_function    cluster       0
    5         1          3  working_time    cluster       0
    6         2          3        gender  diversify       0
    7         2          3  job_function    cluster       0
    8         2          3  working_time    cluster       0
    >>>
```

## Change Log

For a detailed log of changes see [CHANGELOG.md](CHANGELOG.md).

## TODO

- [x] Work on simplified SolutionCallback and consider adding to library.
- [x] Go through `create_numeric_clustering_costs` to look for simplifications.
- [ ] Keep track of costs by team and attribute for better introspection.
- [ ] Consider implementing framework for adding new constraint types.
- [ ] Add documentation for new constraint types.
