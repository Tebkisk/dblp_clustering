# import implementation of ROCK algorithm
from clustering import ROCK

# create test instance of ROCK class
#   parameter 1: name of data set .csv file in ./data directory
#   paramater 2: similarity threshold
#   parameter 3: num desired clusters
#   parameter 4: are data points labelled in first column?
#   parameter 5: does data need to be binarized?

test_instance = ROCK('house-votes-84.data', 0.73, 2, True, True)

# run clustering algorithm
test_instance.cluster()

# remove outliers
test_instance.remove_outliers(3)

# display results
print(test_instance.get_cluster_info())
