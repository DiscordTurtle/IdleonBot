import cv2, numpy as np, pyautogui

import pyautogui, json

# load your pixel_data.json
with open("computer_vision/pixel_data.json") as f:
    pd = json.load(f)

key = "ping_pong_game_start_pixel"
data = pd[key]
x, y = data["position"]["x"], data["position"]["y"]
stored_rgb = data["rgb"]
actual_rgb = pyautogui.pixel(x, y)

print(f"{key} → stored pos=({x},{y})  stored rgb={stored_rgb}   actual rgb={actual_rgb}")




# grab a small screenshot around your pixel
r = 10
img = pyautogui.screenshot(region=(x-r, y-r, 2*r, 2*r))
frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
cv2.circle(frame, (r, r), 3, (0,0,255), -1) # center dot

cv2.imshow("Pixel Check", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()