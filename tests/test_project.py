from os import remove
from os.path import isdir, isfile, basename, dirname, realpath, join

import pandas as pd

from project import Project


TEST_DIR = dirname(realpath(__file__))
test_project = Project(join(TEST_DIR, 'test_project'))


def test_initialization(tmpdir):
    pj = Project(str(tmpdir))

    for directory in [pj.data_dir, pj.results_dir, pj.dir]:
        assert isdir(directory)


def test_subdir_lookup():
    pj = test_project

    assert isfile(pj.data_file('data_file.txt'))
    assert isfile(pj.results_file('result.txt'))

    assert len(pj.data_files()) == 3
    assert len(pj.results_files()) == 1

    txt_files = pj.data_files('*.txt')
    assert 'data_file.txt' in [basename(f) for f in txt_files]

    csvs = pj.data_files(regex=r'data_.+\.(csv|tsv)')
    assert 'data_file.csv' in [basename(f) for f in csvs]


def test_read_json_df():
    pj = test_project
    df1 = pj.read_json_df('data_file.json', subdir='data')
    df2 = pj.read_json_df('data_file', subdir='data')

    for df in [df1, df2]:
        assert list(df.columns) == ['foo', 'baz']  # Check order is preserved
        assert df.loc[1, 'foo'] == 'boo'


def test_dump_df_as_json():
    pj = test_project
    df = pd.DataFrame([{'foo': 1, 'bar': 2},
                       {'foo': 3, 'bar': 4}])

    target_file = pj.dump_df_as_json(df, 'test_df')
    assert isfile(target_file)

    df_read = pj.read_json_df(target_file)
    assert all(df == df_read)

    remove(target_file)  # Cleanup
    assert not isfile(target_file)


def test_read_csv():
    pj = test_project
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

