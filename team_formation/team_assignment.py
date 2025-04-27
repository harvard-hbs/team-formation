#!/usr/bin/env python
# coding: utf-8
# ---
# title: Team Formation as Constraint Satisfaction
# ---
# ## Problem Statement
#
# Dividing a large learning cohort into smaller teams for group work,
# discussion, or other activity is a common requirement in many learning
# contexts. It is easy to automate the formation of randomly assigned
# teams, but there can be rules, guidelines, and goals guiding the
# desired team composition to support learning objectives and other
# goals which can complicate manual and automated team creation.
#
# The approach described in this document provides a technical framework
# and implementation to support specifying team formation objectives in
# a declarative fashion and can automatically generate teams based on
# those objectives. There is also a description of how to measure and
# evaluate the created teams with respect to the specified objectives.
#
# The team formation objectives currently supported are team size and
# *diversification* and *clustering* around participant
# attributes. *Diversification* in this context is defined as the goal
# of having the distribution of a particular attribute value on each
# team reflect the distribution of that attribute value in the overall
# learning cohort. For example, if the overall learning cohort has 60%
# women and 40% men, a diversification goal on gender would attempt to
# achieve 60/40 female/male percentages on each team or, more
# specifically, to achieve the female/male participant counts that are
# closest to 60%/40% for the particular team size.
#
# *Clustering* is defined as the goal of having all team members share a
# particular attribute value. For example, if there is a `job_function`
# attribute with values of `Contributor`, `Manager`, and `Executive` a
# clustering goal would be to have each team contain participants with a
# single value of the `job_function` attribute to facilitate sharing
# of common experiences.
#
# Cluster variables can also be multi-valued indicated by a list of
# acceptable values for the participant. For example, if there is a
# `working_time` variable with hour ranges `00-05`, `05-10`, `10-15`,
# `15-20`, and `20-24`. A participant might have the values `["00-05",
# "20-24"]` indicating that both those time ranges are acceptable.
#
# In order to balance possibly conflicting objectives and goals of the
# team formation process we allow a weight to specified for each
# constraint to indicate the priority of the objective in relation
# to the others.
#
# ## Team Formation as Constraint Satisfaction using CP-SAT
#
# The problem of dividing participants into specified team sizes guided
# by diversity and clustering constraints can be stated as a [Constraint
# Satisfaction
# Problem](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem)
# (CSP) with a set of variables with integer domains and constraints on
# the allowed combinations.
#
# There is a very efficient constraint solver that uses a variety of
# constraint solving techniques from the Google Operational Research
# team called [Google OR-Tools
# CP-SAT](https://developers.google.com/optimization/cp/cp_solver) that
# we are using for this team assignment problem.
#
# The remainder of the document describes how to frame the team
# formation problem in the CP-SAT constraint model to be solved by the
# CP-SAT solver.
#
# ## Input Data
#
# The input to the team formation process is a set of participants with
# category-valued attributes, a target team size, and a set of
# constraints. The specification of the constraints is done with a
# dictionary with keys attribute names from the `participants` data frame as
# keys, a type of `diversify` or `cluster`, and a numeric `weight`.

import logging
import re
import sys
import pandas as pd
from itertools import chain
from collections import Counter, defaultdict

from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)

# ## Problem Representation
#
# We will represent the problem as an instance of the `TeamAssignment`
# class containing related data and methods to create the CP-SAT
# variables and constraints.
#
class TeamAssignment:
    """Create team assignments based on participant attributes and constraints

    Examples
    --------
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
    """

    CT_DIVERSIFY = "diversify"
    """String representing diversify constraints"""
    CT_CLUSTER = "cluster"
    """String representing cluster constraints"""
    CT_CLUSTER_NUMERIC = "cluster_numeric"
    """String representing cluster constraints on numeric values"""
    CT_DIFFERENT = "different"
    """String representing different constraints"""
    CONSTRAINT_TYPES = [
        CT_DIVERSIFY, CT_CLUSTER, CT_CLUSTER_NUMERIC, CT_DIFFERENT
    ]
    """List of all constraints types."""

    def __init__(
        self, participants, constraints, target_team_size, less_than_target=False
    ):
        
        self.model = cp_model.CpModel()
        """The CP-SAT model for creating variables and constraints"""

        self.solution_found = False
        """The `solve` method will set this to `True` if a solution is found"""
        
        self.participants = participants
        """Input variable: participants with attributes"""

        self.num_participants = len(self.participants)
        """Number of participants"""

        self.attr_constraints = constraints.set_index("attribute").to_dict("index")
        """Input variable: constraints with name, type, and priority"""

        # Make lists of boolean and numeric attributes based on constraint
        # type and verify types.
        self.attr_names = []
        self.numeric_attr_names = []
        for attr_name in self.attr_constraints:
            ct_type = self.attr_constraints[attr_name]["type"]
            if ct_type == self.CT_CLUSTER_NUMERIC:
                logger.info(f"Creating {ct_type} numeric constraint on '{attr_name}'.")
                self.numeric_attr_names.append(attr_name)
            elif ct_type in self.CONSTRAINT_TYPES:
                logger.info(f"Creating {ct_type} category constraint on '{attr_name}'.")
                self.attr_names.append(attr_name)
            else:
                logger.error(
                    f"Unknown constraint type '{ct_type}' on attribute '{attr_name}'"
                )
                raise ValueError("Unknown constraint type", ct_type)

        #: Input variable: desired target team size
        self.target_team_size = target_team_size

        #: Input variable: make non-target-size teams one bigger or smaller
        self.less_than_target = less_than_target

        #: Calculated sizes of the teams
        self.team_sizes = calc_team_sizes(
            self.num_participants, self.target_team_size, self.less_than_target
        )
        #: Number of teams
        self.num_teams = len(self.team_sizes)
        logger.info(f"Creating {self.num_teams} teams of size {self.team_sizes}")

        # ### Attribute Value Boolean Variable Names
        #
        # Turn the categorical attribute values
        # into a set of boolean variables 
        self.attr_vals = {}
        for attr_name in self.attr_names:
            bool_vars = categories_to_bool_vars(attr_name, self.participants[attr_name])
            self.attr_vals[attr_name] = bool_vars

        # ### Participant Variables
        #
        # Next we create the `parti_vars` array with one entry for each
        # participant. Each particpant's entry in the array contains a map from
        # attribute name to the list of CP-SAT variables.
        # 1. For each categorical attribute a set of boolean variables indicating
        # whether the participant has that value of the attribute. A constraint
        # of `bool_var == 1` for the presence of the value in the data and
        # `bool_var == 0` for the other attribute values.
        # 2. For each numeric variable there is an integer variable with
        # the numeric value for that participant.
        #
        self.parti_vars = []
        for id, parti in self.participants.iterrows():
            attr_vars = defaultdict(list)
            for attr_name in self.attr_vals:
                bool_vars = []
                parti_vals = parti[attr_name]
                # If a participant can have multiple values of an attribute,
                # they are represented as a list.
                if isinstance(parti_vals, list):
                    verb = "has"
                else:
                    verb = "is"
                    parti_vals = [parti_vals]
                attr_vals = [
                    make_attr_value_name(attr_name, pv, verb) for pv in parti_vals
                ]
                for bool_var_cat in self.attr_vals[attr_name]:
                    bool_var = self.model.new_bool_var(bool_var_cat)
                    bool_vars.append(bool_var)
                    if bool_var_cat in attr_vals:
                        self.model.add(bool_var == 1)
                    else:
                        self.model.add(bool_var == 0)
                attr_vars[attr_name] = bool_vars
            # We don't need variables for the numeric values, we just
            # use the literals. We can maybe modify the boolean case
            # to use a similar approach.
            # for attr_name in self.numeric_attr_names:
            #     parti_var = self.model.NewIntVar(
            #         self.participants[attr_name].min(),
            #         self.participants[attr_name].max(),
            #         f"{attr_name}_parti_val_{id}"
            #     )
            #     self.model.Add(parti_var == self.participants)
            self.parti_vars.append(attr_vars)

        # ### Team Assignment Constraints
        #
        # We have already calculated the size of each team reflected in the
        # `team_sizes` variable that is indexed by team number and holds the
        # size of each team. We now create an array of `num_teams` boolean
        # variables for each participant indicating whether that participant is
        # on the corresponding team. That array of team assignment variables is
        # put in the `parti_vars` map of each participant with the key `"team"`.
        #
        # We also add a constraint that the sum of each participant's team
        # boolean variables must be `1` (a participant can only be on one team)
        # and another constraint that the sum of each of the boolean variables for
        # each team must be equal to the team size to ensure the correct number
        # of participants in each team.

        ## Create team variables
        for id in range(self.num_participants):
            # Each participant has a boolean per team to indicate team membership
            parti_team_vars = []
            for team_num, team_size in enumerate(self.team_sizes):
                team_var = self.model.NewBoolVar(f"parti_{id}_in_team_{team_num}")
                parti_team_vars.append(team_var)
            self.parti_vars[id]["team"] = parti_team_vars
            # Add a constraint so a participant can only be in one team
            self.model.Add(cp_model.LinearExpr.Sum(parti_team_vars) == 1)

        ## Enforce desired team size on each team
        for team_num, team_size in enumerate(self.team_sizes):
            team_vars = [
                self.parti_vars[id]["team"][team_num]
                for id in range(self.num_participants)
            ]
            self.model.Add(cp_model.LinearExpr.Sum(team_vars) == team_size)

        # ### Team Attribute Value Count Variables
        #
        # Both the diversity and clustering constraints used for team formation
        # are defined in terms of team-by-team attribute value counts. We use a
        # `team_value_count` map keyed by the attribute name with an array value
        # indexed by team; for each team there is an array indexed by attribute
        # value containing an integer variable representing the count of
        # that attribute value in the corresponding team.
        #
        # [Describe the mechanism for calculating the counts here.]
        #
        # The count of the number of females in team `0` is
        # `team_value_count["gender"][0][0]`.

        ## Create the map from attribute names to array of teams
        ## containing attribute value counts.
        self.team_value_count = {
            attr_name: self.create_attr_counts(attr_name)
            for attr_name in self.attr_names
        }

        # ### Team Diversity and Clustering Constraints
        #
        # While all of the constraints defined so far have been all or nothing
        # and necessary for the proper functioning of the model (for example,
        # the setting of the participant attribute values and team sizes) the
        # diversity and clustering constraints will be defined with cost
        # functions that go up when the teams are farther away from the desired
        # state and equal to zero in the optimal situation. This allows for
        # over-constraining the model and letting the constraint engine take
        # into account the weights, providing a solution as close as we can get
        # given the participants and their provided attributes.
        #
        # #### Diversity
        #
        # We consider a team to be ideally diverse with respect to a particular
        # attribute when the distribution of each attribute value is the same in
        # the team as it is in the entire participant population. For example if
        # there are 60% women and 40% men in the full population, then a team
        # will be ideally diverse for the gender attribute if there are 60%
        # women and 40% men in that team. We turn those percentage values into
        # integer count targets for each attribute value in a particular-sized
        # team and define the cost function as the absolute value of the
        # difference from the target count, summed across all the variables and
        # multipled by the constraint weight.
        #
        # We define a `population_distribution` method that returns the
        # percentage of each attribute in the full population and then cache
        # that in a `population_dist` map for later use.
        #
        # The `value_count_targets` method uses the population distribution and
        # a team size to return the ideal count for each attribute value in a
        # team of a particular team size. It is important that rounding be used
        # when turning the percentage into a target value count (rather than
        # truncation) to ensure that the target counts add up to the team size.

        # #### Clustering
        #
        # We consider a team to be ideal with respect to an attribute clustering
        # constraint if all of the members of the team have a single value for
        # that attribute. For example, if the `job_function` attribute has
        # values `Contributor`, `Manager`, and `Executive` and a team's size is `3`,
        # then one ideal team configuration is to have all three team members
        # with a `job_function` value of `Contributor`. One way to test for that
        # situation is to compute the maximum of the team's attribute value
        # counts and take its maximum. If the maximum is equal to the team size,
        # then ideal clustering is achieved for the team. We define the
        # clustering cost function to be the difference between the maximum of a
        # team's attribute value counts as the team size, summed across all of
        # the teams and multiplied by the constraint weight.
        #
        # [Put some more details about the calculation mechanism here.]
        #
        # The cost constraints variables are kept in a flat list containing all
        # of the cost variables. We also calculate the population distributions
        # for the diversity constraints in this step.
        #

        # Diversity constraints rely on a measurement of the distribution
        # of the attribute values across the entire population.
        self.population_dist = {}

        # The list of all cost variables
        self.attr_costs = []

        for attr_name in self.attr_constraints:
            constraint = self.attr_constraints[attr_name]
            if constraint["type"] == self.CT_DIVERSIFY:
                pop_dist = self.population_distribution(attr_name)
                logger.info(f"Population distribution for {attr_name}: {dict(pop_dist)}")
                self.population_dist[attr_name] = pop_dist
                costs = self.create_diversity_costs(attr_name)
            if constraint["type"] == self.CT_CLUSTER:
                costs = self.create_clustering_costs(attr_name)
            if constraint["type"] == self.CT_CLUSTER_NUMERIC:
                costs = self.create_numeric_clustering_costs_range(attr_name)
            if constraint["type"] == self.CT_DIFFERENT:
                costs = self.create_difference_costs(attr_name)
            if constraint["weight"] != 1:
                costs = [cost * constraint["weight"] for cost in costs]
            self.attr_costs.extend(costs)

        ## Minimize the sum of the cost variables
        #
        # The last step before solving for team assignments is informing the model
        # of the need to minimize the sum of the cost variables.
        #
        self.model.Minimize(cp_model.LinearExpr.Sum(self.attr_costs))

    def __repr__(self):
        repr = (
            f"TeamAssignment(n={self.num_participants}, "
            f"constraints={len(self.attr_constraints)}, "
            f"target={self.target_team_size}, "
            f"solution={self.solution_found})"
        )
        return repr

    # ## Methods
    #
    # ### Team Attribute Value Count Variables
    #
    def create_attr_counts(self, attr_name):
        """Create attribute value counts for each team."""
        team_attr_counts = []
        attr_vals = self.attr_vals[attr_name]
        for team_num, team_size in enumerate(self.team_sizes):
            team_counts = []
            for attr_val_index, attr_val in enumerate(attr_vals):
                parti_counts = []
                team_attr_count = self.model.NewIntVar(
                    0, team_size, f"team_{team_num}_{attr_val}_count"
                )
                for id in range(self.num_participants):
                    team_var = self.parti_vars[id]["team"][team_num]
                    attr_var = self.parti_vars[id][attr_name][attr_val_index]
                    parti_count = self.model.new_int_var(
                        0,
                        team_size,
                        f"parti_{id}_team_{team_num}_{attr_val}_count"
                    )
                    # Use team_var*attr_var to calculate And(team_var, attr_var)
                    self.model.add_multiplication_equality(
                        parti_count, [team_var, attr_var]
                    )
                    logger.info(f"{parti_count} == {team_var}*{attr_var}")
                    # This is an alternative that doesn't seem to perform as well
                    # self.model.Add(parti_count == attr_var).OnlyEnforceIf(team_var)
                    # self.model.Add(parti_count == 0).OnlyEnforceIf(team_var.Not())
                    parti_counts.append(parti_count)
                self.model.add(team_attr_count == cp_model.LinearExpr.Sum(parti_counts))
                team_counts.append(team_attr_count)
            team_attr_counts.append(team_counts)
        return team_attr_counts

    # ### Team Diversity and Clustering Constraints
    #
    def population_distribution(self, attr_name):
        """Returns the percentage of each attribute value of the
        specified attribute in a mapping from value to percentage."""
        pop_dist = (
            self.participants[attr_name].value_counts(normalize=True).sort_index()
        )
        return pop_dist

    def value_count_targets(self, attr_name, team_size):
        pop_dist = self.population_dist[attr_name]
        targets = (pop_dist * team_size).round().astype(int)
        return targets

    def create_diversity_costs(self, attr_name):
        """Create costs variables for diversity optimization."""
        diversity_costs = []
        num_values = len(self.attr_vals[attr_name])
        pop_dist = self.population_dist[attr_name]
        for team_num, team_size in enumerate(self.team_sizes):
            targets = self.value_count_targets(attr_name, team_size)
            for val in range(num_values - 1):
                cost_var = self.model.NewIntVar(
                    0, team_size, f"{attr_name}_cost_{team_num}_{val}"
                )
                # Broken in ortools-9.12.4544:
                # self.model.add_abs_equality(
                #     cost_var,
                #     (self.team_value_count[attr_name][team_num][val] -
                #      targets.iloc[val]),
                # )
                # Work-around for bug:
                diff_expr = (
                    (self.team_value_count[attr_name][team_num][val] -
                     targets.iloc[val])
                )
                self.model.add_max_equality(cost_var, [diff_expr, -diff_expr])
                diversity_costs.append(cost_var)
        return diversity_costs

    # #### Clustering
    #
    def create_clustering_costs(self, attr_name):
        """Create cost variables for clustering optimization."""
        clustering_costs = []
        for team_num, team_size in enumerate(self.team_sizes):
            max_count_var = self.model.new_int_var(
                0, team_size, f"{attr_name}_max_count[{team_num}]"
            )
            cost_var = self.model.new_int_var(
                0, team_size, f"{attr_name}_cost[{team_num}]"
            )
            self.model.add_max_equality(
                max_count_var, self.team_value_count[attr_name][team_num]
            )
            # `max_count_var` == `team_size` and `cost_var` == 0 when
            # there is a shared value by all members of the team. To consider:
            # do we want to reward all team members sharing more than
            # one value which would require keeping track of all value counts
            # that equal team size.
            self.model.add(cost_var == (team_size - max_count_var))
            clustering_costs.append(cost_var)
        return clustering_costs

    # #### Numeric Clustering
    #
    def create_numeric_clustering_costs_range(self, attr_name):
        """Create costs variables for numeric clustering optimization."""
        parti_vals = self.participants[attr_name]
        attr_min = parti_vals.min()
        attr_max = parti_vals.max()
        numeric_clustering_costs = []
        for team_num, team_size in enumerate(self.team_sizes):
            # Create a variable for the team's min, max, range
            team_min = self.model.new_int_var(
                attr_min,
                attr_max,
                f"{attr_name}_team_min_{team_num}"
            )
            team_max = self.model.new_int_var(
                attr_min,
                attr_max,
                f"{attr_name}_team_max_{team_num}"
            )
            team_range = self.model.new_int_var(
                0,
                (attr_max - attr_min),
                f"{attr_name}_team_range_{team_num}"
            )
            for parti_id in range(self.num_participants):
                self.model.add(
                    team_min <= parti_vals[parti_id]
                ).only_enforce_if(self.parti_vars[parti_id]["team"][team_num])
                self.model.add(
                    team_max >= parti_vals[parti_id]
                ).only_enforce_if(self.parti_vars[parti_id]["team"][team_num])
            self.model.add(team_range == (team_max - team_min))
            numeric_clustering_costs.append(team_range)
        return numeric_clustering_costs

    # #### Numeric Clustering
    #
    def create_numeric_clustering_costs_mad(self, attr_name):
        """Create costs variables for numeric clustering optimization."""
        parti_vals = self.participants[attr_name]
        attr_min = parti_vals.min()
        attr_max = parti_vals.max()
        attr_min_dev = 0
        attr_max_dev = attr_max - attr_min
        numeric_clustering_costs = []
        for team_num, team_size in enumerate(self.team_sizes):
            # Create a variable for the team's mean
            team_mean = self.model.new_int_var(
                attr_min,
                attr_max,
                f"{attr_name}_team_mean_{team_num}"
            )
            team_attr_vals = []
            team_abs_deviations = []
            for parti_id in range(self.num_participants):
                parti_team_val = self.model.new_int_var(
                    min(attr_min, 0),
                    max(attr_max, 0),
                    f"parti_{parti_id}_team_{team_num}_{attr_name}",
                )
                self.model.add_multiplication_equality(
                    parti_team_val,
                    [
                        self.parti_vars[parti_id]["team"][team_num],
                        parti_vals[parti_id],
                    ]
                )
                team_attr_vals.append(parti_team_val)
                parti_dev = self.model.NewIntVar(
                    attr_min_dev,
                    attr_max_dev,
                    f"{attr_name}_parti_{parti_id}_dev",
                )
                # Broken 9.12.4544
                # self.model.add_abs_equality(
                #     parti_dev,
                #     (team_mean - parti_vals[parti_id]),
                # )
                diff_expr = (team_mean - parti_vals[parti_id])
                self.model.add_max_equality(
                    parti_dev,
                    [diff_expr, -diff_expr],
                )
                maybe_parti_dev = self.model.NewIntVar(
                    min(attr_min_dev, 0),
                    max(attr_max_dev, 0),
                    f"{attr_name}_parti_{parti_id}_maybe_dev",
                )
                self.model.add_multiplication_equality(
                    maybe_parti_dev,
                    [
                        self.parti_vars[parti_id]["team"][team_num],
                        parti_dev,
                        
                    ],
                )
                team_abs_deviations.append(maybe_parti_dev)
            # Create a variable for the team's mean absolute deviation
            team_mad = self.model.NewIntVar(
                0,
                (attr_max - attr_min),
                f"{attr_name}_mad_{team_num}"
            )
            # Set the MAD equal to the average of absolute deviations
            self.model.add(team_mad * team_size == sum(team_abs_deviations))
            numeric_clustering_costs.append(team_mad)
        return numeric_clustering_costs

    def create_difference_costs(self, attr_name):
        """Create cost variables for attribute difference optimization."""
        diff_costs = []
        for team_num, team_size in enumerate(self.team_sizes):
            for value_count_var in self.team_value_count[attr_name][team_num]:
                val_name = value_count_var.name
                count_over_1 = self.model.new_int_var(
                    0, team_size, f"{attr_name}_{val_name}_count_over[{team_num}]"
                )
                self.model.add_max_equality(
                    count_over_1,
                    [(value_count_var - 1), 0],
                )
                diff_costs.append(count_over_1)
        return diff_costs
    
    # ## Solving the Model
    #
    # The `solve` method creates a `CpSolver` object and calls its `solve`
    # method on the model we have created. The status is checked for an
    # optimal or feasible solution and, if found, the team assignments
    # are assigned to the participants.

    def solve(self, solution_callback=None, log_progress=False):
        self.solver = cp_model.CpSolver()
        if log_progress:
            self.solver.parameters.log_search_progress = True
            self.solver.parameters.log_to_stdout = True
        # This alternative is for establishing a callback for interrupting before
        # an optimal solution is found.
        self.status = self.solver.Solve(self.model, solution_callback=solution_callback)
        self.solution_found = (self.status == cp_model.OPTIMAL) or (
            self.status == cp_model.FEASIBLE
        )
        if not self.solution_found:
            print(f"Warning: solution was not found: {self.status}")
        else:
            team_assignments = []
            for id in range(self.num_participants):
                for team_num in range(self.num_teams):
                    if self.solver.Value(self.parti_vars[id]["team"][team_num]):
                        team_assignments.append(team_num)
            self.participants["team_num"] = team_assignments

    # ## Evaluating Team Assignments
    #
    # The primary way to evaluate the team assignments is to do a
    # team-by-team calculation for each attribute constraint to
    # determine how many participants have been mis-assigned
    # in terms of diversifaction target count or membership in
    # the predominant clustering group.

    def evaluate_teams(self):
        if not self.solution_found:
            print("Warning: solution has not been found")
            return None
        team_info_list = []
        for team_num, team_size in enumerate(self.team_sizes):
            team_partis = self.participants[
                self.participants["team_num"] == team_num
            ]
            team_info = {
                "team_num": team_num,
                "team_size": team_size,
            }
            for attr_name in self.attr_constraints:
                ct_type = self.attr_constraints[attr_name]["type"]
                if ct_type == self.CT_DIVERSIFY:
                    pop_targets = self.value_count_targets(attr_name, team_size)
                    team_counts = team_partis[attr_name].value_counts().sort_index()
                    missed = (
                        (pop_targets - team_counts)
                        .fillna(0)
                        # Only need of one pos/neg pair
                        .pipe(lambda x: x[x > 0])
                        .sum()
                        .astype(int)
                    )
                    team_info[attr_name] = missed
                elif ct_type == self.CT_CLUSTER:
                    max_count = max_attr_value_count(team_partis[attr_name])
                    missed = team_size - max_count
                elif ct_type == self.CT_CLUSTER_NUMERIC:
                    missed = (team_partis[attr_name].max() - team_partis[attr_name].min())
                elif ct_type == self.CT_DIFFERENT:
                    missed = team_size - team_partis[attr_name].nunique()
                team_info[attr_name] = missed
            team_info_list.append(team_info)
        team_info = pd.DataFrame(team_info_list)
        return team_info


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, stop_after_seconds=None):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.stop_after_seconds = stop_after_seconds

    def on_solution_callback(self):
        print(f"{self.wall_time=}, {self.objective_value=}, {self.num_conflicts=}")
        if (self.stop_after_seconds and
            (self.wall_time > self.stop_after_seconds)):
            print(f"Stopping search after {self.wall_time} seconds")
            self.stop_search()

# ## Functions
#
# ### Team Sizes
#
# The specification also needs to include a `target_team_size` and a
# boolean `less_than_target` that should be true if the teams that are
# not of the target size should be of smaller size, and false if the
# non-target-sized teams should be larger.


def calc_team_sizes(pop_size, target_size, less_than=True):
    if less_than:
        num_teams = (pop_size + target_size - 1) // target_size
        base_team_size = pop_size // num_teams
        extra_members = pop_size % num_teams
        team_sizes = [
            (base_team_size + 1) if (i < extra_members) else base_team_size
            for i in range(num_teams)
        ]
    else:
        num_teams = pop_size // target_size
        base_team_size = pop_size // num_teams
        extra_members = pop_size % num_teams
        team_sizes = [
            base_team_size if (i >= extra_members) else (base_team_size + 1)
            for i in range(num_teams)
        ]
    return team_sizes


# ### Attribute Value Boolean Variable Names
#
# Each of the attributes is incorporated into the model as a set of
# boolean variables that indicates whether the attribute has that
# particular value for a particular participant. We could have used an
# integer-valued variable with a domain of `{0, 1}` for a two-valued
# attribute, a domain of `{0, 1, 2}` for three values, etc., but the
# boolean "has-value" type of variable is the native form for the CP-SAT
# solver, so that was used.
#
# First we create the `attr_vals` map from the attribute name to a list
# of boolean attributes, one for each attribute value.


def make_attr_value_name(attr_name, cat_value, verb):
    """Create simplified attribute value name"""
    cat_value_str = str(cat_value)
    all_alpha = re.sub(r"\W", "_", cat_value_str).lower()
    val_name = re.sub(r"_+", "_", all_alpha)
    attr_val_name = f"{attr_name}_{verb}_{val_name}"
    return attr_val_name


def categories_to_bool_vars(attr_name, cat_values):
    if sum(cat_values.isnull()) > 0:
        raise ValueError("Missing values for attribute", attr_name)
    if isinstance(cat_values.iloc[0], list):
        unique_cats = sorted(set(chain.from_iterable(cat_values)))
        verb = "has"
    else:
        unique_cats = sorted(set(cat_values))
        verb = "is"
    val_names = [
        make_attr_value_name(attr_name, cat_value, verb) for cat_value in unique_cats
    ]
    return val_names


# ## Evaluating Team Assignments
#
def max_attr_value_count(team_vals):
    if isinstance(team_vals.iloc[0], list):
        attr_vals = chain.from_iterable(team_vals)
    else:
        attr_vals = team_vals
    max_count = max(Counter(attr_vals).values())
    return max_count
