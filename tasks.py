import os
import time
import json
from auxiliary import fetch_profile

DATA_DIR = "data"

#TODO, whatever you want to active farm
def idle_task():
    """
    Called whenever the queue is empty.
    """
    print(f"[{time.strftime('%X')}] idle_task: no scheduled work, sleeping briefly…")
    time.sleep(2)
    
#TODO
def collect_refinery(profile_name: str):
    """
    Collects refinery data for the given profile.
    This is a placeholder function for future implementation.
    """
    print(f"[{time.strftime('%X')}] collect_refinery called for '{profile_name}' - not implemented yet.")
   
#TODO
def collect_critters(profile_name: str):
    """
    Collects critters data for the given profile.
    This is a placeholder function for future implementation.
    """
    print(f"[{time.strftime('%X')}] collect_critters called for '{profile_name}' - not implemented yet.")
 
 
#TODO   
def deposit_loot(profile_name: str):
    """
    Deposits loot for the given profile.
    This is a placeholder function for future implementation.
    """
    print(f"[{time.strftime('%X')}] deposit_loot called for '{profile_name}' - not implemented yet.")