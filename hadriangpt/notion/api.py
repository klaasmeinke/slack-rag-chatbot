from datetime import datetime, timedelta
from notion_client import Client
import os
from pydantic import BaseModel
from typing import List, Optional


class Page(BaseModel):
    url: str
    last_edited: datetime
    header: str
    content: str = ''
    is_scraped: bool = False
    _depth = 0  # used to track indentation level when blocks are scraped

    def __str__(self):
        return self.header + self.content

    def scrape(self, client):
        if self.is_scraped:
            return
        self.is_scraped = True
        block_id = self.url[-32:]
        self._depth = 0
        self.scrape_block(client, block_id)

    def scrape_block(self, client: Client, block_id: str):
        """ recursive function that scrapes a block and its children and adds them to the content """
        children = client.blocks.children.list(block_id, page_size=100)['results']

        for block in children:
            formatted_block = self.format_block(block)
            if formatted_block:
                formatted_block = formatted_block.replace('\n', '\n'+self._depth*'  ')
                self.content += formatted_block
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


class Notion:
    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_API_KEY"))
        self.pages: List[Page] = []
        self.get_all_pages()  # creates a list of unscraped pages

    def scrape_pages(self, last_edited_gt: datetime = datetime(year=2000, month=1, day=1)):
        for page in self.pages:
            if page.last_edited > last_edited_gt:
                page.scrape(self.client)
                print('\n\n' + str(page))

    def get_all_pages(self):
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

            parent_id = id_to_parent_id.get(result['id'])
            while parent_id in id_to_parent_id:
                title = id_to_title[parent_id] + ' / ' + title
                parent_id = id_to_parent_id[parent_id]

            title = 'Title: ' + title

            formatted_properties = ''

            for prop_name, prop_info in result['properties'].items():
                if prop_info['id'] == 'title':
                    continue
                formatted_properties += f'\n{prop_name}: '
                formatted_properties += self._extract_content_from_properties(prop_info)

            header = title + formatted_properties
            url = result['url']
            last_edited = datetime.strptime(result['last_edited_time'], "%Y-%m-%dT%H:%M:%S.%fZ")

            page = Page(header=header, url=url, last_edited=last_edited)
            self.pages.append(page)

    def _extract_content_from_properties(self, _prop_info: dict) -> str:
        """ recursive function that iteratively unpack the properties dict to extract content"""
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


def test_notion_scraping():
    notion = Notion()
    print(f'found {len(notion.pages)} notion pages in total')

    days = 10
    last_edited_gt = datetime.now() - timedelta(days=days)
    pages = [p for p in notion.pages if p.last_edited > last_edited_gt]
    print(f'found {len(pages)} pages that were edited in last {days} days')

    notion.scrape_pages(last_edited_gt)


if __name__ == "__main__":
    test_notion_scraping()
