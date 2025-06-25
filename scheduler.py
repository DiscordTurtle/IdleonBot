import threading
import time
import queue
import signal
import sys

from auxiliary import load_config
import tasks

CONFIG_PATH = "config.json"

class ScheduledJob:
    __slots__ = ("func", "args", "interval", "next_run")
    def __init__(self, func, args=(), interval=60):
        self.func     = func
        self.args     = args
        self.interval = interval
        self.next_run = time.time() + interval

def producer_loop(q, jobs, stop_evt, new_job_evt):
    while not stop_evt.is_set():
        now = time.time()
        for job in jobs:
            if job.next_run <= now:
                q.put(job)
                job.next_run = now + job.interval
                new_job_evt.set()      # signal idle_task to break out
        # sleep until the soonest next_run
        next_runs = [j.next_run for j in jobs]
        wait = max(0, min(next_runs) - time.time())
        stop_evt.wait(timeout=wait)

def consumer_loop(q, stop_evt, new_job_evt):
    while not stop_evt.is_set():
        try:
            job = q.get(timeout=1)
            try:
                job.func(*job.args)
            except Exception as e:
                print(f"[{time.strftime('%X')}] Job error: {e}")
            finally:
                q.task_done()
        except queue.Empty:
            tasks.idle_task(stop_evt, new_job_evt)

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
        ScheduledJob(tasks.collect_refinery,
                     args=(profile_name,),
                     interval=15),
        # public-API refresh every 4 hours
        # ScheduledJob(tasks.refresh_public_profile,
        #              args=(profile_name,),
        #              interval=4*60*60),
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