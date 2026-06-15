from sqlalchemy import create_engine, text
import pandas as pd
from data.config import db_host, db_pass


engine = create_engine(f"postgresql+psycopg2://postgres:{db_pass}@{db_host}:5432/derpibooru")


def query(q, params=None):
    with engine.connect() as c:
        return c.execute(text(q), params)

def get_image_data(df: pd.DataFrame):
    result = query(f"""
        SELECT * FROM get_image_data(:ids);
        """,
        { 'ids': df['id'].to_list() }
    ).all() if df.shape[0] else []

    return pd.DataFrame(result, columns=['id', 'created_at', 'image_format', 'score', 'tags'])

def get_skipped(df: pd.DataFrame):
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
    """).all())
