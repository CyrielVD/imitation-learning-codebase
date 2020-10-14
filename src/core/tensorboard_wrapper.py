import os
from typing import List

import torch
from torch.utils.tensorboard import SummaryWriter
import numpy as np

from src.core.data_types import Distribution


class TensorboardWrapper(SummaryWriter):

    def __init__(self, log_dir: str):
        super().__init__(log_dir)
        self.step = 0
        self._output_file = os.path.join(log_dir, 'results.txt')

    def set_step(self, step: int):
        self.step = step

    def increment_step(self):
        self.step += 1

    def _add_scalar(self, tag: str, value: float) -> None:
        with open(self._output_file, 'a') as f:
            f.write(f"{self.step} : {tag} = {value} \n")
        self.add_scalar(tag, value, global_step=self.step)

    def write_distribution(self, distribution: Distribution, tag: str = ""):
        self._add_scalar(f"{tag}_mean" if tag != "" else "mean", distribution.mean)
        self._add_scalar(f"{tag}_std" if tag != "" else "std", distribution.std)
        self._add_scalar(f"{tag}_min" if tag != "" else "min", distribution.min)
        self._add_scalar(f"{tag}_max" if tag != "" else "max", distribution.max)

    def write_scalar(self, data: float, tag: str):
        self._add_scalar(tag, data)

    def write_gif(self, frames: List[np.ndarray] = None) -> None:
        if frames is None:
            return
        video_tensor = torch.stack([torch.as_tensor(f, dtype=torch.uint8) for f in frames]).unsqueeze(dim=0)
        if len(video_tensor.shape) == 4:  # add channel dimension in case of grayscale images
            video_tensor.unsqueeze_(dim=2)
        self.add_video(tag='game play', vid_tensor=video_tensor)
