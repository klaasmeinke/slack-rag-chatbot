from datetime import datetime
from smartsearch.config import Config
import json
from notion_client import Client
from smartsearch.notion_page import Page
import os
from tqdm import tqdm
from typing import Dict, List


class Notion:
    def __init__(self, config: Config, fetch_pages: bool = False, scrape_pages: bool = False):
        self.config = config
        self.client = Client(auth=config.NOTION_API_KEY)
        self.pages: Dict[str, Page] = dict()
        if not os.path.exists(config.file_notion) and not (fetch_pages and scrape_pages):
            err = f'notion data file {config.file_notion} must exist when not fetching or creating notion pages.'
            raise ValueError(err)
        self.load_from_data()

        if fetch_pages:
            self.fetch_pages()  # creates a list of unscraped pages
        if scrape_pages:
            self.scrape_pages()

    @property
    def unscraped_pages(self) -> List[str]:
        return [page.url for page in self.pages.values() if not page.is_scraped]

    def scrape_pages(self):
        for url in tqdm(self.unscraped_pages, desc='Scraping Notion Pages', disable=not self.unscraped_pages):
            self.pages[url].scrape(client=self.client)
            self.save_data()

    def add_page(self, page: Page):
        if page.url in self.pages:
            self.pages[page.url].update_from_page(page)
        else:
            self.pages[page.url] = page

    def keep_last_n_pages(self, n: int):
        """use for testing"""
        last_edited_list = sorted([p.last_edited for p in self.pages.values()])
        threshold = last_edited_list[-n]
        self.pages = {url: page for url, page in self.pages.items() if page.last_edited >= threshold}

    def fetch_pages(self):
        """fill self.pages with all pages from notion (unscraped)"""

        # make api requests to get all pages and append them to results
        has_more = True
        start_cursor = None
        results = []

        while has_more:
            response = self.client.search(query='', page_size=100, start_cursor=start_cursor)

            start_cursor = response['next_cursor']
            has_more = response['has_more']
            results += response['results']

        # get titles of all results
        def extract_title_from_response(_result) -> str:

            if _result['object'] == 'database':
                if not len(_result['title']):
                    return 'Untitled'
                return _result['title'][0]['text']['content']

            for key in _result['properties']:
                if _result['properties'][key]['id'] == 'title':
                    if _result['properties'][key]['title'] and 'text' in _result['properties'][key]['title'][0]:
                        return _result['properties'][key]['title'][0]['text']['content']
                    else:
                        return 'Untitled'
            return 'Untitled'

        id_to_title = {result['id']: extract_title_from_response(result) for result in results}

        # dictionary of each result's parent allows for parents in page titles
        id_to_parent_id = {
            result['id']: result['parent'][result['parent']['type']] for result in results
            if 'parent' in result
        }

        for result in results:
            if result['object'] != 'page':
                continue

            # get page title including chain of parents
            title = extract_title_from_response(result)
            last_edited = datetime.strptime(result['last_edited_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            url = result['url']

            parent_id = id_to_parent_id.get(result['id'])
            while parent_id in id_to_parent_id:
                title = id_to_title[parent_id] + '/' + title
                parent_id = id_to_parent_id[parent_id]

            header_items = [f'Title: {title}', f'Last Edited: {last_edited}']
            formatted_properties = [
                f'{prop_name}: {self._extract_content_from_properties(prop_info)}'
                for prop_name, prop_info in result['properties'].items()
                if prop_info['id'] != 'title'
            ]
            header_items += formatted_properties
            header = '\n'.join(header_items)

            page = Page(header=header, url=url, last_edited=last_edited)
            self.add_page(page)

    def _extract_content_from_properties(self, _prop_info: dict) -> str:
        """recursively unpack the properties dict and extract content"""
        _child = _prop_info
        while isinstance(_child, dict) and 'type' in _child:
            _child = _child[_child['type']]
        while isinstance(_child, dict) and 'name' in _child:
            _child = _child['name']
        while isinstance(_child, dict) and 'plain_text' in _child:
            _child = _child['plain_text']
        while isinstance(_child, dict) and 'content' in _child:
            _child = _child['content']
        while isinstance(_child, dict) and 'email' in _child:
            _child = _child['email']
        if isinstance(_child, dict) and 'id' in _child:
            return ''
        if not _child:
            return ''
        if isinstance(_child, list):
            _child = ' '.join(self._extract_content_from_properties(x) for x in _child)

        return str(_child).strip()

    def save_data(self):
        directory = os.path.dirname(self.config.file_notion)
        if directory:
            os.makedirs(directory, exist_ok=True)

        data = [p.save_to_dict() for p in self.pages.values()]
        with open(self.config.file_notion, 'w') as f:
            json.dump(data, f)

    def load_from_data(self):
        if not os.path.exists(self.config.file_notion):
            return
        with open(self.config.file_notion) as json_file:
            data: List[Dict[str, str]] = json.load(json_file)
        for page_data in data:
            page = Page.load_from_dict(page_data)
            self.add_page(page)


def refresh_data():
    print('Fetching all pages from notion... ', end='')
    config = Config()
    notion = Notion(config=config, fetch_pages=True)
    print(len(notion.pages))

    print(f'Scraping {len(notion.unscraped_pages)} pages')
    notion.scrape_pages()


if __name__ == "__main__":
    refresh_data()
