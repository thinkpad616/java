import boto3
from botocore.exceptions import ClientError
import os
from typing import List, Optional

from cardcore_direct_filemove.exceptions import FileNotConfigured
from cardcore_direct_filemove.models import AppContext, FileContext, DirectTransferContext
from cardcore_direct_filemove.file_config import get_file_context

# Initialize S3 client
s3_client = boto3.client('s3')


def upload_to_s3(file_context: FileContext):
    """
    Uploads a file to S3 and creates a marker file after successful upload.

    Args:
    - file_context (FileContext): Context containing file details for upload.

    Raises:
    - FileNotConfigured: If the file is not configured in the environment.
    - ClientError: If there's an error during file upload.
    """
    if file_context.direct_transfer:
        # Check if the file is configured in the environment
        if not file_context.direct_transfer.destination_bucket:
            raise FileNotConfigured(f'Configuration not found for file: {file_context.basename}')

        # Upload the file to S3
        try:
            s3_client.upload_file(
                file_context.basename,
                file_context.direct_transfer.destination_bucket,
                file_context.direct_transfer.destination_key
            )
            print(f"File {file_context.basename} uploaded successfully to S3.")
            
            # Create marker file with upload status
            create_marker_file(file_context.basename, "uploaded")

        except ClientError as e:
            print(f"Error uploading file {file_context.basename} to S3: {e.response['Error']['Message']}")
            raise e


def create_marker_file(filename: str, status: str):
    """
    Creates a marker file with the given filename and status.

    Args:
    - filename (str): Name of the file to create marker for.
    - status (str): Status of the file upload.

    Raises:
    - OSError: If marker file creation fails.
    """
    marker_filename = f"{filename}.marker"
    marker_content = f"Status: {status}"
    try:
        with open(marker_filename, 'w') as marker_file:
            marker_file.write(marker_content)
        print(f"Created marker file {marker_filename} with status: {status}")
    except OSError as e:
        print(f"Failed to create marker file {marker_filename}: {e}")
        raise e


def check_previous_marker_files(filename: str) -> Optional[str]:
    """
    Checks previous marker files for the given filename.

    Args:
    - filename (str): Name of the file to check.

    Returns:
    - str: Status from marker file if found, None otherwise.
    """
    marker_filename = f"{filename}.marker"
    if os.path.exists(marker_filename):
        try:
            with open(marker_filename, 'r') as marker_file:
                status = marker_file.read()
            print(f"Found previous marker file {marker_filename} with status: {status}")
            return status
        except OSError as e:
            print(f"Failed to read marker file {marker_filename}: {e}")
            raise e
    else:
        print(f"No previous marker file found for {filename}")
        return None


def upload_file_with_markers(app_context: AppContext):
    """
    Uploads a file to S3 with marker file management.

    Args:
    - app_context (AppContext): Application context containing input key details.

    Raises:
    - FileNotConfigured: If the file is not configured in the environment.
    """
    # Get file context based on the application context
    file_context = get_file_context(app_context)

    # Check previous marker files
    previous_status = check_previous_marker_files(file_context.basename)
    
    # Proceed with file upload only if there's no previous marker or if the previous marker indicates success
    if not previous_status or "uploaded" in previous_status.lower():
        upload_to_s3(file_context)
    else:
        print(f"File {file_context.basename} upload skipped due to previous marker status: {previous_status}")


if __name__ == "__main__":
    # Example usage
    app_context = AppContext(
        app="my_app",
        env=Environment.DEV,  # Replace with your environment
        region=Region.WEST,  # Replace with your region
        input_bucket="my_input_bucket",
        input_key="my_input_key"
    )

    upload_file_with_markers(app_context)
