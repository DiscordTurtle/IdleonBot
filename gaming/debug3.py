import json, pyautogui, cv2, numpy as np

with open("computer_vision/regions.json") as f:
    regs = json.load(f)

for key, (l,t,w,h) in regs.items():
    print(f"{key} → left={l},top={t},w={w},h={h}")
    shot = pyautogui.screenshot(region=(l,t,w,h))
    cv2.imshow(key, cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR))

cv2.waitKey(0)
cv2.destroyAllWindows()