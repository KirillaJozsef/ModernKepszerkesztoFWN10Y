"""
Modern, Tkinter + CustomTkinter + OpenCV képszerkesztő
Verzió: 3.13 (kód célja Python 3.13 alatt futtatni)

Főbb funkciók :
 - Szép, modern GUI a customtkinter-rel
 - Valós idejű (folyamatos) előnézet: forgatás, flip, fényerő/kontraszt, blur, filter kiválasztó
 - Forgatás csúszkával (-180..180)
 - Flip-ek csúszkával (0/1) — egyszerű, gyors toggle-élmény csúszkával
 - Resize (beviteli mezők) és Crop (drag-to-select)
 - Filterek legördülőből: None, Grayscale, Blur, Canny, Emboss, Sepia
 - Undo/Redo és hibamentes Reset 
 - Mentés Unicode útvonalakkal (Windows-friendly imencode+tofile)

Telepítés:
    pip install customtkinter opencv-python pillow numpy

Futtatás:
    python tk_cv_image_editor.py
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageFilter
import cv2
import numpy as np
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernImageEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Modern Képszerkesztő Készítette: Kirilla József, Neptunkód: FWN10Y")
        self.geometry("1200x760")

        # Image data (BGR numpy)
        self.original = None    # original image (immutable)
        self.img = None         # current image (BGR)
        self.preview = None     # preview image (PIL)
        self.history = []
        self.redo_stack = []

        # Crop
        self.cropping = False
        self.crop_start = None
        self.crop_box = None

        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self):
        # Left control panel
        left = ctk.CTkFrame(self, width=320, corner_radius=8)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=12, pady=12)

        ctk.CTkLabel(left, text="Fájlok", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(6,4))
        btn_open = ctk.CTkButton(left, text="Megnyitás", command=self.open_image)
        btn_save = ctk.CTkButton(left, text="Mentés", command=self.save_image)
        btn_open.pack(fill='x', pady=4)
        btn_save.pack(fill='x', pady=4)

        # Undo/Redo/Reset
        ur = ctk.CTkFrame(left)
        ur.pack(fill='x', pady=6)
        ctk.CTkButton(ur, text="Visszavonás (Undo)", command=self.undo).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ctk.CTkButton(ur, text="Mégis (Redo)", command=self.redo).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        ctk.CTkButton(left, text="Reset (eredeti)", command=self.reset_image).pack(fill='x', pady=6)

        # Transform controls
        ctk.CTkLabel(left, text="Transzformok", font=ctk.CTkFont(weight='bold')).pack(anchor='w', pady=(8,2))
        # Rotation slider
        self.angle_var = tk.DoubleVar(value=0.0)
        ctk.CTkLabel(left, text="Forgatás (°)").pack(anchor='w')
        self.angle_slider = ctk.CTkSlider(left, from_=-180, to=180, number_of_steps=360, command=self._on_transform_change, variable=self.angle_var)
        self.angle_slider.pack(fill='x', pady=2)

        # Flip sliders (0 or 1)
        self.fliph_var = tk.IntVar(value=0)
        self.flipv_var = tk.IntVar(value=0)
        ctk.CTkLabel(left, text="Flip H (0/1)").pack(anchor='w')
        self.fliph_slider = ctk.CTkSlider(left, from_=0, to=1, number_of_steps=1, command=self._on_transform_change, variable=self.fliph_var)
        self.fliph_slider.pack(fill='x', pady=2)
        ctk.CTkLabel(left, text="Flip V (0/1)").pack(anchor='w')
        self.flipv_slider = ctk.CTkSlider(left, from_=0, to=1, number_of_steps=1, command=self._on_transform_change, variable=self.flipv_var)
        self.flipv_slider.pack(fill='x', pady=2)

        # Resize
        ctk.CTkLabel(left, text="Átméretezés (px)").pack(anchor='w', pady=(8,0))
        rframe = ctk.CTkFrame(left)
        rframe.pack(fill='x', pady=4)
        self.w_entry = ctk.CTkEntry(rframe, placeholder_text="Szélesség")
        self.h_entry = ctk.CTkEntry(rframe, placeholder_text="Magasság")
        self.w_entry.grid(row=0, column=0, padx=4, pady=2, sticky='ew')
        self.h_entry.grid(row=1, column=0, padx=4, pady=2, sticky='ew')
        ctk.CTkButton(left, text="Átméretez", command=self.resize_image).pack(fill='x', pady=4)

        # Filters and adjustments
        ctk.CTkLabel(left, text="Effektek & Állítások", font=ctk.CTkFont(weight='bold')).pack(anchor='w', pady=(8,0))

        # Brightness / Contrast
        self.brightness_var = tk.DoubleVar(value=0.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        ctk.CTkLabel(left, text="Fényerő").pack(anchor='w')
        ctk.CTkSlider(left, from_=-100, to=100, variable=self.brightness_var, number_of_steps=200, command=self._on_transform_change).pack(fill='x')
        ctk.CTkLabel(left, text="Kontraszt").pack(anchor='w')
        ctk.CTkSlider(left, from_=0.1, to=3.0, variable=self.contrast_var, number_of_steps=58, command=self._on_transform_change).pack(fill='x')

        # Blur slider
        self.blur_var = tk.IntVar(value=0)
        ctk.CTkLabel(left, text="Blur (Gauss) - kernel radius").pack(anchor='w')
        ctk.CTkSlider(left, from_=0, to=25, variable=self.blur_var, number_of_steps=25, command=self._on_transform_change).pack(fill='x')

        # Filters dropdown
        ctk.CTkLabel(left, text="Filterek").pack(anchor='w', pady=(6,0))
        self.filter_var = tk.StringVar(value='None')
        self.filter_menu = ctk.CTkOptionMenu(left, values=['None', 'Grayscale', 'Blur', 'Canny', 'Emboss', 'Sepia'], command=lambda v: self._on_transform_change())
        self.filter_menu.pack(fill='x', pady=4)

        # Crop button
        ctk.CTkButton(left, text="Crop (kijelöléssel)", command=self.toggle_crop).pack(fill='x', pady=8)

        # Apply / Commit
        ctk.CTkButton(left, text="Commit (mentés history-be)", command=self.commit).pack(fill='x', pady=8)

        # Right: canvas area
        right = ctk.CTkFrame(self, corner_radius=8)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        # top toolbar info
        topbar = ctk.CTkFrame(right)
        topbar.pack(fill='x')
        self.info_label = ctk.CTkLabel(topbar, text="Nincs kép betöltve")
        self.info_label.pack(side='left', padx=8, pady=6)

        # Canvas
        self.canvas = tk.Canvas(right, bg='#1f2937')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas.bind('<ButtonPress-1>', self._on_mouse_down)
        self.canvas.bind('<B1-Motion>', self._on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)

        # keep reference to PhotoImage
        self._photo = None

    def _bind_shortcuts(self):
        self.bind('<Control-o>', lambda e: self.open_image())
        self.bind('<Control-s>', lambda e: self.save_image())
        self.bind('<Control-z>', lambda e: self.undo())
        self.bind('<Control-y>', lambda e: self.redo())

    # ---------------- File I/O ----------------
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[('Images','*.png;*.jpg;*.jpeg;*.bmp;*.tiff'),('All','*.*')])
        if not path:
            return
        bgr = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if bgr is None:
            messagebox.showerror('Hiba','Nem sikerült megnyitni a képet')
            return
        if len(bgr.shape) == 2:
            bgr = cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
        self.original = bgr.copy()
        self.img = bgr.copy()
        self.history = [self.original.copy()]
        self.redo_stack.clear()
        self._update_info()
        self._refresh_preview()

    def save_image(self):
        if self.img is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png'),('JPEG','*.jpg'),('BMP','*.bmp')])
        if not path:
            return
        ext = path.split('.')[-1]
        success, buf = cv2.imencode('.' + ext, self.img)
        if success:
            buf.tofile(path)
        else:
            messagebox.showerror('Hiba','Mentés nem sikerült')

    # ---------------- History ----------------
    def commit(self):
        if self.img is None:
            return
        # push current displayed state (apply current transforms to img permanently)
        new = self._get_transformed(self.img, preview=False)
        self.img = new
        # push to history but avoid duplicate identical tail
        if not self.history or not np.array_equal(self.history[-1], self.img):
            self.history.append(self.img.copy())
        self.redo_stack.clear()
        self._refresh_preview()

    def undo(self):
        if len(self.history) <= 1:
            return
        last = self.history.pop()
        self.redo_stack.append(last)
        self.img = self.history[-1].copy()
        # reset sliders to neutral so preview corresponds to actual image
        self._reset_preview_controls()
        self._refresh_preview()

    def redo(self):
        if not self.redo_stack:
            return
        img = self.redo_stack.pop()
        self.history.append(img.copy())
        self.img = img.copy()
        self._reset_preview_controls()
        self._refresh_preview()

    def reset_image(self):
        if self.original is None:
            return
        # Proper reset: set history to only the original (no repeated push)
        self.img = self.original.copy()
        self.history = [self.original.copy()]
        self.redo_stack.clear()
        self._reset_preview_controls()
        self._refresh_preview()

    # ---------------- Transforms & Filters (preview/live) ----------------
    def _on_transform_change(self, _=None):
        # live preview: compute transformed preview from current image
        if self.img is None:
            return
        self._refresh_preview()

    def _reset_preview_controls(self):
        # neutralize sliders
        self.angle_var.set(0.0)
        self.fliph_var.set(0)
        self.flipv_var.set(0)
        self.brightness_var.set(0.0)
        self.contrast_var.set(1.0)
        self.blur_var.set(0)
        self.filter_menu.set('None')

    def _get_transformed(self, base_bgr, preview=True):
        # take base_bgr (numpy BGR) and apply current control values
        img = base_bgr.copy()
        # rotate
        angle = float(self.angle_var.get())
        if abs(angle) > 0.0001:
            # rotate around center
            (h, w) = img.shape[:2]
            M = cv2.getRotationMatrix2D((w/2, h/2), -angle, 1.0)
            cos = abs(M[0,0]); sin = abs(M[0,1])
            # compute new bounding dims
            nW = int((h * sin) + (w * cos))
            nH = int((h * cos) + (w * sin))
            M[0,2] += (nW / 2) - w/2
            M[1,2] += (nH / 2) - h/2
            img = cv2.warpAffine(img, M, (nW, nH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        # flips
        fh = int(round(self.fliph_var.get()))
        fv = int(round(self.flipv_var.get()))
        if fh and fv:
            img = cv2.flip(img, -1)
        elif fh:
            img = cv2.flip(img, 1)
        elif fv:
            img = cv2.flip(img, 0)

        # brightness/contrast
        alpha = float(self.contrast_var.get())
        beta = float(self.brightness_var.get())
        img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

        # blur
        k = int(self.blur_var.get())
        if k > 0:
            k = k if k % 2 == 1 else k + 1
            img = cv2.GaussianBlur(img, (k,k), 0)

        # filters dropdown
        fil = self.filter_menu.get()
        if fil == 'Grayscale':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif fil == 'Canny':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif fil == 'Emboss':
            kernel = np.array([[ -2,-1,0],[-1,1,1],[0,1,2]])
            img = cv2.filter2D(img, -1, kernel) + 128
        elif fil == 'Sepia':
            img = cv2.transform(img, np.matrix([[0.393,0.769,0.189],[0.349,0.686,0.168],[0.272,0.534,0.131]]))
            img = np.clip(img, 0, 255).astype(np.uint8)
        elif fil == 'Blur':
            img = cv2.GaussianBlur(img, (11,11), 0)

        return img

    # ---------------- Display ----------------
    def _refresh_preview(self):
        # produce preview from self.img with current sliders
        if self.img is None:
            self.canvas.delete('all')
            self.info_label.configure(text='Nincs kép betöltve')
            return
        transformed = self._get_transformed(self.img, preview=True)
        # convert to PIL image
        rgb = cv2.cvtColor(transformed, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)

        # store for crop mapping
        self.preview = pil

        # fit to canvas
        c_w = self.canvas.winfo_width() or 800
        c_h = self.canvas.winfo_height() or 600
        pil_ratio = pil.width / pil.height
        canvas_ratio = c_w / c_h
        if pil.width > c_w or pil.height > c_h:
            if pil_ratio > canvas_ratio:
                new_w = c_w
                new_h = int(c_w / pil_ratio)
            else:
                new_h = c_h
                new_w = int(c_h * pil_ratio)
            disp = pil.resize((new_w, new_h), Image.LANCZOS)
        else:
            disp = pil.copy()
            new_w, new_h = disp.size

        self._disp_w, self._disp_h = disp.size
        self._disp_off_x = (c_w - self._disp_w) // 2
        self._disp_off_y = (c_h - self._disp_h) // 2

        self._photo = ImageTk.PhotoImage(disp)
        self.canvas.delete('all')
        self.canvas.create_image(c_w//2, c_h//2, image=self._photo)

        # if crop box exists, draw
        if self.crop_box:
            x0, y0, x1, y1 = self.crop_box
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='yellow', width=2, tags='crop')

        self._update_info()

    def _update_info(self):
        htxt = f"Kép: {self.img.shape[1]}x{self.img.shape[0]}" if self.img is not None else "Nincs kép"
        self.info_label.configure(text=htxt)

    # ---------------- Resize / Crop UI ----------------
    def resize_image(self):
        if self.img is None:
            return
        try:
            w = int(self.w_entry.get())
            h = int(self.h_entry.get())
            if w <=0 or h <=0:
                raise ValueError
        except Exception:
            messagebox.showwarning('Érvénytelen','Adj meg helyes szélesség és magasság egész számokat')
            return
        resized = cv2.resize(self.img, (w,h), interpolation=cv2.INTER_AREA)
        self.img = resized
        self.history.append(self.img.copy())
        self.redo_stack.clear()
        self._reset_preview_controls()
        self._refresh_preview()

    def toggle_crop(self):
        if self.img is None:
            return
        self.cropping = not self.cropping
        if self.cropping:
            messagebox.showinfo('Crop','Jelöld ki a területet a képen (húzd az egérrel).')
        else:
            self.crop_box = None
            self._refresh_preview()

    def _on_mouse_down(self, event):
        if not self.cropping:
            return
        self.crop_start = (event.x, event.y)

    def _on_mouse_move(self, event):
        if not self.cropping or not self.crop_start:
            return
        x0, y0 = self.crop_start
        x1, y1 = event.x, event.y
        self.crop_box = (min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1))
        self._refresh_preview()

    def _on_mouse_up(self, event):
        if not self.cropping or not self.crop_start:
            return
        self.cropping = False
        # apply crop
        if not self.crop_box:
            return
        x0, y0, x1, y1 = self.crop_box
        # map displayed coords to original preview image coords
        dx0 = max(x0 - self._disp_off_x, 0)
        dy0 = max(y0 - self._disp_off_y, 0)
        dx1 = max(min(x1 - self._disp_off_x, self._disp_w), 0)
        dy1 = max(min(y1 - self._disp_off_y, self._disp_h), 0)
        if dx1 - dx0 <= 1 or dy1 - dy0 <= 1:
            messagebox.showwarning('Crop', 'Kivágás túl kicsi')
            self.crop_box = None
            self._refresh_preview()
            return
        # map to preview (transformed) full-size image
        scale_x = self.preview.width / self._disp_w
        scale_y = self.preview.height / self._disp_h
        px0 = int(dx0 * scale_x)
        py0 = int(dy0 * scale_y)
        px1 = int(dx1 * scale_x)
        py1 = int(dy1 * scale_y)

        # we applied transforms on top of self.img to get preview; to crop original image consistently,
        # we'll compute transformed full image then crop that result and set as new base image
        transformed_full = self._get_transformed(self.img, preview=False)
        h, w = transformed_full.shape[:2]
        # adjust if indexes go out of bounds
        px0 = np.clip(px0, 0, w-1); px1 = np.clip(px1, 0, w)
        py0 = np.clip(py0, 0, h-1); py1 = np.clip(py1, 0, h)
        cropped = transformed_full[py0:py1, px0:px1].copy()
        if cropped.size == 0:
            messagebox.showwarning('Crop','Hiba a kivágás során')
            self.crop_box = None
            self._refresh_preview()
            return
        self.img = cropped
        self.history.append(self.img.copy())
        self.redo_stack.clear()
        self.crop_box = None
        self._reset_preview_controls()
        self._refresh_preview()

    # ---------------- Helpers ----------------
    def _on_closing(self):
        self.destroy()

if __name__ == '__main__':
    app = ModernImageEditor()
    app.protocol('WM_DELETE_WINDOW', app._on_closing)
    app.mainloop()
