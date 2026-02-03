# IdleonBot

Create a config.json following config_example.json
Put store to chest on last slot on any skill page


Task importance for creation
1) deposit loot every 30 minutes while active farming
2) Automatic hourly clicking for alchemy 
3)

---

## Overlay Locations Maker (auxiliary/locations_maker.py) 🔧

A small GUI tool to create and save screen locations (buttons) for use with the bot.

### Run
- From the project root:
  - python auxiliary/locations_maker.py

### Dependencies
- Requires Pillow for screen capture (ImageGrab). Install with:
  - pip install -r requirements.txt

### Features ✅
- Add a new marker and give it a custom **name** when created.
- Right-side **panel** lists all markers with their name and current screen center coordinates.
- **Rename** and **Delete** markers from the panel.
- **Move** markers by dragging them anywhere on screen; the list and coordinate fields update automatically.
- The panel is **movable** itself: drag the "Buttons" header to reposition it if it's in the way. 🎯
- You can edit a marker's exact coordinates in the panel using the **X/Y** fields and the **Set XY** button.
- When saving, a **Save As** dialog lets you choose the JSON filename; saved JSONs go to `saved_locations/` and the most recent is also written to `saved_locations/last_buttons.json`.
- Saved JSONs now include the panel position under the `panel` key; use the new **Load...** button to load an existing JSON and restore markers and the panel position. 🔁
- Use the **Close** button to exit the overlay without saving if you need to discard changes. ❌

### Notes & Tips 💡
- The saved JSON format includes name, center (x, y) and the RGB color taken at the marker center.
- Panel position persistence and additional shortcuts are not yet implemented; open an issue or request if you'd like persistence added.

---
 