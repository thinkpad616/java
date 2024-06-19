from __future__ import annotations

import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable

import dx_requests
import structlog

from cardcore_direct_filemove import s3_util
from cardcore_direct_filemove.models import AppContext, FileContext, Environment

logger = structlog.stdlib.get_logger()


class IngestionStatus(Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"

    @staticmethod
    def from_onestream_status(status: str) -> IngestionStatus:
        if status in {"COMPLETED"}:
            return IngestionStatus.COMPLETED
        elif status in {"QUARANTINED", "VALIDATION_FAILED", "TOKENIZATION_FAILED", "USER_CANCELED", "ABORTED"}:
            return IngestionStatus.FAILED
        else:
            # assume any other state means ingestion is still in progress
            # notably, OneStream has a "FAILED" status which results in the ingestion being retried on their end,
            # so we don't consider it a failure yet
            return IngestionStatus.IN_PROGRESS


def _upload_to_s3(local_path: str, bucket: str, key: str, line_skipper: Callable[[str], bool] | None = None):
    upload_start = time.perf_counter()
    try:
        s3_util.upload_trimmed_file(
            local_path,
            bucket,
            key,
            line_skipper=line_skipper,
        )
    except Exception as e:
        logger.error("Trim and upload file to S3 Failed")
        raise e
    logger.info("file.onestream-publish.s3-upload", upload_duration=(time.perf_counter() - upload_start))


def _upstream_env_value(app_context: AppContext) -> str:
    if app_context.env == Environment.PROD:
        env = "PROD"
    else:
        env = "QA"
    return f"{env}-{str.upper(app_context.region.value)}"


class OneStreamService:
    _requestor: dx_requests.Requestor

    def __init__(self, app_context: AppContext, client_id: str, client_secret: str, retries: int = 5) -> None:
        self._requestor = dx_requests.Requestor(
            client_id=client_id,
            client_secret=client_secret,
            api_retries=retries,
        )
        headers = {"X-Upstream-Env": _upstream_env_value(app_context)}
        self._requestor.add_headers(headers)

    def publish_file(self, local_path: str, file_context: FileContext):
        """
        Publish a file to OneStream, implemented using the OneStream File Pull API. The file at the provided path is
        uploaded to S3 and then a request is made to the OneStream API to pull the file for ingestion.
        """
        _upload_to_s3(
            local_path,
            file_context.onestream_transfer.destination_bucket,
            file_context.onestream_transfer.destination_key,
            line_skipper=file_context.onestream_transfer.file_metadata.line_skipper,
        )
        file_submission_id = self._call_onestream_filepull(file_context)
        self._wait_for_ingestion(file_submission_id, file_context)

    def _call_onestream_filepull(self, file_context: FileContext) -> str:
        bucket = file_context.onestream_transfer.destination_bucket
        key = file_context.onestream_transfer.destination_key
        source_file_path = f"s3://{bucket}/{key}"
        file_name = source_file_path.rsplit("/", 1)[-1]

        file_metadata = file_context.onestream_transfer.file_metadata
        json_data = {
            "businessApplication": file_metadata.business_application,
            "schemaName": file_metadata.schema_name,
            "fileSubmissions": [
                {
                    "fileName": file_name,
                    "fileType": file_metadata.file_type,
                    "decodeMetadata": file_metadata.decode_metadata,
                    "customDelimiter": file_metadata.custom_delimiter,
                    "sourceFilePath": source_file_path,
                }
            ],
            "awsIamRole": file_context.onestream_transfer.iam_role_arn,
        }

        onestream_response = self._requestor.post(
            "/internal-operations/developer-platform/stream-management/file-pull-submissions",
            json=json_data,
            version=1,
        )

        if onestream_response != 200:
            logger.error(f"HttpError: {onestream_response.status_code} Server Error: {onestream_response.reason}")

        file_submission_id = onestream_response.json().get("fileSubmissionId")

        if file_submission_id is None:
            raise Exception("OneStream FilePuller API file_submission_id is null.")

        logger.info("file.onestream-publish.submitted", file_submission_id=file_submission_id)
        return file_submission_id

    def _wait_for_ingestion(self, file_submission_id: str, file_context: FileContext):
        # find the time after which we should stop polling and assume an error
        # (never less than five minutes, makes sure we can always poll a couple of times)
        poll_timeout = max(file_context.onestream_transfer.status_polling_timeout_mins, 5)
        stop_time = datetime.now() + timedelta(minutes=poll_timeout)
        status = IngestionStatus.IN_PROGRESS

        while datetime.now() < stop_time:
            status = self._check_ingestion_status(file_submission_id)
            logger.info("file.onestream-publish.check-status", status=status.value)

            if status == IngestionStatus.COMPLETED:
                break

            # two minute intervals between status checks
            time.sleep(120)
        if status != IngestionStatus.COMPLETED:
            raise Exception(
                f"Ingestion did not complete within waiting period, "
                f"last status: {status.value}, FileSubmissionId: {file_submission_id}"
            )

    def _check_ingestion_status(self, file_submission_id: str) -> IngestionStatus:
        onestream_response = self._requestor.get(
            "/internal-operations/developer-platform/stream-management/file-submissions/" + file_submission_id,
            version=1,
        )

        if onestream_response != 200:
            logger.error(f"HttpError: {onestream_response.status_code} Server Error: {onestream_response.reason}")

        json_response = onestream_response.json()
        status = IngestionStatus.from_onestream_status(json_response.get("submissionStatus"))

        if status == IngestionStatus.COMPLETED:
            file_submissions = json_response.get("fileSubmissions")
            for file_submission in file_submissions:
                filename = file_submission["fileSubmissionDefinition"]["sourceFilePath"]
                record_count = file_submission["ingestionSummary"]["sentMessageCount"]
                logger.info("file.onestream-publish.meta", onestream_filename=filename, record_count=record_count)

        return status
