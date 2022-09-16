import os
from distutils.core import setup
from setuptools import find_packages

pkg_dir = os.path.dirname(__name__)

with open(os.path.join(pkg_dir, 'requirements.txt')) as fd:
    requirements = fd.read().splitlines()

setup(
    name='image-classification',
    version='0.1.0',
    packages=find_packages('.', exclude=['data*',
                                         'lightning_logs*']),
    extras_require={},
    long_description=open('README.md').read(),
    install_requires=requirements,
)
