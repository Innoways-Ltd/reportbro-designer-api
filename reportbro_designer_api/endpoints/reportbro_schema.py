# -*- coding: utf-8 -*-
"""
@create: 2022-07-25 10:39:19.

@author: ppolxda

@desc: ReportBro Api
"""

from typing import List
from typing import Optional
from typing import Union

from pydantic import Field

from reportbro_designer_api.backend import schemas as ss
from reportbro_designer_api.utils.model import BaseModel
from reportbro_designer_api.utils.model import DataResponse
from reportbro_designer_api.utils.model import ListResponse


class TemplateListData(ss.TemplateInfo):
    """TemplateList."""

    template_designer_page: str = Field(title="Template Designer Page")


class TemplateDescData(ss.TemplateConfigInfo):
    """TemplateList."""

    template_designer_page: str = Field(title="Template Designer Page")


class TemplateDownLoadData(BaseModel):
    """TemplateDownLoadData."""

    download_key: str = Field(title="Pdf download key")
    download_url: str = Field(title="Pdf download url")


class RequestCreateTemplate(ss.BaseTemplate):
    """RequestCreateTemplate."""


class RequestUploadTemplate(BaseModel):
    """RequestUploadTemplate."""

    report: dict = Field(title="Template Data")
    template_name: Optional[str] = Field(default=None, title="Template Name")
    template_type: Optional[str] = Field(default=None, title="Template Type")


class RequestGenerateTemplate(BaseModel):
    """RequestGenerateTemplate."""

    output_format: str = Field(
        "pdf", title="Output Format(pdf|xlsx)", pattern=r"^(pdf|xlsx)$"
    )
    data: dict = Field(title="Source Data")


class RequestGenerateDataTemplate(BaseModel):
    """RequestGenerateTemplate."""

    tid: str = Field(title="Template id")
    version_id: Union[str, None] = Field(default=None, title="Template version id")
    data: dict = Field(default_factory=dict, title="Source Data")


class RequestGenerateUrlTemplate(BaseModel):
    """RequestGenerateTemplate."""

    pdf_url: str = Field(title="Download url for pdf")


class RequestGenerateReviewTemplate(BaseModel):
    """RequestReviewTemplate."""

    report: dict = Field(title="Template Data")
    data: dict = Field(default_factory=dict, title="Source Data")


class RequestGenerateTUrlTemplate(BaseModel):
    """RequestGenerateTUrlTemplate."""

    report_url: dict = Field(title="Template Data")
    data: dict = Field(default_factory=dict, title="Source Data")


class PdfData(BaseModel):
    """PdfData."""

    filename: str = Field(title="Pdf file name")
    report_file: bytes = Field(default_factory=dict, title="Pdf Data")


class RequestMultiGenerateTemplate(BaseModel):
    """RequestMultiGenerateTemplate."""

    output_format: str = Field(
        "pdf", title="Output Format(pdf|xlsx)", pattern=r"^(pdf|xlsx)$"
    )
    templates: List[
        Union[
            RequestGenerateUrlTemplate,
            RequestGenerateTUrlTemplate,
            RequestGenerateDataTemplate,
            RequestGenerateReviewTemplate,
        ]
    ] = Field(default_factory=list, title="Input templates list")


class RequestReviewTemplate(RequestGenerateTemplate):
    """RequestReviewTemplate."""

    report: dict = Field(title="Template Data")
    is_test_data: bool = Field(title="Is test data")


class RequestCloneTemplate(BaseModel):
    """RequestCloneTemplate."""

    from_tid: str = Field(title="Clone from template id")
    from_version_id: Optional[str] = Field(None, title="Clone from Template version id")


class RequestCopyTemplate(BaseModel):
    """RequestCopyTemplate."""

    from_tid: str = Field(title="Copy from template id")
    from_version_id: Optional[str] = Field(None, title="Copy from Template version id")
    new_template_name: Optional[str] = Field(None, title="New template name")
    new_template_type: Optional[str] = Field(None, title="New template type")


class TemplateListResponse(ListResponse[TemplateListData]):
    """TemplateListResponse."""


class TemplateDescResponse(DataResponse[TemplateDescData]):
    """TemplateDescResponse."""


class TemplateDataResponse(DataResponse[TemplateListData]):
    """TemplateDataResponse."""


class TemplateDownLoadResponse(DataResponse[TemplateDownLoadData]):
    """TemplateDownLoadResponse."""
