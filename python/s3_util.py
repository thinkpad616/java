from typing import Callable

import boto3
from smart_open import open as smart_open

_S3_CLIENT = None


def _s3_client():
    global _S3_CLIENT
    if not _S3_CLIENT:
        _S3_CLIENT = boto3.client("s3")
    return _S3_CLIENT


def download_file(source_bucket: str, source_key: str, local_dest_path: str):
    _s3_client().download_file(
        Bucket=source_bucket,
        Key=source_key,
        Filename=local_dest_path,
    )


def upload_file(source_path: str, dest_bucket: str, dest_key: str):
    _s3_client().upload_file(
        Filename=source_path,
        Bucket=dest_bucket,
        Key=dest_key,
        ExtraArgs={"ACL": "bucket-owner-full-control"},
    )


def get_object(bucket: str, key: str) -> bytes:
    return _s3_client().get_object(Bucket=bucket, Key=key)["Body"].read()


def upload_trimmed_file(
    source_path: str, dest_bucket: str, dest_key: str, line_skipper: Callable[[str], bool] | None = None
):
    def _no_skips(_: str) -> bool:
        return False

    if not line_skipper:
        line_skipper = _no_skips

    s3_dest = f"s3://{dest_bucket}/{dest_key}"
    with smart_open(source_path, encoding="latin-1") as fin:
        with smart_open(s3_dest, "w", encoding="UTF-8") as s3_out:
            for line in fin:
                if line_skipper(line):
                    continue
                s3_out.write(line)
