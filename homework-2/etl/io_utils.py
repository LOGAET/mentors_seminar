from __future__ import annotations

import os
from io import BytesIO

import pandas as pd
import s3fs
from minio import Minio
from sqlalchemy import create_engine, text


def pg_engine():
    url = (
        f"postgresql+psycopg2://{os.environ.get('PG_USER', 'oilfield')}:"
        f"{os.environ.get('PG_PASSWORD', 'oilfield_pass')}"
        f"@{os.environ.get('PG_HOST', 'postgres')}:"
        f"{os.environ.get('PG_PORT', '5432')}"
        f"/{os.environ.get('PG_DB', 'oilfield')}"
    )
    return create_engine(url, pool_pre_ping=True)


def minio_client() -> Minio:
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    endpoint_host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    return Minio(
        endpoint_host,
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin123"),
        secure=secure,
    )


def s3_fs() -> s3fs.S3FileSystem:
    return s3fs.S3FileSystem(
        key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret=os.environ.get("MINIO_SECRET_KEY", "minioadmin123"),
        client_kwargs={"endpoint_url": os.environ.get("MINIO_ENDPOINT", "http://minio:9000")},
    )


def read_table(table: str, bucket: str | None = None) -> pd.DataFrame:
    bucket = bucket or os.environ.get("MINIO_BUCKET", "oilfield")
    fs = s3_fs()
    paths = fs.glob(f"{bucket}/raw/{table}/**/*.parquet")
    if not paths:
        raise FileNotFoundError(f"В MinIO нет данных для таблицы '{table}'")
    frames = [pd.read_parquet(f"s3://{p}", filesystem=fs) for p in paths]
    return pd.concat(frames, ignore_index=True)


def write_mart(df: pd.DataFrame, mart_name: str, bucket: str = "marts") -> str:
    client = minio_client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    buf = BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow", compression="snappy")
    buf.seek(0)
    key = f"{mart_name}.parquet"
    client.put_object(bucket, key, buf, length=buf.getbuffer().nbytes)
    return f"s3://{bucket}/{key}"


def write_mart_to_pg(df: pd.DataFrame, table: str, schema: str = "marts") -> None:
    engine = pg_engine()
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    df.to_sql(table, engine, schema=schema, if_exists="replace", index=False)
