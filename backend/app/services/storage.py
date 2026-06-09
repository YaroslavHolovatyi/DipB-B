"""
Object storage adapter — generates presigned upload URLs.

The mobile app posts a `multipart/form-data` request directly to the bucket
URL we hand back; the backend never streams large image bodies. In local dev
we hand back a no-op `file://` URL pointing into the OS tempdir so the rest
of the flow keeps working without S3/R2 credentials.
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PresignedUpload:
    """Bundle a client uses to upload a single object."""

    upload_url: str         # PUT this URL with the file body
    public_url: str         # GET-able URL once the upload completes
    key: str                # storage key (used in the DB row)
    expires_in: int         # seconds


class StorageService(Protocol):
    async def presign_upload(self, *, prefix: str, content_type: str) -> PresignedUpload: ...


# --------------------------------------------------------------------------- #
# Stub
# --------------------------------------------------------------------------- #
class StubStorageService:
    """Writes nothing — just hands back a stable temp path."""

    def __init__(self) -> None:
        self._base = Path(tempfile.gettempdir()) / "bb-uploads"
        self._base.mkdir(parents=True, exist_ok=True)

    async def presign_upload(self, *, prefix: str, content_type: str) -> PresignedUpload:  # noqa: ARG002
        key = f"{prefix.strip('/')}/{uuid.uuid4().hex}"
        file_path = self._base / key.replace("/", "_")
        logger.info("StubStorageService: handing back file:// URL for %s", key)
        return PresignedUpload(
            upload_url=f"file://{file_path}",
            public_url=f"file://{file_path}",
            key=key,
            expires_in=3600,
        )


# --------------------------------------------------------------------------- #
# Live — S3 / Cloudflare R2 presigner (lazy boto3 import)
# --------------------------------------------------------------------------- #
class S3StorageService:
    def __init__(self) -> None:
        import boto3  # noqa: PLC0415

        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

    async def presign_upload(self, *, prefix: str, content_type: str) -> PresignedUpload:
        key = f"{prefix.strip('/')}/{uuid.uuid4().hex}"
        upload_url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
        public_url = (
            f"{settings.s3_endpoint_url.rstrip('/')}/{self._bucket}/{key}"
            if settings.s3_endpoint_url
            else f"https://{self._bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"
        )
        return PresignedUpload(upload_url=upload_url, public_url=public_url, key=key, expires_in=3600)


def build_storage_service() -> StorageService:
    if settings.s3_bucket and settings.s3_access_key_id:
        return S3StorageService()
    return StubStorageService()
