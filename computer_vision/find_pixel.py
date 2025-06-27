import pyautogui
import json
import time

def get_pixel_info():
    # Get screen size for relative positions
    screen_width, screen_height = pyautogui.size()
    print("Move your mouse to the pixel, then press Ctrl+C in the console to copy the output.")

    try:
        while True:
            x, y = pyautogui.position()
            pixel_color = pyautogui.screenshot().getpixel((x, y))
            
            # Calculate relative positions
            #rel_x = round(x / screen_width, 4)
            #rel_y = round(y / screen_height, 4)

            output = {
                    "position": {
                        "x": x,
                        "y": y,
                        "relative_x": round(x / screen_width, 4),
                    },
                    "rgb": {
                        "r": pixel_color[0],
                        "g": pixel_color[1],
                        "b": pixel_color[2]
                    }
                }
            
            print(json.dumps(output, indent=2), end="\r")
            time.sleep(0.20)
    except KeyboardInterrupt:
        # When you hit Ctrl+C, print the final value for easy copy
        print("\nFinal output:")
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    get_pixel_info()