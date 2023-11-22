import os
from typing import Dict, List

import pandas as pd
from pydantic import BaseModel
from notion_client import Client


def get_all_pages(client: Client) -> pd.DataFrame:
    has_more = True
    i = 0
    results = []
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

        filtered_results = [
            {k: v for k, v in page.items() if k in ['id', 'url', 'last_edited_time', 'archived']}
            for page in response['results']
        ]

        results += filtered_results

    results = pd.DataFrame(results)
    results = results[~results['archived']]  # remove archived pages

    return results


class Document(BaseModel):
    document_url: str
    source_url: str
    content: str


def get_blocks(client: Client, page_id: str, url: str) -> List[Document]:
    all_blocks = client.blocks.children.list(page_id, page_size=100)['results']

    all_blocks = pd.DataFrame(all_blocks)

    if all_blocks.empty:
        return []

    all_blocks = all_blocks[all_blocks['type'] == 'paragraph']

    if all_blocks.empty:
        return []

    all_blocks = all_blocks[all_blocks['paragraph'].apply(lambda x: bool(x['rich_text']))]

    if all_blocks.empty:
        return []

    all_blocks = all_blocks[['id', 'paragraph']]
    all_blocks['paragraph'] = all_blocks['paragraph'].apply(lambda x: x['rich_text'])
    all_blocks['paragraph'] = all_blocks['paragraph'].apply(
        lambda x: ' '.join([y['text']['content'] for y in x if 'text' in y.keys()])
    )

    # print(all_blocks)
    # print(all_blocks.columns)

    documents = [
        Document(document_url=url, source_url=url, content=row['paragraph'])
        for _, row in all_blocks.iterrows()
    ]

    return documents


def get_all_blocks(client: Client, limit) -> List[Document]:
    pages = get_all_pages(client)

    print(f'got {len(pages)} pages')

    paragraphs = []

    for page_id, url in zip(pages['id'], pages['url']):
        _blocks = get_blocks(client, page_id, url)

        if _blocks:
            paragraphs += _blocks

        if len(paragraphs) > limit:
            break

        print(f'got {len(paragraphs)} paragraphs', end='\r')

    print(f'got {len(paragraphs)} paragraphs')

    return paragraphs


if __name__ == "__main__":
    notion_client = Client(auth=os.getenv("NOTION_API_KEY"))

    blocks = get_all_blocks(notion_client, limit=50)

    print(len(blocks))
    for block in blocks[:10]:
        print(block.dict())
    # print(notion_client.pages.retrieve())
