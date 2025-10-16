"""
State management for resuming tutorial generation from checkpoints.
"""
import json
import os
from typing import Dict, Any, Optional

STATE_FILE = "tutorial_state.json"

def save_state(project_name: str, stage: str, data: Dict[str, Any]):
    """
    Save the current state of tutorial generation.

    Args:
        project_name: Name of the project
        stage: Current stage (e.g., "fetch", "identify", "analyze", etc.)
        data: Data to save for this stage
    """
    state = {}

    # Load existing state if available
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except:
            pass

    # Update state for this project
    if project_name not in state:
        state[project_name] = {}

    state[project_name][stage] = {
        "data": data,
        "completed": True
    }

    # Save state
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved state for stage: {stage}")


def load_state(project_name: str, stage: str) -> Optional[Dict[str, Any]]:
    """
    Load saved state for a specific stage.

    Args:
        project_name: Name of the project
        stage: Stage to load (e.g., "fetch", "identify", etc.)

    Returns:
        Saved data if available, None otherwise
    """
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        if project_name in state and stage in state[project_name]:
            if state[project_name][stage].get("completed"):
                print(f"✓ Loaded cached state for stage: {stage}")
                return state[project_name][stage]["data"]
    except:
        pass

    return None


def clear_state(project_name: str):
    """Clear saved state for a project."""
    if not os.path.exists(STATE_FILE):
        return

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        if project_name in state:
            del state[project_name]

            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            print(f"✓ Cleared state for project: {project_name}")
    except:
        pass


def get_last_completed_stage(project_name: str) -> Optional[str]:
    """Get the last completed stage for a project."""
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        if project_name in state:
            stages = ["fetch", "identify", "analyze", "order", "write", "combine"]
            for stage in reversed(stages):
                if stage in state[project_name] and state[project_name][stage].get("completed"):
                    return stage
    except:
        pass

    return None
