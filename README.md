# Project

`Project` is a handy Python class that will deal with your project's `data` and
`results` subdirectories. Typical usage:

```python
from project import Project

pj = Project('path/to/your/project/basedir')
# => results and data subdirectories will be created if they don't exist
```

If you move some data files to the `data` dir, you can list all, some or one:

```python
pj.data_files()
# => All files under /data

pj.data_files(pattern='*.vcf')
# => Glob pattern for VCF files under /data

pj.data_files(regex=r'(vcf|bam)$')
# => Regex for VCF and BAM files under /data

pj.data_file('sample1.vcf')
# Returns the complete path to that data file
```

Whenever you need to write some data to results, you can use `Project` to
easily get full filepaths:

```python
path = pj.results_file('my_new_results.txt')
# => /home/juan/myproject/results/my_new_results.txt

with open(path, 'w') as f:
    f.write(some_new_results)
```

`Project` is specially handy when you need to dump a pandas DataFrame to a CSV
or load a CSV file as a pandas DataFrame:

```python
pj.dump_df(my_dataframe, 'results')
# => Will write a 'results.csv' under /results

pj.dump_df(other_dataframe, 'new_data', subdir='data')
# => Will write a 'new_data.csv' under /data

pj.dump_df(my_dataframe, 'results.tsv')
# => Specify '.tsv' to get a TSV file written instead of a CSV

pj.dump_df(my_dataframe, 'results', header=None, index=None)
# => Any extra keyword arguments will be passed to pandas.DataFrame.to_csv()
```

`Project` will try to JSONify fields when all non-null data belong to the same
Python type, e.g. lists or dicts.

```python
df = pd.DataFrame({'a': [[1, 2], [3, 4]], 'b': [[5, 6], [7, 8]]})
pj.dump_df(df, 'with_lists')
# => Will write "with_lists.csv" and jsonify the lists [1, 2], [3, 4], etc.
```

Next time you read that same CSV, `Project` will load the JSON fields and
convert them back to Python objects.

```python
df = pj.read_csv('with_lists')
# => Get a DataFrame with the JSON fields loaded back to Python objects.

df = pj.read_csv('some_data.csv', subdir='data', dtype={'colname': int})
# => Read CSV from another subdir. The extra keyword arguments (here, dtype)
#    are passed to pandas.read_csv()
```

`Project` also has read and dump utilities for df <-> JSON:

```python
pj.dump_df_as_json(my_dataframe, 'info')
# => Will write a 'info.json' under /results
pj.read_json_df('info')
# => Will read the 'info.json' in /results
```

## Installation

```bash
git clone https://github.com/biocodices/project.git
cd project
python setup.py install
```
