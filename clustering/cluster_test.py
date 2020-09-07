from clustering import ROCK

# Cluster conferences held at least 4 times between 1960 and 1990
# Each author included in dataset has published 12 papers in that timeframe
# Each author included in dataset has published 5 papers to the included conferences

# Set clustering threshold to 0.225 (i.e. conferences must share at least 22.5% of authors to be considered 'similar')
# Set desired number of clusters to 1 (it is expected that the algorithm will halt prior to this point being reached)

instance = ROCK('1960-1990-4-12-5', 0.225, 1)
instance.cluster()
instance.show_cluster_info()
