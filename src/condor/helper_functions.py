import copy
import os
import shlex
import subprocess
import time
from typing import List, Union, Dict

import yaml

from src.core.utils import get_date_time_tag


def strip_command(command: str) -> str:
    command = command.split(' ')[1]  # python path/to/file.py --config config_file --> path/to/file.py
    command = os.path.basename(command)  # path/to/file.py --> file.py
    command = command.split('.')[0]  # file.py --> file
    return str(command)


def strip_variable(value) -> str:
    if not isinstance(value, float) and '.' in str(value):
        value = value.split('.')[-2]
    if isinstance(value, float):
        value = f'{value:.0e}'
    value = str(value)
    value = os.path.basename(value)
    if value.startswith('"'):
        value = value[1:]
    if value.endswith('"'):
        value = value[:-1]
    return value


def get_variable_name(variable_name: str) -> str:
    #  '[config][0][name]' -> 'name'
    return strip_variable(variable_name.split(']')[-2].split('[')[-1])


def create_configs(base_config: Union[dict, str], output_path: str, adjustments: Dict[str, list]) -> List[str]:
    if isinstance(base_config, str):
        with open(base_config, 'r') as f:
            base_config = yaml.load(f, Loader=yaml.FullLoader)

    base_config['output_path'] = output_path

    if len(adjustments.keys()) == 0:
        config_path = os.path.join(base_config['output_path'], 'configs', f'{get_date_time_tag()}.yml')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(base_config, f)
        return [config_path]

    # assert each adjusting variable name comes with an equal number of values
    variable_value_lengths = [len(variable_values) for variable_values in adjustments.values()]
    assert min(variable_value_lengths) == max(variable_value_lengths)

    configs = []
    for value_index in range(variable_value_lengths[0]):
        new_config = copy.deepcopy(base_config)
        # loop over variable names to adjust new config
        for variable_name in adjustments.keys():
            value = adjustments[variable_name][value_index]
            exec(f'new_config{variable_name} = value')
        # use first variable_name to define config_name
        variable_name = list(adjustments.keys())[0]
        value = adjustments[variable_name][value_index]
        config_path = os.path.join(base_config['output_path'], 'configs',
                                   f'{get_date_time_tag()}_{get_variable_name(variable_name)}_'
                                   f'{strip_variable(value)}.yml')
        while os.path.isfile(config_path):
            time.sleep(1)
            config_path = os.path.join(base_config['output_path'], 'configs',
                                       f'{get_date_time_tag()}_{get_variable_name(variable_name)}_'
                                       f'{strip_variable(value)}.yml')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(new_config, f)
        configs.append(config_path)
    return configs


class Dag:

    def __init__(self, lines_dag_file: str, dag_directory: str):
        os.makedirs(dag_directory)
        assert len(lines_dag_file.split('\n')) > 3
        self._dag_file = os.path.join(dag_directory, 'dag_file')
        with open(self._dag_file, 'w') as dag_file_stream:
            dag_file_stream.write(lines_dag_file)

    def submit(self) -> int:
        return subprocess.call(shlex.split(f'condor_submit_dag {self._dag_file}'))