from datetime import datetime
from hadriangpt.config import Config
import json
from notion_client import Client
import os
from pydantic import BaseModel
from ratemate import RateLimit  # type: ignore
from tqdm import tqdm
from typing import Dict, List, Optional


rate_limit = RateLimit(max_count=3, per=1, greedy=True)


class Page(BaseModel):
    url: str
    header: str
    last_edited: datetime
    content: str = ''
    last_scraped: datetime = datetime.min
    _depth: int = 0  # used to track indentation level when blocks are scraped

    def __str__(self):
        return self.header + self.content

    @property
    def is_scraped(self):
        return self.last_scraped >= self.last_edited

    def scrape(self, client):
        if self.is_scraped:
            return
        self.last_scraped = datetime.now()
        block_id = self.url[-32:]
        self._depth = 0
        self.scrape_block(client, block_id)

    def scrape_block(self, client: Client, block_id: str):
        """ recursive function that scrapes a block and its children and adds them to the content """
        children = client.blocks.children.list(block_id, page_size=100)['results']
        rate_limit.wait()

        for block in children:
            formatted_block = self.format_block(block)
            if formatted_block:
                self.content += formatted_block.replace('\n', '\n'+self._depth*'  ')
            if block['has_children'] and block['type'] != 'child_page':
                self._depth += 1
                self.scrape_block(client, block_id=block['id'])
                self._depth -= 1

    @staticmethod
    def format_block(block) -> Optional[str]:

        prefixes = {
            'child_page': '\nchild page: ',
            'code': '\n```',
            'callout': '\n',
            'paragraph': '\n',
            'heading_3': '\n###',
            'heading_2': '\n##',
            'heading_1': '\n# ',
            'to_do': '\n- ',
            'numbered_list_item': '\n- ',
            'bulleted_list_item': '\n- ',
        }

        suffixes = {
            'child_page': '',
            'code': '```',
            'callout': '',
            'paragraph': '',
            'heading_3': '',
            'heading_2': '',
            'heading_1': '',
            'to_do': '',
            'numbered_list_item': '',
            'bulleted_list_item': '',
        }

        block_type = block['type']
        if block_type not in prefixes.keys():
            return None

        if 'rich_text' in block[block_type] and block[block_type]['rich_text']:
            block_content = prefixes[block_type]
            block_content += ''.join([b['text']['content'] for b in block[block_type]['rich_text'] if 'text' in b])
            block_content += suffixes[block_type]
            if block_type == 'to_do':
                block_content += ' (done)' if block['to_do']['checked'] else ' (to-do)'
            return block_content

        elif 'title' in block[block_type] and block[block_type]['title']:
            block_content = prefixes[block_type]
            block_content += block[block_type]['title']
            block_content += suffixes[block_type]
            return block_content

        return None

    def save_to_dict(self) -> Dict[str, str]:
        return {
            'url': self.url,
            'header': self.header,
            'content': self.content,
            'last_edited': self.last_edited.isoformat(),
            'last_scraped': self.last_scraped.isoformat(),
        }

    @classmethod
    def load_from_dict(cls, data: Dict[str, str]) -> 'Page':
        typed_data = {
            k: (datetime.fromisoformat(v) if k in ['last_edited', 'last_scraped'] else v)
            for k, v in data.items()
        }
        return cls(**typed_data)  # type: ignore

    def update_from_page(self, page: 'Page'):
        assert self.url == page.url, "can only update from another page that has the same url"

        if page.last_edited > self.last_edited:
            self.last_edited = page.last_edited
            self.header = page.header

        if page.last_scraped > self.last_scraped:
            self.last_scraped = page.last_scraped
            self.content = page.content


class Notion:
    def __init__(self, fetch_pages: bool = False, scrape_pages: bool = False):
        self.client = Client(auth=Config.notion_api_key)
        self.pages: Dict[str, Page] = dict()
        self.load_from_data()

        if fetch_pages:
            self.fetch_pages()  # creates a list of unscraped pages
        if scrape_pages:
            self.scrape_pages()

    @property
    def unscraped_pages(self) -> List[str]:
        return [page.url for page in self.pages.values() if not page.is_scraped]

    @property
    def page_list(self) -> List[Page]:
        return list(self.pages.values())

    def scrape_pages(self):
        if self.unscraped_pages:
            print('scraping notion pages')
            for url in tqdm(self.unscraped_pages):
                self.pages[url].scrape(client=self.client)
                self.save_data()

    def add_page(self, page: Page):
        if page.url in self.pages:
            self.pages[page.url].update_from_page(page)
        else:
            self.pages[page.url] = page

    def keep_last_n_pages(self, n: int):
        """ used for testing """
        last_edited_list = sorted([p.last_edited for p in self.page_list])
        threshold = last_edited_list[-n]
        self.pages = {url: page for url, page in self.pages.items() if page.last_edited >= threshold}

    def fetch_pages(self):
        """ fill self.pages with all pages from notion (unscraped) """

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
        """recursive function that unpacks the properties dict to extract content"""
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
        data = [p.save_to_dict() for p in self.pages.values()]
        os.makedirs(Config.data_dir, exist_ok=True)
        with open(Config.notion_data_file, 'w') as f:
            json.dump(data, f)

    def load_from_data(self):
        if not os.path.exists(Config.notion_data_file):
            return
        with open(Config.notion_data_file) as json_file:
            data: List[Dict[str, str]] = json.load(json_file)
        for page_data in data:
            page = Page.load_from_dict(page_data)
            self.add_page(page)


def refresh_data():
    print('Fetching all pages from notion... ', end='')
    notion = Notion(fetch_pages=True, scrape_pages=True)
    print(len(notion.pages))

    print(f'Scraping {len(notion.unscraped_pages)} pages')
    notion.scrape_pages()


if __name__ == "__main__":
    refresh_data()
