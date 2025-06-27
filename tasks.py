
import time
from computer_vision.image_functions import click_image
from computer_vision.pixel_functions import check_pixel, click_pixel
import json
import pyautogui


DATA_DIR = "data"

REGIONS = "computer_vision/regions.json"


chest_key = "chest_skill_pixel"
skillbar_up_pixel = "skillbar_up_pixel"



with open(REGIONS, "r") as f:
    regions = json.load(f)


def idle_task(stop_evt, new_job_evt):
    """
    Called whenever the queue is empty. Cooperative: will bail out as soon as
    new_job_evt is set by the producer.
    """
    print(f"[{time.strftime('%X')}] >>> starting idle_task")
    new_job_evt.clear()
    while not stop_evt.is_set() and not new_job_evt.is_set():
        # do a unit of idle work, or just sleep
        time.sleep(1)
    print(f"[{time.strftime('%X')}] <<< idle_task interrupted")

# placeholder stubs
def check_refinery(profile_name: str):
    print(f"[{time.strftime('%X')}] collect_refinery: not implemented")

def collect_critters(profile_name: str):
    print(f"[{time.strftime('%X')}] collect_critters: not implemented")

def deposit_loot():
    print(f"[{time.strftime('%X')}] >>> deposit_loot:")
    if not check_pixel(skillbar_up_pixel, tolerance=20):
        print(f"Skills are not active, activating skills.")
        pyautogui.press('q')
    time.sleep(0.3)
    if check_pixel(chest_key, tolerance=10):
        click_pixel(chest_key)
        print(f"Clicked on {chest_key} pixel.")
        return True
    for i in range(3):
        if check_pixel(chest_key, tolerance=10):
            click_pixel(chest_key)
            print(f"Clicked on {chest_key} pixel.")
            break
        elif check_pixel(skillbar_up_pixel, tolerance=10):
            click_pixel(skillbar_up_pixel)
            print(f"Changed skillbar")
            time.sleep(1)
        else:
            print(f"Could not find {chest_key} or {skillbar_up_pixel} pixel.")
    
    time.sleep(0.5)
    if check_pixel(skillbar_up_pixel, tolerance=10):
        click_pixel(skillbar_up_pixel)
        print(f"Clicked on skillbar up pixel to close skills.")
    
    print(f"[{time.strftime('%X')}] <<< deposit_loot:")
    time.sleep(1)

    
    
def check_gaming(profile_name: str):
    print(f"[{time.strftime('%X')}] check_gaming: not implemented")
    
def check_sneaking(profile_name: str):
    print(f"[{time.strftime('%X')}] check_sneaking: not implemented")
    
def check_construction(profile_name: str):
    print(f"[{time.strftime('%X')}] check_construction: not implemented")

def check_plinko(profile_name: str):
    print(f"[{time.strftime('%X')}] check_plinko: not implemented")
    
def check_afk(profile_name: str):
    print(f"[{time.strftime('%X')}] check_afk: not implemented")
    
def check_library(profile_name: str):
    #TODO implement some library ranking system for which book to get
    print(f"[{time.strftime('%X')}] check_library: not implemented")
    
def check_sailing(profile_name: str):
    print(f"[{time.strftime('%X')}] check_sailing: not implemented")
    
def go_active_farm(profile_name: str):
    print(f"[{time.strftime('%X')}] go_active_farm: not implemented")