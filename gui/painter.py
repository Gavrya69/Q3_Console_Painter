import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

from core.image_loader import ImageLoader, PALLETE


class PainterApp:
    def __init__(self, parent, width: int = 60, height: int = 40):
        self.parent = parent
        self.current_color = (0, 0, 0)

        self.loader = ImageLoader(width, height)

        self.canvas_frame = ttk.Frame(self.parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>', self.on_brush)
        self.canvas.bind('<B1-Motion>', self.on_brush)
        self.canvas.bind('<Button-3>', self.on_fill)
        self.canvas.bind('<Configure>', lambda e: self.redraw())

        self.palette_frame = ttk.Frame(self.parent)
        self.palette_frame.pack(fill=tk.X)
        self._create_palette_buttons()

        self.show_grid = False
        self.scale_x = 1
        self.scale_y = 1
        self.tk_image = None
        
        self.redraw()


    def _create_palette_buttons(self):
        self.palette_buttons = {}
        
        btn = tk.Button(
            self.palette_frame,
            text='∅',
            width=2,
            command=lambda: self.set_color(None)
        )
        btn.pack(side=tk.LEFT, padx=1)
        self.palette_buttons[None] = btn
        
        for _, rgb in PALLETE.items():
            btn = tk.Button(
                self.palette_frame,
                bg='#%02x%02x%02x' % rgb,
                width=2,
                command=lambda c=rgb: self.set_color(c)
            )
            btn.pack(side=tk.LEFT, padx=1, pady=1)
            self.palette_buttons[rgb] = btn
            
        self.active_button = None
        self.set_color(self.current_color)


    def _make_checkerboard(self, w, h, size=10):
        img = Image.new('RGB', (w, h), (200, 200, 200))
        d = ImageDraw.Draw(img)

        for y in range(0, h, size):
            for x in range(0, w, size):
                if (x // size + y // size) % 2 == 0:
                    d.rectangle([x, y, x+size, y+size], fill=(240, 240, 240))
        return img
    
    
    def set_color(self, color):
        self.current_color = color

        if self.active_button:
            self.active_button.config(relief=tk.RAISED, bd=2)

        btn = self.palette_buttons.get(color)
        if btn:
            btn.config(relief=tk.SUNKEN, bd=4)
            self.active_button = btn


    def set_image(self, pil_image: Image.Image):
        self.loader.original_image = pil_image.copy()
        self.loader.resize_image(self.loader.width, self.loader.height)
        self.redraw()
        

    def resize(self, width: int, height: int):
        self.loader.resize_image(width, height)
        self.redraw()


    def clear(self, width: int, height: int):
        self.loader = ImageLoader(width, height)
        self.redraw()

    
    def flood_fill(self, start_x, start_y, new_color):
        self.loader.edited_image = self.loader.edited_image.copy()

        img = self.loader.edited_image
        pixels = img.load()

        w, h = img.size
        target_color = pixels[start_x, start_y]

        if target_color == new_color:
            return

        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()

            if x < 0 or y < 0 or x >= w or y >= h:
                continue

            if pixels[x, y] != target_color:
                continue

            pixels[x, y] = new_color

            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))


    def on_brush(self, event):
        img = self.loader.edited_image
        if img is None:
            return

        px = int(event.x / self.scale_x)
        py = int(event.y / self.scale_y)

        if not (0 <= px < self.loader.width and 0 <= py < self.loader.height):
            return

        # цвет
        if self.current_color is None:
            color = (0, 0, 0, 0)
        else:
            color = (*self.current_color, 255)

        self.loader.edited_image = img.copy()

        self.loader.edited_image.putpixel((px, py), color)
        self.redraw()
    
    
    def on_fill(self, event):
        img = self.loader.edited_image
        if img is None:
            return

        px = int(event.x / self.scale_x)
        py = int(event.y / self.scale_y)

        if not (0 <= px < self.loader.width and 0 <= py < self.loader.height):
            return

        if self.current_color is None:
            color = (0, 0, 0, 0)
        else:
            color = (*self.current_color, 255)

        self.loader.edited_image = img.copy()

        self.flood_fill(px, py, color)
        self.redraw()


    def redraw(self):
        img = self.loader.edited_image
        if img is None:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return

        self.scale_x = cw / img.width
        self.scale_y = ch / img.height

        new_size = (int(img.width * self.scale_x), int(img.height * self.scale_y))
        
        checker = self._make_checkerboard(*new_size)
        scaled_img = img.resize(new_size, Image.NEAREST)
        
        composed = checker.convert('RGBA')
        composed.alpha_composite(scaled_img)

        self.tk_image = ImageTk.PhotoImage(composed)

        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        if self.show_grid:
            for x in range(img.width + 1):
                self.canvas.create_line(
                    x * self.scale_x, 0,
                    x * self.scale_x, new_size[1],
                    fill='gray'
                )

            for y in range(img.height + 1):
                self.canvas.create_line(
                    0, y * self.scale_y,
                    new_size[0], y * self.scale_y,
                    fill='gray'
                )
