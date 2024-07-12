from setuptools import setup

with open("team_formation/_version.txt") as f:
    version = f.read().strip()

setup(
    name="team-formation",
    version=version,
    description=(
        "A tool to form teams from a larger group based "
        "on clustering and diversity constraints"
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/harvard-hbs/team-formation/",
    author="Brent Benson",
    license="MIT",
    install_requires=[
        "pandas>=2.0",
        "ortools>=9.2",
        "streamlit>=1.30",
        "humanize>=4.9",
    ],
    package_data={
        "team_formation": ["_version.txt"],
    }
)
