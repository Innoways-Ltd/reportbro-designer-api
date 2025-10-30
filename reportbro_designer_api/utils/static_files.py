# -*- coding: utf-8 -*-
"""
@create: 2022-07-22 17:44:59.

@author: ppolxda

@desc: static_files utilities
"""

import re
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse


class UiStaticFiles(StaticFiles):
    """UiStaticFiles."""

    FILE_PATH_REGIX = re.compile(r'(href|src)="\/ui\/(.*?)"')
    FILE_JS_PATH_REGIX = re.compile(r"index-(.*?).js$")
    # Regex to find path:"/api/..." patterns that need to be replaced
    FILE_JS_API_REGIX = re.compile(r'path:"/api')

    async def get_response(self, path: str, scope):
        """get_response."""
        # Prevent redirect for paths like /ui/{company} (no trailing slash)
        if path and not path.endswith("/") and "/" not in path:
            # If the path is a single segment (e.g., 'irmsdev2'), do not redirect
            # Instead, return 404 or let router handle it
            return PlainTextResponse("Not Found", status_code=404)

        response = await super().get_response(path, scope)

        if isinstance(response, FileResponse) and isinstance(response.path, str):
            scheme = scope.get("scheme", "http")
            headers = dict(scope.get("headers", []))
            host = headers.get(b"host", b"localhost").decode()

            if len(self.FILE_JS_PATH_REGIX.findall(response.path)) > 0:
                with open(response.path, "r", encoding="utf8") as fs:
                    content = fs.read()

                root_path = scope.get("root_path", "")
                app_root_path = scope.get("app_root_path", scope.get("root_path", ""))

                content = content.replace(
                    'path:"/ui",', f'path:"{root_path}",'
                )
                content = self.FILE_JS_API_REGIX.sub(
                    f'path:"{app_root_path}', content
                )
                return PlainTextResponse(content=content, media_type="text/javascript")

            if response.path.endswith("index.html"):
                with open(response.path, "r", encoding="utf8") as fs:
                    content = fs.read()

                base_url = f"{scheme}://{host}"
                content = self.FILE_PATH_REGIX.sub(f'\\1="{base_url}/ui/\\2"', content)
                return HTMLResponse(content=content)
        return response