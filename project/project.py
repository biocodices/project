from os import mkdir
from os.path import join, expanduser, abspath, basename, isdir
from glob import glob
from contextlib import redirect_stdout
from io import StringIO
import time
import json

import numpy as np
import pandas as pd


class Project:
    def __init__(self, base_dir):
        self.dir = abspath(expanduser(base_dir))
        self.name = basename(self.dir)
        self.data_dir = join(self.dir, 'data')
        self.results_dir = join(self.dir, 'results')

        for directory in [self.dir, self.data_dir, self.results_dir]:
            if not isdir(directory):
                mkdir(directory)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.name)

    def _files_in_subdir(self, subdir, pattern, regex):
        """
        List all the files in subdir that match the given glob pattern or regex.
        """
        if pattern and regex:
            raise ValueError("Specify pattern OR regex, not both!")

        all_files = glob(join(subdir, (pattern or '*')))

        if not pattern and not regex:
            return all_files

        if regex:
            return [fn for fn in all_files if re.search(regex, fn)]

        if pattern:
            return [fn for fn in glob(join(subdir, pattern))]

    def _file_in_subdir(self, subdir, filename):
        return join(subdir, filename)

    def data_files(self, pattern=None, regex=None):
        """
        List all the files in /data that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.data_dir, pattern, regex)

    def results_files(self, pattern=None):
        """
        List all the files in /results that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.results_dir, pattern, regex)

    def results_file(self, filename):
        return self._file_in_subdir(self.reslts_dir, filename)

    def data_file(self, filename):
        return self._file_in_subdir(self.data_dir, filename)

    def dump_df(self, df, filename, subdir='results', index=None, **kwargs):
        """
        Dump the dataframe to a CSV in subdir with the given filename.
        Include '.tsv' in the filename to make it a TSV file!
        It will try to JSONify Python objects if they're consistent.
        Extra **kwargs are passed to pandas.DataFrame.to_csv()
        """
        t0 = time.time()
        if 'sep' not in kwargs:
            if filename.endswith('.tsv'):
                kwargs['sep'] = '\t'
            else:
                kwargs['sep'] = ','

        if kwargs['sep'] == ',' and not filename.endswith('.csv'):
            filename += '.csv'

        if index is None:
            # Don't include the index if it's just ordered numbers
            # This guessing can be overriden by specifying 'index'
            num_index_types = [
                pd.indexes.range.RangeIndex,
                pd.indexes.numeric.Int64Index
            ]
            index = (type(df.index) not in num_index_types)

        filepath = self._file_in_subdir(subdir, filename)
        print('Writing to "%s"' % filepath)

        columns_to_jsonify = []
        for column_name, series in df.iteritems():
            types = series.dropna().map(type).unique()
            if len(types) == 1 and types[0] in (list, dict):
                columns_to_jsonify.append(column_name)

        if columns_to_jsonify:
            # I need to copy the df to serialize some columns without modifying
            # the original dataframe that was passed as an argument.
            # TODO: There might be a better way to do this. Potential RAM hog.
            df = df.copy()
            for column_name in columns_to_jsonify:
                print('  JSONifying "%s"' % column_name)
                df[column_name] = df[column_name].map(json.dumps)

        df.to_csv(filepath, index=index, **kwargs)
        print('Took {:.2f} seconds\n'.format(time.time() - t0))

        return filepath

    def _series_as_JSON(self, series):
        """Try to read a pandas Series as JSON. Returns None if it fails."""
        try:
            new_series = series.fillna('""').map(json.loads).replace('', np.nan)
            print('  Parsed %s as JSON' % series.name)
            return new_series
        except ValueError:
            return None

    def read_csv(self, filename, subdir='results', **kwargs):
        """
        Read a CSV file in any of the Project's subdirectories (default:
        'results') into a pandas.DataFrame. It will try to parse as JSON the
        fields with dtype=np.object and convert them to Python objects. Extra
        **kwargs are passed to pd.read_csv().
        """
        t0 = time.time()
        filepath = join(self.dir, subdir, filename)
        print('Reading "{}"'.format(filename))
        df = pd.read_csv(filepath, **kwargs)

        # Don't try to parse a column as JSON if a dtype was already specified
        # And only keep 'object' dtypes, since they have strings in them!
        maybe_JSON_series = [series for colname, series in df.iteritems()
                             if colname not in kwargs.get('dtype', {}) and
                             series.dtype == np.dtype('object')]

        for new_series in map(self._series_as_JSON, maybe_JSON_series):
            if new_series is not None:
                df[new_series.name] = new_series

        # Get the memory usage data from the DataFrame
        captured_output = StringIO()
        with redirect_stdout(captured_output):
            df.info(memory_usage='deep')  # This function prints to stdout

        info_lines = [line for line in captured_output.getvalue().split('\n')
                      if 'memory' in line]
        print('\n'.join(info_lines))

        elapsed = time.time() - t0
        print('Took {:.2f} seconds'.format(elapsed), '\n')

        return df

    def save_last_plot(self, filename):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Seems you don't have matplotlib installed!")
            return

        filepath = self.results_file(filename)
        plt.savefig(filepath, bbox_inches='tight')
        print('Written to', filepath)

