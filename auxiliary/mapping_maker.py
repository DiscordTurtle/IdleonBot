"""
Simple Mapping Maker UI

Purpose:
- Load available needle images from `saved_images/gaming/` (PNG files)
- Let user add named regions (x,y,w,h) or import regions JSON
- Select multiple needles and multiple regions and create a mapping
- Save/load mapping collections as JSON files

Run: python auxiliary/mapping_maker.py
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk


class MappingMakerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mapping Maker")
        self.root.geometry("900x600")

        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.saved_images_dir = os.path.join(self.repo_root, 'saved_images', 'gaming')
        os.makedirs(self.saved_images_dir, exist_ok=True)
        self.saved_mappings_dir = os.path.join(self.repo_root, 'saved_mappings')
        os.makedirs(self.saved_mappings_dir, exist_ok=True)

        # Left: needles
        left = tk.Frame(self.root)
        left.pack(side='left', fill='y', padx=6, pady=6)
        tk.Label(left, text='Needles (multi-select)').pack()
        self.needles_lb = tk.Listbox(left, selectmode='extended', width=40, height=25)
        self.needles_lb.pack()
        btn_f = tk.Frame(left)
        btn_f.pack(fill='x')
        tk.Button(btn_f, text='Refresh', command=self.refresh_needles).pack(side='left')
        tk.Button(btn_f, text='Preview', command=self.preview_selected_needle).pack(side='left')

        # Mid: regions
        mid = tk.Frame(self.root)
        mid.pack(side='left', fill='y', padx=6, pady=6)
        tk.Label(mid, text='Regions (multi-select)').pack()
        self.regions_lb = tk.Listbox(mid, selectmode='extended', width=40, height=20)
        self.regions_lb.pack()
        rbtn_f = tk.Frame(mid)
        rbtn_f.pack(fill='x')
        tk.Button(rbtn_f, text='Add Region', command=self.add_region).pack(side='left')
        tk.Button(rbtn_f, text='Import Regions', command=self.import_regions).pack(side='left')
        tk.Button(rbtn_f, text='Remove', command=self.remove_region).pack(side='left')

        tk.Label(mid, text='Region Preview (coords)').pack(pady=(8,0))
        self.region_preview = tk.Label(mid, text='', bg='#111', fg='white', width=35, height=4, anchor='nw', justify='left')
        self.region_preview.pack(pady=(4,0))

        # Right: mappings
        right = tk.Frame(self.root)
        right.pack(side='left', fill='both', expand=True, padx=6, pady=6)
        tk.Label(right, text='Mappings').pack()
        self.map_lb = tk.Listbox(right, width=50, height=18)
        self.map_lb.pack(fill='both', expand=True)
        mbtn_f = tk.Frame(right)
        mbtn_f.pack(fill='x')
        tk.Button(mbtn_f, text='Create Mapping', command=self.create_mapping).pack(side='left')
        tk.Button(mbtn_f, text='Delete Mapping', command=self.delete_mapping).pack(side='left')
        tk.Button(mbtn_f, text='Save Mappings', command=self.save_mappings).pack(side='left')
        tk.Button(mbtn_f, text='Load Mappings', command=self.load_mappings).pack(side='left')

        # Preview pane for needle image
        self.preview_top = tk.Toplevel(self.root)
        self.preview_top.title('Needle Preview')
        self.preview_top.geometry('360x240')
        self.preview_label = tk.Label(self.preview_top)
        self.preview_label.pack(fill='both', expand=True)

        # Internal state
        self.regions = []  # list of {'name':..., 'x':..,'y':..,'w':..,'h':..}
        self.mappings = []  # list of {'name':..., 'needles':[paths], 'regions':[region dicts]}

        self.refresh_needles()
        self.update_regions_list()
        self.update_mappings_list()

        # listbox bindings
        self.regions_lb.bind('<<ListboxSelect>>', self.on_region_select)

    def refresh_needles(self):
        self.needles_lb.delete(0, 'end')
        files = sorted([f for f in os.listdir(self.saved_images_dir) if f.lower().endswith('.png')])
        for f in files:
            self.needles_lb.insert('end', f)

    def preview_selected_needle(self):
        sel = self.needles_lb.curselection()
        if not sel:
            messagebox.showinfo('Preview', 'Select a needle image first.')
            return
        fname = self.needles_lb.get(sel[0])
        path = os.path.join(self.saved_images_dir, fname)
        try:
            im = Image.open(path)
            im.thumbnail((360, 240), Image.LANCZOS)
            self._preview_img = ImageTk.PhotoImage(im)
            self.preview_label.config(image=self._preview_img)
        except Exception as e:
            messagebox.showinfo('Preview', f'Failed to load image: {e}')

    def add_region(self):
        name = simpledialog.askstring('Region name', 'Enter name for region (optional):')
        coords = simpledialog.askstring('Region coords', 'Enter x,y,w,h (integers):')
        if not coords:
            return
        try:
            parts = [int(p.strip()) for p in coords.split(',')]
            if len(parts) != 4:
                raise ValueError('Expected 4 integers')
            r = {'name': name or f'Region_{len(self.regions)+1}', 'x': parts[0], 'y': parts[1], 'w': parts[2], 'h': parts[3]}
            self.regions.append(r)
            self.update_regions_list()
        except Exception as e:
            messagebox.showinfo('Add Region', f'Invalid coords: {e}')

    def import_regions(self):
        p = filedialog.askopenfilename(initialdir=self.saved_images_dir, filetypes=[('JSON files','*.json'),('All files','*')])
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showinfo('Import', f'Failed to open: {e}')
            return
        # data may be {'mappings':[...]} or list of regions
        imported = []
        if isinstance(data, dict) and 'regions' in data:
            imported = data['regions']
        elif isinstance(data, list):
            imported = data
        else:
            messagebox.showinfo('Import', 'JSON format not recognized (expected list of regions or {"regions": [...]})')
            return
        count = 0
        for r in imported:
            try:
                if all(k in r for k in ('x','y','w','h')):
                    name = r.get('name') or f'Region_{len(self.regions)+1}'
                    self.regions.append({'name': name, 'x': int(r['x']), 'y': int(r['y']), 'w': int(r['w']), 'h': int(r['h'])})
                    count += 1
            except Exception:
                pass
        self.update_regions_list()
        messagebox.showinfo('Import', f'Imported {count} regions')

    def remove_region(self):
        sel = list(self.regions_lb.curselection())
        if not sel:
            messagebox.showinfo('Remove', 'Select region(s) to remove')
            return
        for i in reversed(sel):
            try:
                self.regions.pop(i)
            except Exception:
                pass
        self.update_regions_list()

    def on_region_select(self, event=None):
        sel = self.regions_lb.curselection()
        if not sel:
            self.region_preview.config(text='')
            return
        idx = sel[0]
        r = self.regions[idx]
        self.region_preview.config(text=f"{r.get('name')}\n{r.get('x')},{r.get('y')},{r.get('w')},{r.get('h')}")

    def create_mapping(self):
        nsel = self.needles_lb.curselection()
        rsel = self.regions_lb.curselection()
        if not nsel or not rsel:
            messagebox.showinfo('Create Mapping', 'Select at least one needle and one region')
            return
        needles = [self.needles_lb.get(i) for i in nsel]
        # store relative paths
        needles = [os.path.relpath(os.path.join(self.saved_images_dir, n), self.repo_root) for n in needles]
        regions = [self.regions[i] for i in rsel]
        name = simpledialog.askstring('Mapping name', 'Enter mapping name:', initialvalue=f'Map_{len(self.mappings)+1}')
        if not name:
            return
        m = {'name': name, 'needles': needles, 'regions': regions}
        self.mappings.append(m)
        self.update_mappings_list()

    def delete_mapping(self):
        sel = self.map_lb.curselection()
        if not sel:
            messagebox.showinfo('Delete', 'Select mapping to delete')
            return
        for i in reversed(sel):
            try:
                self.mappings.pop(i)
            except Exception:
                pass
        self.update_mappings_list()

    def save_mappings(self):
        if not self.mappings:
            messagebox.showinfo('Save', 'No mappings to save')
            return
        default = os.path.join(self.saved_mappings_dir, 'mappings.json')
        p = filedialog.asksaveasfilename(initialdir=self.saved_mappings_dir, initialfile=os.path.basename(default), defaultextension='.json')
        if not p:
            return
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump({'mappings': self.mappings}, f, indent=2)
            messagebox.showinfo('Save', f'Saved {len(self.mappings)} mappings to {p}')
        except Exception as e:
            messagebox.showinfo('Save', f'Failed to save: {e}')

    def load_mappings(self):
        p = filedialog.askopenfilename(initialdir=self.saved_mappings_dir, filetypes=[('JSON','*.json'),('All files','*')])
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showinfo('Load', f'Failed to open: {e}')
            return
        loaded = data.get('mappings') if isinstance(data, dict) else data
        if not isinstance(loaded, list):
            messagebox.showinfo('Load', 'Invalid mappings file')
            return
        self.mappings = loaded
        self.update_mappings_list()
        messagebox.showinfo('Load', f'Loaded {len(self.mappings)} mappings')

    def update_regions_list(self):
        self.regions_lb.delete(0, 'end')
        for r in self.regions:
            self.regions_lb.insert('end', f"{r.get('name')}  —  ({r.get('x')},{r.get('y')},{r.get('w')},{r.get('h')})")

    def update_mappings_list(self):
        self.map_lb.delete(0, 'end')
        for m in self.mappings:
            self.map_lb.insert('end', f"{m.get('name')}  —  {len(m.get('needles',[]))} needles / {len(m.get('regions',[]))} regions")

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = MappingMakerApp()
    app.run()
