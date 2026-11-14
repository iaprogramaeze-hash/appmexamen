"""Errores del dominio auth; T3 los mapea a respuestas HTTP (§6, PD-24)."""
from __future__ import annotations


class AuthError(Exception):
    """Base del dominio auth (login, sesiones y tokens)."""


class InvalidRefreshTokenError(AuthError):
    """Refresh token desconocido o vencido (analisis.txt 2.2)."""


class RefreshReuseDetectedError(AuthError):
    """Un refresh ya usado volvió a presentarse: familia revocada (analisis.txt 2.2)."""
