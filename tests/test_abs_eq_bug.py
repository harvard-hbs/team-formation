from ortools.sat.python import cp_model

def main():
    test_abs_eq_bug()

def test_abs_eq_bug():    
    model = cp_model.CpModel()
    # Variable to track cost for deviation from target count of 2
    cost_var_0 = model.new_int_var(0, 3, "team_0_cost")
    # The actual team count
    team_count_0 = model.new_int_var(0, 3, "team_0_count")
    diff_expr = team_count_0 - 2
    # Change this back when bug is fixed
    # cost_constraint = model.add_abs_equality(cost_var_0, diff_expr)
    cost_constraint = model.add_max_equality(cost_var_0, [diff_expr, -diff_expr])
    print("Cost constraint:")
    print(cost_constraint.proto)
    # Set actual team count to 0
    model.add(team_count_0 == 0)
    # Look for solution
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    print(f"Solver status: {status} (should be {cp_model.OPTIMAL})")
    assert(status == cp_model.OPTIMAL)
    actual_cost = solver.Value(cost_var_0)
    print(f"Actual cost: {actual_cost} (should be 2)")
    assert(actual_cost == 2)

if __name__ == "__main__":
    main()
    
