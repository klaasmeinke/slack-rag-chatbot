from datetime import datetime
from notion_client import Client
from ratemate import RateLimit  # type: ignore
from typing import Dict


class Page:

    def __init__(
        self, url: str,
        header: str,
        last_edited: datetime,
        body: str = '',
        last_scraped: datetime = datetime.min
    ):
        self.url = url
        self.header = header
        self.content = body
        self.last_scraped = last_scraped
        self.last_edited = last_edited
        self._depth: int = 0

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
        """recursively scrapes a block and its children, adding them to self.content"""
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
