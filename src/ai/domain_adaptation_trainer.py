#!/usr/bin/python3.8
import torch
from torch import nn
import numpy as np

from src.ai.base_net import BaseNet
from src.ai.trainer import TrainerConfig, Trainer
from src.ai.losses import *
from src.ai.deep_supervision import DeepSupervision
from src.ai.utils import get_reward_to_go, get_checksum_network_parameters, data_to_tensor
from src.core.data_types import Distribution, Dataset
from src.core.logger import get_logger, cprint
from src.core.tensorboard_wrapper import TensorboardWrapper
from src.core.utils import get_filename_without_extension
from src.data.data_loader import DataLoader

"""Given model, config, data_loader, trains a model and logs relevant training information
Adds extra data loader for target data.
Use epsilon to specify balance between (1 - epsilon) * L_task + epsilon * L_domain_adaptation
Apply deep supervision to intermediate outputs of the network
"""


class DomainAdaptationTrainer(Trainer):

    def __init__(self, config: TrainerConfig, network: BaseNet, quiet: bool = False):
        super().__init__(config, network, quiet=True)

        self._config.epsilon = 0.2 if self._config.epsilon == "default" else self._config.epsilon

        self.target_data_loader = DataLoader(config=self._config.target_data_loader_config)
        self.target_data_loader.load_dataset()
        self._domain_adaptation_criterion = eval(f'{self._config.domain_adaptation_criterion}()') \
            if not self._config.domain_adaptation_criterion == 'default' else MMDLossJordan()
        self._domain_adaptation_criterion.to(self._device)

        if not quiet:
            self._logger = get_logger(name=get_filename_without_extension(__file__),
                                      output_path=config.output_path,
                                      quiet=False)
            cprint(f'Started.', self._logger)

    def train(self, epoch: int = -1, writer=None) -> str:
        self.put_model_on_device()
        total_error = []
        for source_batch, target_batch in zip(self.data_loader.sample_shuffled_batch(),
                                              self.target_data_loader.sample_shuffled_batch()):
            self._optimizer.zero_grad()
            targets = data_to_tensor(source_batch.actions).type(self._net.dtype).to(self._device)
            # task loss
            predictions = self._net.forward(source_batch.observations, train=True)
            loss = (1 - self.epsilon) * self._criterion(predictions, targets).mean()

            # add domain adaptation loss
            loss += self.epsilon * self._domain_adaptation_criterion(self._net.get_features(source_batch.observations,
                                                                                            train=True),
                                                                     self._net.get_features(target_batch.observations,
                                                                                            train=True))

            loss.backward()
            if self._config.gradient_clip_norm != -1:
                nn.utils.clip_grad_norm_(self._net.parameters(),
                                         self._config.gradient_clip_norm)
            self._optimizer.step()
            self._net.global_step += 1
            total_error.append(loss.cpu().detach())
        self.put_model_back_to_original_device()

        if self._scheduler is not None:
            self._scheduler.step()

        error_distribution = Distribution(total_error)
        if writer is not None:
            writer.set_step(self._net.global_step)
            writer.write_distribution(error_distribution, 'training')
            if self._config.store_output_on_tensorboard and epoch % 30 == 0:
                writer.write_output_image(predictions, 'source/predictions')
                writer.write_output_image(targets, 'source/targets')
                writer.write_output_image(torch.stack(source_batch.observations), 'source/inputs')
                writer.write_output_image(self._net.forward(target_batch.observations, train=True),
                                          'target/predictions')
                writer.write_output_image(torch.stack(target_batch.observations), 'target/inputs')

        return f' training {self._config.criterion} {error_distribution.mean: 0.3e} [{error_distribution.std:0.2e}]'
