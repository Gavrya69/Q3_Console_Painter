import os
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image


PALLETE = {
    'a': (255, 0, 0),
    'b': (255, 92, 0),
    'c': (255, 149, 0),
    'd': (255, 200, 0),
    'e': (255, 255, 0),
    'f': (200, 255, 0),
    'g': (149, 255, 0),
    'h': (92, 255, 0),
    'i': (0, 255, 0),
    'j': (0, 255, 92),
    'k': (0, 255, 149),
    'l': (0, 255, 200),
    'm': (0, 255, 255),
    'n': (0, 200, 255),
    'o': (0, 149, 255),
    'p': (0, 92, 255),
    'q': (0, 0, 255),
    'r': (92, 0, 255),
    's': (149, 0, 255),
    't': (200, 0, 255),
    'u': (255, 0, 255),
    'v': (255, 0, 200),
    'w': (255, 0, 149),
    'x': (255, 0, 92),
    'y': (255, 255, 255),
    'z': (172, 172, 255),
    '9': (149, 149, 149),
    '0': (0, 0, 0),
}


class ImageLoader:
    def __init__(self, width: int = 60, height: int = 40):
        self.width = width
        self.height = height
        
        self.original_image = Image.new('RGBA', size=(width, height), color=(255, 255, 255, 0))
        self.edited_image = None
        
        self.quantize_image()

    
    def load_image(self, path: str, with_alpha: bool = False) -> bool:
        if not os.path.exists(path):
            return False
        try:
            img = Image.open(path).convert('RGBA')

            if with_alpha:
                np_img = np.array(img)
                alpha = np_img[:, :, 3]
                alpha[alpha < 250] = 0
                alpha[alpha >= 250] = 255
                np_img[:, :, 3] = alpha
                img = Image.fromarray(np_img, 'RGBA')
            else:
                bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(bg, img)

            self.original_image = img
            self.width, self.height = img.size
            self.edited_image = img.copy()
            self.quantize_image()
            
            return True
        except Exception as e:
            print(f'Error loading image: {e}')
            return False


    def resize_image(self, width: int, height: int) -> None:
        self.edited_image = self.original_image.copy().resize((width, height), Image.Resampling.NEAREST)
        self.width, self.height = self.edited_image.size
        self.quantize_image()
    

    def quantize_image(self) -> None:
        if self.edited_image is None:
            if self.original_image is None:
                raise ValueError('Image not loaded')
            self.edited_image = self.original_image.copy()

        img = self.edited_image.convert('RGBA')
        img_np = np.array(img)

        rgb = img_np[:, :, :3]
        alpha = img_np[:, :, 3]

        keys = list(PALLETE.keys())
        colors = np.array([PALLETE[k] for k in keys], dtype=np.uint8)

        h, w, _ = rgb.shape
        pixels = rgb.reshape(-1, 3)

        tree = cKDTree(colors)
        _, indices = tree.query(pixels)
        new_rgb = colors[indices].reshape((h, w, 3))

        result = np.dstack((new_rgb, alpha))
        self.edited_image = Image.fromarray(result, 'RGBA')
