import os
import time
import json
from auxiliary import fetch_profile

DATA_DIR = "data"

def idle_task():
    """
    Called whenever the queue is empty.
    """
    print(f"[{time.strftime('%X')}] idle_task: no scheduled work, sleeping briefly…")
    time.sleep(2)

def fetch_and_save(profile_name: str):
    """
    Fetches the profile and writes it to data/<profile_name>.json
    """
    print(f"[{time.strftime('%X')}] Running fetch for '{profile_name}'…")
    data = fetch_profile(profile_name)
    if not data:
        print(f"[{time.strftime('%X')}] No data returned.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, f"{profile_name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[{time.strftime('%X')}] Saved to {out_path}")
    
def collect_refinery(profile_name: str):
    """
    Collects refinery data for the given profile.
    This is a placeholder function for future implementation.
    """
    print(f"[{time.strftime('%X')}] collect_refinery called for '{profile_name}' - not implemented yet.")
    