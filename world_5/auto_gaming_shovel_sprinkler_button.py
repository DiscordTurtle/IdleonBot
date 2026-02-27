"""
Automated gaming loop.

Behavior:
- Loads `saved_locations/gaming.json` to get `Harvest` coordinates.
- Loads `saved_locations/log_minigame.json` to get `log_minigame_center` coords.
- Loads search region from `saved_regions/gaming_region.json`.
- Loads needle images from `saved_images/gaming/`:
    - `sprinkler.png`, `log.png`, `squirrel.png`, `squirrel_2.png`, and `log_minigame.png` (for presence detection)
- Loop:
    - Click `Harvest` button
    - Screenshot region and template-match for each needle; if found, click the detected center
    - If `log_minigame` template is present, repeatedly click `log_minigame_center` until it disappears
    - Repeat until 's' or 'q' is pressed (global hotkey when `keyboard` is available; otherwise console 's' reads)

Run with:
    python auto_gaming.py

Dependencies: pyautogui, Pillow, opencv-python (for template matching). Install missing packages with pip.
"""
import os
import json
import time
import sys
import threading
import msvcrt

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except Exception:
    KEYBOARD_AVAILABLE = False

try:
    import pyautogui
except Exception:
    print('pyautogui is required. Install with: python -m pip install pyautogui')
    raise

# optional opencv
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

from PIL import ImageGrab, Image

# import upgrade_garden from sibling module
sys.path.insert(0, os.path.dirname(__file__))
from upgrade_sequence import upgrade_garden


def load_locations(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        entries = data.get('buttons') or data.get('list') or []
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError('Unsupported saved locations format')
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


def load_region(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    r = data.get('region')
    if not r:
        raise ValueError('No region found in JSON')
    return int(r['x']), int(r['y']), int(r['w']), int(r['h'])


def load_templates(repo_root):
    names = ['log.png', 'squirrel.png', 'squirrel_2.png', 'squirrel_upgrade.png', 'chem_plant_1.png', 'chem_plant_2.png', 'log_minigame.png', 'rat.png', 'rat_upgrade.png', 'rat_upgrade_2.png']
    templates = {}
    for fname in names:
        path = os.path.join(repo_root, 'saved_images', 'gaming', fname)
        key = os.path.splitext(fname)[0]
        if not os.path.exists(path):
            templates[key] = {'missing': True, 'path': path}
            continue
        try:
            pil = Image.open(path).convert('RGBA')
            w, h = pil.size
            entry = {'missing': False, 'path': path, 'w': w, 'h': h}
            if CV2_AVAILABLE:
                arr = np.array(pil)
                if arr.shape[2] == 4:
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                else:
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                entry['cv'] = arr
            else:
                entry['cv'] = None
            templates[key] = entry
        except Exception as e:
            templates[key] = {'missing': True, 'path': path, 'error': str(e)}
    return templates


def match_template_multi(img_cv, tpl_cv, tpl_w, tpl_h, scales=(0.8, 0.9, 1.0, 1.1), method=cv2.TM_CCOEFF_NORMED):
    # returns (best_val, best_loc, best_size)
    best_val = -1.0
    best_loc = None
    best_size = (tpl_w, tpl_h)
    for scale in scales:
        new_w = max(1, int(tpl_w * scale))
        new_h = max(1, int(tpl_h * scale))
        if new_w > img_cv.shape[1] or new_h > img_cv.shape[0]:
            continue
        try:
            if scale == 1.0:
                tpl_scaled = tpl_cv
            else:
                tpl_scaled = cv2.resize(tpl_cv, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            res = cv2.matchTemplate(img_cv, tpl_scaled, method)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_size = (new_w, new_h)
        except Exception:
            continue
    return best_val, best_loc, best_size


def main():
    base = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(base, '..'))

    # load locations
    try:
        gaming = load_locations(os.path.join(repo_root, 'saved_locations', 'gaming.json'))
    except Exception as e:
        print('Error loading gaming locations:', e)
        return

    try:
        loglocs = load_locations(os.path.join(repo_root, 'saved_locations', 'log_minigame.json'))
    except Exception:
        loglocs = {}

    for required in ('Harvest', 'sprinkler', 'shovel'):
        if required not in gaming:
            print(f"'{required}' not found in saved_locations/gaming.json")
            return

    harvest = gaming['Harvest']
    sprinkler_btn = gaming['sprinkler']
    shovel_btn = gaming['shovel']
    log_button = loglocs.get('log_minigame_center')

    # region for searching
    try:
        rx, ry, rw, rh = load_region(os.path.join(repo_root, 'saved_regions', 'gaming_region.json'))
    except Exception as e:
        print('Error loading region:', e)
        return

    # templates
    templates = load_templates(repo_root)

    # set up keyboard stop
    stop_event = threading.Event()
    if KEYBOARD_AVAILABLE:
        keyboard.add_hotkey('s', lambda: stop_event.set())
        keyboard.add_hotkey('q', lambda: stop_event.set())
        print("Running. Stop with 's' or 'q' (global hotkey) or Ctrl+C.")
    else:
        print("Running. Stop with Ctrl+C or press 's' in this console to quit.")

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.01

    per_thresholds = {'log': 0.1, 'squirrel': 0.1, 'squirrel_2': 0.1, 'squirrel_upgrade': 0.85, 'chem_plant_1': 0.1, 'chem_plant_2': 0.1, 'log_minigame': 0.7, 'rat': 0.1, 'rat_upgrade': 0.85, 'rat_upgrade_2': 0.85}
    scales = [0.85, 0.9, 1.0, 1.05]
    click_delay = 0.05  # delay after clicks to reduce missed clicks
    check_log = False  # set to True to enable log template searching/clicking

    iteration = 1
    try:
        while True:
            print(f'Iteration {iteration}')
            if stop_event.is_set():
                print('Stop key pressed. Exiting.')
                break

            if not KEYBOARD_AVAILABLE:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch.lower() in ('s', 'q'):
                            print(f'Stop key ({ch}) pressed. Exiting.')
                            break
                except Exception:
                    pass

            # Start every iteration by clicking Harvest twice, then sprinkler twice, then shovel twice
            try:
                pyautogui.click(harvest['x'], harvest['y'])
                time.sleep(click_delay)
                pyautogui.click(harvest['x'], harvest['y'])
                time.sleep(click_delay)
                # pyautogui.click(sprinkler_btn['x'], sprinkler_btn['y'])
                # time.sleep(click_delay)
                # pyautogui.click(sprinkler_btn['x'], sprinkler_btn['y'])
                # time.sleep(click_delay)
                pyautogui.click(shovel_btn['x'], shovel_btn['y'])
                time.sleep(click_delay)
                pyautogui.click(shovel_btn['x'], shovel_btn['y'])
                print(f'[{iteration}] Clicked Harvest x2, sprinkler x2, shovel x2')
            except Exception as e:
                print(f'[{iteration}] Failed to click buttons:', e)

            # screenshot region and search for needles in order
            try:
                screen = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).convert('RGB')
                img_np = np.array(screen)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f'[{iteration}] Region capture failed:', e)
                img_cv = None

            found_map = {}  # name -> (center_x, center_y, score)
            check_squirrels = (iteration % 50 == 0)
            if img_cv is not None and CV2_AVAILABLE:
                # chem plants: check every iteration and click if present
                for chem in ('chem_plant_1', 'chem_plant_2'):
                    chem_entry = templates.get(chem)
                    if chem_entry and not chem_entry.get('missing') and chem_entry.get('cv') is not None:
                        cval, cloc, csize = match_template_multi(img_cv, chem_entry['cv'], chem_entry['w'], chem_entry['h'], scales=scales)
                        if cval >= per_thresholds.get(chem, 0.1) and cloc is not None:
                            cx = rx + cloc[0] + csize[0] // 2
                            cy = ry + cloc[1] + csize[1] // 2
                            try:
                                pyautogui.click(cx, cy)
                                print(f'[{iteration}] Clicked {chem} at ({cx},{cy}) score={cval:.2f}')
                            except Exception as e:
                                print(f'[{iteration}] Failed to click {chem}:', e)
                            time.sleep(click_delay)

                for name in ('squirrel', 'squirrel_2', 'rat', 'log'):
                    # only check squirrels and rats every 100 iterations
                    if name in ('squirrel', 'squirrel_2', 'rat') and not check_squirrels:
                        continue
                    if name == 'log' and not check_log:
                        continue
                    entry = templates.get(name)
                    if not entry or entry.get('missing') or entry.get('cv') is None:
                        continue
                    best_val, best_loc, best_size = match_template_multi(img_cv, entry['cv'], entry['w'], entry['h'], scales=scales)
                    thresh = per_thresholds.get(name, 0.1)
                    if best_val >= thresh and best_loc is not None:
                        center_x = rx + best_loc[0] + best_size[0] // 2
                        center_y = ry + best_loc[1] + best_size[1] // 2
                        found_map[name] = (center_x, center_y, best_val)

            # Click in preferred order.
            preferred_order = ['squirrel', 'squirrel_2', 'rat', 'log']
            for name in preferred_order:
                if name in found_map:
                    cx, cy, score = found_map[name]
                    try:
                        pyautogui.click(cx, cy)
                        print(f'[{iteration}] Clicked {name} at ({cx},{cy}) score={score:.2f}')
                    except Exception as e:
                        print(f'[{iteration}] Failed to click {name}:', e)
                    time.sleep(click_delay)

                    # after clicking a squirrel, look for a 'squirrel_upgrade' template and click it up to 10 times if present
                    if name in ('squirrel', 'squirrel_2'):
                        sus = templates.get('squirrel_upgrade')
                        if sus and not sus.get('missing') and sus.get('cv') is not None:
                            try:
                                # wait briefly for upgrade to appear, then re-capture region and search for upgrade
                                time.sleep(0.1)
                                screen2 = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).convert('RGB')
                                img_np2 = np.array(screen2)
                                img_cv2 = cv2.cvtColor(img_np2, cv2.COLOR_RGB2BGR)
                                up_val, up_loc, up_size = match_template_multi(img_cv2, sus['cv'], sus['w'], sus['h'], scales=scales)
                                if up_val >= per_thresholds.get('squirrel_upgrade', 0.85) and up_loc is not None:
                                    up_x = rx + up_loc[0] + up_size[0] // 2
                                    up_y = ry + up_loc[1] + up_size[1] // 2
                                    try:
                                        for _ in range(10):
                                            pyautogui.click(up_x, up_y)
                                            time.sleep(click_delay)
                                        print(f'[{iteration}] Clicked squirrel_upgrade 10 times at ({up_x},{up_y}) score={up_val:.2f}')
                                    except Exception as e:
                                        print(f'[{iteration}] Failed to click squirrel_upgrade:', e)
                            except Exception as e:
                                print(f'[{iteration}] Error searching for squirrel_upgrade:', e)
                    # after clicking a rat, look for a 'rat_upgrade' template and click it up to 10 times if present
                    if name == 'rat':
                        # wait briefly for upgrade to appear, then re-capture region
                        time.sleep(0.1)
                        try:
                            screen2 = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).convert('RGB')
                            img_np2 = np.array(screen2)
                            img_cv2 = cv2.cvtColor(img_np2, cv2.COLOR_RGB2BGR)
                        except Exception as e:
                            print(f'[{iteration}] Region capture failed for rat upgrade check:', e)
                            img_cv2 = None

                        for rat_tpl_name in ('rat_upgrade', 'rat_upgrade_2'):
                            rat_up = templates.get(rat_tpl_name)
                            if img_cv2 is not None and rat_up and not rat_up.get('missing') and rat_up.get('cv') is not None:
                                try:
                                    up_val, up_loc, up_size = match_template_multi(img_cv2, rat_up['cv'], rat_up['w'], rat_up['h'], scales=scales)
                                    if up_val >= per_thresholds.get(rat_tpl_name, 0.85) and up_loc is not None:
                                        up_x = rx + up_loc[0] + up_size[0] // 2
                                        up_y = ry + up_loc[1] + up_size[1] // 2
                                        try:
                                            for _ in range(10):
                                                pyautogui.click(up_x, up_y)
                                                time.sleep(click_delay)
                                            print(f'[{iteration}] Clicked {rat_tpl_name} 10 times at ({up_x},{up_y}) score={up_val:.2f}')
                                        except Exception as e:
                                            print(f'[{iteration}] Failed to click {rat_tpl_name}:', e)
                                except Exception as e:
                                    print(f'[{iteration}] Error searching for {rat_tpl_name}:', e)

            # small delay to allow UI update
            time.sleep(0.12)

            # check for log_minigame presence after Harvest
            if CV2_AVAILABLE:
                try:
                    screen = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).convert('RGB')
                    img_np = np.array(screen)
                    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                except Exception:
                    img_cv = None

                lm = templates.get('log_minigame')
                if img_cv is not None and lm and not lm.get('missing') and lm.get('cv') is not None:
                    lm_val, lm_loc, lm_size = match_template_multi(img_cv, lm['cv'], lm['w'], lm['h'], scales=scales)
                    if lm_val >= per_thresholds.get('log_minigame', 0.1) and lm_loc is not None:
                        if log_button:
                            print(f'[{iteration}] Log minigame detected; clicking log_minigame_center repeatedly until it disappears.')
                            # repeat clicking until log_minigame disappears or stop pressed
                            while True:
                                if stop_event.is_set():
                                    break
                                try:
                                    pyautogui.click(log_button['x'], log_button['y'])
                                except Exception as e:
                                    print(f'[{iteration}] Failed to click log_minigame button:', e)
                                time.sleep(0.5)
                                # re-check presence
                                try:
                                    screen = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).convert('RGB')
                                    img_np = np.array(screen)
                                    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                                    lm_val2, _, _ = match_template_multi(img_cv, lm['cv'], lm['w'], lm['h'], scales=scales)
                                    if lm_val2 < per_thresholds.get('log_minigame', 0.1):
                                        print(f'[{iteration}] Log minigame no longer present.')
                                        break
                                except Exception:
                                    break
                        else:
                            print(f'[{iteration}] Log minigame detected but no saved location to click (log_minigame_center missing).')

            # Every 50 iterations, run the upgrade sequence
            if iteration % 50 == 0:
                try:
                    time.sleep(0.5)
                    upgrade_garden()
                    print(f'[{iteration}] Ran upgrade_garden sequence')
                except Exception as e:
                    print(f'[{iteration}] Failed to run upgrade_garden:', e)

            # main loop delay
            time.sleep(0.3)
            iteration += 1
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
