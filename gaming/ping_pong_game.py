import cv2
import numpy as np
import threading
import pyautogui
from mss import mss
import time
import json
# Regions for template matching

with open("computer_vision/regions.json", "r") as f:
    region_data = json.load(f)


ball_region = region_data.get("ping_pong_game_region")
slider_region = region_data.get("ping_pong_slider_region")


BALL_REGION = {'top': int(ball_region[0]), 
               'left': int(ball_region[1]), 
               'width': int(ball_region[2]), 
               'height': int(ball_region[3])}
SLIDER_REGION = {'top': int(slider_region[0]), 
                 'left': int(slider_region[1]), 
                 'width': int(slider_region[2]), 
                 'height': int(slider_region[3])}

# Load templates for ball and slider
ball_template = cv2.imread('computer_vision/images/ping_pong_ball.png', 0)
slider_template = cv2.imread('computer_vision/images/ping_pong_slider.png', 0)

# Function to track ball using template matching
def track_ball(frame, result):
    region = frame[BALL_REGION['top']:BALL_REGION['top'] + BALL_REGION['height'],
                   BALL_REGION['left']:BALL_REGION['left'] + BALL_REGION['width']]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray, ball_template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)
    ball_x = max_loc[0] + BALL_REGION['left']
    ball_y = max_loc[1] + BALL_REGION['top']
    result['ball_position'] = (ball_x, ball_y)

# Function to track slider using template matching
def track_slider(frame, result):
    region = frame[SLIDER_REGION['top']:SLIDER_REGION['top'] + SLIDER_REGION['height'],
                   SLIDER_REGION['left']:SLIDER_REGION['left'] + SLIDER_REGION['width']]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray, slider_template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)
    slider_x = max_loc[0] + SLIDER_REGION['left']
    result['slider_position'] = (slider_x, SLIDER_REGION['top'])

# Function to adjust slider position
def adjust_slider(result):
    while True:
        try:
            ball_pos = result.get('ball_position', (0, 0))
            slider_pos = result.get('slider_position', (0, 0))
            if ball_pos and slider_pos:
                if ball_pos[0] > slider_pos[0]:
                    pyautogui.press('right')
                elif ball_pos[0] < slider_pos[0]:
                    pyautogui.press('left')
            time.sleep(0.05)  # Delay to prevent continuous pressing
        except Exception as e:
            print(f"Error adjusting slider: {e}")

def main():
    sct = mss()
    monitor = sct.monitors[1]
    result = {}

    adjust_thread = threading.Thread(target=adjust_slider, args=(result,), daemon=True)
    adjust_thread.start()

    while True:
        try:
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            ball_thread = threading.Thread(target=track_ball, args=(frame, result))
            slider_thread = threading.Thread(target=track_slider, args=(frame, result))

            ball_thread.start()
            slider_thread.start()

            ball_thread.join()
            slider_thread.join()

            cv2.imshow('Ping Pong', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error in main loop: {e}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
   