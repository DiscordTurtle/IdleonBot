import threading
import time
import queue
import signal
import sys

from auxiliary import load_config
import tasks

from scheduler import ScheduledJob, producer_loop, consumer_loop

CONFIG_PATH = "config.json"
PIXEL_DATA = "computer_vision/pixel_data.json"
REGIONS = "computer_vision/regions.json"
CHARACTER_SLOTS = "data/character_slots.json"

def main():
    stop_evt    = threading.Event()
    new_job_evt = threading.Event()

    # handle Ctrl+C
    def on_sigint(sig, frame):
        print("\nShutting down…")
        stop_evt.set()
    signal.signal(signal.SIGINT, on_sigint)

    cfg = load_config(CONFIG_PATH)
    profile_name = cfg.get("profile_name")
    if not profile_name:
        print(f"Missing 'profile_name' in {CONFIG_PATH}")
        sys.exit(1)

    jobs = [
        # game-related tasks
        #some of these times can be pulled from data instead of hardcoded
        ScheduledJob(tasks.collect_critters,
                     args=(profile_name,),
                     interval=20*60),
        # ScheduledJob(tasks.check_refinery,
        #              args=(profile_name,),
        #              interval=15),
        ScheduledJob(tasks.deposit_loot,
                     args=(),
                     interval=25*60),
    ]

    q = queue.Queue()
    prod = threading.Thread(target=producer_loop,
                             args=(q, jobs, stop_evt, new_job_evt),
                             daemon=True)
    cons = threading.Thread(target=consumer_loop,
                             args=(q, stop_evt, new_job_evt),
                             daemon=True)

    prod.start()
    cons.start()

    print("Scheduler running. Press Ctrl+C to stop.")
    stop_evt.wait()
    prod.join()
    cons.join()
    print("Goodbye.")

if __name__ == "__main__":
    main()