# -*- coding: utf-8 -*-
"""
@create: 2022-07-25 10:39:05.

@author: ppolxda

@desc: page_view
"""

import json
import token
import httpx
from enum import Enum
from gettext import NullTranslations
from typing import Any, List
from typing import Optional
from typing import Union

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from reportbro_designer_api.settings import settings

from ..backend.backends.base import BackendBase
from ..clients import FONTS_LOADER
from ..clients import get_meth_cli
from ..clients import get_default_report_cli
from ..errors import TemplageNotFoundError

router = APIRouter()
TAGS: List[Union[str, Enum]] = ["Static Page"]
templates = Jinja2Templates(
    directory=settings.TEMPLATES_PATH, extensions=["jinja2.ext.i18n"]
)

translation = NullTranslations()
templates.env.install_gettext_translations(translation)  # pylint: disable=no-member


@router.get("/templates", tags=TAGS, name="Templates Manage page")
async def templates_index_page():
    """Templates Manage page."""
    return RedirectResponse("/templates")

@router.get("/designer/{tid}", tags=TAGS, name="Templates Designer page")
async def templates_designer_page(
    request: Request,
    tid: str = Path(title="Template id"),
    version_id: Optional[str] = Query(None, title="Template version id"),
    menu_show_debug: bool = Query(True, title="Show Menu Debug", alias="menuShowDebug"),
    menu_sidebar: bool = Query(False, title="Show Menu Sidebar", alias="menuSidebar"),
    locale: str = Query(
        settings.PDF_LOCALE,
        title="Show Menu Language(zh_cn|de_de|en_us)",
        alias="locale",
        pattern=r"^(zh_cn|de_de|en_us)$",
    ),
    client: BackendBase = Depends(get_meth_cli),
):
    """Templates Designer page."""
    obj = await client.get_template(tid, version_id)
    if not obj:
        raise TemplageNotFoundError("template not found")

    version_id = obj.version_id
    return templates.TemplateResponse(
        "designer.html.jinja2",
        {
            "request": request,
            "tid": tid,
            "version_id": version_id,
            "report": json.dumps(obj.report, indent=2),
            "fonts": FONTS_LOADER.fonts_jinja,
            "default_font": settings.PDF_DEFAULT_FONT,
            "menu_sidebar": menu_sidebar,
            "menu_show_debug": menu_show_debug,
            "locale": locale,
        },
    )
@router.get("/designer", tags=TAGS, name="Templates Designer page")
async def templates_designer_page_no_tid(
    request: Request,
    url: str = Query(None, title="API URL", description="The URL of the API to fetch the template"),
    token: str = Query(None, title="API Token"),
    menu_show_debug: bool = Query(True, title="Show Menu Debug", alias="menuShowDebug"),
    menu_sidebar: bool = Query(False, title="Show Menu Sidebar", alias="menuSidebar"),
    locale: str = Query(
        settings.PDF_LOCALE,
        title="Show Menu Language(zh_cn|de_de|en_us)",
        alias="locale",
        pattern=r"^(zh_cn|de_de|en_us)$",
    ),
):
    # """Templates Designer page."""
    if url and token:
        # 🔐 Call external API with token
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(url, headers=headers)
                response.raise_for_status()
                res = json.loads(response.content)
                dataR = res.get("Data", {}).get("report", {})
            except httpx.HTTPError as e:
                print(f"[designer] Error fetching template via token: {e}")
                dataR = {}
    else:
        # Load default template
        dataR = get_default_report_cli()
        if not dataR:
            raise TemplageNotFoundError("default template not found")
    return templates.TemplateResponse(
        "designer.html.jinja2",
        {
            "request": request,
            "tid": 'test',
            "version_id": 'default',
            "report": json.dumps(dataR),
            "is_default": True,
            "fonts": FONTS_LOADER.fonts_jinja,
            "default_font": settings.PDF_DEFAULT_FONT,
            "menu_sidebar": menu_sidebar,
            "menu_show_debug": menu_show_debug,
            "locale": locale,
        },
    )