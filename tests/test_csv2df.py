from os.path import dirname, join, isfile
from tempfile import gettempdir

import pandas as pd

from project import read_csv, dump_df


def test_read_csv():
    fn = join(dirname(__file__), 'test_project/data/data_file.csv')
    df = read_csv(fn)
    assert all(type(item) is dict for item in df['dicts'])
    assert all(type(item) is list for item in df['lists'])


def test_dump_df(tmpdir):
    df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [['1'], ['2'], ['3']],
            'c': [{'a': 1}, {'b': 2}, {'c': 3}]
        })

    filename = join(gettempdir(), '_test_dump')
    result_filename = dump_df(df, filename)
    assert isfile(result_filename)
    assert result_filename == filename + '.csv'

    # Read the dumped CSV with pandas to check it's valid
    new_df = pd.read_csv(result_filename)
    assert all(new_df.columns == ['a', 'b', 'c'])
    assert new_df.shape == (3, 3)

    # Try a TSV instead of a CSV
    filename = join(gettempdir(), '_test_dump.tsv')
    result_filename = dump_df(df, filename)
    assert isfile(result_filename)
    assert result_filename == filename

    # Read the dumped TSV with pandas to check it's valid
    new_df = pd.read_table(result_filename)
    assert all(new_df.columns == ['a', 'b', 'c'])
    assert new_df.shape == (3, 3)

