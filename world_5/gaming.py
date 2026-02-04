"""
Simple automation loop using saved locations JSON.

Behavior: while True -> click "Harvest" every 3 seconds. Stop when 's' or 'q' is pressed.

This script reads `saved_locations/gaming.json` and expects an entry named "Harvest"
containing `center` with `x` and `y` ints.

Run with:
    python gaming.py

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
except Exception:
    print("pyautogui is required. Install with: python -m pip install pyautogui")
    raise


def load_locations(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Saved locations file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Support both dict-with-buttons and older list formats
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
        if 'x' in center and 'y' in center and name:
            mapping[name] = {'x': int(center['x']), 'y': int(center['y'])}
        elif 'x' in entry and 'y' in entry and name:
            mapping[name] = {'x': int(entry['x']), 'y': int(entry['y'])}
    return mapping


def main():
    base = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(base, '..'))
    json_file = os.path.join(repo_root, 'saved_locations', 'gaming.json')

    try:
        locs = load_locations(json_file)
    except Exception as e:
        print(f"Error loading locations: {e}")
        sys.exit(1)

    if 'Harvest' not in locs:
        print("Required entry 'Harvest' not found in the JSON file.")
        print(f"Found keys: {list(locs.keys())}")
        sys.exit(1)

    harvest = locs['Harvest']

    # pyautogui safety and settings
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.01

    stop_event = threading.Event()
    if KEYBOARD_AVAILABLE:
        keyboard.add_hotkey('s', lambda: stop_event.set())
        keyboard.add_hotkey('q', lambda: stop_event.set())
        print(f"Starting loop. Harvest: {harvest}. Stop with Ctrl+C, or press 's'/'q' (global hotkey) to quit.")
    else:
        print(f"Starting loop. Harvest: {harvest}. Stop with Ctrl+C or press 's' in this console to quit.")

    try:
        while True:
            if stop_event.is_set():
                print('Stop key pressed. Exiting loop.')
                break

            if not KEYBOARD_AVAILABLE:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch.lower() in ('s', 'q'):
                            print(f'\nStop key ({ch}) pressed. Exiting loop.')
                            break
                except Exception:
                    pass

            pyautogui.click(harvest['x'], harvest['y'])

            # wait 3 seconds between presses
            time.sleep(3)
    except KeyboardInterrupt:
        print('\nStopped by user (KeyboardInterrupt).')
    finally:
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass


if __name__ == '__main__':
    main()
