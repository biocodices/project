from setuptools import setup, find_packages


with open('requirements.txt') as f:
    dependencies = f.read().split('\n')

setup(
    name='Project',
    version='1.0',
    description=("A handy utility to deal with a project's data and results "
                 "subdirectories and files, specially CSVs"),
    url='https://github.com/biocodices/project',
    author='Juan Manuel Berros',
    author_email='juanmaberros@gmail.com',
    license='MIT',
    packages=find_packages()
)

