import streamlit.web.cli as stcli
import sys
import os

def main():
    # Get the directory of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Construct the path to team_assignment_ui.py
    ui_path = os.path.join(dir_path, "team_assignment_ui.py")
    
    sys.argv = ["streamlit", "run", ui_path]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
