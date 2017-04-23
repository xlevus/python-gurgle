from setuptools import setup, find_packages

setup(
    name="gurgle",
    version="0.0-prototype",
    author="Chris Targett",
    url='https://github.com/xlevus/gurgle',
    packages=find_packages(exclude=['tests', 'example', 'docs']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7,'],
    install_requires=["tornado"],
    entry_points={
        'console_scripts': [
            'gurgle=gurgle.cli:cli',]})
