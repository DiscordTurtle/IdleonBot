"""
Simple automation loop using saved locations JSON.

Behavior: while True -> click "Reset" once, sleep 5s, repeat.

This script reads `saved_locations/boss_fighting.json` (relative to this file) and expects
an entry with name "Reset" containing `center` with `x` and `y` ints.

Run with:
    python boss_fighting.py

Stop with Ctrl+C or press 'q'.
"""
import os
import json
import time
import sys
import msvcrt

try:
    import pyautogui
except Exception as e:
    print("pyautogui is required. Install with: python -m pip install pyautogui")
    raise


def load_locations(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Saved locations file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for entry in data:
        name = entry.get('name')
        center = entry.get('center')
        if name and isinstance(center, dict) and 'x' in center and 'y' in center:
            mapping[name] = {'x': int(center['x']), 'y': int(center['y'])}
    return mapping


def main():
    base = os.path.dirname(__file__)
    json_file = os.path.join(base, 'saved_locations', 'boss_fighting.json')

    try:
        locs = load_locations(json_file)
    except Exception as e:
        print(f"Error loading locations: {e}")
        sys.exit(1)

    if 'Reset' not in locs:
        print("Required entry 'Reset' not found in the JSON file.")
        print(f"Found keys: {list(locs.keys())}")
        sys.exit(1)

    reset = locs['Reset']

    # pyautogui safety and settings
    pyautogui.FAILSAFE = False
    # small pause between pyautogui calls (can be adjusted)
    pyautogui.PAUSE = 0.01

    print(f"Starting loop. Reset: {reset}. Stop with Ctrl+C or press 'q'.")
    try:
        while True:
            # if a key was pressed in the console, check for 'q' to quit
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch.lower() == 'q':
                        print('\nStop key (q) pressed. Exiting loop.')
                        break
            except Exception:
                # non-fatal if console input isn't available
                pass
            # click Reset once
            pyautogui.click(reset['x'], reset['y'])

            # wait 10 seconds before next click
            time.sleep(10)
    except KeyboardInterrupt:
        print('\nStopped by user (KeyboardInterrupt).')


if __name__ == '__main__':
    main()
