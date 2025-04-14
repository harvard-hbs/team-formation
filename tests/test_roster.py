import datetime
import humanize
import logging
import os
import pandas as pd
import sys

# logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from ortools.sat.python import cp_model
from team_formation.team_assignment import TeamAssignment

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_ROSTER = os.path.join(TEST_DIR, "data", "test_roster_2.csv")

class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, stop_after_seconds=None):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.start_time = datetime.datetime.now()
        self.stop_after_seconds = stop_after_seconds

    def on_solution_callback(self):
        objective_value = self.ObjectiveValue()
        num_conflicts = self.NumConflicts()
        cur_time = datetime.datetime.now()
        time_diff = cur_time - self.start_time
        time_diff_human = humanize.naturaldelta(time_diff)
        print(
            f"Elapsed time: {time_diff_human}, Number of conflicts: {num_conflicts}, Objective value: {objective_value}"
        )
        if self.stop_after_seconds and (time_diff.seconds > self.stop_after_seconds):
            print(f"Stopping after {time_diff} elapsed.")
            self.StopSearch()

def roster_model():
    partis = pd.read_csv(TEST_ROSTER)
    constraints = pd.DataFrame({
        "attribute": ["work_experience_years"],
        "type": ["cluster_numeric"],
        "weight": 1,
    })
    target_team_size = 7
    ta = TeamAssignment(
        partis,
        constraints,
        target_team_size,
        less_than_target=True,
    )
    return ta

def test_roster():
    ta = roster_model()
    ta.solve(solution_callback=SolutionCallback(stop_after_seconds=15))
    print(ta.participants.sort_values("team_num").to_string())
    print([ta.solver.Value(var) for var in ta.attr_costs])

def main():
    test_roster()
    
if __name__ == "__main__":
    main()
