from setuptools import find_packages
from setuptools import setup

setup(
    name='turtlebot4_navigation',
    version='2.0.1',
    packages=find_packages(
        include=('turtlebot4_navigation', 'turtlebot4_navigation.*')),
)
