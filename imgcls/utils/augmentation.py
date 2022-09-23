import imgaug.augmenters as iaa
from typing import Tuple

def prepare_data_augs(image_size: int = 224) -> Tuple[iaa.Sequential, iaa.Sequential]:

    train_affine = iaa.geometric.Affine(scale=(0.85, 1.15), translate_percent=(0, 0.15), rotate=(-25, 25), mode='edge')

    test_resize = iaa.Resize({'shorter-side': int(image_size/0.875), 'longer-side': 'keep-aspect-ratio'}, interpolation='cubic')
    test_crop = iaa.CropToFixedSize(width=image_size, height=image_size, position="center")

    data_augs = iaa.Sequential([
        train_affine,
        iaa.Fliplr(0.5), # horizontally flip 50% of all images
        iaa.Invert(0.5),
        iaa.Resize(image_size, interpolation='cubic'),
        ], random_order=False)

    data_aug_test = iaa.Sequential([
        test_resize,
        test_crop,
        ], random_order=False)

    return data_augs, data_aug_test
