from __future__ import print_function
from setuptools import setup, find_packages  # , Command

conf_dir = "/etc/sawtooth"

setup(
    name='token-processor',
    version='0.1',
    description='Da Client',
    author='Author <author email>',
    url='https://github.com/author/da',
    packages=find_packages(),
    install_requires=[
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
    ],
    entry_points={
        'console_scripts': [
            'token-tp = token_processor.main:main',
        ]
    })
