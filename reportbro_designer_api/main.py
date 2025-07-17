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
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from .errors import ReportbroError
from .router import router
from .settings import settings
from .utils.logger import LOGGER
from .utils.model import ErrorResponse
from .version import __VERSION__


class TrustProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to handle proxy headers for HTTPS detection."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle the request and modify scheme if HTTPS proxy headers are present."""
        # Check for HTTPS from proxy headers
        if (request.headers.get("x-forwarded-proto") == "https" or
            request.headers.get("x-forwarded-protocol") == "https" or
            request.headers.get("x-forwarded-ssl") == "on"):
            
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


class UiStaticFiles(StaticFiles):
    """UiStaticFiles."""

    FILE_PATH_REGIX = re.compile(r'(href|src)="\/ui\/(.*?)"')
    FILE_JS_PATH_REGIX = re.compile(r"index-(.*?).js$")
    FILE_JS_API_REGIX = re.compile(r'="/api",')

    async def get_response(self, path: str, scope):
        """get_response."""
        response = await super().get_response(path, scope)
        # if response.status_code == 404:
        #     response = await super().get_response(".", scope)
        # request.url_for(
        if isinstance(response, FileResponse) and isinstance(response.path, str):
            # Check for HTTPS from proxy headers only if proxy headers are trusted
            headers = dict(scope.get("headers", []))
            scheme = "http"
            
            # Check common proxy headers for HTTPS only if trust is enabled
            if settings.TRUST_PROXY_HEADERS and (
                headers.get(b"x-forwarded-proto") == b"https" or
                headers.get(b"x-forwarded-protocol") == b"https" or
                headers.get(b"x-forwarded-ssl") == b"on"
            ):
                scheme = "https"
            
            if len(self.FILE_JS_PATH_REGIX.findall(response.path)) > 0:
                with open(response.path, "r", encoding="utf8") as fs:
                    content = fs.read()

                root_path = scope.get("root_path", "")
                app_root_path = scope.get("app_root_path", scope.get("root_path", ""))
                
                # Ensure the paths use the correct scheme
                if scheme == "https":
                    if root_path and not root_path.startswith("https://"):
                        if root_path.startswith("http://"):
                            root_path = root_path.replace("http://", "https://", 1)
                        elif not root_path.startswith("/"):
                            # If it's a relative path, we don't need to modify it
                            pass
                    
                    if app_root_path and not app_root_path.startswith("https://"):
                        if app_root_path.startswith("http://"):
                            app_root_path = app_root_path.replace("http://", "https://", 1)

                content = content.replace(
                    'path:"/ui",', f'path:"{root_path}",'
                )
                content = self.FILE_JS_API_REGIX.sub(
                    f'="{app_root_path}",', content
                )
                return PlainTextResponse(content=content, media_type="text/javascript")

            if response.path.endswith("index.html"):
                with open(response.path, "r", encoding="utf8") as fs:
                    content = fs.read()

                # Use the same scheme detection as above
                url_ = URL(scope=scope)
                # Manually construct the URL with the correct scheme
                if scheme == "https" and url_.scheme == "http":
                    url_str = str(url_).replace("http://", "https://", 1)
                    url_ = URL(url_str)
                
                content = self.FILE_PATH_REGIX.sub(f'\\1="{url_}\\2"', content)
                return HTMLResponse(content=content)
        return response


def get_app() -> FastAPI:
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
    
    rapp.mount(
        "/ui/",
        UiStaticFiles(directory=os.path.join(settings.STATIC_PATH, "ui"), html=True),
        name="Ui Page",
    )
    rapp.mount("/static", StaticFiles(directory=settings.STATIC_PATH), name="static")
    rapp.include_router(router)

    # Test endpoint for HTTPS proxy detection
    @rapp.get("/test-https-detection")
    async def test_https_detection(request: Request):
        """Test endpoint to verify HTTPS proxy header detection."""
        return {
            "request_url": str(request.url),
            "request_scheme": request.url.scheme,
            "base_url": str(request.base_url),
            "trust_proxy_headers": settings.TRUST_PROXY_HEADERS,
            "static_url": str(request.url_for("static", path="css/base.css")),
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
        return JSONResponse(
            ErrorResponse(
                code=HTTP_500_INTERNAL_SERVER_ERROR, error="unknow error"
            ).dict(),
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return rapp


app = get_app()
