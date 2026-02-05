import os
import numpy as np
import zipfile
from scipy.spatial import cKDTree

from core.image_loader import PALLETE


OUTPATH = './temp'


class CFGWriter:
    def __init__(self, image, print_method='say'):
        if image is None:
            raise ValueError('Image is None')
        self.image = image
        self.print_method = print_method
        
        
    def save_cfg(self, output_path: str = OUTPATH, wait_time: int = 6, fps: int = None, next_frame: str = None):
        keys = list(PALLETE.keys())
        colors = np.array([PALLETE[k] for k in keys], dtype=np.uint8)

        img_np = np.array(self.image.convert('RGBA'))
        h, w, _ = img_np.shape
        
        rgb_pixels = img_np[:, :, :3].reshape(-1, 3)
        alpha = img_np[:, :, 3].reshape(-1)
        
        tree = cKDTree(colors)
        _, indices = tree.query(rgb_pixels)

        char_map = []
        for i, a in enumerate(alpha):
            if a == 0:
                char_map.append(' ')
            else:
                char_map.append(keys[indices[i]])

        char_map = np.array(char_map).reshape((h, w))
        
        lines = []
        for y in range(h):
            line = f'{self.print_method} "'
            last_char = None
            for x in range(w):
                char = char_map[y][x]
                if char == ' ':
                    line += ' '
                elif last_char != char:
                    line += f'^{char}'
                    last_char = char
                else:
                    line += ''
            line += '"'
            lines.append(line)
            if wait_time:
                lines.append(f'wait {wait_time}')
        
        # for video
        if fps:
            lines.append(f'wait {fps}')
        if next_frame is not None:
            lines.append(f'exec {next_frame}')

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
            
            
class PK3Writer:
    def __init__(self, frames: list, print_method='say', fps=6):
        self.frames = frames
        self.print_method = print_method
        self.fps = fps
        
        
    def save_pk3(self, output_path: str):
        os.makedirs(OUTPATH, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        frame_files = []

        for idx, frame in enumerate(self.frames, start=1):
            frame_name = f'{base_name}_frame{idx}.cfg'
            frame_path = os.path.join(OUTPATH, frame_name)

            next_frame = f'{base_name}_frame{idx+1}.cfg'
            if idx >= len(self.frames):
                next_frame = None                 
            
            frame_cfg = CFGWriter(image=frame, print_method=self.print_method)
            frame_cfg.save_cfg(output_path=frame_path, wait_time=0, fps=self.fps, next_frame=next_frame)
            frame_files.append(frame_path)
            
            yield idx + 1
            
            

        # Start cfg
        start_cfg_name = f'start_{base_name}.cfg'
        start_cfg_path = os.path.join(OUTPATH, start_cfg_name)
        with open(start_cfg_path, 'w') as f:
            f.write(f'exec {base_name}_frame1.cfg\n')
        frame_files.append(start_cfg_path)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as pk3:
            for file_path in frame_files:
                pk3.write(file_path, os.path.basename(file_path))