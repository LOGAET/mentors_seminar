from __future__ import annotations

import argparse
import io
import logging
import os
import sys
from dataclasses import dataclass

import pandas as pd
from minio import Minio
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("etl")


@dataclass
class Config:
    pg_host: str
    pg_port: int
    pg_user: str
    pg_password: str
    pg_db: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str

    @classmethod
    def from_env(cls, args: argparse.Namespace) -> "Config":
        return cls(
            pg_host=args.host or os.environ.get("PG_HOST", "localhost"),
            pg_port=int(args.port or os.environ.get("PG_PORT", 5432)),
            pg_user=os.environ.get("PG_USER", "oilfield"),
            pg_password=os.environ.get("PG_PASSWORD", "oilfield_pass"),
            pg_db=os.environ.get("PG_DB", "oilfield"),
            minio_endpoint=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
            minio_access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin123"),
            minio_bucket=os.environ.get("MINIO_BUCKET", "oilfield"),
        )


def make_engine(cfg: Config):
    url = (
        f"postgresql+psycopg2://{cfg.pg_user}:{cfg.pg_password}"
        f"@{cfg.pg_host}:{cfg.pg_port}/{cfg.pg_db}"
    )
    return create_engine(url, pool_pre_ping=True)


def make_minio(cfg: Config) -> Minio:
    endpoint = cfg.minio_endpoint.replace("http://", "").replace("https://", "")
    secure = cfg.minio_endpoint.startswith("https://")
    client = Minio(endpoint, access_key=cfg.minio_access_key,
                   secret_key=cfg.minio_secret_key, secure=secure)
    if not client.bucket_exists(cfg.minio_bucket):
        client.make_bucket(cfg.minio_bucket)
        log.info("Создан bucket: %s", cfg.minio_bucket)
    return client


def upload_parquet(client: Minio, bucket: str, key: str, df: pd.DataFrame) -> None:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow", compression="snappy")
    buf.seek(0)
    client.put_object(
        bucket_name=bucket,
        object_name=key,
        data=buf,
        length=buf.getbuffer().nbytes,
        content_type="application/octet-stream",
    )
    log.info("  -> s3://%s/%s  (%d rows, %.1f KB)", bucket, key, len(df),
             buf.getbuffer().nbytes / 1024)


def extract_table(engine, table: str, schema: str = "oilfield") -> pd.DataFrame:
    log.info("Извлекаю %s.%s", schema, table)
    return pd.read_sql(text(f"SELECT * FROM {schema}.{table}"), engine)


def export_with_date_partition(
    client: Minio, bucket: str, df: pd.DataFrame, table: str, date_column: str
) -> None:
    if df.empty:
        log.warning("%s: пустой DataFrame, пропускаю", table)
        return

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df["__dt"] = df[date_column].dt.strftime("%Y-%m-%d")

    for dt, part in df.groupby("__dt"):
        key = f"raw/{table}/dt={dt}/{table}.parquet"
        upload_parquet(client, bucket, key, part.drop(columns=["__dt"]))


def export_flat(client: Minio, bucket: str, df: pd.DataFrame, table: str) -> None:
    key = f"raw/{table}/{table}.parquet"
    upload_parquet(client, bucket, key, df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", default=None)
    args = parser.parse_args()

    cfg = Config.from_env(args)
    log.info("PostgreSQL: %s:%s/%s", cfg.pg_host, cfg.pg_port, cfg.pg_db)
    log.info("MinIO:      %s, bucket=%s", cfg.minio_endpoint, cfg.minio_bucket)

    engine = make_engine(cfg)
    client = make_minio(cfg)

    for table in ["wells", "pump_failures"]:
        df = extract_table(engine, table)
        export_flat(client, cfg.minio_bucket, df, table)

    export_with_date_partition(
        client, cfg.minio_bucket,
        extract_table(engine, "production"),
        table="production", date_column="prod_date",
    )
    export_with_date_partition(
        client, cfg.minio_bucket,
        extract_table(engine, "telemetry"),
        table="telemetry", date_column="ts",
    )
    export_with_date_partition(
        client, cfg.minio_bucket,
        extract_table(engine, "well_targets"),
        table="well_targets", date_column="target_date",
    )
    export_with_date_partition(
        client, cfg.minio_bucket,
        extract_table(engine, "pump_sensors"),
        table="pump_sensors", date_column="ts",
    )
    export_with_date_partition(
        client, cfg.minio_bucket,
        extract_table(engine, "deliveries"),
        table="deliveries", date_column="delivery_date",
    )

    log.info("ETL завершён успешно")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("ETL упал")
        sys.exit(1)
