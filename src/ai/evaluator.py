#!/usr/bin/python3.7

from dataclasses import dataclass
import numpy as np
import torch
from torch import nn
from dataclasses_json import dataclass_json

from src.ai.model import Model
from src.core.config_loader import Config
from src.core.logger import get_logger, cprint
from src.data.dataset_loader import DataLoaderConfig, DataLoader

"""Given model, config, data_loader, evaluates a model and logs relevant training information

Depends on ai/architectures, data/data_loader, core/logger
"""


@dataclass_json
@dataclass
class EvaluatorConfig(Config):
    data_loader_config: DataLoaderConfig = None
    device: str = 'cpu'
    criterion: str = 'MSELoss'


class Evaluator:

    def __init__(self, config: EvaluatorConfig, model: Model, quiet: bool = False):
        self._config = config
        self._model = model
        self._data_loader = DataLoader(config=self._config.data_loader_config)
        self._logger = get_logger(name=__name__,
                                  output_path=config.output_path,
                                  quite=False)
        if not quiet:
            cprint(f'Started.', self._logger)
        self._criterion = eval(f'nn.{self._config.loss}(reduction=\'none\').to(self._config.device)')

        self._data_loader.load_dataset(input_sizes=self._model.get_input_sizes(),
                                       output_sizes=self._model.get_output_sizes())

        self._minimum_error = float(10**6)

    def evaluate(self, save_checkpoints: bool = False) -> None:
        total_error = []
        for run in self._data_loader.get_data():
            model_outputs = self._model.forward(run.get_input())
            for output_index, output in enumerate(model_outputs):
                targets = run.get_output()[output_index]
                error = self._criterion(output, targets)
                total_error.append(error.mean())
                cprint(f'{run.outputs.keys()[output_index]}: {error} {self._config.criterion}.')
        total_error = float(torch.Tensor(total_error).mean())
        if save_checkpoints and total_error < self._minimum_error:
            self._model.save_to_checkpoint(tag='best')
            self._minimum_error = total_error
