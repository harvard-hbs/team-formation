#!/usr/bin/env python3
"""Example script demonstrating the Team Formation API with SSE streaming."""

import json
import requests


def main():
    """Run a simple team assignment example using the API."""
    # API endpoint
    url = "http://localhost:8000/assign_teams"

    # Sample team formation request
    payload = {
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

    print("=" * 70)
    print("Team Formation API Example")
    print("=" * 70)
    print(f"\nSending request to {url}")
    print(f"Participants: {len(payload['participants'])}")
    print(f"Constraints: {len(payload['constraints'])}")
    print(f"Target team size: {payload['target_team_size']}")
    print(f"Max time: {payload['max_time']}s")
    print("\n" + "-" * 70)

    try:
        # Make streaming request
        with requests.post(url, json=payload, stream=True, timeout=30) as response:
            response.raise_for_status()

            event_type = None

            print("\nReceiving Server-Sent Events:\n")

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode('utf-8')

                if line.startswith('event:'):
                    event_type = line[7:].strip()

                elif line.startswith('data:'):
                    data = json.loads(line[6:])

                    if event_type == 'progress':
                        print(f"📊 {data['message']}")

                    elif event_type == 'complete':
                        print("\n" + "-" * 70)
                        print("✅ Team Assignment Complete!")
                        print("-" * 70)
                        print(f"\nStats:")
                        print(f"  - Total solutions found: {data['stats']['solution_count']}")
                        print(f"  - Total time: {data['stats']['wall_time']:.2f}s")
                        print(f"  - Number of teams: {data['stats']['num_teams']}")
                        print(f"  - Participants: {data['stats']['num_participants']}")

                        print(f"\nTeam Assignments:")
                        print("-" * 70)

                        # Group by team
                        teams = {}
                        for participant in data['participants']:
                            team_num = participant['team_number']
                            if team_num not in teams:
                                teams[team_num] = []
                            teams[team_num].append(participant)

                        # Display teams
                        for team_num in sorted(teams.keys()):
                            members = teams[team_num]
                            print(f"\nTeam {team_num + 1} ({len(members)} members):")
                            for member in members:
                                print(f"  • ID {member['id']:2d}: "
                                      f"{member['gender']:6s} | "
                                      f"{member['job_function']:12s} | "
                                      f"{member['years_experience']:2d} yrs exp")

                    elif event_type == 'error':
                        print(f"\n❌ Error: {data['message']}")

            print("\n" + "=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server.")
        print("   Make sure the server is running:")
        print("   $ team-formation-api")
        return 1

    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out.")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
