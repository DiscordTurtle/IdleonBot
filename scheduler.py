import threading
import time
import queue
import signal
import sys

from auxiliary import load_config
import tasks

CONFIG_PATH = "config.json"

class ScheduledJob:
    """
    Holds a callable, its args, its interval (secs), and next_run timestamp.
    """
    __slots__ = ("func", "args", "interval", "next_run")

    def __init__(self, func, args=(), interval=60):
        self.func = func
        self.args = args
        self.interval = interval
        self.next_run = time.time() + interval

def producer_loop(q: queue.Queue, jobs: list[ScheduledJob], stop_evt: threading.Event):
    """
    Enqueue jobs when their next_run comes due, then sleep until the next due time.
    """
    while not stop_evt.is_set():
        now = time.time()
        for job in jobs:
            if job.next_run <= now:
                q.put(job)
                job.next_run = now + job.interval

        # sleep until the soonest next_run
        next_times = [job.next_run for job in jobs]
        wait = max(0, min(next_times) - time.time())
        stop_evt.wait(timeout=wait)

def consumer_loop(q: queue.Queue, stop_evt: threading.Event):
    """
    Take the oldest job off the queue and run it.
    If no job arrives within 1s, run the idle_task instead.
    """
    while not stop_evt.is_set():
        try:
            job: ScheduledJob = q.get(timeout=1)
            try:
                job.func(*job.args)
            except Exception as e:
                print(f"[{time.strftime('%X')}] Error in job: {e}")
            finally:
                q.task_done()
        except queue.Empty:
            tasks.idle_task()

def main():
    # handle Ctrl+C gracefully
    stop_evt = threading.Event()
    def on_sigint(signum, frame):
        print("\nShutting down…")
        stop_evt.set()
    signal.signal(signal.SIGINT, on_sigint)

    # load config
    cfg = load_config(CONFIG_PATH)
    profile_name = cfg.get("profile_name")
    if not profile_name:
        print(f"Missing 'profile_name' in {CONFIG_PATH}")
        sys.exit(1)

    # declare your periodic jobs here
    jobs = [
        # fetch every 20 minutes
        ScheduledJob(func=tasks.fetch_and_save,
                     args=(profile_name,),
                     interval=20*60),
        # fetch every 4 hours
        ScheduledJob(func=tasks.fetch_and_save,
                     args=(profile_name,),
                     interval=4*60*60),
        ScheduledJob(func=tasks.collect_refinery,
                     args=(profile_name,),
                     interval=2),
    ]

    q = queue.Queue()
    prod = threading.Thread(target=producer_loop, args=(q, jobs, stop_evt), daemon=True)
    cons = threading.Thread(target=consumer_loop, args=(q, stop_evt), daemon=True)

    prod.start()
    cons.start()

    print("Scheduler running. Press Ctrl+C to stop.")
    # block until stopped
    stop_evt.wait()
    prod.join()
    cons.join()
    print("Goodbye.")

if __name__ == "__main__":
    main()