import os

import yaml


def load_yaml(file):
    with open(file) as f:
        try:
            conf = yaml.load(f, Loader=yaml.FullLoader)
            return conf

        except yaml.YAMLError as exception:
            print(exception)


def load_config(config_dir):

    try:
        custom_cfg = os.path.join(config_dir, 'config.yaml')
        conf = load_yaml(custom_cfg)
        return conf

    except FileNotFoundError as exception:
        print(exception)

        try:
            default_cfg = os.path.join(config_dir, 'default-config.yaml')
            conf = load_yaml(default_cfg)
            return conf

        except FileNotFoundError as exception:
            print(exception)

    return -255
