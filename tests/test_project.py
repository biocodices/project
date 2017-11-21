from os import remove, getpid
from tempfile import gettempdir
from os.path import isdir, isfile, dirname, realpath, join
from unittest.mock import MagicMock
import json
import requests

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

    result = pj._file_in_subdir('some-subdir', non_existent_filename,
                              check_exists=False)
    assert result == join(pj.dir, 'some-subdir', non_existent_filename)

    # Unambiguous pattern in a subdir
    unambiguous_pattern = '_in_subdir'
    result = pj._file_in_subdir(pj.data_dir, unambiguous_pattern,
                                check_exists=True)
    assert result == join(pj.dir, 'data/subdir/file_in_subdir.txt')

    # Unambiguous pattern in data dir
    unambiguous_pattern = 'file.json'
    result = pj._file_in_subdir(pj.data_dir, unambiguous_pattern,
                                check_exists=True)
    assert result == join(pj.dir, 'data/data_file.json')

    # Unambiguous but incomplete pattern
    unambiguous_pattern = 'file.tx'
    result = pj._file_in_subdir(pj.data_dir, unambiguous_pattern,
                                check_exists=True)
    assert result == join(pj.dir, 'data/data_file.txt')

    with pytest.raises(FileNotFoundError):
        ambiguous_pattern = 'data_*'
        pj._file_in_subdir(pj.dir, ambiguous_pattern, check_exists=True)


def test_data_files(pj):
    data_files = [
        'subdir/file_in_subdir.txt',
        'data_file.csv',
        'data_file.json',
        'data_file.txt',
    ]
    for data_file in data_files:
        assert join(pj.data_dir, data_file) in pj.data_files()

    assert pj.data_files(pattern='*.csv')[0].endswith('data_file.csv')
    assert len(pj.data_files(regex=r'\.(csv|txt)')) == 3

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


## The code for this is not yet functional, and it's also commented out in
## the Project class:

#  def test_get_notebook_name(monkeypatch):
    #  fn = '/run/user/1000/jupyter/kernel-123-abc-lalala.json'
    #  mock = MagicMock(return_value=fn)
    #  monkeypatch.setattr(kernel, 'get_connection_file', mock)
    #  kernels_json = [{'notebook': {'path': 'nb-name.ipynb'},
                     #  'kernel': {'id': '123-abc-lalala'}}]

    #  # Mock requests response to simulate a running local kernel
    #  class Response:
        #  text = json.dumps(kernels_json)

    #  monkeypatch.setattr(requests, 'get', lambda _: Response)

    #  assert Project.get_notebook_name() == 'nb-name'


#  def test_from_notebook(monkeypatch):
    #  monkeypatch.setattr(Project, 'get_notebook_name', lambda: 'Nb-Name')
    #  mock_init = MagicMock(return_value=None)
    #  monkeypatch.setattr(Project, '__init__', mock_init)

    #  Project.from_notebook()
    #  mock_init.assert_called_once_with(base_dir='Nb-Name')

    #  # It won't create a project directory after an "Untitled" notebook!
    #  monkeypatch.setattr(Project, 'get_notebook_name', lambda: 'Untitled')
    #  with pytest.raises(ValueError):
        #  Project.from_notebook()


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

