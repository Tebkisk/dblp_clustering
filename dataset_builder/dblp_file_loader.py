from tqdm import tqdm
from itertools import (takewhile, repeat)

# Function to could the number of lines in the dblp xml file
def file_line_count(filename):
    f = open(filename, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
    return sum( buf.count(b'\n') for buf in bufgen if buf )

# Function to read dblp xml file into memory one line at a time
def load_dblp_file(dblp_file_path):
    dblp_content = ""
    num_lines = file_line_count(dblp_file_path)
    pbar = tqdm(total=num_lines, desc='Loading dblp file', leave=False)
    with open(dblp_file_path) as f:
        for line in f:
            dblp_content += line
            pbar.update(1)
    pbar.close()
    return dblp_content
