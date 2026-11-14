"""Reloj de negocio: fecha de calendario en America/Argentina/Buenos_Aires.

RB-23: los límites de ventana son inclusivos por fecha de calendario en la
timezone del backend, fijada en America/Argentina/Buenos_Aires. AR no aplica
horario de verano desde 2009, así que el offset es fijo UTC-3 y basta con
restarle 3 horas al instante UTC (A-SDD3-2) sin instalar una base de zonas.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def hoy_buenos_aires() -> date:
    """Fecha de calendario actual en America/Argentina/Buenos_Aires (RB-23)."""
    return (datetime.now(UTC) - timedelta(hours=3)).date()
