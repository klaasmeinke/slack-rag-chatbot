import os
from typing import List

import pandas as pd
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


def get_blocks(client: Client, page_id: str) -> pd.DataFrame:
    all_blocks = client.blocks.children.list(page_id, page_size=100)['results']

    all_blocks = pd.DataFrame(all_blocks)

    if all_blocks.empty:
        return pd.DataFrame()

    all_blocks = all_blocks[all_blocks['type'] == 'paragraph']

    if all_blocks.empty:
        return pd.DataFrame()

    all_blocks = all_blocks[all_blocks['paragraph'].apply(lambda x: bool(x['rich_text']))]

    if all_blocks.empty:
        return pd.DataFrame()

    all_blocks = all_blocks[['id', 'paragraph']]
    all_blocks['paragraph'] = all_blocks['paragraph'].apply(lambda x: x['rich_text'])
    all_blocks['paragraph'] = all_blocks['paragraph'].apply(
        lambda x: ' '.join([y['text']['content'] for y in x if 'text' in y.keys()])
    )

    return all_blocks


def get_all_blocks(client: Client, limit) -> List[str]:
    pages = get_all_pages(client)

    print(f'got {len(pages)} pages')

    paragraphs = []

    for page_id in pages['id']:
        _blocks = get_blocks(client, page_id)
        if not _blocks.empty:
            paragraphs += _blocks['paragraph'].tolist()

        if len(paragraphs) > limit:
            break

        print(f'got {len(paragraphs)} paragraphs', end='\r')

    print(f'got {len(paragraphs)} paragraphs')

    return paragraphs


if __name__ == "__main__":
    notion_client = Client(auth=os.getenv("NOTION_API_KEY"))

    blocks = get_all_blocks(notion_client, limit=50)

    print(len(blocks))
    # print(notion_client.pages.retrieve())
