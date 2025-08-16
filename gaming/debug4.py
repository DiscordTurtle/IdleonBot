import cv2
for tpl_path in ["computer_vision/images/ping_pong_ball.png",
                 "computer_vision/images/ping_pong_slider.png"]:
    img = cv2.imread(tpl_path, cv2.IMREAD_UNCHANGED)
    print(tpl_path, "shape:", img.shape, "dtype:", img.dtype)
    cv2.imshow(tpl_path, img)
cv2.waitKey(0)
cv2.destroyAllWindows()