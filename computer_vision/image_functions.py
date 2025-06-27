import json
import pyautogui
import time

region_data_file = "computer_vision/regions.json"

with open(region_data_file, "r") as f:
    region_data = json.load(f)


def get_region(region_key):
    """
    Returns the region box for the given key.
    region_box: (left, top, width, height)
    """
    region_box = region_data.get(region_key)
    if not region_box:
        print(f"Region '{region_key}' not found.")
        return None
    return region_box


def find_image(region_key, template_image_path, confidence=0.85):
    """
    Looks for `template_image_path` in the given region (box).
    If found, clicks on its center.
    region_box: (left, top, width, height)
    """
    #region box under this format: "skills_region": [1098, 919, 668, 100]
    region_box = get_region(region_key)
    if not region_box:
        return None

    try:
        button_location = pyautogui.locateCenterOnScreen(
            template_image_path, confidence=confidence, region=region_box
        )
        if button_location:
            print(f"Found {template_image_path} at {button_location}")
            return button_location
        else:
            print(f"{template_image_path} not found in region.")
            return None
            
    except Exception as e:
        print(f"Error occurred while finding image: {e}")
        return None

def find_and_click_image(region_key, template_image_path, confidence=0.85):
    """
    Looks for `template_image_path` in the given region (box).
    If found, clicks on its center.
    region_box: (left, top, width, height)
    """
    region_box = get_region(region_key)
    if not region_box:  
        return None
    
    
    location = find_image(region_box, template_image_path, confidence)
    if location:
        pyautogui.click(location)



if __name__ == "__main__":
    # Example usage
    region = (0, 0, 800, 600)  # Define the region to search in
    image_path = "path/to/your/image.png"  # Replace with your image path

    # Find and click the image
    find_and_click_image(region, image_path)
    
    # Wait for a moment to observe the click
    time.sleep(2)
    
    # Find the image again
    found_location = find_image(region, image_path)
    if found_location:
        print(f"Image found at: {found_location}")
    else:
        print("Image not found.")