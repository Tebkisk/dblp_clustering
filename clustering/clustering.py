import os, sys, pandas as pd, numpy as np, heapq_max as hmax
from tqdm import tqdm, trange

class ROCK:
    # Constructor
    def __init__(self, filename, threshold, num_clusters, classified = True, binarize = True):
        filepath = f"./datasets/{filename}.csv"
        # Check if dataset present in
        if os.path.isfile(filepath):
            if binarize == True:
                self.__data = self.binarize_data(pd.read_csv(filepath))
            else:
                self.__data = pd.read_csv(filepath)
                print(self.__data)
            self.__data_size = len(self.__data.index)
            self.__desired_num_clusters = int(num_clusters)
            self.__threshold = float(threshold)
            self.__expected_links_exponent =  1.0 + (2.0 * ( (1.0 - threshold) / (1.0 + threshold)))
            self.__clusters = dict(zip(range(self.__data_size),[[index] for index in range(self.__data_size)]))
            self.__link = None
            self.__local_heaps = None
            self.__global_heap = None
            if classified == True:
                self.__classified = True
            else:
                self.__classified = False
        else:
            print(f"File {filename} not in ./datasets directory.")
            sys.exit()

    def binarize_data(self,csv):
        df = csv
        initial_cols = csv.columns.tolist()[1:] # removes
        pbar = tqdm(total = len(initial_cols), desc='Binarizing data')
        for col in initial_cols:
            suffixes = csv[col].unique().tolist()
            for suffix in suffixes:
                if suffix != '?':
                    new_col = col + "_" + suffix
                    df[new_col] = [1 if x == suffix else 0 for x in csv.loc[:, col]]
            del df[col]
            pbar.update(1)
        pbar.close()
        return df

    def get_jaccard_similarity(self,index_1, index_2):
        instance_1 = self.__data.iloc[index_1].tolist()
        instance_2 = self.__data.iloc[index_2].tolist()
        if instance_1 == instance_2:
            return 1.0
        similar = 0.0
        different = 0.0

        for i in range(1, len(instance_1)): #change to data_length?
            if instance_1[i] == 1 and instance_2[i] == 1:
                similar += 1.0
            elif instance_1[i] == 1:
                different += 1.0
            elif instance_2[i] == 1:
                different += 1.0
        return similar / (similar + different)

    def create_adjacency_matrix(self):
        # generate initial adjacency matrix, with all values set to 0
        matrix = np.zeros((self.__data_size,self.__data_size))
        for i in trange(0, self.__data_size,desc="Computing links"):
            for j in range(i + 1, self.__data_size):
                sim = self.get_jaccard_similarity(i,j)
                # if data points i and j have a similarity greater than the
                # threshold, set corresponding matrix values to 1
                if (sim >= self.__threshold):
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

    def get_goodness(self,c_i,c_j):
        num_cross_links = self.__link[c_i][c_j]
        n_i = len(self.__clusters[c_i])
        n_j = len(self.__clusters[c_j])

        expected_links_ni = n_i ** self.__expected_links_exponent
        expected_links_nj = n_j ** self.__expected_links_exponent
        expected_links_ni_nj = (n_i + n_j) ** self.__expected_links_exponent
        expected_num_cross_links = expected_links_ni_nj - expected_links_ni - expected_links_nj

        return (num_cross_links / expected_num_cross_links)

    def build_local_heaps(self):
        heaps = {}
        pbar = tqdm(total=len(self.__clusters),desc="Building local heaps")
        for i in list(self.__clusters):
            to_delete = []
            pbar.update(1)
            heaps[i] = []
            for j in self.__clusters:
                if i != j and self.__link[i][j] > 0:
                    heaps[i].append((self.get_goodness(i,j),j))
            if len(heaps[i]) == 0:
                del self.__clusters[i]
                del heaps[i]
                #to_delete.append(i)
            else:
                hmax.heapify_max(heaps[i])

        #for i in to_delete:
        #    del self.__clusters[i]
        #    del heaps[i]
        pbar.close()
        return heaps

    def build_global_heap(self):
        heap = [(self.__local_heaps[i][0],i) for i in self.__local_heaps]
        hmax.heapify_max(heap)
        return heap

    def merge_clusters(self,i,j):
        w = self.__clusters[i] + self.__clusters[j]
        del self.__clusters[j]
        return w

    def get_clusters(self):
        return self.__clusters

    def get_cluster(self,i):
        return self.__clusters[i]

    def remove_outliers(self, size_threshold):
        for cluster in list(self.__clusters.keys()):
            if len(self.__clusters[cluster]) <= size_threshold:
                del self.__clusters[cluster]

    def get_cluster_info(self):
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

    def cluster(self):
        self.__link = self.compute_link()
        self.__local_heaps = self.build_local_heaps()
        self.__global_heap = self.build_global_heap()

        pbar = tqdm(total=len(self.__clusters)-self.__desired_num_clusters,desc="Computing clusters:")
        while len(self.__clusters) > self.__desired_num_clusters and len(self.__global_heap) != 0:

            # u & v extracted from global heap
            u_v = hmax.heappop_max(self.__global_heap)
            u = u_v[1]
            v = u_v[0][1]

            # Q_delete(v)
            for i in range(len(self.__global_heap)):
                if self.__global_heap[i][1] == v:
                    del self.__global_heap[i]
                    hmax.heapify_max(self.__global_heap)
                    break
            # merge(u,v)
            self.__clusters[u] = self.merge_clusters(u,v)

            # to_update = all points in local heaps of u & v
            to_update = list((set([y[1] for y in self.__local_heaps[v]]) - set([u])) | (set([z[1] for z in self.__local_heaps[u]]) - set([v])))

            # empty local heap of u ready for reconstruction
            self.__local_heaps[u] = []

            # for each x in q[u] union q[v]
            for x in to_update:
                # update link between x and u to be link[x][u] + link[x][v]
                self.__link[x][u] = self.__link[x][u] + self.__link[x][v]

                # delete u & v from local heap of x
                try:
                    for i in range(len(self.__local_heaps[x])):
                        if self.__local_heaps[x][i][1] == u:
                            del self.__local_heaps[x][i]
                            hmax.heapify_max(self.__local_heaps[x])
                            break
                    for i in range(len(self.__local_heaps[x])):
                        if self.__local_heaps[x][i][1] == v:
                            del self.__local_heaps[x][i]
                            hmax.heapify_max(self.__local_heaps[x])
                            break

                    # insert (q[x],u,g(x,u)) & insert (q[u],x,g(x,u))
                    hmax.heappush_max(self.__local_heaps[x],(self.get_goodness(u,x),u))
                    hmax.heappush_max(self.__local_heaps[u],(self.get_goodness(u,x),x))
                except KeyError as e:
                    print(f'{x}: Outlier?')
            del self.__local_heaps[v]

            # Q_update(u)
            if self.__local_heaps[u] == []:
                del self.__local_heaps[u]
            self.__global_heap = self.build_global_heap()
            pbar.update(1)
        pbar.close()
