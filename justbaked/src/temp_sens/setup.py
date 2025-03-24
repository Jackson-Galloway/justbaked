from setuptools import setup

package_name = 'temp_sens'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jackson Galloway',
    maintainer_email='jackson.galloway02@gmail.com',
    description='ROS 2 package for reading temperature from MLX90614 sensor',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'serial_temp_reader = temp_sens.serial_temp_reader:main',
        ],
    },
)
