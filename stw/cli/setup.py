from __future__ import print_function
from setuptools import setup, find_packages

conf_dir = "/etc/sawtooth"

setup(
    name='da-client',
    version='0.1',
    description='Da Client',
    author='Author <author email>',
    url='https://github.com/author/da',
    packages=find_packages(),
    install_requires=[
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
        'requests',
        'PyYAML',
        'sawtooth-cli',
    ],
    entry_points={
        'console_scripts': [
            'cli = cli.workflow.cli:main_wrapper',
        ]
    })
