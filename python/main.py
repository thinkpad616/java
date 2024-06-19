import logging
import os
import sys
import tempfile
import time

import structlog

from cardcore_direct_filemove import encryption, utils
from cardcore_direct_filemove import file_config
from cardcore_direct_filemove import s3_util
from cardcore_direct_filemove.exceptions import EnvironmentVariableNotFound, FileNotConfigured, RegionNotActive
from cardcore_direct_filemove.models import DecryptionMode, Environment, Region, AppContext
from cardcore_direct_filemove.onestream import OneStreamService

DEFAULT_APP_NAME = "cardcore-direct-filemove"

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# basic config pulled from https://www.structlog.org/en/stable/standard-library.html
structlog.configure(
    processors=[
        # Needs to be first processor to support contextvars (context-local variables)
        structlog.contextvars.merge_contextvars,
        # If log level is too low, abort pipeline and throw away log entry.
        structlog.stdlib.filter_by_level,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt="iso"),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If the "exc_info" key in the event dict is either true or a
        # sys.exc_info() tuple, remove "exc_info" and render the exception
        # with traceback into the "exception" key.
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a unicode str.
        structlog.processors.UnicodeDecoder(),
        # Render the final event dict as JSON.
        structlog.processors.JSONRenderer(),
    ],
    # `wrapper_class` is the bound logger that you get back from
    # get_logger(). This one imitates the API of `logging.Logger`.
    wrapper_class=structlog.stdlib.BoundLogger,
    # `logger_factory` is used to create wrapped loggers that are used for
    # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
    # string) from the final processor (`JSONRenderer`) will be passed to
    # the method of the same name as that you've called on the bound logger.
    logger_factory=structlog.stdlib.LoggerFactory(),
    # Effectively freeze configuration after creating the first bound logger.
    cache_logger_on_first_use=True,
)

logger = structlog.stdlib.get_logger()


def main():
    app_start = time.perf_counter()
    try:
        # bind at least an app name so that logs are searchable even if setup fails
        structlog.contextvars.bind_contextvars(app=DEFAULT_APP_NAME)
        # configure application based on incoming env vars (impacts all further steps)
        app_context = _get_context_from_environment()
        # bind logging context available from environment
        structlog.contextvars.bind_contextvars(
            app=app_context.app,
            env=app_context.env.value,
            region=app_context.region.value,
            input_bucket=app_context.input_bucket,
            input_key=app_context.input_key,
        )

        # stop now if we are not the active region (and the region check is not skipped)
        utils.enforce_active_region(app_context.region)

        file_context = file_config.get_file_context(app_context)
        # bind logging context available from the parsed config
        structlog.contextvars.bind_contextvars(
            basename=file_context.basename,
            decryption_mode=file_context.decryption_mode.value,
            direct_transfer=file_context.direct_transfer is not None,
            onestream_transfer=file_context.onestream_transfer is not None,
        )
        logger.info("app.start")
        with tempfile.TemporaryDirectory() as temp_dir:
            # download file from S3
            download_start = time.perf_counter()
            path = os.path.join(temp_dir, "from_s3")
            s3_util.download_file(app_context.input_bucket, app_context.input_key, path)
            logger.info("file.download", download_duration=(time.perf_counter() - download_start))
            # create a crypt service based on what decryption mode we are using
            if file_context.decryption_mode == DecryptionMode.PGP:
                decryption_service = _setup_pgp_service()
            elif file_context.decryption_mode == DecryptionMode.PASSTHROUGH_PGP:
                decryption_service = _setup_pgp_passthrough_service()
            else:
                decryption_service = None

            # Use the crypt service to decrypt the file
            if decryption_service is not None:
                decrypt_start = time.perf_counter()
                decrypted_path = os.path.join(temp_dir, "decrypted")
                decryption_service.decrypt_file(path, decrypted_path)
                path = decrypted_path
                logger.info("file.decrypt", decrypt_duration=(time.perf_counter() - decrypt_start))

            # TODO: Support encryption methods
            # create a crypt service based on what encryption mode we are using
            # encryption_service = None

            # Use the crypt service to encrypt the file
            # if encryption_service is not None:
            #     encryption_service.encrypt("...", "...", "...")
            # write file to destination
            if file_context.direct_transfer:
                prev_context = structlog.contextvars.bind_contextvars(
                    destination_bucket=file_context.direct_transfer.destination_bucket,
                    destination_key=file_context.direct_transfer.destination_key,
                    encryption_mode=file_context.direct_transfer.encryption_mode.value,
                )
                upload_start = time.perf_counter()
                logger.info("file.internal-upload.start")
                s3_util.upload_file(
                    path, file_context.direct_transfer.destination_bucket, file_context.direct_transfer.destination_key
                )
                logger.info("file.internal-upload.finish", upload_duration=(time.perf_counter() - upload_start))
                structlog.contextvars.reset_contextvars(**prev_context)
            try:
                if file_context.onestream_transfer:
                    prev_context = structlog.contextvars.bind_contextvars(
                        onestream_schema=file_context.onestream_transfer.file_metadata.schema_name,
                        destination_bucket=file_context.onestream_transfer.destination_bucket,
                        destination_key=file_context.onestream_transfer.destination_key,
                        encryption_mode=file_context.onestream_transfer.encryption_mode.value,
                    )
                    upload_start = time.perf_counter()
                    logger.info("file.onestream-publish.start")
                    onestream_service = _setup_onestream_service(app_context)
                    onestream_service.publish_file(path, file_context)
                    logger.info("file.onestream-publish.finish", upload_duration=(time.perf_counter() - upload_start))
                    structlog.contextvars.reset_contextvars(**prev_context)
            except Exception as exc:
                logger.exception("file.onestream-publish.exception", exc_info=exc)
    except FileNotConfigured:
        logger.warning("file.skipped")
    except RegionNotActive:
        logger.info("region-check.not-active")
    except Exception:
        logger.exception("app.failed")
        raise
    logger.info("app.finish", app_duration=(time.perf_counter() - app_start))


def _get_required_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        raise EnvironmentVariableNotFound(f"{name} was not set")


def _get_context_from_environment() -> AppContext:
    app = os.environ.get("APP_NAME", DEFAULT_APP_NAME)
    env = _get_required_env("ENV")
    region = _get_required_env("AWS_REGION")
    bucket = _get_required_env("S3_BUCKET_NAME")
    key = _get_required_env("S3_OBJECT_KEY")
    return AppContext(
        app=app,
        env=Environment(env),
        region=Region(region),
        input_bucket=bucket,
        input_key=key,
    )


def _setup_pgp_service() -> encryption.PGPService:
    keyring = _get_required_env("APP_PGP_KEYRING")
    passphrase = _get_required_env("APP_PGP_PASSPHRASE")
    return encryption.PGPService(keyring=keyring, passphrase=passphrase)


def _setup_pgp_passthrough_service() -> encryption.PGPService:
    passthrough_keyring = _get_required_env("APP_PGP_PASSTHROUGH_KEYRING")
    passthrough_passphrase = _get_required_env("APP_PGP_PASSTHROUGH_PASSPHRASE")
    return encryption.PGPService(keyring=passthrough_keyring, passphrase=passthrough_passphrase)


def _setup_onestream_service(app_context: AppContext) -> OneStreamService:
    # CoS paths (and therefore environment variable names) are different in prod vs nonprod >:(
    if app_context.env == Environment.PROD:
        client_id = _get_required_env("APP_P_CLIENT_ID")
        client_secret = _get_required_env("APP_P_CLIENT_SECRET")
    else:
        client_id = _get_required_env("APP_QA_CLIENT_ID")
        client_secret = _get_required_env("APP_QA_CLIENT_SECRET")
    return OneStreamService(app_context, client_id, client_secret)


if __name__ == "__main__":
    main()
