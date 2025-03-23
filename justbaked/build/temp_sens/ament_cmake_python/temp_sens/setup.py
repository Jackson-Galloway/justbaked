from setuptools import find_packages
from setuptools import setup

setup(
    name='temp_sens',
    version='0.0.0',
    packages=find_packages(
        include=('temp_sens', 'temp_sens.*')),
)
