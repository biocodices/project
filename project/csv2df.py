from os.path import basename, getsize, isfile
import time
import logging
import json
from io import StringIO
from contextlib import redirect_stdout
from functools import wraps

import numpy as np
import pandas as pd
from humanfriendly import format_size
import coloredlogs


logger = logging.getLogger(__name__)
coloredlogs.install('INFO')


def log_elapsed_time(func):
    """Decorates a function: it times how long it takes to execute and logs
       the elapsed time when it ends."""

    @wraps(func)
    def wrapped_function(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        logger.info('Took {:.2f} seconds'.format(time.time() - t0))
        return result

    return wrapped_function


@log_elapsed_time
def dump_df(df, filepath, index=None, **kwargs):
    """
    Dump the dataframe to a CSV in the given filepath. Include '.tsv' in the
    filepath to make it a TSV file!

    It will try to JSONify Python objects if they're consistent.

    By default, the dataframe index will NOT be dumped if it's numeric. This
    behavior can be orverriden specifying index=True.

    Extra **kwargs will be passed to pandas.DataFrame.to_csv()
    """
    nrows, ncols = df.shape
    ncells = df.size
    logger.info(f'Will dump a dataframe with {nrows:,} rows ' +
                f'and {ncols:,} cols (number of cells: {ncells:,})')

    if 'sep' not in kwargs:
        if '.tsv' in filepath:
            kwargs['sep'] = '\t'
        else:
            kwargs['sep'] = ','

    if kwargs['sep'] == ',' and not '.csv' in filepath:
        filepath += '.csv'

    if index is None:
        # Don't include the index if it's just ordered numbers
        # This guessing can be overriden by specifying 'index' as True
        num_index_types = [
            pd.core.indexes.range.RangeIndex,
            pd.core.indexes.numeric.Int64Index
        ]
        index = (type(df.index) not in num_index_types)

    columns_to_jsonify = []
    for column_name, series in df.iteritems():
        types = series.dropna().map(type).unique()
        # I will JSONify a Series if all the non-null elements are from the
        # same type and that type is either a list or a dict.
        if len(types) == 1 and types[0] in (list, dict):
            columns_to_jsonify.append(column_name)

    if columns_to_jsonify:
        # I need to copy the df to serialize some columns without modifying
        # the original dataframe that was passed as an argument.
        # TODO: There might be a better way to do this. Potential RAM hog.
        df = df.copy()
        for column_name in columns_to_jsonify:
            logger.info('JSONify "{}"'.format(column_name))
            df[column_name] = df[column_name].map(json.dumps)

    logger.info('Writing to "{}"'.format(filepath))
    df.to_csv(filepath, index=index, **kwargs)
    logger.info('File "{}" is {}'.format(basename(filepath),
                                         format_size(getsize(filepath))))

    return filepath


@log_elapsed_time
def read_csv(filepath, **kwargs):
    """
    Wrapper function around pandas.read_csv: reads a CSV file into a
    pandas.DataFrame.

    Aditionally, for each column it will try to parse the fields as JSON
    if the column has dtype=np.object (i.e. string), and convert them to
    Python objects like lists or dicts.

    If the JSON parsing fails for the any of the series items, it will
    leave it as it is, like it isn't JSON. NaN values are handled and left
    as NaN after the parsing.

    Extra **kwargs are passed to pd.read_csv().
    """
    if not isfile(filepath):
        filepath += '.csv'
    if not isfile(filepath):
        filepath = filepath.replace('.csv', '.tsv')
    if not isfile(filepath):
        filepath = filepath.replace('.tsv', '')  # Undo the modifications
        msg = "No file '{}' found.".format(filepath)
        raise FileNotFoundError(msg)

    logger.info('Reading "{}"'.format(basename(filepath)))
    df = pd.read_csv(filepath, **kwargs)

    # Don't try to parse a column as JSON if a dtype was already specified
    # And only keep 'object' dtypes, since they have strings in them!
    maybe_JSON_series = [series for colname, series in df.iteritems()
                         if colname not in kwargs.get('dtype', {}) and
                         series.dtype == np.dtype('object')]

    for new_series in map(_series_as_JSON, maybe_JSON_series):
        if new_series is not None:
            df[new_series.name] = new_series

    # Get the memory usage data from the DataFrame
    captured_output = StringIO()
    with redirect_stdout(captured_output):
        df.info(memory_usage='deep')  # This function prints to stdout

    info_lines = [line for line in captured_output.getvalue().split('\n')
                  if 'memory' in line]
    logger.info('\n'.join(info_lines))

    return df


def _series_as_JSON(series):
    """Try to read a pandas Series as JSON. Returns None if it fails."""
    try:
        new_series = series.fillna('""').map(json.loads).replace('', np.nan)
        logger.info('Parsed "{}" as JSON'.format(series.name))
        return new_series
    except ValueError:
        return None

