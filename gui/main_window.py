import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from PIL import ImageTk, Image

from core.video_loader import VideoLoader
from gui.painter import PainterApp


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Q3 Console Painter')
        self.root.geometry('930x900')
        self.root.minsize(930, 400)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.image_frame = ImageFrame(self.notebook)
        self.notebook.add(self.image_frame, text='Image')

        self.image_frame = VideoFrame(self.notebook)
        self.notebook.add(self.image_frame, text='Video')


class ImageFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # -------------- Toolbar --------------
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Button(toolbar, text='Open', command=self.open_image).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Clear', command=self.clear_image).pack(side=tk.LEFT, padx=3)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        self.var_grid = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text='Grid', variable=self.var_grid, command=self.toggle_grid).pack(side=tk.LEFT, padx=3)

        ttk.Button(toolbar, text='Pixel aspect', command=self.fix_pixel_aspect).pack(side=tk.LEFT, padx=3)

        # -------------- Main Frame --------------
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(main_frame, width=220)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # -------------- Size Frame --------------
        size_box = ttk.LabelFrame(control_frame, text='Image size')
        size_box.pack(fill=tk.X, pady=8)

        self.var_width = tk.IntVar(value=80)
        self.var_height = tk.IntVar(value=40)
        
        size_spins_box = ttk.Frame(size_box, padding=2)
        size_spins_box.pack(fill=tk.X, pady=8)
        ttk.Spinbox(size_spins_box, from_=1, to=100, increment=5 ,textvariable=self.var_width, width=6).pack(side=tk.LEFT)
        ttk.Label(size_spins_box, text='x').pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(size_spins_box, from_=1, to=100, increment=5, textvariable=self.var_height, width=6).pack(side=tk.LEFT)
        
        ttk.Button(size_box, text='Apply', command=self.resize_image).pack(pady=2, fill=tk.X,)
        
        # -------------- Export Frame --------------
        export_box = ttk.LabelFrame(control_frame, text='Export')
        export_box.pack(fill=tk.X, pady=8)
        
        wait_frame = ttk.Frame(export_box)
        wait_frame.pack(fill=tk.X, pady=8)
        
        ttk.Label(wait_frame, text='Wait:').pack(side=tk.LEFT, padx=15)
        self.var_wait = tk.IntVar(value=5)
        ttk.Spinbox(wait_frame, from_=0, to=500, textvariable=self.var_wait, width=6).pack(side=tk.LEFT)
        
        print_method_box = ttk.Frame(export_box)
        print_method_box.pack(fill=tk.X, pady=8)
        self.print_method = tk.StringVar(value='say')
        ttk.Radiobutton(print_method_box, text='say', value='say', variable=self.print_method).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(print_method_box, text='echo', value='echo', variable=self.print_method).pack(side=tk.RIGHT, padx=10)

        ttk.Button(export_box, text='Create CFG', command=self.export_cfg).pack(fill=tk.X, pady=10)
        
        # -------------- Painter --------------
        self.painter = PainterApp(parent=display_frame, width=self.var_width.get(), height=self.var_height.get())
        

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[('Images', '*.jpg *.jpeg *.png *.tga *.bmp')]
        )
        if not path:
            return
        
        file_ext = path.lower().split('.')[-1]
        with_alpha = False

        if file_ext in ('png', 'tga'):
            with_alpha = messagebox.askyesno(
                'Import alpha',
                'Image supports transparency.\nImport with alpha channel?'
            )
            
        loader = self.painter.loader
        if not loader.load_image(path, with_alpha=with_alpha):
            messagebox.showerror('Error', 'Failed to load image')
            return

        loader.resize_image(self.var_width.get(), self.var_height.get())
        self.painter.redraw()
        
        
    def fix_pixel_aspect(self):
        img = self.painter.loader.edited_image
        if img is None:
            return

        w = img.width
        h = img.height

        target_ratio = w / (h * 2)

        canvas = self.painter.canvas
        canvas.update_idletasks()

        current_w = canvas.winfo_width()
        new_h = int(current_w / target_ratio)

        root = self.winfo_toplevel()
        root.update_idletasks()

        frame_w = root.winfo_width() - canvas.winfo_width()
        frame_h = root.winfo_height() - canvas.winfo_height()

        root.geometry(f"{current_w + frame_w}x{new_h + frame_h}")

    
    def toggle_grid(self):
        self.painter.show_grid = self.var_grid.get()
        self.painter.redraw()
    
    
    def resize_image(self):
        self.painter.resize(self.var_width.get(), self.var_height.get())
        

    def clear_image(self):
        self.painter.clear(self.var_width.get(), self.var_height.get())


    def export_cfg(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.cfg',
            filetypes=[('CFG files', '*.cfg')]
        )
        if not path:
            return

        from core.cfg_writer import CFGWriter
        writer = CFGWriter(self.painter.loader.edited_image, self.print_method.get())
        writer.save_cfg(path, wait_time=self.var_wait.get())

        messagebox.showinfo('Done', 'CFG file saved')



class VideoFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.master = parent
        self.loader = VideoLoader()
        self.current_frame = 0
        self.playing = False
        self.tk_frame = None

        # -------- Toolbar --------
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Button(toolbar, text='Open', command=self.open_video).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Clear', command=self.clear_video).pack(side=tk.LEFT, padx=3)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(toolbar, text='Play', command=self.play_video).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text='Pause', command=self.pause_video).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text='Restart', command=self.restart_video).pack(side=tk.LEFT, padx=3)

        # -------- Main area --------
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame, width=220)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # -------- Size box --------
        size_box = ttk.LabelFrame(control_frame, text='Video size')
        size_box.pack(fill=tk.X, pady=8)

        self.var_width = tk.IntVar(value=80)
        self.var_height = tk.IntVar(value=40)

        size_spins = ttk.Frame(size_box)
        size_spins.pack(fill=tk.X, pady=8)

        ttk.Spinbox(size_spins, from_=1, to=100, increment=5, textvariable=self.var_width, width=6).pack(side=tk.LEFT)
        ttk.Label(size_spins, text='x').pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(size_spins, from_=1, to=100, increment=5, textvariable=self.var_height, width=6).pack(side=tk.LEFT)

        ttk.Button(size_box, text='Apply', command=self.resize_video)\
            .pack(fill=tk.X, pady=2)

        # -------- Export box --------
        export_box = ttk.LabelFrame(control_frame, text='Export')
        export_box.pack(fill=tk.X, pady=8)

        wait_frame = ttk.Frame(export_box)
        wait_frame.pack(fill=tk.X, pady=8)

        ttk.Label(wait_frame, text='Wait:').pack(side=tk.LEFT, padx=15)
        self.var_wait = tk.IntVar(value=5)
        ttk.Spinbox(wait_frame, from_=1, to=100, textvariable=self.var_wait, width=6).pack(side=tk.LEFT)

        print_frame = ttk.Frame(export_box)
        print_frame.pack(fill=tk.X, pady=8)

        self.print_method = tk.StringVar(value='say')
        ttk.Radiobutton(print_frame, text='say', value='say', variable=self.print_method).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(print_frame, text='echo', value='echo', variable=self.print_method).pack(side=tk.RIGHT, padx=10)

        ttk.Button(export_box, text='Create PK3', command=self.export_pk3).pack(fill=tk.X, pady=10)

        # -------- Video display --------
        self.video_canvas = tk.Canvas(display_frame, bg='black')
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        
    def open_video(self):
        path = filedialog.askopenfilename(filetypes=[('Videos', '*.mp4')])
        if not path:
            return
        if not self.loader.load_video(path):
            messagebox.showerror('Error', 'Failed to load video')
            return

        self.process_video()
    
    
    def clear_video(self):
        self.playing = False
        self.current_frame = 0
        self.video_canvas.delete('all')
        self.loader.edited_video = []
        self.loader.original_video = []
    
    
    def process_video(self):
        progress_win = tk.Toplevel(self.master)
        progress_win.title('Processing Video')
        x = self.master.winfo_x() + (self.master.winfo_width() - progress_win.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - progress_win.winfo_height()) // 2
        progress_win.geometry(f'300x80+{x}+{y}')
        progress_win.transient(self.master)
        progress_win.grab_set()

        total_frames = self.loader.frame_count
        lbl_progress = ttk.Label(progress_win, text='Processing frames...')
        lbl_progress.pack(pady=10)
        progress = ttk.Progressbar(progress_win, maximum=total_frames, length=250, mode='determinate')
        progress.pack(pady=5)

        def start_process_video():
            progress_gen = self.loader.process_all_frames(self.var_width.get(), self.var_height.get())
            for step in progress_gen:
                progress['value'] = step
                lbl_progress['text'] = f'Processing frames... {step}/{total_frames}'
                progress_win.update_idletasks()

            progress_win.destroy()
            messagebox.showinfo('Done', 'Video processed!')
        
        Thread(target=start_process_video, daemon=True).start()
        
    
    def show_frame(self, idx):        
        frame = self.loader.edited_video[idx]
        canvas_w = self.video_canvas.winfo_width()
        canvas_h = self.video_canvas.winfo_height()
        frame_resized = frame.resize((canvas_w, canvas_h), Image.NEAREST)
        self.tk_frame = ImageTk.PhotoImage(frame_resized)
        self.video_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_frame)
    

    def play_video(self):
        if not self.playing:
            self.playing = True
            self._play_loop()


    def _play_loop(self):
        if not self.playing:
            return

        self.show_frame(self.current_frame)
        self.current_frame += 1
        if self.current_frame >= len(self.loader.edited_video):
            self.current_frame = 0

        fps = self.loader.fps or 30
        self.after(int(1000 / fps), self._play_loop)


    def pause_video(self):
        self.playing = False


    def restart_video(self):
        self.show_frame(0)
        self.playing = False
        self.current_frame = 0
        


    def resize_video(self):
        if self.loader.original_video is None:
            return
        self.process_video()
        
        
    def export_pk3(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.pk3',
            filetypes=[('PK3 files', '*.pk3')]
        )
        if not path:
            return
        
        progress_win = tk.Toplevel(self.master)
        progress_win.title('Creating pk3 file')
        x = self.master.winfo_x() + (self.master.winfo_width() - progress_win.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - progress_win.winfo_height()) // 2
        progress_win.geometry(f'300x80+{x}+{y}')
        progress_win.transient(self.master)
        progress_win.grab_set()

        total_frames = self.loader.frame_count
        lbl_progress = ttk.Label(progress_win, text='Processing frames...')
        lbl_progress.pack(pady=10)
        progress = ttk.Progressbar(progress_win, maximum=total_frames, length=250, mode='determinate')
        progress.pack(pady=5)

        from core.cfg_writer import PK3Writer
        writer = PK3Writer(self.loader.edited_video, self.print_method.get(), self.var_wait.get())
        def start_process_video():
            progress_gen = writer.save_pk3(path)
            for step in progress_gen:
                progress['value'] = step
                lbl_progress['text'] = f'Processing frames... {step}/{total_frames}'
                progress_win.update_idletasks()

            progress_win.destroy()
            messagebox.showinfo('Done', 'PK3 file saved!')
        
        Thread(target=start_process_video, daemon=True).start()