import threading
import time
import queue
import signal
import sys
import json
import os

from auxiliary import load_config
import tasks

CONFIG_PATH = "config.json"
TASK_TIME_PATH = "task_times.json"

def load_task_times():
    if os.path.exists(TASK_TIME_PATH):
        try:
            with open(TASK_TIME_PATH, "r") as f:
                text = f.read().strip()
                if not text:
                    return {}  # File is empty, so return empty dict
                return json.loads(text)
        except json.JSONDecodeError:
            print(f"Warning: {TASK_TIME_PATH} contains invalid JSON; resetting.")
            return {}
    return {}

def save_task_time(job_key, timestamp):
    task_times = load_task_times()
    task_times[job_key] = timestamp
    with open(TASK_TIME_PATH, "w") as f:
        json.dump(task_times, f, indent=2)

class ScheduledJob:
    __slots__ = ("func", "args", "interval", "next_run", "key")
    def __init__(self, func, args=(), interval=60, key=None, last_run=None):
        self.func     = func
        self.args     = args
        self.interval = interval
        self.key      = key or self._make_key()
        if last_run is not None:
            self.next_run = last_run + interval
        else:
            self.next_run = time.time() + interval
    
    def _make_key(self):
        return f"{self.func.__name__}_{'_'.join(map(str, self.args))}"

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
                save_task_time(job.key, time.time())
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

    task_times = load_task_times()

    job_specs = [
        # (function, args, interval)
        (tasks.collect_critters, (profile_name,), 20*60),
        (tasks.check_refinery, (profile_name,), 15),
        # Add more jobs as needed
    ]
    jobs = []
    for func, args, interval in job_specs:
        key = func.__name__
        last_run = task_times.get(key)
        jobs.append(ScheduledJob(func, args=args, interval=interval, key=key, last_run=last_run))

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