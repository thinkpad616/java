class OneStreamService:
    _requestor: dx_requests.Requestor

    def __init__(self, app_context: AppContext, client_id: str, client_secret: str, retries: int = 5) -> None:
        self.app_context = app_context  # Store the app_context for later use
        self._requestor = dx_requests.Requestor(
            client_id=client_id,
            client_secret=client_secret,
            api_retries=retries,
        )
        headers = {"X-Upstream-Env": _upstream_env_value(app_context)}
        self._requestor.add_headers(headers)

    def _get_api_version(self) -> int:
        """Determine the API version based on the environment."""
        return 2 if self.app_context.env == Environment.QA else 1

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

        version = self._get_api_version()
        onestream_response = self._requestor.post(
            "/internal-operations/developer-platform/stream-management/file-pull-submissions",
            json=json_data,
            version=version,
        )

        if onestream_response.status_code != 200:
            logger.error(
                f"HttpError: {onestream_response.status_code} Server Error: {onestream_response.reason} "
                f"Response Payload: {onestream_response.text}"
            )

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
        version = self._get_api_version()
        onestream_response = self._requestor.get(
            "/internal-operations/developer-platform/stream-management/file-submissions/" + file_submission_id,
            version=version,
        )

        if onestream_response.status_code != 200:
            logger.error(
                f"HttpError: {onestream_response.status_code} Server Error: {onestream_response.reason} "
                f"Response Payload: {onestream_response.text}"
            )

        json_response = onestream_response.json()
        status = IngestionStatus.from_onestream_status(json_response.get("submissionStatus"))

        if status == IngestionStatus.COMPLETED:
            file_submissions = json_response.get("fileSubmissions")
            for file_submission in file_submissions:
                filename = file_submission["fileSubmissionDefinition"]["sourceFilePath"]
                record_count = file_submission["ingestionSummary"]["sentMessageCount"]
                logger.info("file.onestream-publish.meta", onestream_filename=filename, record_count=record_count)

        return status
