"""Errores de dominio y contrato de error único PD-24 (analisis.txt 5 y 6).

PD-24 (cerrado en SDD-1 T3): TODA respuesta de error es JSON con la forma
{ "code": "clase-de-problema", "detail": "mensaje" } y "errors" SÓLO en 422.
Los códigos son kebab-case estables por clase (p. ej. "ventana-cerrada").
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base: status + code kebab-case estable; errors[] y headers opcionales."""

    status_code: int = 500
    code: str = "error-interno"

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        errors: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code or self.code
        self.detail = detail or self.code.replace("-", " ")
        self.errors = errors
        self.headers = headers
        super().__init__(self.detail)

    def to_response(self) -> JSONResponse:
        body: dict[str, Any] = {"code": self.code, "detail": self.detail}
        if self.status_code == 422 and self.errors:
            body["errors"] = self.errors
        return JSONResponse(
            status_code=self.status_code, content=body, headers=self.headers
        )


class NotFoundError(AppError):
    status_code = 404
    code = "no-encontrado"


class UnauthorizedError(AppError):
    status_code = 401
    code = "no-autenticado"


class ForbiddenError(AppError):
    status_code = 403
    code = "sin-permiso"


class ConflictError(AppError):
    status_code = 409
    code = "conflicto"


class DomainValidationError(AppError):
    status_code = 422
    code = "validacion"


_HTTP_CODES: dict[int, str] = {
    400: "solicitud-invalida",
    401: "no-autenticado",
    403: "sin-permiso",
    404: "no-encontrado",
    405: "metodo-no-permitido",
    409: "conflicto",
    422: "validacion",
    429: "limite-de-peticiones",
}


def register_error_handlers(app: FastAPI) -> None:
    """Registra el contrato PD-24: una sola forma de error para toda la API."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return exc.to_response()

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(part) for part in err["loc"][1:]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "code": "validacion",
                "detail": "Solicitud inválida",
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "error-http")
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code, "detail": str(exc.detail)},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, __: Exception) -> JSONResponse:
        # Nunca filtrar detalles internos (analisis.txt 0: superficie mínima).
        return JSONResponse(
            status_code=500, content={"code": "error-interno", "detail": "Error interno"}
        )
