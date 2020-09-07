import os, sys, pandas as pd, numpy as np, heapq_max as hmax
from tqdm import tqdm, trange
from collections import OrderedDict

class ROCK:
    # Constructor
    def __init__(self, filename, threshold, num_clusters, classified = False, binarize = False):
        filepath = f"./datasets/{filename}.csv"
        # Check if dataset present in datasets directory
        if os.path.isfile(filepath):
            # Binarize dataset into 1/0 values if necessary
            if binarize == True:
                self.__data = self.binarize_data(pd.read_csv(filepath))
            else:
                self.__data = pd.read_csv(filepath)
            self.__classified = classified
            self.__data_size = len(self.__data.index)
            self.__desired_num_clusters = int(num_clusters)
            self.__threshold = float(threshold)
            self.__expected_links_exponent =  1.0 + (2.0 * ( (1.0 - threshold) / (1.0 + threshold)))

            # Each cluster starts out as a singleton list within a dictionary (i.e. {1 : [1], 2: [2], ...})
            self.__clusters = dict(zip(range(self.__data_size),[[index] for index in range(self.__data_size)]))
            self.__link = None
            self.__local_heaps = None
            self.__global_heap = None
        else:
            # Halt execution if specified dataset file does not exist
            print(f"File {filename} not in ./datasets directory.")
            sys.exit()

    def binarize_data(self, csv):
        # To binarize data, loop over initial columns
        # extract all possible values for each column
        # create new columns, one for each possible value (ignoring missing data represented by '?')
        # populate each new column with 1 representing the original value (e.g. 'y') and 0 for all others
        # delete original column

        df = csv
        initial_cols = csv.columns.tolist()[1:] # removes row label (conference name)
        pbar = tqdm(total = len(initial_cols), desc='Binarizing data')
        for col in initial_cols:
            initial_values = csv[col].unique().tolist()
            for value in initial_values:
                if value != '?':
                    new_col = col + "_" + value
                    df[new_col] = [1 if x == value else 0 for x in csv.loc[:, col]]
            del df[col]
            pbar.update(1)
        pbar.close()
        return df

    def get_jaccard_similarity(self, index_1, index_2):
        # Calculates |A ⋂ B | / | A ⋃ B | or cardinality of the intersection of A & B over the union of A & B
        # More simply, the number of elements contained within both A and B, divided by the number of elements in A or B

        row_1 = self.__data.iloc[index_1].tolist()
        row_2 = self.__data.iloc[index_2].tolist()

        # If the two rows are identical, they have a similarity of 1.0
        if row_1 == row_2:
            return 1.0

        # Else, calculate their similarity
        similar = 0.0
        different = 0.0

        for i in range(1, len(row_1)):
            if row_1[i] == 1 and row_2[i] == 1:
                similar += 1.0
            elif row_1[i] == 1:
                different += 1.0
            elif row_2[i] == 1:
                different += 1.0
        return similar / (similar + different)

    def create_adjacency_matrix(self):
        # This naive approach is very costly and grows quickly in execution time relative to input
        # Consider implementing compute_link procedure from fig. 4 of ROCK paper?

        # generate initial adjacency matrix, with all values set to 0
        matrix = np.zeros((self.__data_size,self.__data_size))
        for i in trange(0, self.__data_size,desc="Creating adjacency matrix"):
            for j in range(i + 1, self.__data_size):
                similarity = self.get_jaccard_similarity(i,j)
                # if data points i and j have a similarity greater than the
                # threshold, set corresponding matrix values to 1
                if (similarity >= self.__threshold):
                    matrix[i][j] = 1
                    matrix[j][i] = 1
        return matrix

    def compute_link(self):
        # create adjacency matrix
        adj = self.create_adjacency_matrix()
        # square it
        link = np.dot(adj,adj)
        # return completed link matrix
        return link

    def get_goodness(self, cluster_i , cluster_j):
        # The 'goodness measure' is a criterion function for determining which clusters should be merged
        # The higher the value of the criterion function, the better the two candidate clusters are for merging
        # The goodness measure is determined by dividing the number of cross links between two clusters by the expected number of cross links

        num_cross_links = self.__link[cluster_i][cluster_j]

        # n_i and n_j represent the number of points in cluster_i and cluster_j respectively
        n_i = len(self.__clusters[cluster_i])
        n_j = len(self.__clusters[cluster_j])

        expected_links_ni_nj = (n_i + n_j) ** self.__expected_links_exponent
        expected_links_ni = n_i ** self.__expected_links_exponent
        expected_links_nj = n_j ** self.__expected_links_exponent

        expected_num_cross_links = expected_links_ni_nj - expected_links_ni - expected_links_nj

        return (num_cross_links / expected_num_cross_links)

    def build_local_heaps(self):
        # Each cluster in the dataset has a local heap
        # The contents of each local heap for arbitrary cluster c_i is a reference to every other cluster c_j
        # such that the number of links between them is non-zero.
        # Each data point in a local heap is a tuple in which the first element is the goodness measure between clusters c_i and c_j
        # and the second element is a reference to cluster c_j
        # The contents of each local heap is ordered by the goodness measures from highest to lowest

        heaps = {}
        pbar = tqdm(total=len(self.__clusters),desc="Building local heaps")
        for i in list(self.__clusters):
            pbar.update(1)
            heaps[i] = []
            for j in self.__clusters:
                if i != j and self.__link[i][j] > 0:
                    heaps[i].append((self.get_goodness(i,j),j))
            if len(heaps[i]) == 0:
                del self.__clusters[i]
                del heaps[i]
            else:
                hmax.heapify_max(heaps[i])
        pbar.close()
        return heaps

    def build_global_heap(self):
        # The global heap is a heap containing the maximal elements of each local heap
        # it is ordered in the same way as local heaps, by goodness measure from highest to lowest
        # Thus, at any given time the maximal element of the global heap and the first element of the local heap it references
        # represent the two best clusters to merge at any given step of the algorithm

        heap = [(self.__local_heaps[i][0],i) for i in self.__local_heaps]
        hmax.heapify_max(heap)
        return heap

    def merge_clusters(self,cluster_i,cluster_j):
        # To merge clusters, the lists of elements in cluster_j are added to cluster_i
        # Subsequently, cluster_j is removed from the list of clusters
        merged_cluster = self.__clusters[cluster_i] + self.__clusters[cluster_j]
        del self.__clusters[cluster_j]
        return merged_cluster

    def remove_outliers(self, size_threshold):
        for cluster in list(self.__clusters.keys()):
            if len(self.__clusters[cluster]) <= size_threshold:
                del self.__clusters[cluster]

    def cluster(self):
        # Create squared adjacency matrix from data
        self.__link = self.compute_link()

        # Create initial local and global heaps
        self.__local_heaps = self.build_local_heaps()
        self.__global_heap = self.build_global_heap()

        pbar = tqdm(total=len(self.__clusters)-self.__desired_num_clusters,desc="Computing clusters:")

        # Continually merge clusters until desired number of clusters reached or the global heap is empty
        while len(self.__clusters) > self.__desired_num_clusters and len(self.__global_heap) != 0:

            # Extract best candidate clusters (i and j) for merging from the global heap
            best_clusters = hmax.heappop_max(self.__global_heap)
            cluster_i = best_clusters[1]
            cluster_j = best_clusters[0][1]

            # Delete cluster_j from the global heap as it is being merged into cluster_i
            for i in range(len(self.__global_heap)):
                if self.__global_heap[i][1] == cluster_j:
                    del self.__global_heap[i]
                    hmax.heapify_max(self.__global_heap)
                    break

            # Merge clusters i and j
            self.__clusters[cluster_i] = self.merge_clusters(cluster_i, cluster_j)


            # to_update = all points in local heaps of cluster_i & cluster_j
            points_in_cluster_i = set([y[1] for y in self.__local_heaps[cluster_i]]) - set([cluster_j])
            points_in_cluster_j = set([z[1] for z in self.__local_heaps[cluster_j]]) - set([cluster_i])
            to_update =  list(points_in_cluster_i | points_in_cluster_j)

            # empty local heap of cluster_i ready for reconstruction
            self.__local_heaps[cluster_i] = []

            # for each cluster_x in the union of local heaps for clusters i and j
            for cluster_x in to_update:
                # update link between cluster_x and cluster_i to be link[cluster_x][cluster_i] + link[cluster_x][cluster_j]
                self.__link[cluster_x][cluster_i] = self.__link[cluster_x][cluster_i] + self.__link[cluster_x][cluster_j]

                # delete clusters i and j from the local heap of cluster_x
                try:
                    for i in range(len(self.__local_heaps[cluster_x])):
                        if self.__local_heaps[cluster_x][i][1] == cluster_i:
                            del self.__local_heaps[cluster_x][i]
                            hmax.heapify_max(self.__local_heaps[cluster_x])
                            break
                    for i in range(len(self.__local_heaps[cluster_x])):
                        if self.__local_heaps[cluster_x][i][1] == cluster_j:
                            del self.__local_heaps[cluster_x][i]
                            hmax.heapify_max(self.__local_heaps[cluster_x])
                            break

                    # update local heap for cluster x with new entry for cluster_i
                    # update local heap for cluster_i with new entry for cluster_x
                    hmax.heappush_max(self.__local_heaps[cluster_x], (self.get_goodness(cluster_i, cluster_x), cluster_i))
                    hmax.heappush_max(self.__local_heaps[cluster_i], (self.get_goodness(cluster_i, cluster_x), cluster_x))
                except KeyError as e:
                    # | operator for set difference makes this uneccessary...
                    print(f'{x}: Outlier?')

            # delete local heap for cluster_j
            del self.__local_heaps[cluster_j]

            # Q_update(u)
            # if local heap for cluster_i is now empty, delete it from local heaps
            if self.__local_heaps[cluster_i] == []:
                del self.__local_heaps[cluster_i]
            # rebuild global heap based on updated local heaps
            self.__global_heap = self.build_global_heap()
            pbar.update(1)
        pbar.close()

    def get_cluster_info(self):
        # Create output string for discovered clusters
        output = ""
        cluster_count = 1
        if self.__classified == True:
            labels = self.__data[self.__data.columns.tolist()[0]].unique().tolist()
            for i in self.__clusters:
                label_counts = {}
                labels_in_cluster = [self.__data.iloc[x].tolist()[0] for x in self.__clusters[i]]
                for label in labels:
                    label_counts[label] = labels_in_cluster.count(label)
                output +=  ("Cluster " + str(cluster_count) + ": ")
                for j in label_counts:
                    output += (str(label_counts[j]) + " " + str(j) + ", ")
                output += "\b\b.\n"
                cluster_count += 1
        else:
            for i in self.__clusters :
                labels_in_cluster = [self.__data.iloc[x].tolist()[0] for x in self.__clusters[i]]
                output += ("Cluster " + str(cluster_count) + ":\n")
                for label in labels_in_cluster:
                    output += ("\t" + label + "\n")
                cluster_count += 1
        return output

    def get_cluster_detail(self, cluster):
        # Retrieve authors present in cluster + how many times they appear
        authors = {}
        cluster = list(self.__clusters.keys())[cluster-1]
        for conf in self.__clusters[cluster]:
            for i in range(0,len(self.__data.iloc[conf])):
                if self.__data.iloc[conf][i] == 1:
                    try:
                        authors[self.__data.columns.values[i]] += 1
                    except:
                        authors[self.__data.columns.values[i]] = 1

        authors = sorted(authors.items(), key = lambda x: x[1], reverse = True)
        authors = OrderedDict(authors)

        return authors

    def show_cluster_info(self):
        # Display output of get_cluster_info method
        print(self.get_cluster_info())

    def show_cluster_detail(self, cluster, max_authors = None):
        # Display output of get_cluster_detail method with optional max number of authors to display
        authors = self.get_cluster_detail(cluster)
        if max_authors:
            for author in list(authors.keys())[:max_authors]:
                print(f'{author}: {authors[author]}')
        else:
            for author in authors:
                print(f'{author}: {authors[author]}')
