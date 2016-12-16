from setuptools import setup, find_packages


with open('requirements.txt') as f:
    dependencies = f.read().split('\n')

with open('README.md') as f:
    long_description = f.read()

setup(
    name='Project',
    version='1.1',
    description=("A handy utility to deal with a project's data and results "
                 "subdirectories and files, specially CSVs."),
    long_description=long_description,
    url='https://github.com/biocodices/project',
    author='Juan Manuel Berros',
    author_email='juanmaberros@gmail.com',
    license='MIT',
    install_requires=dependencies,
    packages=find_packages(),
)

