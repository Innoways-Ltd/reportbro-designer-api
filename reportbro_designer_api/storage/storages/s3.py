# -*- coding: utf-8 -*-
"""
@create: 2023-06-21 20:59:09.

@author: ppolxda

@desc: S3 Storage
"""
from io import BytesIO
from typing import Optional

from fastapi import BackgroundTasks
from filetype import guess

from reportbro_designer_api.utils.s3_client import S3Client
from reportbro_designer_api.utils.s3_client import hook_create_bucket_when_not_exist
from reportbro_designer_api.utils.s3_client import hook_object_not_exist

from ...errors import StorageError
from .base import StorageBase


class S3Storage(StorageBase):
    """S3Storage."""

    def __init__(self, s3cli: S3Client):
        """init."""
        self._s3cli = s3cli

    def bucket(self):
        """Bucket name."""
        return self._s3cli.bucket_name

    async def clean_all(self):
        """Clean database, This api only use for test."""
        await self._s3cli.clear_bucket()

    @hook_create_bucket_when_not_exist()
    async def generate_presigned_url(self, s3_key: str) -> str:
        """Put file."""
        s3_obj = self.s3parse(s3_key)

        assert s3_obj.hostname
        async with self._s3cli.s3cli() as client:
            download_url = await client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": s3_obj.hostname, "Key": s3_obj.path},
                ExpiresIn=3600,
            )
            return download_url

    @hook_create_bucket_when_not_exist()
    async def put_file(
        self, s3_key: str, file_buffer: bytes, background_tasks: Optional[BackgroundTasks] = None
    ):
        """Put file."""
        s3_obj = self.s3parse(s3_key)
        
        # Try to guess the content type
        content = guess(file_buffer)
        if content:
            content_type = content.mime
        else:
            # If filetype can't detect, try to determine from filename or default to JSON
            if s3_obj.path.endswith('.json'):
                content_type = 'application/json'
            elif s3_obj.path.endswith('.pdf'):
                content_type = 'application/pdf'
            elif s3_obj.path.endswith('.xlsx'):
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                # Default to octet-stream for unknown files
                content_type = 'application/octet-stream'
        assert s3_obj.hostname
        async with self._s3cli.s3cli() as client:
            res = await client.put_object(
                Bucket=s3_obj.hostname,
                Key=s3_obj.path,
                Body=BytesIO(file_buffer),
                ContentType=content_type,
            )
            if res.get("ResponseMetadata", {}).get("HTTPStatusCode", "") != 200:
                raise StorageError(f"Save file error[{res}]")

    @hook_create_bucket_when_not_exist()
    @hook_object_not_exist()
    async def get_file(self, s3_key: str) -> Optional[bytes]:
        """Get file."""
        s3_obj = self.s3parse(s3_key)
        assert s3_obj.hostname
        async with self._s3cli.s3cli() as client:
            res = await client.get_object(Bucket=s3_obj.hostname, Key=s3_obj.path)
            data = await res["Body"].read()
            return data
