# -*- coding: utf-8 -*-
"""
@create: 2024-10-29

@author: GitHub Copilot

@desc: FastAPI Dependencies for multi-tenant support
"""
from typing import Optional
from fastapi import Path, HTTPException, Request, Depends
from starlette.status import HTTP_400_BAD_REQUEST

from .backend.backends.base import BackendBase
from .clients import create_s3_backend, create_db_backend
from .settings import settings
from .storage import StorageMange, S3Storage, LocalStorage
from .clients import create_s3_client


async def get_company_context_from_path(
    company: str = Path(description="Company code for tenant isolation")
) -> str:
    """
    Extract company context from URL path parameter.
    
    Args:
        company: Company code from URL path
        
    Returns:
        str: Company code to use for tenant isolation
        
    Raises:
        HTTPException: If company code is invalid
    """
    # Validate company code format (alphanumeric + some special chars)
    if not company or len(company) > 50:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid company code. Must be 1-50 characters."
        )
    
    # Basic validation - only allow alphanumeric, hyphens, and underscores
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in company):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid company code. Only alphanumeric characters, hyphens, and underscores are allowed."
        )
    
    return company


async def get_company_context_default() -> str:
    """
    Get default company context for legacy endpoints.
    
    Returns:
        str: Default company code
    """
    return "default"


async def get_company_context(request: Request) -> str:
    """
    Extract company context from request path.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Company code or 'default' if not in path
    """
    path_params = request.path_params
    company = path_params.get('company')
    
    if company is None:
        return "default"
    
    # Validate company code format (alphanumeric + some special chars)
    if not company or len(company) > 50:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid company code. Must be 1-50 characters."
        )
    
    # Basic validation - only allow alphanumeric, hyphens, and underscores
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in company):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid company code. Only alphanumeric characters, hyphens, and underscores are allowed."
        )
    
    return company


def create_company_db_url(base_url: str, company: str) -> str:
    """
    Create a company-specific database URL by modifying the bucket path.
    
    Args:
        base_url: Original DB_URL from settings
        company: Company code for tenant isolation
        
    Returns:
        str: Modified DB_URL with company path
    """
    if not base_url.startswith(("s3://", "ss3://")):
        # For non-S3 backends, return original URL
        return base_url
    
    if company == "default":
        return base_url
    
    # For S3 URLs, we need to keep the bucket name the same
    # and modify the key prefix instead
    # The company isolation will be handled at the key level, not bucket level
    return base_url


async def get_company_backend(
    company: str = Depends(get_company_context)
) -> BackendBase:
    """
    Get a backend client configured for a specific company.
    
    Args:
        company: Company code for tenant isolation (from dependency)
        
    Returns:
        BackendBase: Backend client configured for the company
    """
    # Create backend with company as the project parameter
    # This way the company isolation happens at the key prefix level
    if settings.DB_URL.startswith("s3://") or settings.DB_URL.startswith("ss3://"):
        backend = create_s3_backend(settings.DB_URL)
        # Override the project name to use company code
        backend.project_name = company
        return backend
    else:
        backend = create_db_backend(settings.DB_URL)
        # Override the project name to use company code
        backend.project_name = company
        return backend


async def get_company_storage(
    company: str = Depends(get_company_context)
) -> StorageMange:
    """
    Get a storage manager configured for a specific company.
    
    Args:
        company: Company code for tenant isolation (from dependency)
        
    Returns:
        StorageMange: Storage manager configured for the company
    """
    # Create storage client with original URL
    if settings.STORAGE_URL.startswith("file://"):
        from .clients import create_local_storage
        storage_client = create_local_storage(settings.STORAGE_URL)
    elif settings.STORAGE_URL.startswith(("s3://", "ss3://")):
        s3cli = create_s3_client(settings.STORAGE_URL)
        storage_client = S3Storage(s3cli)
    else:
        raise TypeError("STORAGE_MODE invalid")
    
    return StorageMange(storage_client)