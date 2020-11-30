from __future__ import print_function
from setuptools import setup, find_packages

setup(
    name='rest-api',
    version='0.1',
    description='Da Client',
    author='Author <author email>',
    url='https://github.com/author/da',
    packages=find_packages(),
    install_requires=[
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
        'secp256k1',
        'requests',
        'sanic',
        # 'fpdf',
        'sanic_cors',
        'pyzmq',
    ],
    entry_points={
        'console_scripts': [
            'rest-api = rest_api.main:main',
        ]
    })
