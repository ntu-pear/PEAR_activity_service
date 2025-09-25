import os
import sys
import argparse

# Add the app directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, app_dir)

def run_activity_sync():
    """Run the activity sync script"""
    from messaging.scripts.activity_sync_script import main
    main()

def run_centre_activity_sync():
    """Run the centre activity sync script"""
    from messaging.scripts.centre_activity_sync_script import main
    main()

def run_activity_preference_sync():
    """Run the activity preference sync script"""
    from messaging.scripts.activity_preference_sync_script import main
    main()

def run_activity_recommendation_sync():
    """Run the activity recommendation sync script"""
    from messaging.scripts.activity_recommendation_sync_script import main
    main()

def list_scripts():
    """List available scripts"""
    print("Available scripts:")
    print("  activity-sync               - Emit ACTIVITY_UPDATED events for existing activities")
    print("  activity-preference-sync    - Emit PREFERENCE_UPDATED events for existing activity preferences")
    print("  activity-recommendation-sync - Emit RECOMMENDATION_UPDATED events for existing activity recommendations")
    print("  centre-activity-sync        - Emit CENTRE_ACTIVITY_UPDATED events for existing centre activities")
    print("")
    print("Usage:")
    print("  python run_scripts.py activity-sync --help")
    print("  python run_scripts.py activity-sync --dry-run")
    print("  python run_scripts.py activity-preference-sync --batch-size 50")

def main():
    if len(sys.argv) < 2:
        list_scripts()
        return
    
    script_name = sys.argv[1]
    
    # Remove script name from sys.argv so the individual scripts can parse their args
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    if script_name == "activity-sync":
        run_activity_sync()
    elif script_name == "activity-preference-sync":
        run_activity_preference_sync()
    elif script_name == "activity-recommendation-sync":
        run_activity_recommendation_sync()
    elif script_name == "centre-activity-sync":
        run_centre_activity_sync()
    elif script_name == "list":
        list_scripts()
    else:
        print(f"Unknown script: {script_name}")
        list_scripts()
        sys.exit(1)

if __name__ == "__main__":
    main()
