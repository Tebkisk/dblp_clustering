import xml_processor, web_scraper, IO_utilities as io_, os, dblp_objects
from collections import OrderedDict
from tqdm import tqdm

class dataset_builder_setup:
    def __init__(self, dblp_filename):
        self.__raw_interface = xml_processor.extractor(dblp_filename)
        self.__web_interface = web_scraper.web_scraper('https://dblp.org')
        self._confs_xml = None
        self._papers_xml = None
        self._authors_xml = None

        self._series_ids = None
        self._conf_series_ids_to_names = None
        self._author_id_lookup = None
        self._disambiguation_ids = None
        self._conf_objects = {}
        self._author_objects = {}

    def extract_all_xml(self):
        pbar = tqdm(total=3, desc='Extracting conference records... ')
        self._confs_xml = self.__raw_interface.extract_records_by_tag('proceedings', 'conf')
        pbar.set_description('Extracting paper records... ')
        pbar.update(1)
        self._papers_xml = self.__raw_interface.extract_records_by_tag('inproceedings', 'conf')
        pbar.set_description('Extracting author records... ')
        pbar.update(1)
        self._authors_xml = self.__raw_interface.extract_records_by_tag('www', 'homepages')
        pbar.set_description('Finished extracting xml')
        pbar.update(1)
        pbar.close()

    def get_conference_series_ids(self):
        conf_series = [self.__raw_interface.extract_record_component('conference_id', x) for x in self._confs_xml]
        conf_series = list(OrderedDict.fromkeys(conf_series))
        return conf_series

    def get_conference_series_names(self, conf_series_ids):
        if self._confs_xml and self._series_ids:
            return self.__web_interface.retrieve_all_conf_series_names(conf_series_ids)

    def create_conf_objects(self, conf_ids_to_names):
        conf_objects = {}
        pbar = tqdm(total=len(self._confs_xml),desc='Creating conference objects ')
        for conf in self._confs_xml:
            conf_series_id = self.__raw_interface.extract_record_component('conference_id', conf)
            conf_year = self.__raw_interface.extract_record_component('conf_year', conf)

            try:
                conf_objects[conf_series_id].addYear(conf_year)
            except:
                conf_objects[conf_series_id] = dblp_objects.dblp_conference(conf_series_id)
                conf_objects[conf_series_id].setName(conf_ids_to_names[conf_series_id])
                conf_objects[conf_series_id].addYear(conf_year)
            pbar.update(1)
        pbar.close()
        return conf_objects

    def get_disambiguation_authors(self, authors_xml):
        disambiguation_authors_xml = [author for author in authors_xml if 'disambiguation' in author]
        disambiguation_ids = [self.__raw_interface.extract_record_component('author_id', author) for author in disambiguation_authors_xml]
        return disambiguation_ids

    def create_author_id_lookup(self, authors_xml):
        author_id_lookup = {}

        pbar = tqdm(total=len(authors_xml))
        for author_record in authors_xml:
            author_id = self.__raw_interface.extract_record_component('author_id',author_record)
            author_names = self.__raw_interface.extract_record_component('author_names',author_record)
            for name in author_names:
                try:
                    print(author_id_lookup[name])
                    print("Houston, we have a fucking problem...")
                except:
                    author_id_lookup[name] = author_id
            pbar.update(1)
        pbar.close()
        return author_id_lookup

    def create_author_objects(self, papers_xml):
        author_objects = {}
        pbar = tqdm(total=len(papers_xml), desc='Creating author objects')
        for paper in papers_xml:

            # Get cross reference to conference
            crossref = self.__raw_interface.extract_record_component('crossref',paper)
            if not crossref == None:
                paper_conf_id = crossref.split('/')[1]
            else:
                paper_url = self.__raw_interface.extract_record_component('url',paper)
                paper_conf_id = paper_url.split('/')[2]

            paper_id = self.__raw_interface.extract_record_component('paper_id',paper)
            paper_year = self.__raw_interface.extract_record_component('conf_year',paper) #CHANGE TO GENERIC YEAR!!
            author_names = self.__raw_interface.extract_record_component('author_names',paper)
            author_ids_for_paper = [self._author_id_lookup[name] for name in author_names]
            author_ids_for_paper = [id for id in author_ids_for_paper if id not in self._disambiguation_ids]

            for author_id in author_ids_for_paper:
                try:
                    author_objects[author_id].addConf(paper_year,paper_conf_id)
                except:
                    try:
                        author_objects[author_id].addConfYear(paper_year)
                        author_objects[author_id].addConf(paper_year,paper_conf_id)
                    except:
                        author_objects[author_id] = dblp_objects.dblp_author(author_id)
                        author_objects[author_id].addConfYear(paper_year)
                        author_objects[author_id].addConf(paper_year,paper_conf_id)

                try:
                    author_objects[author_id].addPaper(paper_year,paper_id)
                except:
                    try:
                        author_objects[author_id].addPaperYear(paper_year)
                        author_objects[author_id].addPaper(paper_year,paper_id)
                    except:
                        #print("Will be interesting if this ever executes...")
                        author_objects[author_id] = dblp_objects.dblp_author(author_id)
                        author_objects[author_id].addPaperYear(paper_year)
                        author_objects[author_id].addPaper(paper_year,paper_id)

            pbar.update(1)
        pbar.close()
        return author_objects

    def start(self):
        return

def main():

    essential_files = [
    'series_ids_to_names',
    'author_id_lookup',
    'disambiguation_ids',
    'conf_objects',
    'author_filenames']

    if all([os.path.isfile(f'./data/{filename}.pkl') for filename in essential_files]):
        print("All essential files exist, dataset builder is ready to use.")
        sys.exit()

    setup = dataset_builder_setup('dblp-2020-08-01')
    setup.extract_all_xml()

    if os.path.isfile('./data/series_ids_to_names.pkl'):
        print('Loading series_ids_to_names.pkl')
        setup._conf_series_ids_to_names = io_.load('series_ids_to_names')
    else:
        setup._series_ids = setup.get_conference_series_ids()
        setup._conf_series_ids_to_names = setup.get_conference_series_names(setup._series_ids)
        io_.save('series_ids_to_names', setup._conf_series_ids_to_names)
        io_.log('series_ids_to_names', setup._conf_series_ids_to_names)

    if os.path.isfile('./data/author_id_lookup.pkl'):
        print('Loading author_id_lookup.pkl')
        setup._author_id_lookup = io_.load('author_id_lookup')
    else:
        setup._author_id_lookup = setup.create_author_id_lookup(setup._authors_xml)
        io_.save('author_id_lookup', setup._author_id_lookup)
        io_.log('author_id_lookup', setup._author_id_lookup)

    if os.path.isfile('./data/disambiguation_ids.pkl'):
        print('Loading disambiguation_ids.pkl')
        setup._disambiguation_ids = io_.load('disambiguation_ids')
    else:
        setup._disambiguation_ids = setup.get_disambiguation_authors(setup._authors_xml)
        io_.save('disambiguation_ids', setup._disambiguation_ids)
        io_.log('disambiguation_ids', setup._disambiguation_ids)

    if os.path.isfile('./data/conf_objects.pkl'):
        print('Loading conf_objects.pkl')
        setup._conf_objects = io_.load('conf_objects')
    else:
        setup._conf_objects = setup.create_conf_objects(setup._conf_series_ids_to_names)
        io_.save('conf_objects', setup._conf_objects)
        io_.log('conf_objects', setup._conf_objects)


    if os.path.isfile('./data/author_filenames.pkl'):
        print('Loading author objects')
        author_filenames = io_.load('author_filenames')
        pbar = tqdm(total=len(author_filenames))
        for file in author_filenames:
            pbar.set_description(file)
            pbar.refresh()
            temp_dict = io_.load(file)
            setup._author_objects.update(temp_dict)
            pbar.update(1)
        pbar.close()
    else:
        setup._author_objects = setup.create_author_objects(setup._papers_xml)
        pbar = tqdm(total=16,desc='Saving author object files to disk. This may take several minutes.', leave=False)

        key_copy = list(setup._author_objects.keys())
        filenames = []
        file_count = 0
        for i in key_copy:
            if len(key_copy) != 0:
                temp_dict = {}
                for j in key_copy[:100000]:
                    temp_dict[j] = setup._author_objects[j]
                filename = "authors_" + str(file_count)
                filenames.append(filename)
                file_count += 1
                io_.save(filename, temp_dict)
                io_.log(filename,temp_dict)
                key_copy = key_copy[100000:]
                pbar.update(1)
        io_.save("author_filenames", filenames)

        pbar.close()

    print("All essential files created, dataset builder is ready to use.")

if __name__ == '__main__':
    main()
