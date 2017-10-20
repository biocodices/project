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

    If you are working from a Jupyter Notebook, you may set the name of
    the notebook as your intended directory name and initialize the project
    in this way:

        > pj = Project.from_notebook()

    Typically, you would copy your input files to `pj.data_dir` and store
    later results on `pj.results_dir`.

    You can then use the project instance to either full filepaths to any file
    in those directories:

        > pj.data_files()  # => list of files under <project>/data
        > pj.results_files()  # => list of files under <project>/results
        > pj.data_files('*.csv')  # => glob pattern to list the CSVs in /data
        > pj.results_files(regex='(csv|tsv)$')
        # => ^ or a regex for CSV/TSVs under /results

    You can dump a pandas.DataFrame and later retrieve it:

        > pj.dump_df(my_dataframe, 'out')
        # => writes to <project>/results/out.csv

        > pj.read_csv('out.csv')
        # => reads from <project>/results/out.csv

    If your pandas DataFrame has jsonable values (lists and dicts, for
    instance), then you might find it better to dump it as JSON:

        > pj.dump_df_as_json(my_dataframe, 'out')
        # => writes to <project>/results/out.json in 'split' format

        > pj.load_json_df('out')  # you can omit the ".json"
        # => loads the same DataFrame, preserving column order and
        #    deserializing the JSON columns

    """

    def __init__(self, base_dir):
        self.dir = abspath(expanduser(base_dir))
        self.name = basename(self.dir)

        print('Initializing Project "{}"'.format(self.name))

        self.data_dir = join(self.dir, 'data')
        self.results_dir = join(self.dir, 'results')

        for directory in [self.dir, self.data_dir, self.results_dir]:
            if not isdir(directory):
                print('Creating dir: {}'.format(directory))
                mkdir(directory)
            else:
                print('Already exists: {}'.format(directory))

    @classmethod
    def from_notebook(cls):
        """
        Initialize a Project using the title of the current notebook as the
        directory name for the project.

        Usage:
            > pj = Project.from_notebook()
        """
        notebook_name = cls.get_notebook_name()

        if notebook_name == 'Untitled':
            msg = 'Please set a name for this notebook that is not "Untitled".'
            raise ValueError(msg)

        return cls(base_dir=notebook_name)

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

    def _file_in_subdir(self, subdir, filename, check_exists=False):
        """
        Search for *filename* under *subdir*. If *check_exists* is set,
        raise if the resulting filepath is not an existing file or dir.
        """
        filepath = join(self.dir, subdir, filename)

        if check_exists and not isfile(filepath) and not isdir(filepath):
            raise FileNotFoundError(filepath)

        return filepath

    def data_files(self, pattern=None, regex=None):
        """
        List all the files in /data that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.data_dir, pattern, regex)

    def data_file(self, filename, check_exists=True):
        """
        Return the full path to a filename in /data. It checks the existence of
        the file or dir and raises if it's not there, unless *check_exists*
        is set to False.
        """
        return self._file_in_subdir(self.data_dir, filename, check_exists)

    def results_files(self, pattern=None, regex=None):
        """
        List the files in /results that match the given glob pattern or regex.
        """
        return self._files_in_subdir(self.results_dir, pattern, regex)

    def results_file(self, filename, check_exists=False):
        """
        Return the full filepath of a file with the given name in /results.

        If *check_exists* is set to True, checks the existence of either a
        file or a dir with the *filename* under self.results_dir.
        """
        return self._file_in_subdir(self.results_dir, filename, check_exists)

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

    def load_json_df(self, filename, subdir='results', **kwargs):
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

    ## This would be nice, but it's not functional so far:

    #  @staticmethod
    #  def get_notebook_name(host='localhost', port='8888'):
        #  """
        #  Gets the name of the current Jupyter notebook (if this code is run
        #  from Jupyter!).

        #  WARNING: This does not work when token authentication is enabled!
        #  """
        #  import json
        #  import requests

        #  from IPython.lib import kernel

        #  connection_file_path = kernel.get_connection_file()
        #  connection_file = basename(connection_file_path)
        #  kernel_id = connection_file.split('-', 1)[1].split('.')[0]

        #  url = 'http://{}:{}/api/sessions'.format(host, port)
        #  response = requests.get(url).text
        #  sessions = json.loads(response)
        #  for session in sessions:
            #  if session['kernel']['id'] == kernel_id:
                #  path = session['notebook']['path']
                #  return basename(path).replace('.ipynb', '')
