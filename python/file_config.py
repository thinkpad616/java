import re

from cardcore_direct_filemove.exceptions import FileConfigurationError, FileNotConfigured
from cardcore_direct_filemove.models import (
    AppContext,
    DecryptionMode,
    EncryptionMode,
    Environment,
    FileConfig,
    FileContext,
    FilenameParts,
    Region,
    DirectTransferConfig,
    OneStreamTransferConfig,
    OneStreamFileMetadata,
    DirectTransferContext,
    OneStreamTransferContext,
)
from cardcore_direct_filemove.onestream_util import tsys_cmf_decode_metadata, tsys_cmf_line_skipper

Config = dict[Environment, dict[str, FileConfig]]


CONFIG: Config = {
    Environment.LOCAL: {
        # --- ACCEPTANCE TEST FILES ---
        "testing.none.none": FileConfig(
            basename="testing.none.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.none.none",
            decryption_mode=DecryptionMode.NONE,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="local/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.pgp.none": FileConfig(
            basename="testing.pgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.pgp.none",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="local/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.passthroughpgp.none": FileConfig(
            basename="testing.passthroughpgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.passthroughpgp.none",
            decryption_mode=DecryptionMode.PASSTHROUGH_PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="local/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        # --- END ACCEPTANCE TEST FILES ---
    },
    Environment.DEV: {
        # --- ACCEPTANCE TEST FILES ---
        "testing.none.none": FileConfig(
            basename="testing.none.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.none.none",
            decryption_mode=DecryptionMode.NONE,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="dev/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.pgp.none": FileConfig(
            basename="testing.pgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.pgp.none",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="dev/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.passthroughpgp.none": FileConfig(
            basename="testing.passthroughpgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.passthroughpgp.none",
            decryption_mode=DecryptionMode.PASSTHROUGH_PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="dev/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        # --- END ACCEPTANCE TEST FILES ---
        # --- PROCESSING FILES ---
        # Dev is an isolated testing environment, files are kept within our bucket for internal testing
        "CVQ7560.INH.GP00.C13350.MASTER.COLLECT": FileConfig(
            basename="CVQ7560.INH.GP00.C13350.MASTER.COLLECT",
            destination_filename_pattern="{YYYYMMDD}_CVQ7560.INH.GP00.C13350.MASTER.COLLECT",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="dev/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "CVQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR": FileConfig(
            basename="CVQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR",
            destination_filename_pattern="{YYYYMMDD}_CVQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="dev/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        # --- END PROCESSING FILES ---
    },
    Environment.QA: {
        # --- ACCEPTANCE TEST FILES ---
        "testing.none.none": FileConfig(
            basename="testing.none.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.none.none",
            decryption_mode=DecryptionMode.NONE,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="qa/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.pgp.none": FileConfig(
            basename="testing.pgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.pgp.none",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="qa/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        "testing.passthroughpgp.none": FileConfig(
            basename="testing.passthroughpgp.none",
            destination_filename_pattern="{YYYYMMDD}_{HHMMSS}_testing.passthroughpgp.none",
            decryption_mode=DecryptionMode.PASSTHROUGH_PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="qa/direct/output/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        # --- END ACCEPTANCE TEST FILES ---
        # --- PROCESSING FILES ---
        # QA is an integrated environment, files are sent to their recipient on a regular basis
        "CVQ7560.INH.GP00.C13350.MASTER.COLLECT": FileConfig(
            basename="CVQ7560.INH.GP00.C13350.MASTER.COLLECT",
            destination_filename_pattern="{YYYYMMDD}_CVQ7560.INH.GP00.C13350.MASTER.COLLECT",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-cardrecoveries-collections-qa-east-1",
                destination_bucket_west="cof-cardrecoveries-collections-qa-west-2",
                destination_prefix="account/Collections_Master/",
                encryption_mode=EncryptionMode.NONE,
            ),
            onestream_transfer=OneStreamTransferConfig(
                destination_bucket_east="cof-card-core-tsys-dev-east",
                destination_bucket_west="cof-card-core-tsys-dev-west",
                destination_prefix="qa/direct/output/onestream/",
                encryption_mode=EncryptionMode.NONE,
                iam_role_arn=(
                    "arn:aws:iam::685250009713:role/BACARDCOREDATAPROCESSING/ASVSDP/OneStream-File-Pull-CCDP-QA"
                ),
                status_polling_timeout_mins=30,
                file_metadata=OneStreamFileMetadata(
                    business_application="bacardcoredataprocessing",
                    schema_name="collections_tsys_cmf_to_onelake_02",
                    file_type="CUSTOM_DELIMITER_NO_HEADER",
                    decode_metadata=tsys_cmf_decode_metadata,
                    custom_delimiter=59,
                    line_skipper=tsys_cmf_line_skipper,
                ),
            ),
        ),
        "CVQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR": FileConfig(
            basename="CVQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR",
            destination_filename_pattern="{YYYYMMDD}_cmf2.direct.test",
            decryption_mode=DecryptionMode.PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-cardrecoveries-collections-cmf-qa-east-1",
                destination_bucket_west="cof-cardrecoveries-collections-cmf-qa-west-2",
                destination_prefix="Card/accounts/collections_master/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
        # --- END PROCESSING FILES
    },
    Environment.PROD: {
        "CPQ7560.INH.GP00.C13350.MASTER.COLLECT": FileConfig(
            basename="CPQ7560.INH.GP00.C13350.MASTER.COLLECT",
            destination_filename_pattern="{YYYYMMDD}_CPQ7560.INH.GP00.C13350.MASTER.COLLECT",
            decryption_mode=DecryptionMode.PASSTHROUGH_PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-cardrecoveries-collections-prod-east-1",
                destination_bucket_west="cof-cardrecoveries-collections-prod-west-2",
                destination_prefix="account/Collections_Master/",
                encryption_mode=EncryptionMode.NONE,
            ),
            onestream_transfer=OneStreamTransferConfig(
                destination_bucket_east="cof-card-core-tsys-prod-east",
                destination_bucket_west="cof-card-core-tsys-prod-west",
                destination_prefix="direct/output/onestream/",
                encryption_mode=EncryptionMode.NONE,
                iam_role_arn=(
                    "arn:aws:iam::427884659784:role/BACARDCOREDATAPROCESSING/ASVSDP/OneStream-File-Pull-CCDP-Prod"
                ),
                status_polling_timeout_mins=30,
                file_metadata=OneStreamFileMetadata(
                    business_application="bacardcoredataprocessing",
                    schema_name="credit_card_recoveries_collections_master_file_v1",
                    file_type="CUSTOM_DELIMITER_NO_HEADER",
                    decode_metadata=tsys_cmf_decode_metadata,
                    custom_delimiter=59,
                    line_skipper=tsys_cmf_line_skipper,
                ),
            ),
        ),
        "CPQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR": FileConfig(
            basename="CPQ7560.INH.GP00.C13350.CURED.COLLECT.MSTR",
            destination_filename_pattern="{YYYYMMDD}_cmf2.direct.test",
            decryption_mode=DecryptionMode.PASSTHROUGH_PGP,
            direct_transfer=DirectTransferConfig(
                destination_bucket_east="cof-cardrecoveries-collections-cmf-prod-east-1",
                destination_bucket_west="cof-cardrecoveries-collections-cmf-prod-west-2",
                destination_prefix="Card/accounts/collections_master/",
                encryption_mode=EncryptionMode.NONE,
            ),
        ),
    },
}


def _get_config_for_file(env: Environment, basename: str, config: Config = CONFIG) -> FileConfig:
    """
    Retrieves the configuration for a given basename according to the supplied context.

    Raises:
        FileNotConfigured - if there is no file config matching the provided basename and context
    """
    file_config = config.get(env, {}).get(basename)
    if not file_config:
        raise FileNotConfigured(f'Configuration not found for "{basename}" in environment "{env.value}"')
    return file_config


def _get_filename_parts_from_object_key(key: str) -> FilenameParts:
    """
    Extracts the parts of the file name from an S3 object key.

    These are the current assumptions of this implementation:
        - The object key may be nested under a folder structure, which is discarded
        - The filename begins with a datestamp (YYYYMMDD) or a full datetime (YYYYMMDD_HHMMSS),
            which is separated from the basename with an underscore
        - The filename ends with some suffix, e.g. init.dat, which is separated from the basename with an underscore

    Examples:
        - The basename of the key "20000101_ABC.FILE_init.dat" is "ABC.FILE"
        - The basename of the key "qa/20200202_123456_TRANSACTION.FILE_init.dat" is "TRANSACTION.FILE"
    """
    # keep everything past the last occurance of a slash (first occurance from the right)
    file = key.rsplit(sep="/", maxsplit=1)[-1]
    # splitting on underscore twice from the end, we have a prefix, the basename, and a suffix
    prefix, basename, suffix = file.rsplit(sep="_", maxsplit=2)
    # get the datestamp and, if present, timestamp from the prefix
    datestamp, _, timestamp = prefix.partition("_")
    return FilenameParts(datestamp=datestamp, timestamp=timestamp, basename=basename, suffix=suffix)


def _apply_transforms(app_context: AppContext, file_config: FileConfig, filename_parts: FilenameParts) -> FileContext:
    """
    Apply any transformations needed to generate a FileContext which can be used by the remainder of the application.
        - Choose the correct bucket according to the application context
        - Apply any placeholder patterns that are present in the file config (e.g. destination filename)
    """
    # apply placeholder patterns to the final filename
    final_filename = pattern = file_config.destination_filename_pattern
    if "{YYYYMMDD}" in final_filename:
        # check if we have enough digits to apply as a datestamp
        if not re.match("^[0-9]{8}$", filename_parts.datestamp):
            raise FileConfigurationError(
                f'Datestamp "{filename_parts.datestamp}" is not valid to apply to pattern "{pattern}"'
            )
        final_filename = final_filename.replace("{YYYYMMDD}", filename_parts.datestamp)
    if "{HHMMSS}" in final_filename:
        # check if we have enough digits to apply as a timestamp
        if not re.match("^[0-9]{6}$", filename_parts.timestamp):
            raise FileConfigurationError(
                f'Timestamp "{filename_parts.timestamp}" is not valid to apply to pattern "{pattern}"'
            )
        final_filename = final_filename.replace("{HHMMSS}", filename_parts.timestamp)
    # create DirectTransferContext if required
    direct_transfer_context = None
    if file_config.direct_transfer:
        final_key = file_config.direct_transfer.destination_prefix + final_filename
        final_bucket = (
            file_config.direct_transfer.destination_bucket_west
            if app_context.region == Region.WEST
            else file_config.direct_transfer.destination_bucket_east
        )
        direct_transfer_context = DirectTransferContext(
            destination_bucket=final_bucket,
            destination_key=final_key,
            encryption_mode=file_config.direct_transfer.encryption_mode,
        )
    # create OneStreamTransferContext if required
    onestream_transfer_context = None
    if file_config.onestream_transfer:
        final_key = file_config.onestream_transfer.destination_prefix + final_filename
        final_bucket = (
            file_config.onestream_transfer.destination_bucket_west
            if app_context.region == Region.WEST
            else file_config.onestream_transfer.destination_bucket_east
        )
        onestream_transfer_context = OneStreamTransferContext(
            destination_bucket=final_bucket,
            destination_key=final_key,
            encryption_mode=file_config.onestream_transfer.encryption_mode,
            iam_role_arn=file_config.onestream_transfer.iam_role_arn,
            status_polling_timeout_mins=file_config.onestream_transfer.status_polling_timeout_mins,
            file_metadata=file_config.onestream_transfer.file_metadata,
        )
    return FileContext(
        basename=file_config.basename,
        decryption_mode=file_config.decryption_mode,
        direct_transfer=direct_transfer_context,
        onestream_transfer=onestream_transfer_context,
    )


def get_file_context(app_context: AppContext) -> FileContext:
    """
    Retrieves the context needed to work with the current file based on the file's configuration,
    the application context, and any other transformations needed.
    """
    filename_parts = _get_filename_parts_from_object_key(app_context.input_key)
    file_config = _get_config_for_file(app_context.env, filename_parts.basename)
    return _apply_transforms(app_context, file_config, filename_parts)
