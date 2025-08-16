import json
import time
import cv2
import numpy as np
import pyautogui

# ─── CONFIG ─────────────────────────────────────────────────────────────
REGIONS_FILE    = "computer_vision/regions.json"
BALL_REGION     = "ping_pong_game_region"
SLIDER_REGION   = "ping_pong_slider_region"
BALL_TPL        = "computer_vision/images/ping_pong_ball.png"
SLIDER_TPL      = "computer_vision/images/ping_pong_slider.png"
MATCH_THRESHOLD = 0.85
WINDOW_NAME     = "PingPong Debug"
# ────────────────────────────────────────────────────────────────────────

# load your regions.json
with open(REGIONS_FILE, "r") as f:
    region_data = json.load(f)

def get_region(key):
    r = region_data.get(key)
    if not r:
        raise KeyError(f"Region '{key}' not in {REGIONS_FILE}")
    # r == [left, top, width, height]
    return tuple(r)

def template_debug_match(full_img_bgr, tpl_path, region):
    """
    Crop full_img to region, match tpl, return:
      - top_left_abs (x,y), bottom_right_abs (x,y), max_confidence
    """
    left, top, w, h = region
    crop = full_img_bgr[top:top+h, left:left+w]
    tpl  = cv2.imread(tpl_path, cv2.IMREAD_UNCHANGED)
    if tpl is None:
        raise FileNotFoundError(tpl_path)
    # if your tpl has alpha, drop it:
    if tpl.shape[2] == 4:
        tpl = cv2.cvtColor(tpl, cv2.COLOR_BGRA2BGR)

    res = cv2.matchTemplate(crop, tpl, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)

    # compute box in full‐screen coords
    tlx = left + maxloc[0]
    tly = top  + maxloc[1]
    brx = tlx + tpl.shape[1]
    bry = tly + tpl.shape[0]

    return (tlx, tly), (brx, bry), maxv

def main():
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800, 600)

    ball_reg   = get_region(BALL_REGION)
    slider_reg = get_region(SLIDER_REGION)

    while True:
        # 1) grab screen once per frame
        screenshot = pyautogui.screenshot()
        frame      = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 2) draw region outlines in GREEN
        for reg in (ball_reg, slider_reg):
            l,t,w,h = reg
            cv2.rectangle(frame, (l,t), (l+w, t+h), (0,255,0), 2)

        # 3) match ball & slider
        b_tl, b_br, b_conf = template_debug_match(frame, BALL_TPL,   ball_reg)
        s_tl, s_br, s_conf = template_debug_match(frame, SLIDER_TPL, slider_reg)

        # 4) draw matches if above threshold
        if b_conf >= MATCH_THRESHOLD:
            cv2.rectangle(frame, b_tl, b_br, (0,0,255), 3)
            cv2.putText(frame, f"{b_conf:.2f}", (b_tl[0], b_tl[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        else:
            cv2.putText(frame, f"BALL miss {b_conf:.2f}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        if s_conf >= MATCH_THRESHOLD:
            cv2.rectangle(frame, s_tl, s_br, (255,0,0), 3)
            cv2.putText(frame, f"{s_conf:.2f}", (s_tl[0], s_tl[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)
        else:
            cv2.putText(frame, f"SLIDER miss {s_conf:.2f}", (10,60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)

        # 5) show
        cv2.imshow(WINDOW_NAME, frame)

        # quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.02)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()