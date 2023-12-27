from datetime import datetime
from smartsearch.docs.abstract import Doc
from notion_client import Client
from ratelimit import limits, sleep_and_retry


class NotionPage(Doc):

    def scrape_doc(self, client: Client):
        if self.is_scraped:
            return
        self.last_scraped = datetime.now()
        block_id = self.url[-32:]
        self._depth = 0
        self.scrape_block(client, block_id)

    @sleep_and_retry
    @limits(calls=3, period=1)
    def scrape_block(self, client: Client, block_id: str):
        """recursively scrapes a block and its children, adding them to self.content"""
        children = client.blocks.children.list(block_id, page_size=100)['results']

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