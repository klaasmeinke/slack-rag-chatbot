from datetime import datetime
from smartsearch.retrievers.docs import Doc
from notion_client import Client
from smartsearch.retrievers.retrieverabc import RetrieverABC
from ratemate import RateLimit  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smartsearch.config import Config


rate_limit = RateLimit(max_count=3, per=1, greedy=True)


class NotionPage(Doc):

    def scrape(self, client: Client):
        if self.is_scraped:
            return
        self.last_scraped = datetime.now()
        block_id = self.url[-32:]
        self._depth = 0
        self.scrape_block(client, block_id)

    def scrape_block(self, client: Client, block_id: str):
        """recursively scrapes a block and its children, adding them to self.content"""
        children = client.blocks.children.list(block_id, page_size=100)['results']
        rate_limit.wait()

        for block in children:
            formatted_block = self.format_block(block)
            if formatted_block:
                self.body += formatted_block.replace('\n', '\n' + self._depth * '  ')
            if block['has_children'] and block['type'] != 'child_page':
                self._depth += 1
                self.scrape_block(client, block_id=block['id'])
                self._depth -= 1

    @staticmethod
    def format_block(block) -> str | None:

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


class NotionRetriever(RetrieverABC):

    def __init__(self, config: 'Config'):
        self.client = Client(auth=config.NOTION_API_KEY)
        super().__init__(
            data_file=config.file_notion,
            doc_type=NotionPage,
            scraping_kwargs={'client': self.client}
        )

    def fetch_docs(self):
        # make api requests to get all pages and append them to self.docs
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

            page = NotionPage(header=header, url=url, last_edited=last_edited)
            self.add_doc(page)

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


def test():
    from smartsearch.config import Config
    config = Config()
    notion = NotionRetriever(config=config)
    notion.fetch_docs()
    notion.scrape_docs()

    for doc in notion.docs:
        print(notion.docs[doc])
        print()


if __name__ == "__main__":
    test()
