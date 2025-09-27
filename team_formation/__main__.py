import streamlit.web.cli as stcli
import sys
import os

def main():
    # Get the directory of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Construct the path to team_assignment_ui.py
    ui_path = os.path.join(dir_path, "team_assignment_ui.py")

    # Preserve original command line arguments and pass them through to streamlit
    original_args = sys.argv[1:]  # Skip the script name
    sys.argv = ["streamlit", "run", ui_path] + original_args
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
