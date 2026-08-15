from typing import Callable
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url="http://192.168.0.29:9000",
    aws_access_key_id=str(os.getenv("MINIO_ROOT_USER")),
    aws_secret_access_key=str(os.getenv("MINIO_PASSWORD")),
)


def get_buckets_list() -> list[str]:
    """
    Returns a list of all buckets available which is required for checking if a bucket
    needs creating when sending files.
    """
    buckets_data = s3.list_buckets()
    buckets = buckets_data["Buckets"]
    buckets_list = [x["Name"] for x in buckets]
    return buckets_list


buckets = get_buckets_list()


def bucket_handler(func: Callable):
    """
    Decorator used to ensure that if a file is being sent to a bucket that doesn't yet
    exist that the bucket will be created on the fly
    """

    def wrapper(**kwargs):
        bucket_name = kwargs.get("bucket_name", "default-bucket")
        bucket_name = bucket_name.replace("_", "-")
        if bucket_name in buckets:
            return func(**kwargs)
        s3.create_bucket(Bucket=bucket_name)
        buckets.append(bucket_name)
        return func(**kwargs)

    return wrapper


@bucket_handler
def send_to_bucket(
    bucket_name: str,
    partition_name: str,
    bytes_: bytes,
    filename: str,
    filetype: str,
    s3=s3,
) -> None:
    """
    Send file to a bucket

    Args:
        - bucket_name: The name of the bucket being posted to
        - partition_name: The name of the partition, if it doens't exist it will be created
        - bytes_: The stream of bytes from the data being uploaded
        - filename: The name of the file as it will appear in the bucket
        - filetype: The file extension. Must include "." prefix of extension
        - s3: The boto3 client object. A default value of the package client will be passed if not populated

    Returns:
        - None
    """
    bucket_name = bucket_name.replace("_", "-")
    s3.put_object(
        Bucket=bucket_name,
        Key=f"{bucket_name}/{partition_name}/{filename}{filetype}",
        Body=bytes_,
        ContentType="application/octet-stream",
    )


def list_files(
    bucket_name: str,
    partitions: str | None = None,
    *,
    s3=s3,
    max_files: int | None = None,
) -> list[str]:
    """
    List all files within a bucket and/or partition.

    Args:
        - bucket_name: The name of the bucket
        - paritions: The string of the partition(s) being searched. If the partition contains
        a sub-partition this can be specified as ```partitions="parent/child"```
        - s3: boto3 client object. Defaults to the package global

    Returns:
        - list of filepaths
    """
    prefix = f"{partitions}/" if partitions else ""
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    files = []
    for page in pages:
        if max_files and len(files) > max_files:
            return files[:max_files]
        files += [file["Key"] for file in page["Contents"]]

    return files


def read_file(bucket_name: str, key: str, s3=s3) -> bytes:
    """
    Reads the content of a file. This function is designed to work with the output of the
    list_files function also available in the package.

    Args:
        - bucket_name: The name of the bucket the file belongs to
        - key: The file key of the file being read. For a file belonging to a partition this
        will be specified as ```"parition/filename.ext"```
        - s3: boto3 client object. Defaults to the package global
    """
    reponse = s3.get_object(Bucket=bucket_name, Key=key)
    content = reponse["Body"].read()
    return content
