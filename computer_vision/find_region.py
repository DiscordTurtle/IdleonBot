import tkinter as tk
import pyautogui

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.3)  # Semi-transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black')
        self.canvas.pack(fill="both", expand=True)
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.box_rect = None

        self.root.bind('<Button-1>', self.on_click)
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.step = 0

    def on_click(self, event):
        # Mouse coordinates relative to whole screen
        screen_x = self.root.winfo_pointerx()
        screen_y = self.root.winfo_pointery()

        if self.step == 0:
            self.start_x, self.start_y = screen_x, screen_y
            self.box_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=3
            )
            self.step = 1
            self.canvas.bind('<Motion>', self.on_motion)
        elif self.step == 1:
            self.end_x, self.end_y = screen_x, screen_y
            # Finalize rectangle
            self.canvas.unbind('<Motion>')
            left   = min(self.start_x, self.end_x)
            top    = min(self.start_y, self.end_y)
            right  = max(self.start_x, self.end_x)
            bottom = max(self.start_y, self.end_y)
            box = (left, top, right - left, bottom - top)
            print("Selected region coords (left, top, width, height):", box)
            self.root.destroy()

    def on_motion(self, event):
        # Live update of rectangle
        screen_x = self.root.winfo_pointerx()
        screen_y = self.root.winfo_pointery()
        self.canvas.coords(self.box_rect, self.start_x, self.start_y, screen_x, screen_y)

    def run(self):
        print("Click and drag: First click sets top-left, release at bottom-right.")
        print("Press ESC to cancel.")
        self.root.mainloop()

if __name__ == '__main__':
    selector = RegionSelector()
    selector.run()
    print("Done.")