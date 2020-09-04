import requests, time, re, html
from tqdm import tqdm

class web_scraper:
    def __init__(self, initial_url):
        self.__base_dblp_url = initial_url
        self.__alt_urls = ['https://dblp.org','http://dblp.uni-trier.de', 'https://dblp2.uni-trier.de ', 'https://dblp.dagstuhl.de']
        self.__alt_urls.remove(initial_url)

    # Method to retrieve full title of conference series by unique id
    def _retrieve_conf_series_name(self, conf_id):
        url = f"{self.__base_dblp_url}/db/conf/{conf_id}/index.html"
        page = requests.get(url)
        if page.status_code == 200:
            re_string = '<h1>([\s\S]*?)</h1>'
            conf_series_name = re.search(re_string, page.text).group(1)

            # In event of a redirection, follow the link and retrieve from there
            redirect_texts = ["Redirecting ...", "Redirect ...", "Redirection ..."]
            if conf_series_name in redirect_texts:
                re_string=f'<p><a href="([\s\S]*?)/db/conf/([\s\S]*?)/index.html"'
                redirect_id = re.search(re_string, page.text).group(2)
                return self.retrieve_conf_series_name(redirect_id)
            else:
                # Use html module to convert html entities (e.g. &amp; -> &)
                return html.unescape(conf_series_name)
        elif page.status_code == 404:
            # Hard coded workarounds for malformed id urls
            # ecoopwException -> ecoopw
            if conf_id == 'ecoopwException':
                return self.retrieve_conf_series_name('ecoopw')
            # planX -> planx
            elif conf_id == 'planX':
                return self.retrieve_conf_series_name('planx')
            else:
                print("Unkown 404 Error")
        elif page.status_code == 429:
            return 'RATE LIMIT FAILURE'
        else:
            print(f"PAGE LOAD ERROR: {page.status_code}")

    # Method to retrieve full titles of a list of conference series ids
    def retrieve_all_conf_series_names(self, conf_ids):
        # Initialise progress bar
        pbar = tqdm(total = len(conf_ids), desc='Fetching conf series names from dblp.org')

        # Declare empty dict structure to hold id -> name pairs
        conf_ids_to_names = {}

        # Loop through all ids in conf_ids argument and attempt to retrieve names from dblp website
        for id in conf_ids:
            conf_name = self._retrieve_conf_series_name(id)

            if not conf_name == 'RATE LIMIT FAILURE':
                conf_ids_to_names[id] = conf_name

            # If server sends a 429 'Too many requests' response, sleep for 5 seconds and swtich to alternate url
            else:
                while conf_name == 'RATE LIMIT FAILURE':
                    time.sleep(5)
                    self.__alt_urls.append(self.__base_dblp_url)
                    self.__base_dblp_url = self.__alt_urls.pop(0)
                    conf_name = self._retrieve_conf_series_name(id)
                conf_ids_to_names[id] = conf_name

            # Upon successful retrieval, increment progress bar
            pbar.update(1)
        pbar.close()
        return conf_ids_to_names
