import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def upload_file_to_s3(input_key, bucket_name, destination_key):
    """
    Uploads a file to S3.

    Args:
    - input_key (str): Key of the input file.
    - bucket_name (str): Name of the destination S3 bucket.
    - destination_key (str): Key of the destination object in S3.

    Raises:
    - ClientError: If there's an error during file upload.
    """
    try:
        s3_client.upload_file(
            input_key,
            bucket_name,
            destination_key
        )
        print(f"File {input_key} uploaded successfully to S3 bucket {bucket_name} as {destination_key}.")
    except ClientError as e:
        print(f"Error uploading file {input_key} to S3 bucket {bucket_name}: {e.response['Error']['Message']}")
        raise e

def list_objects_in_bucket(bucket_name, prefix=""):
    """
    Lists objects in an S3 bucket with a given prefix.

    Args:
    - bucket_name (str): Name of the S3 bucket.
    - prefix (str): Prefix of the object keys to filter.

    Returns:
    - list: List of object keys.

    Raises:
    - ClientError: If there's an error while listing objects in the S3 bucket.
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        objects = response.get('Contents', [])
        return objects
    except ClientError as e:
        print(f"Error listing objects in S3 bucket {bucket_name}: {e.response['Error']['Message']}")
        raise e

def put_object_in_bucket(bucket_name, key, body):
    """
    Uploads an object to an S3 bucket.

    Args:
    - bucket_name (str): Name of the S3 bucket.
    - key (str): Object key.
    - body (str): Object content.

    Raises:
    - ClientError: If there's an error while putting the object in the S3 bucket.
    """
    try:
        s3_client.put_object(
            Body=body,
            Bucket=bucket_name,
            Key=key
        )
        print(f"Object {key} uploaded successfully to S3 bucket {bucket_name}.")
    except ClientError as e:
        print(f"Error uploading object {key} to S3 bucket {bucket_name}: {e.response['Error']['Message']}")
        raise e
