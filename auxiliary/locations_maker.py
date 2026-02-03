import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json
import os
import time
from PIL import ImageGrab


class DraggableButton:
    def __init__(self, parent, name="Button", x=100, y=100, size=40):
        self.parent = parent
        self.name = name
        self.size = size

        # Use a small Canvas so the button appears circular and transparent.
        # Background color matches parent's transparent color so canvas looks invisible.
        self.canvas_widget = tk.Canvas(parent.canvas, width=self.size, height=self.size,
                                       bg=parent.trans_color, highlightthickness=0)

        # Outer circle (transparent fill by using same color as background)
        pad = 2
        self.canvas_widget.create_oval(pad, pad, self.size - pad, self.size - pad,
                                       outline='white', width=1, fill=parent.trans_color, tags=('oval',))
        # Red center dot to show the exact center
        dot_r = max(3, self.size // 10)
        cx = self.size // 2
        cy = self.size // 2
        self.canvas_widget.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                                       outline='red', fill='red', tags=('dot',))

        # place on parent canvas
        self.canvas_widget.place(x=x, y=y)

        self.offset_x = 0
        self.offset_y = 0

        # Bind events for dragging and renaming
        self.canvas_widget.bind("<ButtonPress-1>", self.on_press)
        self.canvas_widget.bind("<B1-Motion>", self.on_motion)
        self.canvas_widget.bind("<ButtonRelease-1>", self.on_release)
        self.canvas_widget.bind("<Double-Button-1>", self.on_rename)

    def on_press(self, event):
        # record offset inside the widget
        self.offset_x = event.x
        self.offset_y = event.y

    def on_motion(self, event):
        canvas = self.parent.canvas
        # pointer coords on screen relative to canvas root
        rel_x = canvas.winfo_pointerx() - canvas.winfo_rootx() - self.offset_x
        rel_y = canvas.winfo_pointery() - canvas.winfo_rooty() - self.offset_y
        self.canvas_widget.place(x=rel_x, y=rel_y)

    def on_release(self, event):
        # after moving, update the list display in parent
        if hasattr(self.parent, "update_list"):
            try:
                self.parent.update_list()
            except Exception:
                pass

    def on_rename(self, event):
        new = simpledialog.askstring("Rename", "New button name:", initialvalue=self.name)
        if new:
            self.name = new
            if hasattr(self.parent, "update_list"):
                try:
                    self.parent.update_list()
                except Exception:
                    pass

    def set_highlight(self, highlight=True):
        color = 'yellow' if highlight else 'white'
        try:
            self.canvas_widget.itemconfig('oval', outline=color)
        except Exception:
            pass

    def get_state(self):
        # return screen center x,y and name
        fx = self.canvas_widget.winfo_rootx()
        fy = self.canvas_widget.winfo_rooty()
        fw = self.canvas_widget.winfo_width()
        fh = self.canvas_widget.winfo_height()
        center_x = fx + fw // 2
        center_y = fy + fh // 2
        return {"name": self.name, "center": {"x": int(center_x), "y": int(center_y)}}


class OverlayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # Prepare full-screen overlay
        self.root = tk.Tk()
        self.root.title("Overlay")
        self.root.attributes("-topmost", True)
        # remove window chrome
        self.root.overrideredirect(True)
        # transparent background color (Windows supports '-transparentcolor')
        self.trans_color = "#123456"
        self.root.config(bg=self.trans_color)
        self.root.wm_attributes("-transparentcolor", self.trans_color)

        # Get screen size and set geometry
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        # Canvas covers everything and will hold frames
        self.canvas = tk.Canvas(self.root, width=self.screen_w, height=self.screen_h, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # small control buttons
        self.add_btn = tk.Button(self.root, text="+ Add", command=self.add_button)
        self.add_btn.place(x=10, y=10)

        # Saved Locations buttons bottom-left
        btn_h = 36
        self.save_btn = tk.Button(self.root, text="Save...", command=self.save_all)
        self.save_btn.place(x=10, y=self.screen_h - btn_h - 10)
        self.load_btn = tk.Button(self.root, text="Load...", command=self.load_file)
        self.load_btn.place(x=100, y=self.screen_h - btn_h - 10)
        self.close_btn = tk.Button(self.root, text="Close", command=self.close_program)
        self.close_btn.place(x=190, y=self.screen_h - btn_h - 10)

        # list of DraggableButton
        self.items = []

        # Side panel to show buttons and coords
        panel_w = 300
        self.panel_frame = tk.Frame(self.root, width=panel_w, height=self.screen_h, bg='#222')
        self.panel_frame.place(x=self.screen_w - panel_w - 10, y=10)

        header = tk.Label(self.panel_frame, text="Buttons", bg='#222', fg='white', font=('Arial', 12, 'bold'), cursor='fleur')
        header.pack(anchor='nw', padx=8, pady=(8, 0))
        # make panel draggable by header
        header.bind('<ButtonPress-1>', self.on_panel_press)
        header.bind('<B1-Motion>', self.on_panel_motion)

        # coordinate editor (shows selected button center coords and allows setting them)
        coord_frame = tk.Frame(self.panel_frame, bg='#222')
        coord_frame.pack(anchor='nw', padx=8, pady=(6, 0), fill='x')
        tk.Label(coord_frame, text='X', bg='#222', fg='white').grid(row=0, column=0)
        self.x_entry = tk.Entry(coord_frame, width=8)
        self.x_entry.grid(row=0, column=1, padx=(4,10))
        tk.Label(coord_frame, text='Y', bg='#222', fg='white').grid(row=0, column=2)
        self.y_entry = tk.Entry(coord_frame, width=8)
        self.y_entry.grid(row=0, column=3, padx=(4,10))
        self.apply_coords_btn = tk.Button(coord_frame, text='Set XY', command=self.apply_coords)
        self.apply_coords_btn.grid(row=0, column=4)

        self.listbox = tk.Listbox(self.panel_frame, width=40, height=26, bg='#333', fg='white', activestyle='none', selectbackground='blue')
        self.listbox.pack(padx=8, pady=8, anchor='nw', fill='y', expand=True)

        self.listbox.bind('<<ListboxSelect>>', self.on_list_select)
        self.listbox.bind('<Double-Button-1>', self.on_list_double)

        btn_frame = tk.Frame(self.panel_frame, bg='#222')
        btn_frame.pack(anchor='s', fill='x', padx=8, pady=8)

        self.rename_btn = tk.Button(btn_frame, text="Rename", command=self.rename_selected)
        self.rename_btn.pack(side='left', padx=4)
        self.delete_btn = tk.Button(btn_frame, text="Delete", command=self.delete_selected)
        self.delete_btn.pack(side='left', padx=4)

        # if user presses Escape, exit overlay
        self.root.bind('<Escape>', lambda e: self.root.destroy())

    def add_button(self):
        default = f"Btn{len(self.items)+1}"
        name = simpledialog.askstring("Button name", "Enter button name:", initialvalue=default)
        # If user cancelled (name is None), do not create a button
        if name is None:
            return
        # If user submitted an empty string, fall back to default
        if name.strip() == "":
            name = default
        # place near center
        x = self.screen_w // 2 - 40
        y = self.screen_h // 2 - 20 + (len(self.items) * 10)
        item = DraggableButton(self, name, x, y)
        self.items.append(item)
        try:
            self.update_list()
            idx = len(self.items) - 1
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        except Exception:
            pass

    def save_all(self):
        if not self.items:
            messagebox.showinfo("Saved Locations", "No buttons to save.")
            return

        # Grab full screen once
        img = ImageGrab.grab()

        out = []
        for it in self.items:
            state = it.get_state()
            cx = state["center"]["x"]
            cy = state["center"]["y"]
            try:
                rgb = img.getpixel((cx, cy))
            except Exception:
                rgb = (0, 0, 0)
            out.append({"name": state["name"], "center": state["center"], "rgb": list(rgb)})

        # ensure folder exists
        folder = os.path.join(os.path.dirname(__file__), "saved_locations")
        os.makedirs(folder, exist_ok=True)

        # default filename suggestion
        ts = int(time.time())
        suggested = os.path.join(folder, f"buttons_{ts}.json")
        file_path = filedialog.asksaveasfilename(initialdir=folder, initialfile=os.path.basename(suggested),
                                                 defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            # user cancelled
            return

        # capture panel position if available
        try:
            pi = self.panel_frame.place_info()
            panel_meta = {"x": int(float(pi.get("x", 0))), "y": int(float(pi.get("y", 0)))}
        except Exception:
            panel_meta = {"x": 0, "y": 0}

        data = {"buttons": out, "panel": panel_meta}

        file_recent = os.path.join(folder, "last_buttons.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(file_recent, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo("Saved Locations", f"Saved {len(out)} buttons to:\n{file_path}")

    def update_list(self):
        # refresh listbox with current button names and coords
        try:
            self.listbox.delete(0, 'end')
            for it in self.items:
                s = it.get_state()
                cx = s['center']['x']
                cy = s['center']['y']
                self.listbox.insert('end', f"{s['name']}  —  ({cx},{cy})")
            # clear highlights and reapply selection highlight
            self.clear_highlights()
            sel = self.listbox.curselection()
            if sel:
                idx = sel[0]
                if 0 <= idx < len(self.items):
                    self.items[idx].set_highlight(True)
                    try:
                        self.populate_coords(idx)
                    except Exception:
                        pass
        except Exception:
            pass

    def on_list_select(self, event):
        sel = self.listbox.curselection()
        self.clear_highlights()
        if sel:
            idx = sel[0]
            if 0 <= idx < len(self.items):
                self.items[idx].set_highlight(True)
                try:
                    self.populate_coords(idx)
                except Exception:
                    pass
        else:
            try:
                # clear entries when nothing selected
                self.x_entry.delete(0, 'end')
                self.y_entry.delete(0, 'end')
            except Exception:
                pass

    def on_list_double(self, event):
        sel = self.listbox.curselection()
        if sel:
            self.rename_selected()

    def rename_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Rename", "No item selected.")
            return
        idx = sel[0]
        it = self.items[idx]
        new = simpledialog.askstring("Rename", "New button name:", initialvalue=it.name)
        if new:
            it.name = new
            self.update_list()

    def delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete", "No item selected.")
            return
        idx = sel[0]
        it = self.items.pop(idx)
        try:
            it.canvas_widget.destroy()
        except Exception:
            pass
        self.update_list()
        try:
            self.x_entry.delete(0, 'end')
            self.y_entry.delete(0, 'end')
        except Exception:
            pass

    def apply_coords(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Set XY", "No item selected.")
            return
        idx = sel[0]
        it = self.items[idx]
        try:
            nx = int(self.x_entry.get())
            ny = int(self.y_entry.get())
        except Exception:
            messagebox.showinfo("Set XY", "Invalid X/Y values. Please enter integers.")
            return
        # convert screen center coords to canvas place coords (top-left)
        try:
            canvas_rootx = self.canvas.winfo_rootx()
            canvas_rooty = self.canvas.winfo_rooty()
            place_x = nx - (it.size // 2) - canvas_rootx
            place_y = ny - (it.size // 2) - canvas_rooty
            it.canvas_widget.place(x=place_x, y=place_y)
            # refresh list to show updated coords
            self.update_list()
            # reselect same item
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        except Exception:
            messagebox.showinfo("Set XY", "Failed to set coordinates.")

    def populate_coords(self, idx):
        if not (0 <= idx < len(self.items)):
            return
        s = self.items[idx].get_state()
        cx = s['center']['x']
        cy = s['center']['y']
        try:
            self.x_entry.delete(0, 'end')
            self.x_entry.insert(0, str(cx))
            self.y_entry.delete(0, 'end')
            self.y_entry.insert(0, str(cy))
        except Exception:
            pass

    def center_to_place(self, cx, cy, size=40):
        # convert screen center coordinates to canvas placement (top-left) coords
        try:
            canvas_rootx = self.canvas.winfo_rootx()
            canvas_rooty = self.canvas.winfo_rooty()
            place_x = int(cx - (size // 2) - canvas_rootx)
            place_y = int(cy - (size // 2) - canvas_rooty)
            return place_x, place_y
        except Exception:
            return cx, cy

    def clear_items(self):
        for it in self.items:
            try:
                it.canvas_widget.destroy()
            except Exception:
                pass
        self.items = []
        try:
            self.update_list()
        except Exception:
            pass

    def load_file(self):
        folder = os.path.join(os.path.dirname(__file__), "saved_locations")
        file_path = filedialog.askopenfilename(initialdir=folder, title="Open saved buttons", filetypes=[("JSON files", "*.json"), ("All files", "*")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showinfo("Load", f"Failed to load file:\n{e}")
            return
        # support either a direct list or our dictionary format
        buttons = []
        panel_meta = None
        if isinstance(data, dict):
            buttons = data.get("buttons") or data.get("list") or []
            panel_meta = data.get("panel") or data.get("_meta", {}).get("panel")
        elif isinstance(data, list):
            buttons = data
        else:
            messagebox.showinfo("Load", "Invalid file format.")
            return

        if not buttons:
            messagebox.showinfo("Load", "No buttons found in file.")

        # clear existing items
        self.clear_items()

        for b in buttons:
            try:
                if not isinstance(b, dict):
                    continue
                name = b.get("name") or f"Btn{len(self.items)+1}"
                center = b.get("center") or {}
                cx = int(center.get("x", self.screen_w // 2))
                cy = int(center.get("y", self.screen_h // 2))
                px, py = self.center_to_place(cx, cy)
                item = DraggableButton(self, name, px, py)
                self.items.append(item)
            except Exception:
                pass

        # ensure geometry is updated so widget positions are available
        try:
            self.root.update_idletasks()
        except Exception:
            pass

        self.update_list()

        # select first item and populate coords so X/Y show correctly
        if self.items:
            try:
                self.listbox.selection_clear(0, 'end')
                self.listbox.selection_set(0)
                self.listbox.see(0)
                self.populate_coords(0)
            except Exception:
                pass

        # restore panel position if included
        if panel_meta and isinstance(panel_meta, dict):
            try:
                px = int(panel_meta.get("x", 0))
                py = int(panel_meta.get("y", 0))
                px = max(0, min(px, self.screen_w - 50))
                py = max(0, min(py, self.screen_h - 50))
                self.panel_frame.place(x=px, y=py)
            except Exception:
                pass

        messagebox.showinfo("Load", f"Loaded {len(self.items)} buttons from:\n{file_path}")

    def on_panel_press(self, event):
        # remember offset inside header
        self._panel_drag_offset_x = event.x
        self._panel_drag_offset_y = event.y

    def on_panel_motion(self, event):
        try:
            rel_x = self.root.winfo_pointerx() - self.root.winfo_rootx() - self._panel_drag_offset_x
            rel_y = self.root.winfo_pointery() - self.root.winfo_rooty() - self._panel_drag_offset_y
            # clamp to screen
            rel_x = max(0, min(rel_x, self.screen_w - 50))
            rel_y = max(0, min(rel_y, self.screen_h - 50))
            self.panel_frame.place(x=rel_x, y=rel_y)
        except Exception:
            pass

    def clear_highlights(self):
        for it in self.items:
            try:
                it.set_highlight(False)
            except Exception:
                pass

    def close_program(self):
        # confirm and close without saving
        try:
            sure = messagebox.askyesno("Close", "Close without saving? Unsaved changes will be lost.")
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
        # add a default button so user sees something (without prompting)
        if not self.items:
            x = self.screen_w // 2 - 40
            y = self.screen_h // 2 - 20
            item = DraggableButton(self, "Btn1", x, y)
            self.items.append(item)
            try:
                self.update_list()
            except Exception:
                pass
        self.root.mainloop()


if __name__ == "__main__":
    app = OverlayApp()
    app.run()
