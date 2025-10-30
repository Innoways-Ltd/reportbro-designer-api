# -*- coding: utf-8 -*-
"""
@create: 2023-10-20 16:12:12.

@author: ppolxda

@desc: main_page_view
"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from ..dependencies import get_company_context

router = APIRouter()


@router.get("/", name="Main page")
async def main_index_page():
    """Web main page."""
    return RedirectResponse("/ui")


# Company-specific main page redirects
@router.get("/{company}", name="Company Main page")
async def company_main_index_page(company: str = Depends(get_company_context)):
    """Company-specific web main page."""
    return RedirectResponse(f"/ui/{company}")


@router.get("/{company}/", name="Company Main page with slash")
async def company_main_index_page_slash(company: str = Depends(get_company_context)):
    """Company-specific web main page with trailing slash."""
    return RedirectResponse(f"/ui/{company}")
