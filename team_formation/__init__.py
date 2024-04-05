import os

package_path = os.path.dirname(os.path.realpath(__file__))
version_file_path = os.path.join(package_path, "_version.txt")

with open(version_file_path) as f:
    __version__ = f.read().strip()

from .team_assignment import TeamAssignment, SolutionCallback
from .working_time import working_times_hours
