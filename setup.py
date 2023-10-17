from setuptools import setup

with open("team_formation/_version.txt") as f:
    version = f.read().strip()

setup(
    name="team_formation",
    version=version,
    description=(
        "A tool to form teams from a larger group based "
        "on clustering and diversity constraints"
    ),
    url="https://github.com/harvard-hbs/team-formation/",
    author="Brent Benson",
    license="MIT",
    install_requires=[
        "pandas>=2.0",
        "ortools>=9.2",
    ],
)
