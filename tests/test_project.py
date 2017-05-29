from os import remove, getpid
from tempfile import gettempdir
from os.path import isdir, isfile, dirname, realpath, join
from unittest.mock import MagicMock

import pytest
import pandas as pd
from IPython.lib import kernel

from project import Project


TEST_DIR = dirname(realpath(__file__))

@pytest.fixture
def pj():
    return Project(join(TEST_DIR, 'test_project'))


def test_initialization():
    dir_name = join(gettempdir(), 'test_project__'.format(getpid()))
    Project(dir_name)  # This step should create all directories

    expected_directories = [
        dir_name,
        join(dir_name, 'data'),
        join(dir_name, 'results')
    ]
    for directory in expected_directories:
        assert isdir(directory)

    # A second initialization should not fail if the target directories exist
    Project(dir_name)


def test_file_in_subdir(pj):
    non_existent_filename = 'non-existent-file'

    with pytest.raises(FileNotFoundError):
        pj._file_in_subdir('data', non_existent_filename, check_exists=True)

    path = pj._file_in_subdir('some-subdir', non_existent_filename,
                              check_exists=False)
    assert path == join(pj.dir, 'some-subdir', non_existent_filename)


def test_data_files(pj):
    data_files = [
        'data_file.csv',
        'data_file.txt',
        'data_file.json',
    ]
    assert pj.data_files() == [join(pj.data_dir, fn) for fn in data_files]
    assert pj.data_files(pattern='*.csv')[0].endswith('data_file.csv')
    assert len(pj.data_files(regex=r'data_.+\.(csv|txt)')) == 2

def test_data_file(pj):
    assert pj.data_file('data_file.csv') == join(pj.data_dir, 'data_file.csv')

    with pytest.raises(FileNotFoundError):
        pj.data_file('non-existent-file')


def test_results_files(pj):
    expected = join(pj.results_dir, 'result.txt')
    assert pj.results_files() == [expected]
    assert pj.results_files('*.txt') == [expected]
    assert pj.results_files('*.no-file') == []
    assert pj.results_files(regex=r'txt$') == [expected]


def test_results_file(pj):
    assert pj.results_file('result.txt') == join(pj.results_dir, 'result.txt')

    with pytest.raises(FileNotFoundError):
        pj.results_file('non-existent-file', check_exists=True)


def test_get_notebook_name(pj, monkeypatch):
    fn = '/run/user/1000/jupyter/kernel-123-abc-lalala.json'
    mock = MagicMock(return_value=fn)
    monkeypatch.setattr(kernel, 'get_connection_file', mock)

    assert pj._get_notebook_name() == '123-abc-lalala'


def test_load_json_df(pj):
    df1 = pj.load_json_df('data_file.json', subdir='data')
    df2 = pj.load_json_df('data_file', subdir='data')

    for df in [df1, df2]:
        assert list(df.columns) == ['foo', 'baz']  # Check order is preserved
        assert df.loc[1, 'foo'] == 'boo'


def test_dump_df_as_json(pj):
    df = pd.DataFrame([{'foo': 1, 'bar': 2},
                       {'foo': 3, 'bar': 4}])

    target_file = pj.dump_df_as_json(df, 'test_df')
    assert isfile(target_file)

    df_read = pj.load_json_df(target_file)
    assert all(df == df_read)

    remove(target_file)  # Cleanup
    assert not isfile(target_file)


def test_read_csv(pj):
    expected_columns = 'int_field string_field dicts lists'.split()

    # Test it infers the trailing '.csv'
    df = pj.read_csv('data_file', subdir='data')
    assert df.columns.all(expected_columns)

    # Test it has the right amount of cols & rows
    df = pj.read_csv('data_file.csv', subdir='data')
    assert df.shape == (10, 4)

    # Test it correctly passes arguments to pandas.read_csv
    df = pj.read_csv('data_file', subdir='data', usecols=[expected_columns[1]])
    assert df.columns.all(expected_columns[1])
    assert df.shape == (10, 1)

