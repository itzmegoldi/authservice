from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.builder import get_clients
from src.pkg import logging
import time

logger = logging.get_logger()


class TokenAuthenticationMiddleware(BaseHTTPMiddleware):
    """Require a valid access token for every endpoint except authentication routes."""

    public_paths = frozenset(
        {
            "/v1/api/user/admin-login",
            "/v1/api/user/refresh",
        }
    )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        # Browsers must be able to complete a CORS preflight before sending an
        # Authorization header on the actual request.
        if request.method == "OPTIONS" or request.url.path in self.public_paths:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return self._unauthorized("Authorization header is required")

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return self._unauthorized("Authorization header must use the Bearer scheme")

        try:
            claims = get_clients().token_client.decode_access_token(token)
            if claims.get("typ") != "user":
                return self._unauthorized("An access token is required")
        except Exception:
            return self._unauthorized("Invalid or expired access token")

        request.state.token_claims = claims
        return await call_next(request)

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    
