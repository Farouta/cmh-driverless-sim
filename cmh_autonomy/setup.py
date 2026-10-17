from setuptools import find_packages, setup

package_name = 'cmh_autonomy'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Fourat Zai El Amri',
    maintainer_email='fourat.amri@hotmail.com',
    description='Autonomy nodes (perception, planning, control) for the CMH driverless car.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_driver = cmh_autonomy.simple_driver:main'
        ],
    },
)
