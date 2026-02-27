"""
Infinite clicker.

Clicks the current mouse position repeatedly.
- Press 'q' to pause/unpause clicking.
- Press 's' to stop the program.
"""
import time
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


def main():
    stop_event = threading.Event()
    pause_event = threading.Event()  # when set, clicking is paused

    if KEYBOARD_AVAILABLE:
        keyboard.add_hotkey('s', lambda: stop_event.set())
        keyboard.add_hotkey('q', lambda: (pause_event.clear() if pause_event.is_set() else pause_event.set()))
        print("Running. 'q' = pause/unpause, 's' = stop (global hotkeys). Ctrl+C also stops.")
    else:
        print("Running. 'q' = pause/unpause, 's' = stop (console keys). Ctrl+C also stops.")

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.01
    click_delay = 0.05

    try:
        while True:
            if stop_event.is_set():
                print('Stop key pressed. Exiting.')
                break

            if not KEYBOARD_AVAILABLE:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch().lower()
                        if ch == 's':
                            print('Stop key pressed. Exiting.')
                            break
                        elif ch == 'q':
                            if pause_event.is_set():
                                pause_event.clear()
                                print('Resumed.')
                            else:
                                pause_event.set()
                                print('Paused.')
                except Exception:
                    pass

            if pause_event.is_set():
                time.sleep(0.1)
                continue

            pyautogui.click()
            time.sleep(click_delay)
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
