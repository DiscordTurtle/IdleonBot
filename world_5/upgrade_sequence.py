import json
import os
import time

import pyautogui


def load_locations(path):
	if not os.path.exists(path):
		raise FileNotFoundError(path)
	with open(path, 'r', encoding='utf-8') as file:
		data = json.load(file)

	if isinstance(data, dict):
		entries = data.get('buttons') or data.get('list') or []
	elif isinstance(data, list):
		entries = data
	else:
		raise ValueError('Unsupported saved locations format')

	mapping = {}
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		name = entry.get('name')
		center = entry.get('center') or {}

		if name and 'x' in center and 'y' in center:
			mapping[name] = {'x': int(center['x']), 'y': int(center['y'])}
		elif name and 'x' in entry and 'y' in entry:
			mapping[name] = {'x': int(entry['x']), 'y': int(entry['y'])}

	return mapping


def click_button(buttons, name):
	location = buttons.get(name)
	if not location:
		raise KeyError(f"Button '{name}' not found in saved locations")
	pyautogui.click(location['x'], location['y'])


def upgrade_garden():
	base = os.path.dirname(__file__)
	repo_root = os.path.abspath(os.path.join(base, '..'))
	locations_path = os.path.join(repo_root, 'saved_locations', 'gaming.json')
	buttons = load_locations(locations_path)

	pyautogui.FAILSAFE = False
	pyautogui.PAUSE = 0.01

	upgrades_name = 'updates' if 'updates' in buttons else 'Upgrades'

	click_button(buttons, upgrades_name)
	time.sleep(1)

	click_button(buttons, 'bits_value')
	click_button(buttons, 'bits_value')
	time.sleep(1)

	click_button(buttons, 'bits_speed')
	click_button(buttons, 'bits_speed')

	time.sleep(1)

	click_button(buttons, 'close_upgrades')
	click_button(buttons, 'close_upgrades')


if __name__ == '__main__':
	time.sleep(1.5)
	upgrade_garden()
