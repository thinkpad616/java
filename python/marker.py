from s3_util import list_objects_in_bucket, put_object_in_bucket

marker_bucket = 'your-marker-bucket'

def create_marker_file(filename, status):
    """
    Creates a marker file with the given filename and status.

    Args:
    - filename (str): Name of the file to create marker for.
    - status (str): Status of the file upload.

    Raises:
    - ClientError: If marker file creation fails.
    """
    marker_key = f"{filename}.marker"
    marker_content = f"Status: {status}"
    try:
        put_object_in_bucket(marker_bucket, marker_key, marker_content)
        print(f"Created marker file {marker_key} with status: {status}")
    except ClientError as e:
        print(f"Error creating marker file {marker_key} with status: {status}: {e.response['Error']['Message']}")
        raise e


def check_previous_marker_files(filename):
    """
    Checks if there are any previous marker files for the given filename in the S3 bucket.

    Args:
    - filename (str): Name of the file to check for marker files.

    Returns:
    - bool: True if previous marker files exist, False otherwise.

    Raises:
    - ClientError: If there's an error while listing objects in the S3 bucket.
    """
    try:
        response = list_objects_in_bucket(marker_bucket, prefix=f"{filename}.marker")
        marker_files = [obj['Key'] for obj in response]
        if marker_files:
            print(f"Found {len(marker_files)} previous marker files for {filename}")
            return True
        else:
            print(f"No previous marker files found for {filename}")
            return False
    except ClientError as e:
        print(f"Error listing marker files for {filename}: {e.response['Error']['Message']}")
        raise e
