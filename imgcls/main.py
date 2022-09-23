# coding=utf-8                                                 
"""Finetuning the model for image classification."""

import os
import configargparse

from imgcls.data.imgcls_data import ImgClsDataModule
import imgcls.utils.misc as utils


MODEL_DIR = 'lightning_logs'

def main():
    parser = configargparse.ArgParser('Livdet training and evaluation script', 
        config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add_argument('-c', '--my-config', required=True, is_config_file=True, help='config file path')

    parser.add_argument('--seed', default=42, type=int)
    parser.add_argument('--resume', default='', help='resume from checkpoint')
    parser.add_argument('--num_workers', default=2, type=int)
    
    # add datamodule specific args
    parser = ImgClsDataModule.add_model_specific_args(parser)
    args, unknown = parser.parse_known_args()

    print("git:\n  {}\n".format(utils.get_sha()))
 
    # data module
    dm = ImgClsDataModule(args) 
    dm.setup('fit')

    dm.setup('test')


if __name__ == '__main__':
    main()