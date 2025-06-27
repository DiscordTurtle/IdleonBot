from computer_vision.image_functions import find_and_click_image
from computer_vision.image_functions import find_image
from computer_vision.pixel_functions import check_pixel
from computer_vision.pixel_functions import click_pixel, get_pixel_data
import pyautogui
import time
import keyboard

time.sleep(1)

# while not check_pixel("ping_pong_game_start_pixel", tolerance=10):
#     print("Waiting for the ping pong game to start...")
#     time.sleep(1)  # Wait for a second before checking again
#     pass
    
    
# click_pixel("ping_pong_game_start_pixel")
while True:
    ball_location = find_image("ping_pong_game_region", "computer_vision/images/ping_pong_ball.png", confidence=0.85)
    slider_location = find_image("ping_pong_slider_region", "computer_vision/images/ping_pong_slider.png", confidence=0.85)
    #check x coordinates of them, if ball is to the left of slider, move slider left, else move right
    if ball_location and slider_location:
        ball_x = ball_location[0]
        slider_x = slider_location[0]
        if ball_x < slider_x:
            # press left arrow key
            #pyautogui.press('left')
            print("Slider moved left, ball_x:", ball_x, "slider_x:", slider_x)
        elif ball_x > slider_x:
            # press right arrow key
            #pyautogui.press('right')
            print("Slider moved right, ball_x:", ball_x, "slider_x:", slider_x)
    elif not ball_location and slider_location:
        #get slider to center
        slider_x = slider_location[0]
        center_ball_x = get_pixel_data("ping_pong_game_start_pixel")['position']['x']
        if slider_x < center_ball_x:
            # press right arrow key
            pyautogui.press('right')
            print("Slider moved right to center, slider_x:", slider_x, "center_ball_x:", center_ball_x)
        elif slider_x > center_ball_x:
            # press left arrow key
            pyautogui.press('left')
            print("Slider moved left to center, slider_x:", slider_x, "center_ball_x:", center_ball_x)
    else:
        print("Slider not detected")
    #implement keyboard interrupt to stop the game
    if keyboard.is_pressed('q'):
        print("Game stopped by user.")
        break
        
