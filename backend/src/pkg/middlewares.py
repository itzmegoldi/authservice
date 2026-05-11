from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException,Request,Response
from typing import Callable,Awaitable
from src.pkg import logging
import time

logger = logging.get_logger()

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        try:
            response: Response = await call_next(request)
        except HTTPException as he:
            raise he
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")
        return response


class LoggerInitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        request_id = request.headers.get("X-Request-ID", None)
        logging.init_logger_context(request_id=request_id)
        logging.bind_context(app_source="api")
        request_url = str(request.url)
        logger.info(
            "Request Initiated",
            context={ "request_url": request_url},
        )
        start_time = int(time.time() * 1000)

        try:
            response: Response = await call_next(request)
        except HTTPException as he:
            logger.error(
                "Request Failed",
                context={
                    "request_url": request_url,
                    "status_code": he.status_code,
                    "detail": he.detail,
                },
            )
            raise he
        
        processed_time = int(time.time() * 1000) - start_time
        logger.info(
            "Request Completed",
            context={
                "start_time": start_time,
                "processed_time_ms": processed_time,
            }
        )
        logging.clear_context()
        return response
    
