from datetime import datetime
import os
from notion_client import Client
from typing import List, Optional
from pydantic import BaseModel


class Page(BaseModel):
    title: Optional[str]
    url: str
    last_edited: Optional[datetime]
    content: Optional[str] = None


def get_all_pages(client: Client) -> List[Page]:
    """returns pages without content"""
    has_more = True
    i = 0
    pages = []
    start_cursor = None

    while has_more:
        i += 1

        response = client.search(
            query='',
            page_size=100,
            filter={'value': 'page', 'property': 'object'},
            start_cursor=start_cursor
        )

        start_cursor = response['next_cursor']
        has_more = response['has_more']

        new_pages = [
            Page(
                title=page['properties']['title']['title'][0]['text']['content'] if 'title' in page['properties'] else None,
                url=page['url'],
                last_edited=datetime.strptime(page['last_edited_time'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            )
            for page in response['results'] if not page['archived']
        ]

        pages += new_pages

    return pages


def scrape_page(page: Page, client: Client) -> Page:
    """adds content to a single page"""
    all_blocks = client.blocks.children.list(page.url[-32:], page_size=100)['results']

    text = '' if page.title is None else 'Page Title: ' + page.title

    prefixes = {
        'paragraph': '\n',
        'heading_3': '\n###',
        'heading_2': '\n##',
        'heading_1': '\n#'
    }

    for block in all_blocks:

        block_type = block['type']

        if block_type not in prefixes.keys():
            continue

        if not block[block_type]['rich_text']:
            continue

        text += prefixes[block_type]
        text += ''.join([b['text']['content'] for b in block[block_type]['rich_text'] if 'text' in b])

    page.content = text
    return page


if __name__ == "__main__":
    notion_client = Client(auth=os.getenv("NOTION_API_KEY"))

    _pages = get_all_pages(notion_client)

    for _page in _pages:
        print(f'------ {_page.url} --------')
        _page = scrape_page(_page, notion_client)
        print(_page.content)
