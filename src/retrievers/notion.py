from datetime import datetime
from notion_client import Client
from src.retrievers.abc import Retriever
from typing import TYPE_CHECKING
from src.docs import NotionPage

if TYPE_CHECKING:
    from src.config import Config


class NotionRetriever(Retriever):

    def __init__(self, config: 'Config'):
        self.client = Client(auth=config.NOTION_API_KEY)
        super().__init__(
            data_file=config.file_notion,
            doc_type=NotionPage,
            scraping_kwargs={'client': self.client}
        )

    def _fetch_docs(self):
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

            header_items = [title, f'Last Edited: {last_edited}']
            formatted_properties = [
                f'{prop_name}: {self._extract_content_from_properties(prop_info)}'
                for prop_name, prop_info in result['properties'].items()
                if prop_info['id'] != 'title'
            ]
            header_items += formatted_properties
            header = '\n'.join(header_items)

            yield NotionPage(body='', header=header, url=url, last_edited=last_edited)

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
