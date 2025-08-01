# -*- coding: utf-8 -*-
"""
@create: 2022-07-22 17:54:46.

@author: ppolxda

@desc: S3 Api
"""

import base64
import json
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Dict
from typing import List
from typing import Optional

from reportbro_designer_api.errors import BackendError
from reportbro_designer_api.utils.s3_client import S3Client
from reportbro_designer_api.utils.s3_client import hook_create_bucket_when_not_exist
from reportbro_designer_api.utils.s3_client import hook_object_not_exist

from .. import schemas as sa
from .base import BackendBase


class S3BackendClient:
    """S3Backend."""

    def __init__(
        self,
        s3cli: S3Client,
        project: str = "default",
        default_template: Optional[dict] = None,
        query_max_limit: int = 1000,
    ):
        """Init s3."""
        self._s3cli = s3cli
        if default_template is None:
            default_template = {}

        self.project_name = project
        self.default_template = default_template
        self.query_max_limit = query_max_limit

    @property
    def bucket_name(self):
        """Get bucket_name."""
        return self._s3cli.bucket_name

    @asynccontextmanager
    async def s3cli(self):
        """Get s3cli."""
        async with self._s3cli.s3cli() as client:
            yield client

    @staticmethod
    def encode_matedata(data: Dict[str, str]):
        """Encode matedata."""
        return {
            key: base64.b64encode(val.encode("utf8")).decode("utf8")
            for key, val in data.items()
        }

    @staticmethod
    def decode_matedata(data: Dict[str, str]):
        """Decode matedata."""

        def decode(val: str):
            try:
                return base64.b64decode(val.encode("utf8")).decode("utf8")
            except Exception:
                return val

        return {key: decode(val) for key, val in data.items()}

    def make_template_key(
        self, tid: Optional[str] = None, project: Optional[str] = None
    ):
        """Make template key."""
        if not project:
            project = self.project_name

        if tid:
            return "/".join([self._s3cli.TEMPLATES_PREFIX, project, tid])
        else:
            return "/".join([self._s3cli.TEMPLATES_PREFIX, project])

    @hook_create_bucket_when_not_exist()
    async def _get_templates_list(
        self,
        tid: Optional[str] = None,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[sa.TemplateInfo]:
        """Get templates list."""
        assert (
            (template_name or not template_name)
            and (version_id or not version_id)
            and (offset >= 0)
        )

        async with self.s3cli() as client:
            _id_prefix = self.make_template_key(project=project)
            r = await client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=_id_prefix, MaxKeys=limit
            )
            res = []
            for obj in r.get("Contents", []):
                head = await client.head_object(Bucket=self.bucket_name, Key=obj["Key"])
                tinfo = self.__conv_dict(obj, head)

                if (template_type and template_type != tinfo.template_type) or (
                    template_name and template_name != tinfo.template_name
                ):
                    continue

                res.append(tinfo)
            return res

    @classmethod
    def __conv_dict(cls, obj, head):
        """Get Body."""
        assert "/" in obj.get("Key", "")
        return sa.TemplateInfo(
            **{
                "tid": str(obj.get("Key", "")).rsplit("/", maxsplit=1)[-1],
                "version_id": obj.get("VersionId", "") or head["VersionId"],
                "updated_at": head["LastModified"],
                **cls.decode_matedata(dict(head["Metadata"])),
            }
        )

    async def _get_templates_version_list(
        self,
        tid: str,
        project: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[sa.TemplateInfo]:
        """Get templates list."""
        assert offset >= 0

        async with self.s3cli() as client:
            _id_prefix = self.make_template_key(tid, project=project)
            r = await client.list_object_versions(
                Bucket=self.bucket_name, Prefix=_id_prefix, MaxKeys=limit
            )

            res = []
            for obj in r.get("Versions", []):
                head = await client.head_object(
                    Bucket=self.bucket_name,
                    Key=obj["Key"],
                    VersionId=obj.get("VersionId", ""),
                )
                tinfo = self.__conv_dict(obj, head)
                res.append(tinfo)
            return res

    @hook_create_bucket_when_not_exist()
    async def _put_templates(
        self,
        tid: str,
        template_name: str,
        template_type: str,
        report: dict,
        project: Optional[str] = None,
    ) -> sa.BaseTemplateId:
        """Put templates."""
        if not report:
            if self.default_template:
                report = self.default_template
            else:
                report = {}

        if not project:
            project = self.project_name

        object_key = self.make_template_key(tid, project)
        async with self.s3cli() as client:
            res = await client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=BytesIO(json.dumps(report, indent=2).encode()),
                ContentType="application/json",
                Metadata=self.encode_matedata(
                    {
                        "template_name": template_name,
                        "template_type": template_type,
                    }
                ),
            )
            if res.get("ResponseMetadata", {}).get("HTTPStatusCode", "") != 200:
                raise BackendError(f"Save Template File Error[{res}]")

            version_id = res["VersionId"]

            return sa.BaseTemplateId(
                tid=tid,
                version_id=version_id,
            )

    @hook_create_bucket_when_not_exist()
    @hook_object_not_exist()
    async def _get_template(
        self,
        tid: str,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Optional[sa.TemplateConfigInfo]:
        """Get templates."""
        object_key = self.make_template_key(tid, project)

        async with self.s3cli() as client:
            if version_id:
                res = await client.get_object(
                    Bucket=self.bucket_name, Key=object_key, VersionId=version_id
                )
            else:
                res = await client.get_object(Bucket=self.bucket_name, Key=object_key)

            data = await res["Body"].read()
            body = json.loads(str(data.decode("utf8")))
            if not body and self.default_template:
                body = self.default_template

            return sa.TemplateConfigInfo(
                **{
                    "tid": tid,
                    "version_id": res["VersionId"],
                    "updated_at": res["LastModified"],
                    **self.decode_matedata(res["Metadata"]),
                    "report": body,
                }
            )

    @hook_create_bucket_when_not_exist()
    async def _delete_template(
        self,
        tid: str,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
    ):
        """Delete templates version."""
        async with self.s3cli() as client:
            if version_id:
                object_key = self.make_template_key(tid, project)
                delete_list = [(object_key, version_id)]
            else:
                delete_list = [
                    (self.make_template_key(i.tid, project), i.version_id)
                    for i in await self._get_templates_version_list(
                        tid, project=project, limit=10000
                    )
                ]

            await client.delete_objects(
                Bucket=self.bucket_name,
                Delete={
                    "Objects": [
                        {"Key": object_key, "VersionId": version_id}
                        for object_key, version_id in delete_list
                    ],
                },
            )


class S3Backend(S3BackendClient, BackendBase):
    """S3Backend."""

    async def clean_all(self):
        """Clean database, This api only use for test."""
        await self._s3cli.clear_bucket()

    async def is_template_exist(
        self,
        tid: str,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> bool:
        """Is templates Exist."""
        object_id = self.make_template_key(tid, project)
        r = await self._s3cli._is_object_exist(object_id, version_id)
        return r
        
    async def is_template_name_exist(
        self,
        template_name: str,
        exclude_tid: Optional[str] = None,
        project: Optional[str] = None,
    ) -> bool:
        """Check if template name already exists."""
        # Get all templates with this project
        templates = await self.get_templates_list(
            project=project,
            limit=100,  # Increase limit to catch more potential matches
        )
        
        # Check if any template (excluding the one with tid=exclude_tid) has the same name
        for template in templates:
            if template.template_name == template_name and (exclude_tid is None or template.tid != exclude_tid):
                return True
                
        return False

    async def get_templates_list(
        self,
        tid: Optional[str] = None,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[sa.TemplateInfo]:
        """Get templates list."""
        r = await self._get_templates_list(
            tid, version_id, project, template_name, template_type, limit, offset
        )
        return r

    async def get_templates_version_list(
        self,
        tid: str,
        project: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[sa.TemplateInfo]:
        """Get templates version list."""
        r = await self._get_templates_version_list(tid, project, limit, offset)
        return r

    async def get_template(
        self,
        tid: str,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Optional[sa.TemplateConfigInfo]:
        """Get templates."""
        r = await self._get_template(tid, version_id, project)
        return r

    async def put_template(
        self,
        template_name: str,
        template_type: str,
        report: dict,
        tid: Optional[str] = None,
        project: Optional[str] = None,
        skip_name_check: bool = False,
    ) -> sa.BaseTemplateId:
        """Put templates."""
        # Check if template_name is unique (excluding the current tid if specified)
        if template_name and template_name != "" and not skip_name_check:
            name_exists = await self.is_template_name_exist(template_name, exclude_tid=tid, project=project)
            if name_exists:
                from fastapi import HTTPException
                from starlette.status import HTTP_400_BAD_REQUEST
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail=f"Template name '{template_name}' already exists. Template names must be unique."
                )
            
        if tid is None:
            tid = await self.gen_uuid_object_key(project)

        r = await self._put_templates(
            tid, template_name, template_type, report, project
        )
        return r

    async def delete_template(
        self,
        tid: str,
        version_id: Optional[str] = None,
        project: Optional[str] = None,
    ):
        """Delete templates version."""
        r = await self._delete_template(tid, version_id, project)
        return r
