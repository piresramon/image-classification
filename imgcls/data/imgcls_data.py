import configargparse
import numpy as np
from typing import List, Optional, Union

import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

import imgaug.augmenters as iaa

import pytorch_lightning as pl

import imgcls.utils.misc as utils
from imgcls.utils.augmentation import prepare_data_augs


class ImgClsDataset(Dataset):
    """ImgCls dataset."""

    def __init__(self, list_paths: List[str], labels: List[int], normalize=None, transform=None):
        """
        Args:
        list_paths (list of string): List of paths to images.
        labels (list of int): List of targets.
        transform (callable, optional): Optional transform to be applied on a sample by imgaug
        transform (callable, optional): Optional image normalization by torchvision
        """
        self.list_paths = list_paths
        self.labels = labels
        self.transform = transform
        self.normalize = normalize

    def __len__(self):
        return len(self.list_paths)

    def __getitem__(self, idx):
        image = utils.pil_loader(self.list_paths[idx])

        if self.transform:
            image = self.transform.augment_image(np.asarray(image))

        image = transforms.ToTensor()(image)

        if self.normalize:
            image = self.normalize(image)

        return image, self.labels[idx], self.list_paths[idx]


class ImgClsDataModule(pl.LightningDataModule):
    
    def __init__(self, hparams):
        super().__init__()
        self.hparams.update(vars(hparams))

    def setup(self, stage: Optional[str] = None):
        
        assert len(self.hparams.valid_paths) == len(self.hparams.valid_tags), (
            'Please, give a tag for each validation dataset.')
        assert len(self.hparams.test_paths) == len(self.hparams.test_tags), (
            'Please, give a tag for each test dataset.')
            
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
                                         
        if stage == 'fit' or stage is None:

            # Load training data.
            list_paths_train, labels_train = utils.list_files(
                self.hparams.training_paths)

            # Flatten training lists.
            list_paths_train = [item for sublist in list_paths_train for item in sublist]
            self.labels_train = np.concatenate(labels_train, 0).astype(np.int64)

            print('Total training images: {} ({}/{} real/fake)'.format(
                len(list_paths_train),
                (self.labels_train == 1).sum(),
                (self.labels_train == 0).sum()))

            # Load valid data.
            valid_paths = self.hparams.valid_paths
            list_paths_valid, labels_valid = utils.list_files(valid_paths)

            # Flatten valid lists (for printing purposes only).
            list_paths_valid_flattened = [item for sublist in list_paths_valid for item in sublist]
            labels_valid_flattened = np.concatenate(labels_valid, 0).astype(np.int64)

            print('Total validation images: {} ({}/{} real/fake)'.format(
                len(list_paths_valid_flattened),
                (labels_valid_flattened == 1).sum(),
                (labels_valid_flattened == 0).sum()))

            # Data augmentation
            data_augs, data_aug_test = prepare_data_augs(
                self.hparams.image_size)

            # Creating the datasets
            self.train_dataset = ImgClsDataset(
                list_paths_train,
                self.labels_train,
                normalize,
                data_augs)

            self.valid_datasets = []
            for valid_path, list_paths_valid_i, labels_valid_i in zip(valid_paths, list_paths_valid, labels_valid):
                dataset = ImgClsDataset(
                    list_paths_valid_i,
                    labels_valid_i,
                    normalize,
                    data_aug_test)
                self.valid_datasets.append(dataset)

        if stage == 'test' or stage is None:

            # Load test data.
            test_paths = self.hparams.test_paths
            list_paths_test, labels_test = utils.list_files(test_paths)

            # Flatten test lists (for printing purposes only).
            list_paths_test_flattened = [item for sublist in list_paths_test for item in sublist]
            labels_test_flattened = np.concatenate(labels_test, 0).astype(np.int64)

            print('Total test images: {} ({}/{} real/fake)'.format(
                len(list_paths_test_flattened),
                (labels_test_flattened == 1).sum(),
                (labels_test_flattened == 0).sum()))

            # Data augmentation
            _, data_aug_test = prepare_data_augs(
                self.hparams.image_size)

            # Creating the datasets
            self.test_datasets = []
            for test_path, list_paths_test_i, labels_test_i in zip(test_paths, list_paths_test, labels_test):
                dataset = ImgClsDataset(
                    list_paths_test_i,
                    labels_test_i,
                    normalize,
                    data_aug_test)
                self.test_datasets.append(dataset)

    def train_dataloader(self):
        if self.hparams.balance:
            real_count = (self.labels_train == 1).sum()
            fake_count = len(self.labels_train) - real_count
            class_weights = 1. / torch.tensor([fake_count, real_count], dtype=torch.float)
            samples_weights = class_weights[self.labels_train]
            train_sampler = torch.utils.data.sampler.WeightedRandomSampler(
                weights=samples_weights,
                num_samples=len(self.labels_train),
                replacement=True)
            print('=> Using weighted sampler')
        else:
            print('=> Not using weighted sampler')
            train_sampler = None

        return DataLoader(
            self.train_dataset,
            batch_size=self.hparams.train_batch_size,
            shuffle=(train_sampler is None),
            num_workers=self.hparams.num_workers,
            sampler=train_sampler
        )
        
    def get_dataloader(self, dataset: Dataset, batch_size: int, shuffle: bool, num_workers: int) -> DataLoader:
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers
        )

    def val_dataloader(self,) -> Union[DataLoader, List[DataLoader]]:
        dataloaders = []
        for dataset in self.valid_datasets:
            dataloader = self.get_dataloader(
                dataset,
                batch_size=self.hparams.val_batch_size,
                shuffle=False,
                num_workers=self.hparams.num_workers
            )
            dataloaders.append(dataloader)
        return dataloaders

    def test_dataloader(self,) -> Union[DataLoader, List[DataLoader]]:
        dataloaders = []
        for dataset in self.test_datasets:
            dataloader = self.get_dataloader(
                dataset,
                batch_size=self.hparams.val_batch_size,
                shuffle=False,
                num_workers=self.hparams.num_workers
            )
            dataloaders.append(dataloader)
        return dataloaders

    @staticmethod
    def add_model_specific_args(parent_parser):
        parser = configargparse.ArgumentParser(parents=[parent_parser], add_help=False)
        parser.add_argument('--training_paths', metavar='DIR', action='append', required=True,
            help='list of paths to the training datasets')
        parser.add_argument('--valid_paths', metavar='DIR', action='append', required=True,
            help='list of paths to the validation datasets')
        parser.add_argument('--test_paths', metavar='DIR', action='append', required=True,
            help='list of paths to the test datasets')
        parser.add_argument('--valid_tags', action='append', required=True,
            help='list of tags for the validation datasets')
        parser.add_argument('--test_tags', action='append', required=True,
            help='list of tags for the test datasets')
        parser.add_argument('--train_batch_size', default=32, type=int)
        parser.add_argument('--image_size', default=224, type=int,
            help='set the image size according to the model')
        parser.add_argument('--val_batch_size', default=32, type=int)
        parser.add_argument('--balance', dest='balance', action='store_true',
            help='balance the training dataset by resampling')

        return parser
