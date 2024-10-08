import numpy as np
import cv2
import matplotlib.cm as cm
import torch

### must be four characters long (include a space at the end if you have to)
### OG vid_format: str = "mp4v"
vid_format: str = "FFV1"


def read_video_frames(video_path, process_length, target_fps, max_res):
    # a simple function to read video frames
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # round the height and width to the nearest multiple of 64
    height = round(original_height / 64) * 64
    width = round(original_width / 64) * 64

    # resize the video if the height or width is larger than max_res
    if max(height, width) > max_res:
        scale = max_res / max(original_height, original_width)
        height = round(original_height * scale / 64) * 64
        width = round(original_width * scale / 64) * 64

    if target_fps < 0:
        target_fps = original_fps

    stride = max(round(original_fps / target_fps), 1)

    frames = []
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or (process_length > 0 and frame_count >= process_length):
            break
        if frame_count % stride == 0:
            frame = cv2.resize(frame, (width, height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frames.append(frame.astype("float32") / 255.0)
        frame_count += 1
    cap.release()

    frames = np.array(frames)
    return frames, target_fps


def save_video(
    video_frames,
    output_video_path,
    file_name,
    export_type,
    fps: int = 15,
) -> str:

    is_color = video_frames[0].ndim == 3

    for idx, frame in enumerate(video_frames):
        frame_bit_depth = (frame * 65535).astype(np.uint16)
        if is_color:
            frame_bit_depth = cv2.cvtColor(frame_bit_depth, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"{output_video_path}/{file_name}_{export_type}_frame_{idx:04d}.png", frame_bit_depth)


class ColorMapper:
    # a color mapper to map depth values to a certain colormap
    def __init__(self, colormap: str = "inferno"):
        self.colormap = torch.tensor(cm.get_cmap(colormap).colors)

    def apply(self, image: torch.Tensor, v_min=None, v_max=None):
        # assert len(image.shape) == 2
        if v_min is None:
            v_min = image.min()
        if v_max is None:
            v_max = image.max()
        image = (image - v_min) / (v_max - v_min)
        image = (image * 255).long()
        image = self.colormap[image]
        return image


def vis_sequence_depth(depths: np.ndarray, v_min=None, v_max=None):
    visualizer = ColorMapper()
    if v_min is None:
        v_min = depths.min()
    if v_max is None:
        v_max = depths.max()
    res = visualizer.apply(torch.tensor(depths), v_min=v_min, v_max=v_max).numpy()
    return res
