from setuptools import setup
import os

package_name = 'robot_bringup'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), [
            'launch/startup.launch.py',
            'launch/roundone.launch.py',
            'launch/roundtwo.launch.py'
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='Robot bringup package',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'waypoint_navigation_node = robot_bringup.waypoint_navigation_node:main',
            'button_publisher = robot_bringup.button_publisher:main',
            'round_launcher = robot_bringup.round_launcher:main',
        ],
    },
)
