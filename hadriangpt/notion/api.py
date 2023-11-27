from datetime import datetime, timedelta
from notion_client import Client
import os
from pydantic import BaseModel
from typing import List, Optional
from ratemate import RateLimit


_default_client = Client(auth=os.getenv("NOTION_API_KEY"))
rate_limit = RateLimit(max_count=3, per=1, greedy=True)


class Page(BaseModel):
    url: str
    last_edited: datetime
    content: str
    is_scraped: bool

    def scrape(self, client: Client = None, block_id: Optional[str] = None):
        if self.is_scraped and block_id is None:
            return False

        if client is None:
            client = _default_client

        if block_id is None:
            self.is_scraped = True
            block_id = self.url[-32:]
            is_child = False
        else:
            is_child = True

        rate_limit.wait()
        all_blocks = client.blocks.children.list(block_id, page_size=100)['results']

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

        for block in all_blocks:

            block_type = block['type']
            if block_type not in prefixes.keys():
                continue

            if 'rich_text' in block[block_type] and block[block_type]['rich_text']:
                block_content = prefixes[block_type]
                block_content += ''.join([b['text']['content'] for b in block[block_type]['rich_text'] if 'text' in b])
                block_content += suffixes[block_type]
                if block_type == 'to_do':
                    self.content += ' (done)' if block['to_do']['checked'] else ' (to-do)'

            elif 'title' in block[block_type] and block[block_type]['title']:
                block_content = prefixes[block_type]
                block_content += block[block_type]['title']
                block_content += suffixes[block_type]

            else:
                continue

            if is_child:
                block_content = block_content.replace('\n', '\n  ')

            self.content += block_content

            if block['has_children'] and block_type != 'child_page':
                self.scrape(client, block_id=block['id'])


def get_all_pages(client: Client = None) -> List[Page]:
    """ returns all notion pages. pages are not scraped """
    if client is None:
        client = _default_client

    has_more = True
    start_cursor = None
    results = []

    while has_more:
        response = client.search(
            query='',
            page_size=100,
            start_cursor=start_cursor
        )

        start_cursor = response['next_cursor']
        has_more = response['has_more']
        results += response['results']

    def get_title(_result) -> str:

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

    def format_properties(_result):
        prop_string = ''

        def _get_content(_prop_info: dict):
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
                _child = ' '.join(_get_content(x) for x in _child)

            return str(_child).strip()

        for prop_name, prop_info in _result['properties'].items():
            if prop_info['id'] == 'title':
                continue
            prop_string += f'\n{prop_name}: '
            prop_string += _get_content(prop_info)

        return prop_string

    id_to_title = {result['id']: get_title(result) for result in results}

    id_to_parent_id = {
        result['id']: result['parent'][result['parent']['type']] for result in results
        if 'parent' in result
    }

    pages: List[Page] = []

    for result in results:
        if result['object'] != 'page':
            continue

        # get page title including chain of parents
        title = get_title(result)
        parent_id = id_to_parent_id.get(result['id'])

        while parent_id in id_to_parent_id:
            title = id_to_title[parent_id] + ' / ' + title
            parent_id = id_to_parent_id[parent_id]

        title = 'Title: ' + title
        title += format_properties(result)

        url = result['url']
        last_edited = datetime.strptime(result['last_edited_time'], "%Y-%m-%dT%H:%M:%S.%fZ")

        page = Page(content=title, url=url, last_edited=last_edited, is_scraped=False)
        pages.append(page)

    return pages


def test_notion_scraping():
    notion_client = Client(auth=os.getenv("NOTION_API_KEY"))
    pages = get_all_pages(notion_client)
    print(f'found {len(pages)} notion pages in total')

    days = 30
    pages = [p for p in pages if datetime.now() - timedelta(days=days) < p.last_edited]
    print(f'found {len(pages)} pages that were edited in last {days} days')

    for page in pages:
        page.scrape(notion_client)
        print(f'------ {page.url} --------')
        print(page.content)


if __name__ == "__main__":
    test_notion_scraping()
