# dblp_clustering
An updated version of my final year Computer Science Project: Clustering Computer Science Conferences

This project consisted of two parts:

- The 'Dataset Builder' : a collection of modules and classes used to extract information from a DBLP Computer Science Bibliography xml dump which can be found [here](https://dblp.org/xml/)

- An implementation of ROCK: A Robust Clustering Algorithm for Categorical Attributes, the original paper for which can be found [here](http://theory.stanford.edu/~sudipto/mypapers/categorical.pdf)


## Prerequisites

In order to use this software, please ensure that you have a working Python 3.7.x distribution installed as well as the Python package manager pip. You can check if pip is installed on your system by entering the command 'pip -V' in a terminal emulator. If pip is not installed on your system, instructions for installing it can be found here: https://packaging.python.org/installing/

Once both Python and pip are installed, several Python packages need to be installed via the pip package manager:

- numpy: Used for matrix data structures and matrix manipulation (<https://www.numpy.org>)
- pandas: Used for storage of datasets and creation of input .csv files (<https://pandas.pydata.org>)
- heapq_max: Implementation of a max heap data structure. By default, Python only comes with a min heap from the core heapq module (<https://pypi.python.org/pypi/heapq_max/>)
- tqdm: Used for progress bars (<https://pypi.python.org/pypi/tqdm>)
- requests: Used for web scraping (<http://docs.python-requests.org/en/master/>)

You can install all of the above packages through pip with the following single command: 

``` pip install --user numpy pandas tqdm heapq_max requests```

## Dataset Builder

The Dataset Builder is concerned with extracting author and conference participation information from the raw data provided by the [DBLP Computer Science Bibliography](https://dblp.org). This raw data is given in the form of a single xml file several gigabytes in size detailing bibliographic information on scientific publications in the field of Computer Science. The records contained within it describe conference proceedings, journals, academic papers submitted to journals or conferences, books, and the respective authors and editors of the preceeding. 

When used, the Dataset Builder outputs a dataset containing conference names as rows (e.g. European Conference on Object-Oriented Programming (ECOOP)) and unique ids associated with authors as columns. Each row of the dataset contains a list of 0s and 1s with 1 denoting that an author has contributed a paper to this conference and 0 denoting that they have not.

### Prerequisites 

Before running the setup file, please ensure that you have downloaded the latest release of the raw data provided by DBLP. At this time, the most recent file available is dblp-2020-08-01.xml and it can be found [here](https://dblp.org/xml/) as a compressed .gz file. Once downloaded, this file should be placed in the Dataset Builder/data directory.

Additionally, a working internet connection is required during the setup phase to retrieve the names of each conference series as, while they are available on the DBLP website, they are not present in the raw data.

### Setup

Before the Dataset Builder can be used, several files need to be created from the raw xml data. In order to to this, please run the dataset_builder_setup file with the following command: ```python dataset_builder_setup.py```

This initial setup process will take around 40 - 60 minutes depending on your system due to the volume of data structures that need to be created. During this time, please ensure that your system does not enter sleep mode as this will halt execution.

### Usage

The Dataset Builder can be used either with or without command line arguments, in the case that none are provided the user will be prompted for them once the program runs. The parameters are as follows:

- Start year: The first year of the dataset to generate
- End year: The last year of the dataset to generate
- Conference frequency threshold: The number of times a conference must have been held between the start and end years for it to be included in the dataset
- Author publication threshold: The number of papers an author must have been credited for between the start and end years for them to be included in the dataset
- Crossover threshold: Of the selected conferences by the frequency threshold, how many of them must each selected author have published papers to?

If invoked from the command line with arguments, a typical usage would look like this:

 ``` python dataset_builder.py 1991 1995 3 10 5 ```
 
 Which would generate a dataset describing all conferences held a least three times between 1991 and 1995 as well as all authors that published at least 10 papers in general in that time and submitted papers to at least 5 of the conferences in the dataset
 
 If invoked from the command line without arguments, the user will be prompted to enter these parameters as a string separated by spaces. Once a dataset has been generated in this manner, the user will be prompted to enter a name for the dataset and it will be saved in the datasets directory

## Clustering

The clustering module contains an implementation of the [ROCK clustering algorithm](http://theory.stanford.edu/~sudipto/mypapers/categorical.pdf). This is a hierarchical agglomerative clustering algorithm well suited to clustering datasets with categorical as opposed to numerical attributes.

### Usage

Navigate to the /clustering directory and either create a .py script with the following statements or enter them directly into the python REPL:

```python 
from clustering import ROCK
instance = ROCK(dataset, threshold, desired_num_clusters, binarize, classified)
instance.cluster()
instance.remove_outliers(x)
print(instance.get_cluster_info())
```
Where:

- **dataset** is replaced with the filename of the dataset to be clustered
- **threshold** is replaced with a value between 0 and 1 representing the threshold for how similar one instance must be to another at minimum to be considered part of the same cluster
- **desired_num_clusters** is replaced with a number representing the desired number of clusters 
- **binarize** is an optional parameter (default is False) that will convert the categorical values in the dataset to those representable by either a zero or a one. For example, if a column had three possible values (a, b or c), by binarizing the data the column is replaced with three new columns (col_a, col_b, col_c) where a 1 represents the original col value
- **classified** is an optional parameter (default is False) that can be set to True if the data within the dataset is already classified into groups (see House votes example)
