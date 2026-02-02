import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from PIL import ImageTk, Image

from core.image_loader import ImageLoader, PALLETE
from core.video_loader import VideoLoader
from gui.painter import PainterApp


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Q3 Console Painter')
        self.root.geometry('1000x600')

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.image_frame = ImageFrame(self.notebook)
        self.notebook.add(self.image_frame, text='Image')

        self.image_frame = VideoFrame(self.notebook)
        self.notebook.add(self.image_frame, text='Video')


class ImageFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # -------- Import panel (Control frame) --------

        self.var_alpha = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text='Save alpha', variable=self.var_alpha).pack(anchor=tk.W, pady=2)
        ttk.Button(control_frame, text='Open image', command=self.open_image).pack(fill=tk.X, pady=2)

        ttk.Separator(control_frame).pack(fill=tk.X, pady=20)
        
        # -------- Settings panel (Control frame) --------

        ttk.Button(control_frame, text='Clear image', command=self.clear_image).pack(fill=tk.X, pady=2)
        ttk.Label(control_frame, text='Size:').pack(anchor=tk.W, pady=2)

        size_frame = ttk.Frame(control_frame)
        size_frame.pack(fill=tk.X)

        self.var_width = tk.IntVar(value=80)
        self.var_height = tk.IntVar(value=40)

        ttk.Spinbox(size_frame, from_=1, to=100, increment=5,
                    textvariable=self.var_width, width=6).pack(side=tk.LEFT)
        ttk.Label(size_frame, text='x').pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(size_frame, from_=1, to=100, increment=5,
                    textvariable=self.var_height, width=6).pack(side=tk.LEFT)
        
        self.var_grid = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control_frame,
            text='Show grid',
            variable=self.var_grid,
            command=self.toggle_grid
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Button(control_frame, text='Apply', command=self.resize_image).pack(fill=tk.X, pady=2)

        ttk.Separator(control_frame).pack(fill=tk.X, pady=20)
        
        # -------- Export panel (Control frame) --------
        
        ttk.Label(control_frame, text='Wait:').pack(anchor=tk.W)
        self.var_wait = tk.IntVar(value=5)
        ttk.Spinbox(control_frame, from_=0, to=500,
                    textvariable=self.var_wait, width=6).pack(fill=tk.X)

        ttk.Label(control_frame, text='Print method:').pack(anchor=tk.W, pady=(10, 0))
        self.print_method = tk.StringVar(value='say')
        ttk.Radiobutton(control_frame, text='say', value='say',
                        variable=self.print_method).pack(anchor=tk.W)
        ttk.Radiobutton(control_frame, text='echo', value='echo',
                        variable=self.print_method).pack(anchor=tk.W)

        ttk.Button(control_frame, text='Create CFG', command=self.export_cfg).pack(fill=tk.X, pady=10)

        self.painter = PainterApp(
            parent=display_frame,
            width=self.var_width.get(),
            height=self.var_height.get()
        )


    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[('Images', '*.jpg *.jpeg *.png *.tga *.bmp')]
        )
        if not path:
            return

        loader = self.painter.loader
        if not loader.load_image(path, with_alpha=self.var_alpha.get()):
            messagebox.showerror('Error', 'Failed to load image')
            return

        loader.resize_image(self.var_width.get(), self.var_height.get())
        self.painter.redraw()
    
    
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

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # -------- Import panel (Control frame) --------

        ttk.Button(control_frame, text='Open video', command=self.open_video).pack(fill=tk.X, pady=2)
        
        ttk.Separator(control_frame).pack(fill=tk.X, pady=20)
        
        # -------- Video settings panel (Control frame) --------
        
        ttk.Button(control_frame, text='Clear video', command=self.clear_video).pack(fill=tk.X, pady=2)
        ttk.Label(control_frame, text='Size:').pack(anchor=tk.W, pady=2)

        size_frame = ttk.Frame(control_frame)
        size_frame.pack(fill=tk.X)
        self.var_width = tk.IntVar(value=80)
        self.var_height = tk.IntVar(value=40)

        ttk.Spinbox(size_frame, from_=1, to=100, increment=5, textvariable=self.var_width, width=6).pack(side=tk.LEFT, pady=2)
        ttk.Label(size_frame, text='x').pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(size_frame, from_=1, to=100, increment=5, textvariable=self.var_height, width=6).pack(side=tk.LEFT, pady=2)
        
        ttk.Button(control_frame, text='Apply', command=self.resize_video).pack(fill=tk.X, pady=2)

        ttk.Separator(control_frame).pack(fill=tk.X, pady=20)
        
        # -------- Playback panel (Control frame) --------
        
        playback_frame = ttk.Frame(control_frame)
        playback_frame.pack(fill=tk.X)
        
        ttk.Button(playback_frame, text='Play', command=self.play_video, width=5).pack(side=tk.LEFT, fill=tk.X, pady=2)
        ttk.Button(playback_frame, text='Pause', command=self.pause_video, width=5).pack(side=tk.LEFT, fill=tk.X, pady=2)
        ttk.Button(playback_frame, text='Restart', command=self.restart_video, width=5).pack(side=tk.LEFT, fill=tk.X, pady=2)
        
        ttk.Separator(control_frame).pack(fill=tk.X, pady=20)
        
        # -------- Export panel (Control frame) --------
        
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X)

        ttk.Label(export_frame, text='Wait:').pack(fill=tk.X, padx=2)
        self.var_wait = tk.IntVar(value=5)
        ttk.Spinbox(export_frame, from_=1, to=100, textvariable=self.var_wait, width=6).pack(fill=tk.X)

        ttk.Label(export_frame, text='Print method:').pack(fill=tk.X, padx=5)
        
        print_frame = ttk.Frame(control_frame)
        print_frame.pack(fill=tk.X)
        self.print_method = tk.StringVar(value='say') 
        ttk.Radiobutton(print_frame, text='say', value='say', variable=self.print_method).pack(fill=tk.X, pady=2)
        ttk.Radiobutton(print_frame, text='echo', value='echo', variable=self.print_method).pack(fill=tk.X, pady=2)
        
        self.start_cfg_name = ttk.Entry(control_frame)
        self.start_cfg_name.pack(fill=tk.X, pady=2)        
        
        ttk.Button(control_frame, text='Create PK3', command=self.export_pk3).pack(fill=tk.X, pady=2)

        # -------- Video (Display frame) --------
        
        self.video_canvas = tk.Canvas(main_frame, bg='black')
        self.video_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tk_frame = None
        
        
    def open_video(self):
        path = filedialog.askopenfilename(filetypes=[('Videos', '*.mp4')])
        if not path:
            return
        if not self.loader.load_video(path):
            messagebox.showerror('Error', 'Failed to load video')
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
        progress_win.geometry(f"300x80+{x}+{y}")
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
    
    
    def clear_video(self):
        pass
    

    def resize_video(self):
        if self.loader.original_video is None:
            return
        self.process_video()
        
    
    def process_video(self):
        progress_win = tk.Toplevel(self.master)
        progress_win.title('Processing Video')
        x = self.master.winfo_x() + (self.master.winfo_width() - progress_win.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - progress_win.winfo_height()) // 2
        progress_win.geometry(f"300x80+{x}+{y}")
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
        self.playing = True
        self.show_frame(self.current_frame)
        self.current_frame += 1
        if self.current_frame >= len(self.loader.edited_video):
            self.current_frame = 0
        fps = self.loader.fps or 24
        self.after(int(1000 / fps), self.play_video)
        
        
    def pause_video(self):
        self.playing = False

    
    def restart_video(self):
        pass