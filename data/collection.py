from datetime import datetime
import asyncio, os
from data.db import query
from data.fetcher import Fetcher
import pandas as pd
from PIL import Image
from io import BytesIO
from pathlib import Path


def get_next_images(img_df, filtered_table_name, limit) -> list[tuple[int, datetime, str]]:
    return pd.DataFrame(
        query(f"SELECT * FROM {filtered_table_name} WHERE id > {max(img_df["id"]) if img_df.shape[0] else -1} LIMIT {limit}").all(),
        columns=('id', 'created_at', 'image_format')
    )

def get_skipped(df: pd.DataFrame, limit: int):
    highest = max(df["id"])

    return pd.DataFrame(query(f"""
        WITH ids(id) AS (
            VALUES {", ".join(f"({i})" for i in df["id"])}
        )
        SELECT id, created_at, image_format
        FROM filtered f
        WHERE f.id < {highest}
        AND NOT EXISTS (
            SELECT 1
            FROM ids
            WHERE f.id = ids.id
        )
        LIMIT {limit}
    """).all())

async def collect(img_df: pd.DataFrame, img_output_path: Path, wait_time):
    fetcher = Fetcher()
    to_collect = len(img_df)
    img_df = img_df[['id', 'created_at', 'image_format']]

    print(f"""
    Saving to: {img_output_path}
    Collecting: {to_collect}
    """)
    i = 0

    try:
        for (image_id, created_at, image_format) in img_df.itertuples(index=False):
            await asyncio.sleep(wait_time())
            i += 1

            fetch_result = await fetcher.fetch(f'{created_at.strftime('%Y/%-m/%-d')}/{image_id}', image_format)

            if fetch_result is None:
                print(f"Missed {image_id}\n")
                continue
            elif not fetch_result:
                break

            img_bytes = BytesIO(fetch_result)
            img_path = img_output_path / f'{image_id}.{image_format}'
            temp_path = img_output_path / f'{image_id}.tmp.{image_format}'

            try:
                with Image.open(img_bytes) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img.save(temp_path, optimize=(image_format == 'png'))
                    os.replace(temp_path, img_path)

            except Exception as e:
                print(f'Skipping: {img_path} {e}')
            finally:
                temp_path.unlink(True)

            print(f'{'' * 100}\rFetched images: {i}/{to_collect} (%{100 * i / to_collect:.2f})    ID: {image_id}', end='\r')
    except KeyboardInterrupt:
        pass
    finally:
        await fetcher.close()
        print("\nDone")

