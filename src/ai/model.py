#!/usr/bin/python3.7
import os
from dataclasses import dataclass
from enum import IntEnum
from typing import List

import torch
from dataclasses_json import dataclass_json
from torch import nn

from src.ai.architectures import *  # Do not remove
from src.core.config_loader import Config
from src.core.logger import get_logger, cprint, MessageType

"""
Model contains of architectures (can be modular).
Model ensures proper initialization and storage of model parameters.
"""


class InitializationType(IntEnum):
    Xavier: 0
    Constant: 1


@dataclass_json
@dataclass
class ModelConfig(Config):
    load_checkpoint_dir: str = None
    architecture: str = None
    dropout: float = 0.
    initialisation_type: InitializationType = None
    pretrained: bool = False

    def __post_init__(self):
        if self.load_checkpoint_dir is None:
            del self.load_checkpoint_dir


class Model:

    def __init__(self, config: ModelConfig):
        self._config = config
        self._logger = get_logger(name=__name__,
                                  output_path=config.output_path,
                                  quite=False)
        self._checkpoint_directory = os.path.join(self._config.output_path, 'torch_checkpoints')
        os.makedirs(self._checkpoint_directory, exist_ok=True)
        cprint(f'Started.', self._logger)
        self._architecture = eval(f'{self._config.architecture}.Net('
                                  f'dropout={self._config.dropout})')

        if self._config.load_checkpoint_dir:
            self.load_from_checkpoint(checkpoint_dir=self._config.load_checkpoint_dir)
        else:
            self.initialize_architecture_weights(self._config.initialisation_type)

    def forward(self, inputs: List[torch.Tensor], train: bool = False):
        return self._architecture.forward(*inputs, train=train)

    def initialize_architecture_weights(self, initialisation_type: InitializationType = 0):
        for p in self.get_parameters():
            if initialisation_type == InitializationType.Xavier:
                nn.init.xavier_uniform_(p)
            elif initialisation_type == InitializationType.Constant:
                nn.init.constant_(p, 0.001)
            else:
                raise NotImplementedError

    def load_from_checkpoint(self, checkpoint_dir: str):
        # Priority one: best checkpoint
        if os.path.isfile(os.path.join(checkpoint_dir, 'checkpoint_best')):
            self._architecture.load_state_dict(torch.load(os.path.join(checkpoint_dir, 'checkpoint_best')))
        elif os.path.isfile(os.path.join(checkpoint_dir, 'checkpoint_latest')):
            self._architecture.load_state_dict(torch.load(os.path.join(checkpoint_dir, 'checkpoint_latest')))
        else:
            cprint(f'Could not find suitable checkpoint in {checkpoint_dir}', self._logger, MessageType.error)
            raise FileNotFoundError

    def save_to_checkpoint(self, tag: str = ''):
        filename = f'checkpoint_{tag}' if tag != '' else 'checkpoint'
        torch.save(self._architecture.state_dict(), f'{self._checkpoint_directory}/{filename}')
        torch.save(self._architecture.state_dict(), f'{self._checkpoint_directory}/checkpoint_latest')

    def get_input_sizes(self):
        return self._architecture.input_sizes

    def get_output_sizes(self):
        return self._architecture.output_sizes

    def get_parameters(self):
        return self._architecture.parameters()
