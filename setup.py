from setuptools import setup

setup(
    name='main',
    version='0.1',
    py_modules=['src'],
    entry_points={
        'console_scripts': ['src = src:main']
    },
)
