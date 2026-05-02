import boto3
import os
from dotenv import load_dotenv
from logger import ProjectLogger

logger = ProjectLogger("pilake_package")

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id=str(os.getenv("MINIO_ROOT_USER")),
    aws_secret_access_key=str(os.getenv("MINIO_PASSWORD")),
)


def send_to_bucket(
    bucket_name: str,
    partition_name: str,
    _bytes: bytes,
    filename: str,
    filetype: str,
    s3=s3,
) -> None:
    """
    Send file to a bucket

    Args:
        - bucket_name: The name of the bucket being posted to
        - partition_name: The name of the partition, if it doens't exist it will be created
        - _bytes: The stream of bytes from the data being uploaded
        - filename: The name of the file as it will appear in the bucket
        - filetype: The file extension
        - s3: The boto3 client object. A default value of the package client will be passed if not populated

    Returns:
        - None
    """
    s3.put_object(
        Bucket=bucket_name,
        Key=f"{bucket_name}/{partition_name}/{filename}{filetype}",
        Body=_bytes,
        ContentType="application/octet-stream",
    )


def list_files(bucket: str, partition: str = "", s3=s3) -> list[str] | None:
    reponse = s3.list_objects_v2(Bucket=bucket, Prefix=f"{bucket}/{partition}/")
    if "Contents" not in reponse:
        return
    return [x["Key"] for x in reponse["Contents"]]
