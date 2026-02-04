"""
Simple overlay tool to capture needles and regions.

Features:
- Click-and-drag on-screen to create a rectangle (needle or region)
- Captured needle images are saved to `saved_images/gaming/` as PNG
- Captured regions can be saved to `saved_regions/` as JSON files
- Shows a preview of the last captured needle and displays last region coords

Run as a script: python auxiliary/needle_region_maker.py
"""
import os
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import ImageGrab, Image, ImageTk

# optional global mouse capture (allows starting drag anywhere on screen)
try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except Exception:
    mouse = None
    PYNPUT_AVAILABLE = False


class NeedleRegionMaker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # overlay
        self.root = tk.Tk()
        self.root.title("Needle & Region Maker")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.trans_color = "#112233"
        self.root.config(bg=self.trans_color)
        try:
            self.root.wm_attributes("-transparentcolor", self.trans_color)
        except Exception:
            pass

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        self.canvas = tk.Canvas(self.root, width=self.screen_w, height=self.screen_h,
                                bg=self.trans_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # controls
        btn_y = 10
        self.capture_needle_btn = tk.Button(self.root, text="Capture Needle", command=self.start_capture_needle)
        self.capture_needle_btn.place(x=10, y=btn_y)
        self.capture_region_btn = tk.Button(self.root, text="Capture Region", command=self.start_capture_region)
        self.capture_region_btn.place(x=140, y=btn_y)
        self.save_region_btn = tk.Button(self.root, text="Save Region", command=self.save_region)
        self.save_region_btn.place(x=300, y=btn_y)
        self.close_btn = tk.Button(self.root, text="Close", command=self.close)
        self.close_btn.place(x=400, y=btn_y)

        # side preview
        panel_w = 360
        self.panel_frame = tk.Frame(self.root, width=panel_w, height=self.screen_h, bg='#222')
        self.panel_frame.place(x=self.screen_w - panel_w - 10, y=10)
        tk.Label(self.panel_frame, text='Last Needle', bg='#222', fg='white').pack(anchor='nw', padx=8, pady=(8, 0))
        self.needle_preview = tk.Label(self.panel_frame, bg='#111')
        self.needle_preview.pack(padx=8, pady=8)
        tk.Label(self.panel_frame, text='Last Region (x,y,w,h)', bg='#222', fg='white').pack(anchor='nw', padx=8)
        self.region_label = tk.Label(self.panel_frame, text='', bg='#222', fg='white')
        self.region_label.pack(anchor='nw', padx=8)

        # status
        self.status_label = tk.Label(self.root, text='Ready', bg=self.trans_color, fg='white')
        self.status_label.place(x=10, y=40)

        # state
        self.mode = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.last_needle_path = None
        self.last_region = None

        # folders
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.saved_images_dir = os.path.join(self.repo_root, 'saved_images', 'gaming')
        self.saved_regions_dir = os.path.join(self.repo_root, 'saved_regions')
        os.makedirs(self.saved_images_dir, exist_ok=True)
        os.makedirs(self.saved_regions_dir, exist_ok=True)

        # global mouse listener state
        self._mouse_listener = None
        self._dragging = False

        # bindings
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<ButtonPress-3>', self.cancel_capture)
        self.root.bind('<ButtonPress-1>', self._on_root_press)
        self.root.bind('<B1-Motion>', self._on_root_drag)
        self.root.bind('<ButtonRelease-1>', self._on_root_release)
        self.root.bind('<ButtonPress-3>', self.cancel_capture)

    # capture controls
    def start_capture_needle(self):
        self.mode = 'needle'
        if PYNPUT_AVAILABLE:
            self.status('Listening globally for click-drag to capture needle (left-drag). Right-click to cancel.')
            self._start_global_mouse_listener()
        else:
            self.status('Drag to select the needle image region (left-drag). Right-click to cancel.')

    def start_capture_region(self):
        self.mode = 'region'
        if PYNPUT_AVAILABLE:
            self.status('Listening globally for click-drag to capture region (left-drag). Right-click to cancel.')
            self._start_global_mouse_listener()
        else:
            self.status('Drag to select the region to search in (left-drag). Right-click to cancel.')

    def cancel_capture(self, event=None):
        try:
            self._stop_global_mouse_listener()
        except Exception:
            pass
        self.mode = None
        if self.current_rect:
            try:
                self.canvas.delete(self.current_rect)
            except Exception:
                pass
            self.current_rect = None
        self.status('Capture cancelled')

    def on_press(self, event):
        if not self.mode:
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            try:
                self.canvas.delete(self.current_rect)
            except Exception:
                pass
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                         outline='yellow', width=2)

    def on_drag(self, event):
        if not self.mode or not self.current_rect:
            return
        x1, y1 = (self.start_x, self.start_y)
        x2, y2 = (event.x, event.y)
        self.canvas.coords(self.current_rect, x1, y1, x2, y2)

    def on_release(self, event):
        if not self.mode or not self.current_rect:
            return
        x1, y1 = (self.start_x, self.start_y)
        x2, y2 = (event.x, event.y)
        minx = min(x1, x2)
        miny = min(y1, y2)
        maxx = max(x1, x2)
        maxy = max(y1, y2)
        screen_x = self.canvas.winfo_rootx() + minx
        screen_y = self.canvas.winfo_rooty() + miny
        screen_x2 = self.canvas.winfo_rootx() + maxx
        screen_y2 = self.canvas.winfo_rooty() + maxy
        w = max(1, screen_x2 - screen_x)
        h = max(1, screen_y2 - screen_y)
        bbox = (screen_x, screen_y, screen_x + w, screen_y + h)

        try:
            img = ImageGrab.grab(bbox=bbox)
        except Exception as e:
            self.status(f'Capture failed: {e}')
            self.mode = None
            try:
                self.canvas.delete(self.current_rect)
            except Exception:
                pass
            self.current_rect = None
            return

        ts = int(time.time())
        if self.mode == 'needle':
            default_name = f'needle_{ts}.png'
            path = filedialog.asksaveasfilename(title='Save needle image as', initialdir=self.saved_images_dir,
                                                initialfile=default_name, defaultextension='.png', filetypes=[('PNG', '*.png')])
            if not path:
                self.status('Needle save cancelled')
            else:
                try:
                    img.save(path)
                except Exception as e:
                    self.status(f'Failed to save needle: {e}')
                else:
                    try:
                        rel = os.path.relpath(path, self.repo_root)
                    except Exception:
                        rel = path
                    self.last_needle_path = rel
                    try:
                        img2 = img.convert('RGBA')
                        self._needle_tk = ImageTk.PhotoImage(img2.resize((min(300, img2.width), min(200, img2.height)), Image.LANCZOS))
                        self.needle_preview.config(image=self._needle_tk, text='')
                    except Exception:
                        try:
                            self.needle_preview.config(image='', text='(preview failed)')
                        except Exception:
                            pass
                    self.status(f'Needle saved: {rel}')
        else:  # region
            self.last_region = {'x': int(screen_x), 'y': int(screen_y), 'w': int(w), 'h': int(h)}
            self.region_label.config(text=f"{self.last_region['x']},{self.last_region['y']},{self.last_region['w']},{self.last_region['h']}")
            self.status(f'Region set: {self.last_region}')

        try:
            self._stop_global_mouse_listener()
        except Exception:
            pass
        self.mode = None
        try:
            self.canvas.delete(self.current_rect)
        except Exception:
            pass
        self.current_rect = None

    # root bindings forwarding
    def _on_root_press(self, event):
        if not self.mode:
            return
        cx = event.x_root - self.canvas.winfo_rootx()
        cy = event.y_root - self.canvas.winfo_rooty()
        fake = type('E', (), {'x': int(cx), 'y': int(cy)})
        self.on_press(fake)

    def _on_root_drag(self, event):
        if not self.mode:
            return
        cx = event.x_root - self.canvas.winfo_rootx()
        cy = event.y_root - self.canvas.winfo_rooty()
        fake = type('E', (), {'x': int(cx), 'y': int(cy)})
        self.on_drag(fake)

    def _on_root_release(self, event):
        if not self.mode:
            return
        cx = event.x_root - self.canvas.winfo_rootx()
        cy = event.y_root - self.canvas.winfo_rooty()
        fake = type('E', (), {'x': int(cx), 'y': int(cy)})
        self.on_release(fake)

    # global listener
    def _start_global_mouse_listener(self):
        if not PYNPUT_AVAILABLE:
            return
        if self._mouse_listener:
            return
        self._dragging = False
        try:
            self._mouse_listener = mouse.Listener(on_move=self._on_mouse_move, on_click=self._on_mouse_click)
            self._mouse_listener.start()
            self.status('Listening globally for clicks (left-drag anywhere). Right-click to cancel.')
        except Exception as e:
            self.status(f'Global listener failed: {e}')

    def _stop_global_mouse_listener(self):
        if not PYNPUT_AVAILABLE:
            return
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None
        self._dragging = False

    def _on_mouse_click(self, x, y, button, pressed):
        try:
            from pynput.mouse import Button
        except Exception:
            return
        if button == Button.left:
            if pressed and not self._dragging:
                self._dragging = True
                self.root.after(0, lambda: self._on_root_press_with_coords(x, y))
            elif not pressed and self._dragging:
                self._dragging = False
                self.root.after(0, lambda: self._on_root_release_with_coords(x, y))
                self.root.after(0, self._stop_global_mouse_listener)
        elif button == Button.right and pressed:
            self.root.after(0, self.cancel_capture)
            self.root.after(0, self._stop_global_mouse_listener)

    def _on_mouse_move(self, x, y):
        if not self._dragging:
            return
        self.root.after(0, lambda: self._on_root_drag_with_coords(x, y))

    def _on_root_press_with_coords(self, x_root, y_root):
        fake = type('E', (), {'x_root': x_root, 'y_root': y_root})
        self._on_root_press(fake)

    def _on_root_drag_with_coords(self, x_root, y_root):
        fake = type('E', (), {'x_root': x_root, 'y_root': y_root})
        self._on_root_drag(fake)

    def _on_root_release_with_coords(self, x_root, y_root):
        fake = type('E', (), {'x_root': x_root, 'y_root': y_root})
        self._on_root_release(fake)

    def save_region(self):
        if not self.last_region:
            messagebox.showinfo('Save Region', 'No region to save. Capture a region first.')
            return
        default = f"region_{int(time.time())}.json"
        path = filedialog.asksaveasfilename(title='Save region as', initialdir=self.saved_regions_dir,
                                            initialfile=default, defaultextension='.json', filetypes=[('JSON','*.json')])
        if not path:
            self.status('Save region cancelled')
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'region': self.last_region}, f, indent=2)
            self.status(f'Saved region to {path}')
        except Exception as e:
            self.status(f'Failed to save region: {e}')

    def status(self, text):
        try:
            self.status_label.config(text=text)
        except Exception:
            pass

    def close(self):
        try:
            sure = messagebox.askyesno('Close', 'Close without saving?')
        except Exception:
            sure = True
        if sure:
            try:
                self.root.destroy()
            except Exception:
                try:
                    self.root.quit()
                except Exception:
                    pass

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = NeedleRegionMaker()
    app.run()
