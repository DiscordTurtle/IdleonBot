import os
import time
import json


DATA_DIR = "data"

def idle_task(stop_evt, new_job_evt):
    """
    Called whenever the queue is empty. Cooperative: will bail out as soon as
    new_job_evt is set by the producer.
    """
    print(f"[{time.strftime('%X')}] >>> starting idle_task")
    new_job_evt.clear()
    while not stop_evt.is_set() and not new_job_evt.is_set():
        # do a unit of idle work, or just sleep
        time.sleep(1)
    print(f"[{time.strftime('%X')}] <<< idle_task interrupted")

# placeholder stubs
def collect_refinery(profile_name: str):
    print(f"[{time.strftime('%X')}] collect_refinery: not implemented")

def collect_critters(profile_name: str):
    print(f"[{time.strftime('%X')}] collect_critters: not implemented")

def deposit_loot(profile_name: str):
    print(f"[{time.strftime('%X')}] deposit_loot: not implemented")