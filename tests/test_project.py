from os import rmdir, remove
from os.path import isdir, isfile, basename, dirname, realpath, join

import pandas as pd
import pytest

from project import Project


TEST_DIR = dirname(realpath(__file__))
test_project = Project(join(TEST_DIR, 'test_project'))


def test_initialization():
    pj = Project(join(TEST_DIR, 'unexistent_dir'))

    for directory in [pj.data_dir, pj.results_dir, pj.dir]:
        assert isdir(directory)
        rmdir(directory)  # Cleanup

def test_subdir_lookup():
    pj = test_project

    assert isfile(pj.data_file('data_file.txt'))
    assert isfile(pj.results_file('result.txt'))

    assert len(pj.data_files()) == 2
    assert len(pj.results_files()) == 1

    txt_files = pj.data_files('*.txt')
    assert 'data_file.txt' in [basename(f) for f in txt_files]

    csvs = pj.data_files(regex=r'data_.+\.(csv|tsv)')
    assert 'data_file.csv' in [basename(f) for f in csvs]

def test_dump_df():
    df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [['1'], ['2'], ['3']],
            'c': [{'a': 1}, {'b': 2}, {'c': 3}]
        })

    pj = test_project
    fn = pj.dump_df(df, 'test_dump')

    assert isfile(fn)
    remove(fn)

    fn = pj.dump_df(df, 'test_dump.tsv')
    assert isfile(fn)
    assert all(pd.read_table(fn).columns == ['a', 'b', 'c'])
    remove(fn)  # Cleanup

def test_read_csv():
    pj = test_project
    df = pj.read_csv('data_file.csv', subdir='data')
    assert all(type(item) is dict for item in df['dicts'])
    assert all(type(item) is list for item in df['lists'])
