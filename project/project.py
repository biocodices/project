from os import mkdir
from os.path import join, expanduser, abspath, basename, isdir
from glob import glob
import re
import logging

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

    def dump_df(self, df, filename, subdir='results', index=None, **kwargs):
        filepath = self._file_in_subdir(subdir, filename)
        dump_df(df, filepath, index, **kwargs)
        return filepath

    def read_csv(self, filename, subdir='results', **kwargs):
        filepath = join(self.dir, subdir, filename)
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

