from os import mkdir
from os.path import join, expanduser, abspath, basename, isdir, getsize, isfile
from glob import glob
import re
import logging

import pandas as pd
from humanfriendly import format_size

from project.csv2df import dump_df, read_csv


logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class Project:
    """
    This class is meant to help you manage a project's directories and data
    and results filepaths.

    Initializing this class with a valid path will automatically create
    the base_dir if it doesn't exist, and /data and /results subdirs if
    they don't exist under the base_dir.

        > pj = Project('~/path/to/base_dir_of_project')

    After that, you just use it to either get full filepaths to your data and
    results files:

        > pj.data_files()  # => list of files under <project>/data
        > pj.results_files()  # => list of files under <project>/results

    You can use glob patterns or regex to find files:

        > pj.data_files('*.csv')  # => list the CSV files in <project>/data
        > pj.results_files(regex='(csv|tsv)$')  # => list the CSV and TSV files

    And you can dump a pandas.DataFrame and later retrieve it:

        > pj.dump_df(my_dataframe, 'out')
        # => writes to <project>/results/out.csv

        > pj.read_csv('out.csv')
        # => reads from <project>/results/out.csv
    """

    def __init__(self, base_dir):
        self.dir = abspath(expanduser(base_dir))
        self.name = basename(self.dir)
        self.data_dir = join(self.dir, 'data')
        self.results_dir = join(self.dir, 'results')

        for directory in [self.dir, self.data_dir, self.results_dir]:
            if not isdir(directory):
                mkdir(directory)

    def __str__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.name)

    def __repr__(self):
        return "Project('{}')".format(self.dir)

    def _files_in_subdir(self, subdir, pattern, regex):
        """
        List the files in subdir that match the given glob pattern or regex.
        """
        if pattern and regex:
            raise ValueError("Specify pattern OR regex, not both!")

        all_files = glob(join(subdir, (pattern or '*')))

        if not pattern and not regex:
            return all_files

        if pattern:
            return [fn for fn in glob(join(subdir, pattern))]

        if regex:
            return [fn for fn in all_files if re.search(regex, fn)]

    def _file_in_subdir(self, subdir, filename):
        return join(self.dir, subdir, filename)

    def data_files(self, pattern=None, regex=None):
        """
        List all the files in /data that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.data_dir, pattern, regex)

    def data_file(self, filename):
        """Return the full path to a filename in /data."""
        return self._file_in_subdir(self.data_dir, filename)

    def results_files(self, pattern=None, regex=None):
        """
        List the files in /results that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.results_dir, pattern, regex)

    def results_file(self, filename):
        """
        Return the full filepath of a file with the given name in /results
        """
        return self._file_in_subdir(self.results_dir, filename)

    def dump_df_as_json(self, df, filename, subdir='results', **kwargs):
        """
        Dump a pandas.DataFrame as a 'split' formatted JSON file in the given
        subdir (default='results') with the given filename. Adds '.json' to the
        filename if not present.

        'split' should be left as the default orient since it allows to
        preserve the columns order of the dataframe for later use. However,
        you can override this option with orient='records', for instance. If
        you do so, keep in mind you will later need to specify that orient
        option when reading the JSON with read_json_df().

        Extra **kwargs are passed to pandas.DataFrame.to_json().
        """
        if not filename.endswith('json'):
            filename += '.json'
        filepath = self._file_in_subdir(subdir, filename)
        if not 'orient' in kwargs:
            kwargs['orient'] = 'split'
        df.to_json(filepath, **kwargs)
        size = format_size(getsize(filepath))
        logger.info('Dumped a {} JSON to {}'.format(size, filepath))
        return filepath

    def read_json_df(self, filename, subdir='results', **kwargs):
        """
        Read a JSON with the given filename to a pandas.DataFrame. It will
        search in the passed subdir (default='results') and it will try to
        add '.json' to the filename if it fails.

        The default orient is 'split', since it allows to keep the order of
        the columns when serializing/deserializing. You can override this with
        the 'orient' keyword argument, but the orient has to be consistent
        with the format of the target JSON file.

        Extra **kwargs are passed to pandas.read_json().
        """
        filepath = self._file_in_subdir(subdir, filename)
        if not isfile(filepath) and isfile(filepath + '.json'):
            filepath += '.json'
        if not 'orient' in kwargs:
            kwargs['orient'] = 'split'
        return pd.read_json(filepath, **kwargs)

    def dump_df(self, df, filename, subdir='results', index=None, **kwargs):
        filepath = self._file_in_subdir(subdir, filename)
        dump_df(df, filepath, index, **kwargs)
        return filepath

    def read_csv(self, filename, subdir='results', **kwargs):
        filepath = self._file_in_subdir(subdir, filename)
        return read_csv(filepath, **kwargs)

    def save_last_plot(self, filename):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("Seems you don't have matplotlib installed!")
            return

        filepath = self.results_file(filename)
        plt.savefig(filepath, bbox_inches='tight')
        logger.info('Written to', filepath)

