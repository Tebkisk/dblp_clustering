import os, sys, pandas as pd, IO_utilities as io_
from tqdm import tqdm

class dataset_builder():
    def __init__(self, start_year, end_year, conf_freq_threshold, author_pub_threshold, crossover_threshold):

        self.__essential_files = [
        'conf_objects',
        'author_filenames']

        self.__authors = None
        self.__author_id_lookup = None
        self.__disambiguation_ids = None
        self.__confs = None
        self.__conf_name_lookup = None

        self._start_year = start_year
        self._end_year = end_year
        self.__conf_freq_threshold = conf_freq_threshold
        self.__author_pub_threshold = author_pub_threshold
        self.__crossover_threshold = crossover_threshold

        self.__min_year = 9999
        self.__max_year = 0

        self._date_range = None
        self._conferences_to_include = None
        self._authors_to_include = None

    def set_conf_freq_threshold(self, threshold):
        self.__conf_freq_threshold = threshold

    def set_author_pub_threshold(self, threshold):
        self.__author_pub_threshold = threshold

    def set_crossover_threshold(self, threshold):
        self.__crossover_threshold = threshold

    def load_essential_files(self):
        # load conference and author objects from ./data directory

        if not all([os.path.isfile(f'./data/{filename}.pkl') for filename in self.__essential_files]):
            print("Essential file(s) missing, please run setup file.")
            sys.exit()

        author_filenames = io_.load('author_filenames')
        pbar = tqdm(total=len(author_filenames)+1, desc='Loading essential files', leave=False)

        self.__confs = io_.load('conf_objects')
        pbar.update(1)

        author_filenames = io_.load('author_filenames')

        self.__authors = {}
        for file in author_filenames:
            temp_dict = io_.load(file)
            self.__authors.update(temp_dict)
            pbar.update(1)
        pbar.close()

    def set_min_max_years(self):
        # Loop over conference objects and determine earliest & latest year values
        for conf_id in self.__confs:
            for year in self.__confs[conf_id].getYears():
                if int(year) < self.__min_year:
                    self.__min_year = int(year)
                if int(year) > self.__max_year:
                    self.__max_year = int(year)

    def check_year_params(self):
        # Check that the parameters for start & end years are within min & max years
        if self._start_year < self.__min_year:
            print("Start year out of range.")
            return False
        elif self._end_year > self.__max_year:
            print("End year out of range.")
            return False
        elif self._end_year < self._start_year:
            print("End year before start year.")
            return False
        else:
            return True

    def check_thresholds(self):
        # Check that parameters entered for threshold values are integers

        if not type(self.__conf_freq_threshold) == int:
            print("Conference frequency threshold must be an integer.")
            return False
        elif not type(self.__author_pub_threshold) == int:
            print("Author publication threshold must be an integer.")
            return False
        elif not type(self.__crossover_threshold) == int:
            print("Crossover threshold must be an integer")
            return False
        else:
            return True

    def trim_conferences(self):
        confs_to_include = []
        # Loop over conference objects
        # Loop over years attribute of each conference object
        # If conference was held as many or more times than the threshold, include it

        pbar = tqdm(total=len(self.__confs), desc='Trimming conferences to meet frequency threshold', leave=True)
        for conf_id in self.__confs:
            years_within_date_range = []
            for year in self.__confs[conf_id].getYears():
                    if int(year) in self._date_range:
                        years_within_date_range.append(year)

            if len(years_within_date_range) >= self.__conf_freq_threshold:
                confs_to_include.append(conf_id)
            pbar.update(1)
        pbar.close()
        return confs_to_include

    def trim_authors(self):
        authors_to_include = set()

        pbar = tqdm(total=len(self.__authors), desc='Trimming authors to meet publication threshold', leave=True)

        # Loop over all author objects & count total number of papers published within year range
        for author_id in self.__authors:
            num_papers = 0
            for year in self.__authors[author_id].papers:
                if int(year) in self._date_range:
                    num_papers += len(self.__authors[author_id].papers[year])

            # If author has published a sufficient number of papers
            if num_papers >= self.__author_pub_threshold:
                # loop over year keys in author object confs attribute
                for year in self.__authors[author_id].confs:
                    # if year is within date range
                    if int(year) in self._date_range:
                        # loop over conferences published to in that year
                        for conf_id in list(self.__authors[author_id].confs[year]):
                            # if conference id is in conferences_to_include, add author to authors_to_include
                            if conf_id in self._conferences_to_include:
                                authors_to_include.add(author_id)
            pbar.update(1)
        pbar.close()
        return authors_to_include

    def create_dataset(self):
        dataset = {}

        pbar = tqdm(total=len(self._authors_to_include), desc='Creating dataset', leave=True)
        # loop over authors_to_include
        for author_id in self._authors_to_include:
            dataset[author_id] = set()
            # loop over year keys in author object confs attribute
            for year in self.__authors[author_id].confs:
                # if year is within date range
                if int(year) in self._date_range:
                    # loop over conferences published to in that year
                    for conf_id in list(self.__authors[author_id].confs[year]):
                        # if conference id is in conferences_to_include, add conf_id to current row of dataset
                        if conf_id in self._conferences_to_include:
                            dataset[author_id].add(conf_id)
            pbar.update(1)
        pbar.close()
        return dataset

    def create_pandas_dataframe(self, dataset):
        rows = []

        pbar = tqdm(total=len(self._conferences_to_include), desc='Converting dataset to pandas DataFrame', leave=True)
        for conf_id in self._conferences_to_include:
            confs = {}
            for author_id in dataset:
                if conf_id in dataset[author_id]:
                    confs[author_id] = 1
                else:
                    confs[author_id] = 0
            rows.append(confs)
            pbar.update()
        pbar.close()

        labels = []
        for i in range(len(self._conferences_to_include)):
            labels.append(self.__confs[self._conferences_to_include[i]].name)

        dataframe = pd.DataFrame(rows, index=labels)

        dataframe.loc['Total'] = dataframe.sum()
        temp_df = dataframe.T
        # remove authors that contributed to only one conference
        temp_df = temp_df[temp_df["Total"] >= int(self.__crossover_threshold)]
        del temp_df["Total"]

        temp_df.loc['Total'] = temp_df.sum()
        dataframe = temp_df.T
        # remove any conferences that have no authors
        dataframe = dataframe[dataframe["Total"] > 1]
        del dataframe["Total"]

        print (f"Dimensions of final matrix: {len(dataframe.index)} conference series by {len(dataframe.columns)} authors.")
        dataframe.index.names = ['Conference']
        dataframe_name = input("Please enter a name for the dataframe: ")
        dataframe.to_csv('./datasets/X.csv'.replace('X',dataframe_name), encoding='utf-8')
        print("Done. Dataframe saved in ./datasets directory")


def main():
    # If dataset_builder.py was called with command line arguments, generate single dataset
    if len(sys.argv) > 1:
        args = [int(arg) for arg in sys.argv[1:]]
        if len(args) == 5:
            db = dataset_builder(*args)
            db.load_essential_files()
            db.set_min_max_years()
        else:
            print('Incorrect number of parameters provided. 5 expected.')
            sys.exit()

        if not db.check_thresholds():
            print('Threshold test failed')
            sys.exit()
        elif not db.check_year_params():
            print('Year test failed')
            sys.exit()
        else:
            db._date_range = range(db._start_year, db._end_year+1)

        db._conferences_to_include = db.trim_conferences()
        db._authors_to_include = db.trim_authors()
        dataset = db.create_dataset()
        db.create_pandas_dataframe(dataset)

    # Else prompt user for arguments & keep going until user types 'q' or 'quit'
    else:
        db = dataset_builder(None,None,None,None,None)
        db.load_essential_files()
        while True:
            args = input("Please enter values for the following parameters separated by spaces, or type q to quit:\n\tStart year\n\tEnd year\n\tConference frequency threshold\n\tAuthor publication threshold\n\tCrossover threshold\n>>>")

            # If user types 'q' or 'quit', exit the program
            if args in ['q', 'quit']:
                sys.exit()

            args = [int(arg) for arg in args.split(' ')]

            db._start_year = args[0]
            db._end_year = args[1]
            db.set_conf_freq_threshold(args[2])
            db.set_author_pub_threshold(args[3])
            db.set_crossover_threshold(args[4])

            db.set_min_max_years()

            if not db.check_thresholds():
                print('Threshold test failed')
                sys.exit()
            elif not db.check_year_params():
                print('Year test failed')
                sys.exit()
            else:
                db._date_range = range(db._start_year, db._end_year+1)

            db._conferences_to_include = db.trim_conferences()
            db._authors_to_include = db.trim_authors()
            dataset = db.create_dataset()
            db.create_pandas_dataframe(dataset)
            print('\n')

if __name__ == '__main__':
    main()
