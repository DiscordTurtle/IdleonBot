"""
Simple automation loop using saved locations JSON.

Behavior: while True -> click "Pen" once, click "OrderBox" twice, sleep 0.1s, repeat.

This script reads `saved_locations/box_orders.json` (relative to this file) and expects
entries with names "Pen" and "OrderBox" containing `center` with `x` and `y` ints.

Run with:
    python box_orders.py

Stop with Ctrl+C.
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

    # Support both the older list-of-entries format and the newer dict format with a "buttons" key.
    if isinstance(data, dict):
        entries = data.get('buttons') or data.get('list') or []
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("Unsupported saved locations format")

    mapping = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get('name')
        center = entry.get('center') or {}
        # allow older flat entries that put x/y at top-level too
        if 'x' in center and 'y' in center and name:
            mapping[name] = {'x': int(center['x']), 'y': int(center['y'])}
        elif 'x' in entry and 'y' in entry and name:
            mapping[name] = {'x': int(entry['x']), 'y': int(entry['y'])}
    return mapping


def main():
    base = os.path.dirname(__file__)
    # saved_locations is at repository root (parent of this folder)
    repo_root = os.path.abspath(os.path.join(base, '..'))
    json_file = os.path.join(repo_root, 'saved_locations', 'box_orders.json')

    try:
        locs = load_locations(json_file)
    except Exception as e:
        print(f"Error loading locations: {e}")
        sys.exit(1)

    if 'Pen' not in locs or 'OrderBox' not in locs:
        print("Required entries 'Pen' and/or 'OrderBox' not found in the JSON file.")
        print(f"Found keys: {list(locs.keys())}")
        sys.exit(1)

    pen = locs['Pen']
    order = locs['OrderBox']

    # pyautogui safety and settings
    pyautogui.FAILSAFE = False
    # small pause between pyautogui calls (can be adjusted)
    pyautogui.PAUSE = 0.01

    print(f"Starting loop. Pen: {pen}, OrderBox: {order}. Stop with Ctrl+C.")
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
            # click Pen once
            pyautogui.click(pen['x'], pen['y'])
            # click OrderBox twice
            pyautogui.click(order['x'], order['y'])
            # tiny separation to ensure system registers two clicks
            time.sleep(0.02)
            pyautogui.click(order['x'], order['y'])

            # repeat delay
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nStopped by user (KeyboardInterrupt).')


if __name__ == '__main__':
    main()
