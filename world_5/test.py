"""
Realtime template match tester for 'sprinkler' within 'gaming_region'.

Behavior:
- Loads saved_images/sprinkler.png and saved_regions/gaming_region.json
- Every ~0.25s screenshots the region and runs template matching (requires OpenCV)
- If found, draws a circle at the detection center on a transparent overlay and shows "FOUND"
- If not found, shows "NOT FOUND" in the overlay

Run with:
    python test.py

Notes:
- If OpenCV is not installed, the script will show instructions to install it.
"""
import os
import json
import time
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image, ImageTk

# Optional: require cv2 for template matching
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    CV2_AVAILABLE = False


def load_region(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    r = data.get('region')
    if not r:
        raise ValueError('No region found in JSON')
    return int(r['x']), int(r['y']), int(r['w']), int(r['h'])


class RealtimeFinder:
    def __init__(self, needle_path, region_path, poll_interval=0.25, threshold=0.75):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.needle_path = needle_path
        self.region_path = region_path
        self.poll_interval = int(poll_interval * 1000)
        self.threshold = threshold

        if not os.path.exists(self.needle_path):
            raise FileNotFoundError(self.needle_path)
        if not os.path.exists(self.region_path):
            raise FileNotFoundError(self.region_path)

        # load multiple needle images (as BGR numpy for cv2)
        # support sprinkler, log, squirrel(s) as requested
        self.needles = []  # list of dicts: {name, path, w, h, cv}
        probe_names = ['sprinkler.png', 'log.png', 'squirrel.png', 'squirrel_2.png', 'shovel.png']
        for fname in probe_names:
            try:
                path = os.path.join(self.repo_root, 'saved_images', 'gaming', fname)
                if not os.path.exists(path):
                    # file missing; skip but record missing
                    self.needles.append({'name': os.path.splitext(fname)[0], 'path': path, 'missing': True})
                    continue
                pil = Image.open(path).convert('RGBA')
                w, h = pil.size
                entry = {'name': os.path.splitext(fname)[0], 'path': path, 'w': w, 'h': h, 'missing': False}
                if CV2_AVAILABLE:
                    arr = np.array(pil)
                    if arr.shape[2] == 4:
                        arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                    else:
                        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    entry['cv'] = arr
                else:
                    entry['cv'] = None
                self.needles.append(entry)
            except Exception as e:
                # record as missing but continue
                self.needles.append({'name': os.path.splitext(fname)[0], 'path': path, 'missing': True, 'error': str(e)})

        # mapping for per-needle overlays
        self._circles = {}
        self._labels = {}

        self.region = load_region(self.region_path)
        rx, ry, rw, rh = self.region

        # record which needles are present or missing; status will be displayed after canvas is created
        present = [e['name'] for e in self.needles if not e.get('missing')]
        missing = [e['name'] for e in self.needles if e.get('missing')]
        self._initial_present = present
        self._initial_missing = missing

        # Setup overlay UI
        self.root = tk.Tk()
        self.root.title('Realtime Finder - sprinkler')
        self.root.attributes('-topmost', True)
        # no window chrome
        self.root.overrideredirect(True)
        self.trans_color = '#112233'
        self.root.config(bg=self.trans_color)
        try:
            self.root.wm_attributes('-transparentcolor', self.trans_color)
        except Exception:
            pass

        # fullscreen transparent canvas
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        self.canvas = tk.Canvas(self.root, width=self.screen_w, height=self.screen_h, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # status and close button
        self.status_text = self.canvas.create_text(20, 20, anchor='nw', fill='white', text='Initializing...', font=('Arial', 14, 'bold'))
        self.close_btn = tk.Button(self.root, text='Close', command=self.close)
        # place the close button on top-left (not transparent)
        self.close_window = self.canvas.create_window(120, 10, anchor='nw', window=self.close_btn)

        # apply initial status (moved here so canvas exists)
        try:
            if getattr(self, '_initial_missing', None):
                self.canvas.itemconfig(self.status_text, text=f'Missing images: {", ".join(self._initial_missing)}')
            else:
                present = getattr(self, '_initial_present', []) or []
                if present:
                    self.canvas.itemconfig(self.status_text, text=f'Ready: monitoring {", ".join(present)}')
        except Exception:
            pass

        # circle id
        self._circle = None

        # if cv2 missing, show message and stop
        if not CV2_AVAILABLE:
            self.canvas.itemconfig(self.status_text, text='OpenCV not installed. Install with: python -m pip install opencv-python')
            return

        # start periodic search
        self._running = True
        self._schedule_search()

    def _schedule_search(self):
        if not self._running:
            return
        self.search_once()
        self.root.after(self.poll_interval, self._schedule_search)

    def search_once(self):
        rx, ry, rw, rh = self.region
        try:
            screen = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
        except Exception as e:
            self.canvas.itemconfig(self.status_text, text=f'Capture failed: {e}')
            return
        # convert to BGR cv image
        img_np = np.array(screen.convert('RGB'))
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        found_any = []
        # colors per needle
        color_map = {'sprinkler': 'lime', 'log': 'orange', 'squirrel': 'cyan', 'squirrel_2': 'cyan', 'shovel': 'white'}
        for entry in self.needles:
            name = entry.get('name')
            if entry.get('missing') or entry.get('cv') is None:
                # ensure any existing overlay for missing needle is removed
                if name in self._circles:
                    try:
                        self.canvas.delete(self._circles.pop(name))
                    except Exception:
                        pass
                if name in self._labels:
                    try:
                        self.canvas.delete(self._labels.pop(name))
                    except Exception:
                        pass
                continue
            try:
                tpl = entry['cv']
                # multi-scale matching to tolerate scale differences
                best_val = -1.0
                best_loc = None
                best_size = (entry['w'], entry['h'])
                # scales to try (smaller to larger)
                scales = [0.8, 0.9, 1.0, 1.1, 1.2]
                for scale in scales:
                    new_w = max(1, int(entry['w'] * scale))
                    new_h = max(1, int(entry['h'] * scale))
                    # skip if template doesn't fit the search image
                    if new_w > img_cv.shape[1] or new_h > img_cv.shape[0]:
                        continue
                    try:
                        if scale == 1.0:
                            tpl_scaled = tpl
                        else:
                            tpl_scaled = cv2.resize(tpl, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
                    except Exception:
                        continue
                    try:
                        res = cv2.matchTemplate(img_cv, tpl_scaled, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    except Exception:
                        continue
                    if max_val > best_val:
                        best_val = max_val
                        best_loc = max_loc
                        best_size = (new_w, new_h)
                # per-needle threshold fallback
                per_thresholds = {'sprinkler': 0.1, 'log': 0.1, 'squirrel': 0.1, 'squirrel_2': 0.1, 'shovel': 0.1}
                thresh = per_thresholds.get(name, self.threshold)
                if best_val >= thresh and best_loc is not None:
                    top_left = best_loc
                    center_x = rx + top_left[0] + best_size[0] // 2
                    center_y = ry + top_left[1] + best_size[1] // 2
                    found_any.append((name, center_x, center_y, best_val))
                    self._update_overlay_for(name, center_x, center_y, best_val, color_map.get(name, 'lime'))
                else:
                    # remove any stale overlay for this needle
                    if name in self._circles:
                        try:
                            self.canvas.delete(self._circles.pop(name))
                        except Exception:
                            pass
                    if name in self._labels:
                        try:
                            self.canvas.delete(self._labels.pop(name))
                        except Exception:
                            pass
            except Exception as e:
                # per-template error: remove overlays and report in status
                if name in self._circles:
                    try:
                        self.canvas.delete(self._circles.pop(name))
                    except Exception:
                        pass
                if name in self._labels:
                    try:
                        self.canvas.delete(self._labels.pop(name))
                    except Exception:
                        pass
                self.canvas.itemconfig(self.status_text, text=f'Error matching {name}: {e}')
                return

        if found_any:
            s = ', '.join([f"{n}({score:.2f})" for (n, x, y, score) in found_any])
            self.canvas.itemconfig(self.status_text, text=f'FOUND: {s}')
        else:
            self._show_not_found()

    def _update_overlay_for(self, name, x, y, score, color='lime'):
        # create or update circle + label for the given named needle
        r = 24
        x1 = x - r
        y1 = y - r
        x2 = x + r
        y2 = y + r
        # circle
        if name in self._circles and self._circles[name]:
            try:
                self.canvas.coords(self._circles[name], x1, y1, x2, y2)
            except Exception:
                try:
                    self.canvas.delete(self._circles[name])
                except Exception:
                    pass
                self._circles[name] = self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=3)
        else:
            self._circles[name] = self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=3)
        # label above circle
        label_text = f"{name} {score:.2f}"
        lx = x1
        ly = y1 - 18
        if name in self._labels and self._labels[name]:
            try:
                self.canvas.coords(self._labels[name], lx, ly)
                self.canvas.itemconfig(self._labels[name], text=label_text)
            except Exception:
                try:
                    self.canvas.delete(self._labels[name])
                except Exception:
                    pass
                self._labels[name] = self.canvas.create_text(lx, ly, anchor='nw', fill=color, text=label_text, font=('Arial', 10, 'bold'))
        else:
            self._labels[name] = self.canvas.create_text(lx, ly, anchor='nw', fill=color, text=label_text, font=('Arial', 10, 'bold'))

    def _show_not_found(self):
        # remove all overlays
        for k in list(self._circles.keys()):
            try:
                self.canvas.delete(self._circles.pop(k))
            except Exception:
                pass
        for k in list(self._labels.keys()):
            try:
                self.canvas.delete(self._labels.pop(k))
            except Exception:
                pass
        self.canvas.itemconfig(self.status_text, text='NOT FOUND')

    def close(self):
        self._running = False
        try:
            self.root.destroy()
        except Exception:
            try:
                self.root.quit()
            except Exception:
                pass

    def run(self):
        if not CV2_AVAILABLE:
            messagebox.showinfo('Missing dependency', 'OpenCV (opencv-python) is required for template matching.\nInstall with: python -m pip install opencv-python')
            return
        self.root.mainloop()


if __name__ == '__main__':
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    needle = os.path.join(base, 'saved_images', 'gaming', 'sprinkler.png')
    region = os.path.join(base, 'saved_regions', 'gaming_region.json')
    app = RealtimeFinder(needle, region, poll_interval=0.25, threshold=0.75)
    app.run()
