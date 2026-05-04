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
    buckets_data = s3.list_buckets()
    buckets = buckets_data["Buckets"]
    buckets_list = [x["Name"] for x in buckets]
    return buckets_list


buckets = get_buckets_list()


def bucket_handler(func: Callable):
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


def list_files(bucket: str, partition: str = "", s3=s3) -> list[str] | None:
    reponse = s3.list_objects_v2(Bucket=bucket, Prefix=f"{bucket}/{partition}/")
    if "Contents" not in reponse:
        return
    return [x["Key"] for x in reponse["Contents"]]
