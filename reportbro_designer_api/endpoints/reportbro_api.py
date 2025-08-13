# -*- coding: utf-8 -*-
"""
@create: 2022-07-25 10:39:19.

@author: ppolxda

@desc: ReportBro Api
"""

import asyncio
import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from enum import Enum
from functools import partial
from io import BytesIO
from timeit import default_timer as timer
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from urllib.parse import urlencode

import aiohttp
import filetype
import PyPDF2
from aiohttp import ClientTimeout
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi.responses import PlainTextResponse
from fastapi.responses import StreamingResponse
from reportbro import ReportBroError
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_400_BAD_REQUEST

from ..backend.backends.base import BackendBase
from ..clients import FONTS_LOADER
from ..clients import StorageMange
from ..clients import get_meth_cli
from ..clients import get_storage_mange
from ..errors import TemplageNotFoundError
from ..settings import settings
from ..utils.logger import LOGGER
from ..utils.model import ErrorResponse
from ..utils.report import ReportPdf
from ..utils.report import fill_default
from ..utils.report import process_image_urls
from .reportbro_schema import PdfData
from .reportbro_schema import RequestCloneTemplate
from .reportbro_schema import RequestCopyTemplate
from .reportbro_schema import RequestCreateTemplate
from .reportbro_schema import RequestGenerateDataTemplate
from .reportbro_schema import RequestGenerateReviewTemplate
from .reportbro_schema import RequestGenerateTemplate
from .reportbro_schema import RequestGenerateTUrlTemplate
from .reportbro_schema import RequestGenerateUrlTemplate
from .reportbro_schema import RequestImportTemplate
from .reportbro_schema import RequestMultiGenerateTemplate
from .reportbro_schema import RequestReviewTemplate
from .reportbro_schema import RequestUploadTemplate
from .reportbro_schema import TemplateDataResponse
from .reportbro_schema import TemplateDescData
from .reportbro_schema import TemplateDescResponse
from .reportbro_schema import TemplateDownLoadData
from .reportbro_schema import TemplateDownLoadResponse
from .reportbro_schema import TemplateListData
from .reportbro_schema import TemplateListResponse

router = APIRouter()
TAGS: List[Union[str, Enum]] = ["ReportBro Api"]
GEN_TAGS: List[Union[str, Enum]] = ["ReportBro Generate Api"]
# templates = Jinja2Templates(directory=settings.TEMPLATES_PATH)


def is_pdf(data: bytes):
    """is_pdf."""
    rtype = filetype.guess(data)
    return rtype and rtype.extension == "pdf"


@router.get(
    "/templates/list",
    tags=TAGS,
    name="Get templates List",
    response_model=TemplateListResponse,
)
async def main_index_page(
    request: Request,
    client: BackendBase = Depends(get_meth_cli),
):
    """Get templates List."""
    list_ = await client.get_templates_list(limit=settings.PAGE_LIMIT)
    return TemplateListResponse(
        code=HTTP_200_OK,
        error="ok",
        data=[
            TemplateListData(
                **{
                    **i.__dict__,
                    "template_designer_page": str(
                        request.url_for("Templates Designer page", tid=i.tid)
                    ),
                }
            )
            for i in list_
        ],
    )


@router.post(
    "/templates/copy",
    tags=TAGS,
    name="Copy Templates",
    response_model=TemplateDataResponse,
)
async def copy_templates(
    request: Request,
    req: RequestCopyTemplate,
    client: BackendBase = Depends(get_meth_cli),
):
    """Copy Templates to a new template with a new name."""
    # Get the source template
    obj = await client.get_template(req.from_tid, req.from_version_id)
    if not obj:
        raise TemplageNotFoundError("source template not found")

    if not req.from_version_id:
        req.from_version_id = obj.version_id

    # Use the provided new_template_name or default to the source template's name
    new_template_name = req.new_template_name if req.new_template_name else obj.template_name
    # Use the provided template_type or default to the source template's type
    new_template_type = req.new_template_type if req.new_template_type else obj.template_type

    # Add " - Copy" suffix to the template name
    template_name_with_suffix = f"{new_template_name} - Copy"

    try:
        # Create a new template with the copied data
        rrr = await client.put_template(
            template_name=template_name_with_suffix,
            template_type=new_template_type,
            report=obj.report,  # Copy the report data
        )
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=template_name_with_suffix,
                template_type=new_template_type,
                tid=rrr.tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including the duplicate template name error)
        raise ex


@router.get(
    "/templates/{tid}/versions",
    tags=TAGS,
    name="Get templates Versions",
    response_model=TemplateListResponse,
)
async def get_versions(
    request: Request,
    tid: str = Path(title="Template id"),
    client: BackendBase = Depends(get_meth_cli),
):
    """Get templates List."""
    list_ = await client.get_templates_version_list(tid)
    return TemplateListResponse(
        code=HTTP_200_OK,
        error="ok",
        data=[
            TemplateListData(
                **{
                    **i.__dict__,
                    "template_designer_page": str(
                        request.url_for("Templates Designer page", tid=i.tid)
                    ),
                }
            )
            for i in list_
        ],
    )


@router.get(
    "/templates/{tid}/desc",
    tags=TAGS,
    name="Get templates Data",
    response_model=TemplateDescResponse,
)
async def get_templates_data(
    request: Request,
    tid: str = Path(title="Template id"),
    version_id: Optional[str] = Query(
        None, title="Template version id", alias="versionId"
    ),
    client: BackendBase = Depends(get_meth_cli),
):
    """Get templates List."""
    template = await client.get_template(tid, version_id)
    if not template:
        raise TemplageNotFoundError("template not found")

    return TemplateDescResponse(
        code=HTTP_200_OK,
        error="ok",
        data=TemplateDescData(
            **{
                **template.dict(),
                "report": template.report,
                "template_designer_page": str(
                    request.url_for("Templates Designer page", tid=template.tid)
                ),
            }
        ),
    )


@router.put(
    "/templates",
    tags=TAGS,
    name="Create Templates",
    response_model=TemplateDataResponse,
)
async def create_templates(
    request: Request,
    req: RequestCreateTemplate,
    client: BackendBase = Depends(get_meth_cli),
):
    """Templates Manage page."""
    try:
        rrr = await client.put_template(req.template_name, req.template_type, {})
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=req.template_name,
                template_type=req.template_type,
                tid=rrr.tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including the duplicate template name error)
        raise ex


@router.put(
    "/templates/{tid}",
    tags=TAGS,
    name="Create Templates, use own tid",
    response_model=TemplateDataResponse,
)
async def create_templates_tid(
    request: Request,
    req: RequestCreateTemplate,
    tid: str = Path(title="Template id"),
    client: BackendBase = Depends(get_meth_cli),
):
    """Templates Manage page."""
    try:
        rrr = await client.put_template(req.template_name, req.template_type, {}, tid=tid)
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=req.template_name,
                template_type=req.template_type,
                tid=rrr.tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including the duplicate template name error)
        raise ex


@router.post(
    "/templates/import",
    tags=TAGS,
    name="Import Template",
    response_model=TemplateDataResponse,
)
async def import_template(
    request: Request,
    req: RequestImportTemplate,
    client: BackendBase = Depends(get_meth_cli),
):
    """Import Template from JSON data."""
    if not req.template_data:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="template_data is empty",
        )

    # Validate that the template_data has the required structure
    required_keys = ["docElements", "parameters", "documentProperties"]
    if not all(key in req.template_data for key in required_keys):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"template_data must contain: {', '.join(required_keys)}",
        )

    # Create the report structure from the imported data
    report_data = {
        "docElements": req.template_data.get("docElements", []),
        "parameters": req.template_data.get("parameters", []),
        "styles": req.template_data.get("styles", []),
        "watermarks": req.template_data.get("watermarks", []),
        "version": req.template_data.get("version", 5),
        "documentProperties": req.template_data.get("documentProperties", {})
    }

    try:
        # Create new template with imported data
        if req.tid:
            # Import with specific tid
            rrr = await client.put_template(
                tid=req.tid,
                template_name=req.template_name,
                template_type=req.template_type,
                report=report_data,
            )
        else:
            # Import with auto-generated tid
            rrr = await client.put_template(
                template_name=req.template_name,
                template_type=req.template_type,
                report=report_data,
            )
        
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=req.template_name,
                template_type=req.template_type,
                tid=rrr.tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including duplicate template name error)
        raise ex


@router.post(
    "/templates/{tid}",
    tags=TAGS,
    name="Save Templates",
    response_model=TemplateDataResponse,
)
async def save_templates(
    request: Request,
    req: RequestUploadTemplate,
    tid: str = Path(title="Template id"),
    client: BackendBase = Depends(get_meth_cli),
):
    """Save Templates with optional metadata update."""
    if not req.report:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="report is empty",
        )

    obj = await client.get_template(tid)
    if not obj:
        raise TemplageNotFoundError("template not found")

    # Use provided template_name and template_type if available, otherwise keep existing values
    template_name = req.template_name if req.template_name else obj.template_name
    template_type = req.template_type if req.template_type else obj.template_type
    skip_name_check = False
    if not req.template_name:
        skip_name_check = True

    try:
        rrr = await client.put_template(
            tid=tid,
            template_name=template_name,
            template_type=template_type,
            report=req.report,
            skip_name_check=skip_name_check,  # Skip name check to allow updates
        )
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=template_name,
                template_type=template_type,
                tid=tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including the duplicate template name error)
        raise ex


@router.post(
    "/templates/{tid}/clone",
    tags=TAGS,
    name="Clone Templates",
    response_model=TemplateDataResponse,
)
async def clone_templates(
    request: Request,
    req: RequestCloneTemplate,
    tid: str = Path(title="Template id"),
    client: BackendBase = Depends(get_meth_cli),
):
    """Clone Templates."""
    obj = await client.get_template(req.from_tid, req.from_version_id)
    if not obj:
        raise TemplageNotFoundError("template not found")

    if not req.from_version_id:
        req.from_version_id = obj.version_id

    if tid == req.from_tid and obj.version_id == req.from_version_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="tid, from_tid must not same",
        )

    obj_src = await client.get_template(tid)
    if not obj_src:
        raise TemplageNotFoundError("template not found")

    try:
        rrr = await client.put_template(
            tid=tid,
            template_name=obj_src.template_name,
            template_type=obj_src.template_type,
            report=obj.report,
        )
        return TemplateDataResponse(
            code=HTTP_200_OK,
            error="ok",
            data=TemplateListData(
                updated_at=datetime.now(),
                template_name=obj_src.template_name,
                template_type=obj_src.template_type,
                tid=tid,
                version_id=rrr.version_id,
                template_designer_page=str(
                    request.url_for("Templates Designer page", tid=rrr.tid)
                ),
            ),
        )
    except HTTPException as ex:
        # Re-raise HTTPExceptions (including the duplicate template name error)
        raise ex 
    

@router.delete(
    "/templates/{tid}",
    tags=TAGS,
    name="Delete Templates",
    response_model=ErrorResponse,
)
async def delete_templates(
    tid: str = Path(title="Template id"),
    version_id: Optional[str] = Query(
        None, title="Template version id", alias="versionId"
    ),
    client: BackendBase = Depends(get_meth_cli),
):
    """Delete Templates."""
    await client.delete_template(tid, version_id)
    return ErrorResponse(code=HTTP_200_OK, error="ok")


# ----------------------------------------------
#        Template Export/Import
# ----------------------------------------------


@router.post(
    "/templates/{tid}/export",
    tags=TAGS,
    name="Export Template",
)
async def export_template(
    tid: str = Path(title="Template id"),
    version_id: Optional[str] = Query(
        None, title="Template version id", alias="versionId"
    ),
    client: BackendBase = Depends(get_meth_cli),
):
    """Export Template as JSON data."""
    template = await client.get_template(tid, version_id)
    if not template:
        raise TemplageNotFoundError("template not found")

    # Create export data structure
    export_data = {
        "docElements": template.report.get("docElements", []),
        "parameters": template.report.get("parameters", []),
        "styles": template.report.get("styles", []),
        "watermarks": template.report.get("watermarks", []),
        "version": template.report.get("version", 5),
        "documentProperties": template.report.get("documentProperties", {})
    }
    
    # Return JSON directly
    return export_data


# ----------------------------------------------
#        PDF REPORT Generate
# ----------------------------------------------


def gen_file_from_report(
    output_format, report_definition, data, is_test_data, disabled_fill
) -> Tuple[str, bytes]:
    """Review Templates Generate."""
    # all data needed for report preview is sent in the initial PUT request, it contains
    # the format (pdf or xlsx), the report itself (report_definition), the data (test data
    # defined within parameters in the Designer) and is_test_data flag (always True
    # when request is sent from Designer)
    if output_format not in ("pdf", "xlsx"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="outputFormat parameter missing or invalid",
        )

    try:
        if not disabled_fill:
            fill_default(report_definition, data)
        
        # Process imageUrl fields and copy them to source field for external image support
        process_image_urls(report_definition, data)

        report = ReportPdf(report_definition, data, FONTS_LOADER, is_test_data)
    except ReportBroError as ex:
        LOGGER.warning(
            "failed to initialize report: %s %s", str(ex), traceback.format_exc()
        )
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"failed to initialize report[{ex}]",
        ) from ex

    if report.report.errors:
        # return list of errors in case report contains errors, e.g. duplicate parameters.
        # with this information ReportBro Designer can select object containing errors,
        # highlight erroneous fields and display error messages
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=json.dumps(report.report.errors),
        )

    start = timer()
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        if output_format == "pdf":
            report_file = report.generate_pdf(title=settings.PDF_TITLE)
            filename = "report-" + str(now) + ".pdf"
            assert isinstance(report_file, bytearray)
            return filename, bytes(report_file)
        else:
            report_file = report.generate_xlsx()
            filename = "report-" + str(now) + ".xlsx"
            assert isinstance(report_file, bytearray)
            return filename, bytes(report_file)
    except ReportBroError as ex:
        # in case an error occurs during report report generate
        # a ReportBroError exception is thrown
        # to stop processing. We return this error within a list so the error can be
        # processed by ReportBro Designer.
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"failed to generate report[{ex}]",
        ) from ex
    finally:
        end = timer()
        LOGGER.info("pdf generated in %.3f seconds", (end - start))


async def read_file_in_s3(output_format, key, client: StorageMange):
    """Read file in s3."""
    if output_format not in ("pdf", "xlsx"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="outputFormat parameter missing or invalid",
        )

    filename, report_file = await client.get_file(key)

    if output_format == "pdf":
        response = StreamingResponse(
            BytesIO(report_file),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    else:
        response = StreamingResponse(
            BytesIO(report_file),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    return response


@router.put(
    "/templates/review/generate",
    tags=GEN_TAGS,
    name="Generate preview file from template",
)
async def review_templates_gen(
    req: RequestReviewTemplate,
    background_tasks: BackgroundTasks,
    disabled_fill: bool = Query(
        default=False, title="Disable fill empty fields for input data"
    ),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates Generate."""
    filename, report_file = gen_file_from_report(
        req.output_format, req.report, req.data, req.is_test_data, disabled_fill
    )
    assert report_file
    key = await storage.put_file(filename, report_file, background_tasks)
    return PlainTextResponse(key)


@router.get(
    "/templates/review/generate",
    tags=GEN_TAGS,
    name="Get generate preview file",
)
async def review_templates(
    output_format: str = Query(
        "pdf", title="Output Format(pdf|xlsx)", pattern=r"^(pdf|xlsx)$"
    ),
    key: str = Query(title="File Key", min_length=16),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates."""
    r = await read_file_in_s3(output_format, key, storage)
    return r


@router.put(
    "/templates/review/generate/download",
    tags=GEN_TAGS,
    name="Generate preview file from template and Get generate preview file",
    response_model=TemplateDownLoadResponse,
)
async def review_templates_gen_download(
    request: Request,
    req: RequestReviewTemplate,
    background_tasks: BackgroundTasks,
    disabled_fill: bool = Query(
        default=False, title="Disable fill empty fields for input data"
    ),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates Generate."""
    filename, report_file = gen_file_from_report(
        req.output_format, req.report, req.data, req.is_test_data, disabled_fill
    )
    assert report_file
    download_key = await storage.put_file(filename, report_file, background_tasks)
    return TemplateDownLoadResponse(
        code=HTTP_200_OK,
        error="ok",
        data=TemplateDownLoadData(
            download_key=download_key,
            download_url=str(
                request.url_for("Get generate file from multiple template")
            )
            + "?"
            + urlencode(
                {
                    "key": download_key,
                }
            ),
        ),
    )


# ----------------------------------------------
#        PDF REPORT Multiple Generate
# ----------------------------------------------


def generate_pdf_mutil(
    output_format: str,
    disabled_fill: bool,
    req: Union[
        PdfData,
        RequestGenerateReviewTemplate,
    ],
):
    """Review Templates Generate."""
    try:
        if isinstance(req, PdfData):
            return req

        elif isinstance(req, RequestGenerateReviewTemplate):
            filename, report_file = gen_file_from_report(
                output_format,
                req.report,
                req.data,
                False,
                disabled_fill,
            )
            return PdfData(filename=filename, report_file=report_file)

        else:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="templates is invaild",
            )
    except HTTPException as ex:
        return ex.detail

    except Exception as ex:
        # return Exception
        return str(ex)


async def download_pdf(pdf_url):
    """Download PDF."""
    if pdf_url.startswith("file://"):
        with open(pdf_url[7:], "rb") as fss:
            data = fss.read()
        filename, report_file = os.path.basename(pdf_url), data
    else:
        timeout = ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(pdf_url) as resp:
                assert resp.status == 200
                data = await resp.read()
                filename, report_file = os.path.basename(pdf_url), data

    if not is_pdf(report_file):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="pdf_url is not pdf file",
        )

    return PdfData(filename=filename, report_file=report_file)


async def download_template(pdf_url):
    """Download Template."""
    timeout = ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(pdf_url) as resp:
            assert resp.status == 200
            data = await resp.json()
            return data


@router.put(
    "/templates/multi/generate",
    tags=GEN_TAGS,
    name="Generate file from multiple template(PDF Only)",
    response_model=TemplateDownLoadResponse,
)
async def generate_templates_multi_gen(
    request: Request,
    req: RequestMultiGenerateTemplate,
    background_tasks: BackgroundTasks,
    disabled_fill: bool = Query(
        default=False, title="Disable fill empty fields for input data"
    ),
    client: BackendBase = Depends(get_meth_cli),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates Generate."""
    if not req.templates:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="templates is empty",
        )

    templates = []

    # check request templates
    for i in req.templates:
        if isinstance(i, RequestGenerateUrlTemplate):
            report_data = await download_pdf(i.pdf_url)
            templates.append(report_data)

        elif isinstance(i, RequestGenerateTUrlTemplate):
            templage = await download_template(i.report_url)
            if not templage:
                raise TemplageNotFoundError("template not found")

            templates.append(
                RequestGenerateReviewTemplate(report=templage, data=i.data)
            )

        elif isinstance(i, RequestGenerateDataTemplate):
            templage = await client.get_template(i.tid, i.version_id)
            if not templage:
                raise TemplageNotFoundError("template not found")

            templates.append(
                RequestGenerateReviewTemplate(report=templage.report, data=i.data)
            )

        elif isinstance(i, RequestGenerateReviewTemplate):
            templates.append(i)

        else:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="templates is invaild",
            )
    filename = ""
    merge_file = PyPDF2.PdfFileMerger()
    generate_pdf_mutil_ = partial(generate_pdf_mutil, req.output_format, disabled_fill)
    pools: ProcessPoolExecutor = request.app.state.executor
    if pools:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(pools, generate_pdf_mutil_, i) for i in templates
        ]
        results = await asyncio.gather(*futures)
        for data in results:
            if isinstance(data, str):
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail=data,
                )

            filename = data.filename
            merge_file.append(
                PyPDF2.PdfFileReader(stream=BytesIO(initial_bytes=data.report_file))
            )
    else:
        for template in templates:
            filename = data.filename
            data = generate_pdf_mutil_(template)
            merge_file.append(
                PyPDF2.PdfFileReader(stream=BytesIO(initial_bytes=data.report_file))
            )

    rrr = BytesIO()
    merge_file.write(rrr)
    rrr.seek(0)

    download_key = await storage.put_file(filename, rrr.read(), background_tasks)
    return TemplateDownLoadResponse(
        code=HTTP_200_OK,
        error="ok",
        data=TemplateDownLoadData(
            download_key=download_key,
            download_url=str(
                request.url_for("Get generate file from multiple template")
            )
            + "?"
            + urlencode(
                {
                    "key": download_key,
                }
            ),
        ),
    )


@router.get(
    "/templates/multi/generate",
    tags=GEN_TAGS,
    name="Get generate file from multiple template",
)
async def generate_templates_multi(
    key: str = Query(title="File Key", min_length=16),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates."""
    r = await read_file_in_s3("pdf", key, storage)
    return r


# ----------------------------------------------
#        PDF REPORT Generate
# ----------------------------------------------


@router.put(
    "/templates/{tid}/generate",
    tags=GEN_TAGS,
    name="Generate file from template",
    response_model=TemplateDownLoadResponse,
)
async def generate_templates_gen(
    request: Request,
    req: RequestGenerateTemplate,
    background_tasks: BackgroundTasks,
    tid: str = Path(title="Template id"),
    version_id: Optional[str] = Query(
        None, title="Template version id", alias="versionId"
    ),
    disabled_fill: bool = Query(
        default=False, title="Disable fill empty fields for input data"
    ),
    client: BackendBase = Depends(get_meth_cli),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates Generate."""
    templage = await client.get_template(tid, version_id)
    if not templage:
        raise TemplageNotFoundError("template not found")

    filename, report_file = gen_file_from_report(
        req.output_format, templage.report, req.data, False, disabled_fill
    )
    assert report_file
    download_key = await storage.put_file(filename, report_file, background_tasks)
    return TemplateDownLoadResponse(
        code=HTTP_200_OK,
        error="ok",
        data=TemplateDownLoadData(
            download_key=download_key,
            download_url=str(request.url_for("Get generate file", tid=tid))
            + "?"
            + urlencode(
                {
                    "key": download_key,
                }
            ),
        ),
    )


@router.get(
    "/templates/{tid}/generate",
    tags=GEN_TAGS,
    name="Get generate file",
)
async def generate_templates(
    output_format: str = Query(
        "pdf", title="Output Format(pdf|xlsx)", pattern=r"^(pdf|xlsx)$"
    ),
    key: str = Query(title="File Key", min_length=16),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Review Templates."""
    r = await read_file_in_s3(output_format, key, storage)
    return r


@router.put(
    "/templates/name/{template_name}/generate",
    tags=GEN_TAGS,
    name="Generate file from template by name",
    response_model=TemplateDownLoadResponse,
)
async def generate_templates_by_name_gen(
    request: Request,
    req: RequestGenerateTemplate,
    background_tasks: BackgroundTasks,
    template_name: str = Path(title="Template name"),
    version_id: Optional[str] = Query(
        None, title="Template version id", alias="versionId"
    ),
    disabled_fill: bool = Query(
        default=False, title="Disable fill empty fields for input data"
    ),
    client: BackendBase = Depends(get_meth_cli),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Generate template file by template name."""
    LOGGER.info(f"Looking for template with name: '{template_name}'")
    
    # Get all templates and find by name (case-insensitive)
    templates_list = await client.get_templates_list(limit=settings.PAGE_LIMIT)
    
    # Log the found templates for debugging
    LOGGER.info(f"Found {len(templates_list)} templates in total")
    for t in templates_list:
        LOGGER.info(f"Template: {t.template_name} (ID: {t.tid})")
    
    # Find template by name (case-insensitive)
    matching_templates = [t for t in templates_list if t.template_name.lower() == template_name.lower()]
    
    if not matching_templates:
        # Try to find template with partial match
        matching_templates = [t for t in templates_list if template_name.lower() in t.template_name.lower()]
    
    if not matching_templates:
        LOGGER.error(f"Template not found: {template_name}")
        raise TemplageNotFoundError(f"template not found: {template_name}")
    
    # Get the template ID from the first matching template
    template_info = matching_templates[0]
    tid = template_info.tid
    LOGGER.info(f"Using template: {template_info.template_name} (ID: {tid})")
    
    # Get the full template with report data
    templage = await client.get_template(tid, version_id)
    if not templage:
        raise TemplageNotFoundError("template not found")

    filename, report_file = gen_file_from_report(
        req.output_format, templage.report, req.data, False, disabled_fill
    )
    assert report_file
    download_key = await storage.put_file(filename, report_file, background_tasks)
    return TemplateDownLoadResponse(
        code=HTTP_200_OK,
        error="ok",
        data=TemplateDownLoadData(
            download_key=download_key,
            download_url=str(request.url_for("Get generate file by name", template_name=template_name))
            + "?"
            + urlencode(
                {
                    "key": download_key,
                }
            ),
        ),
    )


@router.get(
    "/templates/name/{template_name}/generate",
    tags=GEN_TAGS,
    name="Get generate file by name",
)
async def generate_templates_by_name(
    output_format: str = Query(
        "pdf", title="Output Format(pdf|xlsx)", pattern=r"^(pdf|xlsx)$"
    ),
    key: str = Query(title="File Key", min_length=16),
    storage: StorageMange = Depends(get_storage_mange),
):
    """Get generated file by template name."""
    r = await read_file_in_s3(output_format, key, storage)
    return r
