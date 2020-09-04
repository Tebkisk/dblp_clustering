import pickle
from dblp_objects import (dblp_conference, dblp_author)

# serialise object to disk
def save(name, data):
    filepath = "./data/X.pkl".replace("X",name)
    picklefile = open(filepath, 'wb')
    pickle.dump(data, picklefile)
    picklefile.close()

# load object from disk
def load(name):
    filepath = "./data/X.pkl".replace("X",name)
    picklefile = open(filepath, 'rb')
    data = pickle.load(picklefile)
    picklefile.close()
    return data

# save human readable text file to disk
def log(name, data):
    filepath = "./logs/X.txt".replace("X",name)
    txtfile = open(filepath, "w")

    if type(data) == dict:
        key_type = type(data[list(data.keys())[0]])
        if key_type == dblp_conference or key_type == dblp_author:
            for x in list(data.keys()):
                txtfile.write(f'{data[x].getInfo()}\n')
        else:
            for x in list(data.keys()):
                txtfile.write(f'{x} : {data[x]}\n')
    else:
        for x in data:
            txtfile.write(f'{x}\n')

    txtfile.close()
