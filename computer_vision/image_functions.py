import cv2
import numpy as np
import pyautogui
import json

def get_region(key):
    with open("computer_vision/regions.json", "r") as f:
        region_data = json.load(f)
        return region_data.get(key)

def find_needle_in_region(needle_path, screen_region, region_x=0, region_y=0, region_w=None, region_h=None):
    """
    Finds the absolute (x, y) coordinates of a needle image within a specified screen region.

    Parameters:
    - needle_path: Path to the needle image.
    - region_x, region_y: Top-left coordinates of the region on the screen.
    - region_w, region_h: Width and height of the region.

    Returns:
    - Absolute (x, y) coordinates of the needle if found; otherwise, returns None.
    """
    # Load the needle image
    needle = cv2.imread(needle_path)

    # Perform template matching
    result = cv2.matchTemplate(screen_region, needle, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Threshold for a match (you might need to adjust this based on your images)
    threshold = 0.99
    if max_val >= threshold:
        # Calculate the absolute coordinates of the needle
        needle_x = region_x + max_loc[0]
        needle_y = region_y + max_loc[1]
        # The coordinates are for the top-left corner of the needle. 
        # To get the center, you can adjust by adding half of the needle's width and height.
        needle_w, needle_h = needle.shape[1], needle.shape[0]
        absolute_x = needle_x + needle_w // 2
        absolute_y = needle_y + needle_h // 2
        
        # Draw a bounding box around the needle on the screen region
        top_left = (max_loc[0], max_loc[1])
        bottom_right = (max_loc[0] + needle_w, max_loc[1] + needle_h)
        cv2.rectangle(screen_region, top_left, bottom_right, (0, 255, 0), 2)
        
        # Display the result
        cv2.imshow('Result', screen_region)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return (absolute_x, absolute_y)
    else:
        cv2.imshow('Result', screen_region)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return None

def main():
    region = get_region("ping_pong_slider_region")
    region_x, region_y, region_w, region_h = region
    screen_region = pyautogui.screenshot(region=(region_x, region_y, region_w, region_h))
    screen_region = cv2.cvtColor(np.array(screen_region), cv2.COLOR_RGB2BGR)
    needle_path = "computer_vision/images/ping_pong_slider.png"

    result = find_needle_in_region(needle_path, screen_region, region_x, region_y, region_w, region_h)
    if result:
        print(f"Needle found at absolute coordinates: {result}")
    else:
        print("Needle not found in the specified region.")

if __name__ == "__main__":
    main()