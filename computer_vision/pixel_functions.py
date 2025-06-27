import pyautogui
import json


PIXEL_DATA = "computer_vision/pixel_data.json"
with open(PIXEL_DATA, "r") as f:
    pixel_data = json.load(f)


def get_pixel_data(key):
    """
    Returns the pixel data for the given key.
    pixel_data: Dict containing pixel info (from your JSON).
    """
    if key not in pixel_data:
        print(f"Key '{key}' not found in pixel_data.")
        return None
    return pixel_data[key]


def check_pixel(key, tolerance=0):
    """
    Checks if the specified pixel has the target RGB value (with optional tolerance).
    If so, returns True, otherwise returns False.

    Args:
      key: The key within pixel_data to check (e.g., "chest_skill_pixel").
      tolerance: Allow pixels to differ by this amount for non-exact matches (default 0).
    """
    if key not in pixel_data:
        print(f"Key '{key}' not found in pixel_data.")
        return False

    pos = pixel_data[key]['position']
    target_rgb = pixel_data[key]['rgb']
    x, y = pos['x'], pos['y']

    screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
    pixel_rgb = screenshot.getpixel((0, 0))

    matches = all(
        abs(pixel_rgb[i] - target_rgb[c]) <= tolerance
        for i, c in enumerate(['r', 'g', 'b'])
    )
    print(f"Found key '{key}'")


    if matches:
        return True
    return False


def click_pixel(key):
    pyautogui.click(pixel_data[key]['position']['x'], pixel_data[key]['position']['y'])





