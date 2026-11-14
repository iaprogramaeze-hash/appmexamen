"""Esquemas de request/response de /api/v1/auth (analisis.txt 2.4, 2.5 y 6)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    # Sin min_length en login: la política de 12 caracteres (§2.5) rige al
    # CREAR la clave; el login no filtra la política ni bloquea casos legados.
    password: str = Field(min_length=1, max_length=128)
    #: App que inicia sesión (§2.8): sigme_web | sigme_mobile.
    modulo: str = Field(min_length=1, max_length=30)


class TokenPair(BaseModel):
    access: str
    refresh: str


class AccessOnly(BaseModel):
    access: str


class RefreshRequest(BaseModel):
    refresh: str = Field(min_length=1, max_length=128)


class CambiarClaveRequest(BaseModel):
    clave_actual: str = Field(min_length=1, max_length=128)
    #: §2.5: longitud mínima 12 caracteres.
    clave_nueva: str = Field(min_length=12, max_length=128)


class OlvidoClaveRequest(BaseModel):
    #: Lo que haya cargado el alumno (username, D.N.I. o correo): el backend
    #: coincide contra username O email (case-insensitive).
    identificador: str = Field(min_length=1, max_length=50)


class OlvidoClaveResponse(BaseModel):
    #: Siempre el mismo cuerpo exista o no la cuenta (anti-enumeración).
    status: str


class RestablecerClaveRequest(BaseModel):
    #: Token opaco que llegó por correo (PD-04; sólo se consulta su hash).
    token: str = Field(min_length=1, max_length=512)
    #: §2.5: misma política que el resto de los cambios de clave (min. 12).
    clave_nueva: str = Field(min_length=12, max_length=128)


class RestablecerClaveResponse(BaseModel):
    status: str



class YoResponse(BaseModel):
    id: str
    username: str
    roles: list[str]
    permisos: list[str]
    modulos: list[str]
