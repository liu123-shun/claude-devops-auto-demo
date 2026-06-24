"""
全局统一异常处理
===============
捕获 FastAPI 应用中的各类异常，返回规范的 JSON 错误响应。
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """统一处理 HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """统一处理 ValueError"""
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """统一处理未预期异常"""
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


def register_exception_handlers(app):
    """注册全部异常处理器到 FastAPI 应用"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
