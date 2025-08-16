import time
import cv2
import numpy as np
import pyautogui
from computer_vision.image_functions import find_image

# adjust these to your region keys
BALL_REGION_KEY   = "ping_pong_game_region"
SLIDER_REGION_KEY = "ping_pong_slider_region"
BALL_TEMPLATE     = "computer_vision/images/ping_pong_ball.png"
SLIDER_TEMPLATE   = "computer_vision/images/ping_pong_slider.png"

def visualize_positions(ball_pt=None, slider_pt=None):
    # grab full-screen screenshot
    img = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    if ball_pt:
        x, y = int(ball_pt.x), int(ball_pt.y)
        cv2.circle(frame, (x, y), 20, (0, 0, 255), 4)        # red circle
        cv2.putText(frame, "BALL", (x+25, y+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)

    if slider_pt:
        x, y = int(slider_pt.x), int(slider_pt.y)
        cv2.circle(frame, (x, y), 20, (255, 0, 0), 4)        # blue circle
        cv2.putText(frame, "SLIDER", (x+25, y+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0), 2)

    cv2.imshow("PingPong Debug View", frame)

def main():
    cv2.namedWindow("PingPong Debug View", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("PingPong Debug View", 800, 600)

    while True:
        ball_pt   = find_image(BALL_REGION_KEY,   BALL_TEMPLATE,   confidence=0.5)
        slider_pt = find_image(SLIDER_REGION_KEY, SLIDER_TEMPLATE, confidence=0.5)

        visualize_positions(ball_pt, slider_pt)

        # break on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.02)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()