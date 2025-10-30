# -*- coding: utf-8 -*-
"""
@create: 2022-07-22 17:44:59.

@author: ppolxda

@desc: router
"""
from fastapi import APIRouter

from .endpoints.main_view import router as main_router
from .endpoints.page_view import router as view_router
from .endpoints.reportbro_api import router as reportbro_router

router = APIRouter()

# Legacy routes (backward compatibility)
router.include_router(main_router, prefix="")
router.include_router(reportbro_router, prefix="/api")
router.include_router(view_router, prefix="/view")

# Company-specific routes for multi-tenancy
# These routes support URLs like /api/{company}/templates/list
router.include_router(reportbro_router, prefix="/api/{company}")

# Company-specific view routes using a separate instance to avoid conflicts
company_view_router = APIRouter()

# Copy the routes from view_router but for company-specific access
from .endpoints.page_view import templates_designer_page

company_view_router.add_api_route(
    "/designer/{tid}",
    templates_designer_page,
    methods=["GET"],
    name="Company Templates Designer page"
)

router.include_router(company_view_router, prefix="/view/{company}")
