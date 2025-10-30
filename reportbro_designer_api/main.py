 
# -*- coding: utf-8 -*-
"""
@create: 2022-07-22 17:42:41.

@author: ppolxda

@desc: web main
"""
import os
import re
import traceback
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager

from botocore.exceptions import ClientError
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

try:
    from reportbro.errors import ReportBroInternalError, ReportBroError as ReportBroLibError
except ImportError:
    # Fallback if reportbro is not available
    ReportBroInternalError = Exception
    ReportBroLibError = Exception

from .errors import ReportbroError
from .router import router
from .settings import settings
from .utils.logger import LOGGER
from .utils.model import ErrorResponse
from .utils.static_files import UiStaticFiles
from .version import __VERSION__


class TrustProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to handle proxy headers for HTTPS detection."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle the request and modify scheme if HTTPS proxy headers are present."""
        # Check for HTTPS from proxy headers first
        is_https = (
            request.headers.get("x-forwarded-proto") == "https" or
            request.headers.get("x-forwarded-protocol") == "https" or
            request.headers.get("x-forwarded-ssl") == "on"
        )
        
        # If FORCE_HTTPS is enabled, always use HTTPS
        if settings.FORCE_HTTPS:
            is_https = True
        
        # If proxy headers don't indicate HTTPS, check if request came via standard HTTPS port
        # or if the host matches configured HTTPS domains
        if not is_https:
            host = request.headers.get("host", "")
            # Check if host matches any configured HTTPS domains
            for https_domain in settings.HTTPS_DOMAINS:
                if https_domain.strip() and https_domain.strip() in host:
                    is_https = True
                    break
            # Also check for standard HTTPS port
            if not is_https and request.headers.get("x-forwarded-port") == "443":
                is_https = True
        
        if is_https:
            # Modify the request scope to indicate HTTPS
            request.scope["scheme"] = "https"
            # Also update the server info to reflect HTTPS
            if request.scope.get("server"):
                host, port = request.scope["server"]
                # Use standard HTTPS port if it was HTTP port
                if port == 80:
                    port = 443
                request.scope["server"] = (host, port)
        
        response = await call_next(request)
        return response


def get_app() -> FastAPI:
    # ...existing code...

    # ...existing code...

    """Fastapi app."""

    def print_var():
        # await database.connect()
        LOGGER.info("--------------------------------------")
        for i in rapp.router.routes:
            if not hasattr(i, "methods"):
                continue

            LOGGER.info(f'[{str(",".join(i.methods)):15s}]: {i.name:30s}: {i.path}')  # type: ignore

        # LOGGER.info("--------------------------------------")
        LOGGER.info("\n".join(settings.format_print()))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print_var()
        app.state.executor = (
            ProcessPoolExecutor(settings.PROCESS_POOL_SIZE)
            if settings.PROCESS_POOL_SIZE > 0
            else None
        )

        yield

        LOGGER.info("service shutdown")

        if app.state.executor:
            app.state.executor.shutdown()

    rapp = FastAPI(
        title="Reportbro designer server",
        description="Reportbro designer server",
        version=__VERSION__,
        openapi_prefix=settings.ROOT_PATH,
        openapi_url="/openapi.json" if settings.SHOW_DOC else None,
        docs_url="/docs" if settings.SHOW_DOC else None,
        redoc_url="/redoc" if settings.SHOW_DOC else None,
        root_path=settings.ROOT_PATH,
        root_path_in_servers=settings.ROOT_PATH_IN_SERVERS,
        debug=settings.IS_DEBUG,
        lifespan=lifespan,
        servers=[
            {
                "url": settings.ROOT_PATH if settings.ROOT_PATH else "/",
                "description": "localhost",
            },
        ],
    )
    
    # Configure FastAPI to trust proxy headers for HTTPS detection
    if settings.TRUST_PROXY_HEADERS:
        rapp.add_middleware(TrustProxyHeadersMiddleware)
    
    # Add CORS middleware to allow cross-origin requests
    rapp.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,  # Use the configured origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    
    # Create a separate router for company-specific UI routes
    company_ui_router = APIRouter()
    
    @company_ui_router.get("", name="Default UI Index")
    async def default_ui_index(
        request: Request,
    ):
        """Serve default UI index page (legacy route without company)."""
        import os
        
        index_path = os.path.join(settings.STATIC_PATH, "ui", "index.html")
        
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Get the scheme and host for absolute URLs
            scheme = request.url.scheme
            host = request.headers.get("host", "localhost")
            base_url = f"{scheme}://{host}"
            
            # Replace relative asset paths for legacy route
            content = content.replace('href="./assets/', f'href="{base_url}/ui/assets/')
            content = content.replace('src="./assets/', f'src="{base_url}/ui/assets/')
            
            return HTMLResponse(content=content)
            
        except Exception as e:
            raise HTTPException(status_code=404, detail="UI not found")
    
    @company_ui_router.get("/{company}", name="Company UI Index")
    async def company_ui_index(
        request: Request,
        company: str,
    ):
        """Serve company-specific UI index page."""
        # Read and modify the index.html manually to update asset paths
        import os
        
        index_path = os.path.join(settings.STATIC_PATH, "ui", "index.html")
        
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Get the scheme and host for absolute URLs
            scheme = request.url.scheme
            host = request.headers.get("host", "localhost")
            base_url = f"{scheme}://{host}"
            
            # Replace relative asset paths to point to company-specific routes
            # Replace ./assets/ with absolute paths
            content = content.replace('href="./assets/', f'href="{base_url}/ui/{company}/assets/')
            content = content.replace('src="./assets/', f'src="{base_url}/ui/{company}/assets/')
            # Also replace /ui/ patterns
            content = content.replace('href="/ui/', f'href="{base_url}/ui/{company}/')
            content = content.replace('src="/ui/', f'src="{base_url}/ui/{company}/')
            
            return HTMLResponse(content=content)
            
        except Exception as e:
            raise HTTPException(status_code=404, detail="UI not found")
    
    @company_ui_router.get("/{company}/assets/{filename}", name="Company UI Assets")
    async def company_ui_assets(
        request: Request,
        company: str,
        filename: str,
    ):
        """Serve company-specific UI assets with modified API paths."""
        # Create a UiStaticFiles instance
        ui_static = UiStaticFiles(
            directory=os.path.join(settings.STATIC_PATH, "ui"),
            html=True
        )
        
        # Create a modified scope that includes company context
        scope = dict(request.scope)
        scope["company"] = company
        scope["app_root_path"] = f"/{company}"  # This replaces path:"/api" with path:"/{company}", so frontend builds /api/{company}/...
        scope["root_path"] = f"/ui/{company}"  # This will be used for UI paths
        
        asset_path = f"assets/{filename}"
        
        try:
            response = await ui_static.get_response(asset_path, scope)
            return response
        except Exception as e:
            # If asset not found, return 404
            raise HTTPException(status_code=404, detail="Asset not found")
    
    # Include company UI router before mounting static files
    rapp.include_router(company_ui_router, prefix="/ui")
    
    # Mount static files for default UI assets (without company prefix)
    # This needs to be before /ui/{company} to avoid conflicts
    rapp.mount(
        "/ui/assets",
        StaticFiles(directory=os.path.join(settings.STATIC_PATH, "ui", "assets")),
        name="UiAssets",
    )
    rapp.mount("/static", StaticFiles(directory=settings.STATIC_PATH), name="static")
    rapp.include_router(router)

    # Test endpoint for HTTPS proxy detection
    @rapp.get("/test-https-detection")
    async def test_https_detection(request: Request):
        """Test endpoint to verify HTTPS proxy header detection."""
        # Get all headers for debugging
        all_headers = {k: v for k, v in request.headers.items()}
        
        return {
            "request_url": str(request.url),
            "request_scheme": request.url.scheme,
            "base_url": str(request.base_url),
            "trust_proxy_headers": settings.TRUST_PROXY_HEADERS,
            "static_url": str(request.url_for("static", path="css/base.css")),
            "scope_scheme": request.scope.get("scheme", "not_set"),
            "all_headers": all_headers,
            "relevant_headers": {
                "x-forwarded-proto": request.headers.get("x-forwarded-proto"),
                "x-forwarded-protocol": request.headers.get("x-forwarded-protocol"),
                "x-forwarded-ssl": request.headers.get("x-forwarded-ssl"),
                "host": request.headers.get("host"),
            }
        }

    @rapp.exception_handler(ReportbroError)
    async def report_exception_handler(request: Request, exc: ReportbroError):
        assert request
        LOGGER.warning("report_error[%s]", exc)
        return JSONResponse(
            ErrorResponse(code=HTTP_503_SERVICE_UNAVAILABLE, error=str(exc)).dict(),
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
        )

    @rapp.exception_handler(ReportBroInternalError)
    async def reportbro_internal_error_handler(request: Request, exc):
        assert request
        LOGGER.warning("reportbro_internal_error[%s]", exc)
        return JSONResponse(
            ErrorResponse(code=HTTP_400_BAD_REQUEST, error=str(exc)).dict(),
            status_code=HTTP_400_BAD_REQUEST,
        )

    @rapp.exception_handler(ReportBroLibError)
    async def reportbro_lib_error_handler(request: Request, exc):
        assert request
        LOGGER.warning("reportbro_lib_error[%s]", exc)
        return JSONResponse(
            ErrorResponse(code=HTTP_400_BAD_REQUEST, error=str(exc)).dict(),
            status_code=HTTP_400_BAD_REQUEST,
        )

    @rapp.exception_handler(ClientError)
    async def s3_exception_handler(request: Request, exc: ClientError):
        assert request
        if exc.response.get("Error", {}).get("Code", "") == "NoSuchKey":
            return JSONResponse(
                ErrorResponse(code=HTTP_404_NOT_FOUND, error="NoSuchKey").dict(),
                status_code=HTTP_404_NOT_FOUND,
            )
        else:
            LOGGER.warning("s3_error[%s][%s]", exc, traceback.format_exc())
            return JSONResponse(
                ErrorResponse(
                    code=HTTP_503_SERVICE_UNAVAILABLE, error="NoSuchKey"
                ).dict(),
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
            )

    @rapp.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        assert request
        LOGGER.warning("http_error[%s]", exc.detail)
        return JSONResponse(
            ErrorResponse(code=exc.status_code, error=exc.detail).dict(),
            status_code=exc.status_code,
        )

    @rapp.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        assert request
        LOGGER.error("unknow_error[%s]%s", exc, traceback.format_exc())
        # Return the actual error message instead of generic "unknown error"
        error_message = str(exc) if str(exc) else "unknown error"
        return JSONResponse(
            ErrorResponse(
                code=HTTP_500_INTERNAL_SERVER_ERROR, error=error_message
            ).dict(),
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return rapp






app = get_app()

# Serve /ui by rendering index.html with company set to 'default'
@app.get("/ui", name="Root UI", include_in_schema=False)
async def root_ui_index(request):
    static_path = os.path.join(settings.STATIC_PATH, "ui", "index.html")
    if not os.path.exists(static_path):
        raise HTTPException(status_code=404, detail="UI not found")
    with open(static_path, "r", encoding="utf-8") as f:
        content = f.read()
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", "localhost")
    base_url = f"{scheme}://{host}"
    # Rewrite asset paths for JS/CSS
    content = re.sub(r'href="/ui/(assets/.*?\.css)"', f'href="{base_url}/ui/assets/\\1"', content)
    content = re.sub(r'src="/ui/(assets/.*?\.js)"', f'src="{base_url}/ui/assets/\\1"', content)
    # Rewrite API path in JS to use /default
    content = content.replace('path:"/api', 'path:"/default/api')
    return HTMLResponse(content=content)

# Catch-all route for SPA routing (must be after assets and favicon routes)


# Serve /ui/vite.svg favicon at module level


@app.get("/ui/vite.svg", include_in_schema=False)
async def ui_favicon():
    favicon_path = os.path.join(settings.STATIC_PATH, "ui", "vite.svg")
    if not os.path.exists(favicon_path):
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(favicon_path, media_type="image/svg+xml")
