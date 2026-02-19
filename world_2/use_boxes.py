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
import threading

# Optional: global hotkey support. Falls back to console-only input if not available.
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except Exception:
    KEYBOARD_AVAILABLE = False

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
    reset = locs['ResetStreak']
    use_box = locs['UseBoxes']

    # pyautogui safety and settings
    pyautogui.FAILSAFE = False
    # small pause between pyautogui calls (can be adjusted)
    pyautogui.PAUSE = 0.01

    stop_event = threading.Event()
    if KEYBOARD_AVAILABLE:
        # register global hotkeys (works even when the console is not focused)
        keyboard.add_hotkey('s', lambda: stop_event.set())
        keyboard.add_hotkey('q', lambda: stop_event.set())
        print(f"Starting loop. Pen: {pen}, OrderBox: {order}. Stop with Ctrl+C, or press 's'/'q' (global hotkey) to quit.")
    else:
        print(f"Starting loop. Pen: {pen}, OrderBox: {order}. Stop with Ctrl+C or press 's' in this console to quit.")

    try:
        i = 0
        while True:
            i = i + 1
            # check stop_event set by global hotkey (if available)
            if stop_event.is_set():
                print('Stop key pressed. Exiting loop.')
                break

            # fallback: if global hotkeys aren't available, watch for console keypress
            if not KEYBOARD_AVAILABLE:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch.lower() in ('s', 'q'):
                            print(f'\nStop key ({ch}) pressed. Exiting loop.')
                            break
                except Exception:
                    # non-fatal if console input isn't available
                    pass
            # click UseBoxes once
            pyautogui.click(use_box['x'], use_box['y'])
            # repeat delay
            time.sleep(0.05)
    except KeyboardInterrupt:
        print('\nStopped by user (KeyboardInterrupt).')
    finally:
        # cleanup keyboard hooks if they were registered
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass


if __name__ == '__main__':
    main()
