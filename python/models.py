from dataclasses import dataclass
from enum import Enum
from typing import Callable


class DecryptionMode(Enum):
    NONE = "none"
    PGP = "pgp"
    PASSTHROUGH_PGP = "passthrough_pgp"


class EncryptionMode(Enum):
    NONE = "none"


class Environment(Enum):
    TEST = "test"
    LOCAL = "local"
    DEV = "dev"
    QA = "qa"
    PROD = "prod"


class Region(Enum):
    EAST = "us-east-1"
    WEST = "us-west-2"


@dataclass
class AppContext:
    app: str
    env: Environment
    region: Region
    input_bucket: str
    input_key: str


@dataclass
class DirectTransferConfig:
    destination_bucket_east: str
    destination_bucket_west: str
    destination_prefix: str
    encryption_mode: EncryptionMode


@dataclass
class OneStreamFileMetadata:
    business_application: str
    schema_name: str
    file_type: str
    decode_metadata: str
    custom_delimiter: int
    line_skipper: Callable[[str], bool] | None = None


@dataclass
class OneStreamTransferConfig:
    destination_bucket_east: str
    destination_bucket_west: str
    destination_prefix: str
    encryption_mode: EncryptionMode
    iam_role_arn: str
    status_polling_timeout_mins: int
    file_metadata: OneStreamFileMetadata


@dataclass
class FileConfig:
    basename: str
    destination_filename_pattern: str
    decryption_mode: DecryptionMode
    direct_transfer: DirectTransferConfig | None = None
    onestream_transfer: OneStreamTransferConfig | None = None


@dataclass
class FilenameParts:
    datestamp: str
    timestamp: str
    basename: str
    suffix: str


@dataclass
class DirectTransferContext:
    destination_bucket: str
    destination_key: str
    encryption_mode: EncryptionMode


@dataclass
class OneStreamTransferContext:
    destination_bucket: str
    destination_key: str
    encryption_mode: EncryptionMode
    iam_role_arn: str
    status_polling_timeout_mins: int
    file_metadata: OneStreamFileMetadata


@dataclass
class FileContext:
    basename: str
    decryption_mode: DecryptionMode
    direct_transfer: DirectTransferContext | None = None
    onestream_transfer: OneStreamTransferContext | None = None
