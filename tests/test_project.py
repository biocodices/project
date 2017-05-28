from os import remove, getpid
from tempfile import gettempdir
from os.path import isdir, isfile, basename, dirname, realpath, join

import pytest
import pandas as pd

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


def test_subdir_lookup(pj):
    assert isfile(pj.data_file('data_file.txt'))
    assert isfile(pj.results_file('result.txt'))

    assert len(pj.data_files()) == 3
    assert len(pj.results_files()) == 1

    txt_files = pj.data_files('*.txt')
    assert 'data_file.txt' in [basename(f) for f in txt_files]

    csvs = pj.data_files(regex=r'data_.+\.(csv|tsv)')
    assert 'data_file.csv' in [basename(f) for f in csvs]


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

