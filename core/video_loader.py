import cv2
from PIL import Image

from core.image_loader import ImageLoader


class VideoLoader:
    def __init__(self):
        self.original_video: cv2.VideoCapture | None = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        
        self.edited_video: list[Image.Image] = []

        self.image_loader = ImageLoader()


    def load_video(self, path: str) -> bool:
        self.original_video = cv2.VideoCapture(path)
        if not self.original_video.isOpened():
            return False

        self.frame_count = int(self.original_video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.original_video.get(cv2.CAP_PROP_FPS)
        self.width = int(self.original_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.original_video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.edited_video.clear()
        return True


    def process_all_frames(self, width: int, height: int):
        if self.original_video is None:
            return

        self.edited_video.clear()
        self.original_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.total_frames = int(self.original_video.get(cv2.CAP_PROP_FRAME_COUNT))

        for i in range(self.total_frames):
            ret, frame = self.original_video.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)

            self.image_loader.original_image = pil_frame
            self.image_loader.resize_image(width, height)
            self.image_loader.quantize_image()

            self.edited_video.append(self.image_loader.edited_image.copy())
            
            yield i + 1