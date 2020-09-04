import os.path, re, html, sys, dblp_file_loader
from tqdm import tqdm

class extractor:
    # Constructor
    def __init__(self, dblp_filename):
        self.__dblp_filepath = "./data/" + dblp_filename + ".xml"
        self.__dblp_file = ""
        # Check if specified dblp file is present in ./data directory
        if not os.path.isfile(self.__dblp_filepath):
            print(f"File {dblp_filename}.xml could not be found in ./data directory.")
            sys.exit()
        else:
            self.__dblp_file = dblp_file_loader.load_dblp_file(self.__dblp_filepath)

    def extract_records_by_tag(self, tag, tag_key = None):
        re_string = f"<{tag}([\s\S]*?)</{tag}>"
        if tag_key:
            results = [x.replace('\n','') for x in re.findall(re_string, self.__dblp_file) if f"key=\"{tag_key}" in x]
            results = list(map(html.unescape, results))
        else:
            results = [x.replace('\n','') for x in re.findall(re_string, self.__dblp_file)]
            results = list(map(html.unescape, results))
        return results

    def extract_record_component(self, component, record):
        if component == 'conference_id': # TODO CHANGE TO SERIES!
            re_string = 'key="conf/([\s\S]*?)/'
            result = re.search(re_string, record).group(1)
        elif component == 'series_name':
            re_string = '<series ([\s\S]*?)>([\s\S]*?)</series>'
            result = re.search(re_string, record)
            if result:
                result = result.group(2)
            else:
                return None
        elif component == 'author_id':
            re_string = 'homepages/([\s\S]*?)"'
            result = re.search(re_string, record).group(1)
        elif component == 'author_names':
            re_string = '<author(?:[\s\S]*?)>([\s\S]*?)</author>'
            result = re.findall(re_string, record)
        elif component == 'conf_year':
            re_string = '<year>([\s\S]*?)</year>'
            result = re.search(re_string, record).group(1)
        elif component == 'crossref':
            re_string = '<crossref>([\s\S]*?)</crossref>'
            result = re.search(re_string, record)
            if not result == None:
                result = result.group(1)
            else:
                return None
        elif component == 'url':
            re_string = '<url>([\s\S]*?)</url>'
            result = re.search(re_string, record).group(1)
        elif component == 'paper_id':
            re_string = 'key="([\s\S]*?)"'
            result = re.search(re_string, record).group(1)
        else:
            print("Unknown component argument.")
            return None
        return result
        
    def check_tag_present(self, tag, record):
        re_string = f'<{tag}'
        if re.search(re_string, record):
            return True
        else:
            return False
