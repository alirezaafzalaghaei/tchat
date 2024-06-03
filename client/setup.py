from setuptools import setup, find_packages

setup(
    name='TChat',
    version='0.1.0',
    author='Alireza Afzal Aghaei',
    author_email='alirezaafzalaghaei@gmail.com',
    description='An educational messaging client application.',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests==2.32.3',
        'websocket-client==1.8.0',
        'textual==0.63.6',
        'rich-pixels==3.0.1',
        'platformdirs==4.2.2',
        'pytz'
    ],
    python_requires='>=3.12',
    entry_points={
        'console_scripts': [
            'tchat=tchat.__main__:main',
        ],
    },
    package_data={
        'tchat': ['menu.tcss'],
    },
)

