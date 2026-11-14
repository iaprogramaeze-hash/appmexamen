"""Único lugar que importa todos los routers (analisis.txt 5).

El prefijo de versión (/api/v1) lo aplica la factory en app.main; cada router
declara su propio prefijo. Los dominios se suman acá a medida que se implementan
(SDD-1 auth, SDD-2 SIGME base, próximos: mesas, reportes).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.catalogo.router import router as catalogo_router
from app.features.dispositivos.router import router as dispositivos_router
from app.features.inscripciones.router_inscripciones import (
    router as inscripciones_router,
)
from app.features.mesas.router import router as mesas_router
from app.features.mesas.router_grupos import router as grupos_router
from app.features.mesas.router_mesas import router as examenes_router
from app.features.personas.router import router as personas_router
from app.features.preinscripcion.router import router as preinscripcion_router
from app.features.preinscripcion.router_sigme import router as ventanas_router
from app.features.reportes.router import router as reportes_router
from app.features.usuarios.router_catalogo_seguridad import (
    router as seguridad_router,
)
from app.features.usuarios.router_usuarios import router as usuarios_router

api_router = APIRouter()
api_router.include_router(auth_router)  # el router declara su prefijo /auth
api_router.include_router(preinscripcion_router)  # prefijo /preinscripcion
# Prefijo /sigme: el dominio SIGME Web agrupa personas, usuarios, roles y
# catálogo bajo un solo espacio (§6); sus routers hijos declaran /personas, etc.
api_router.include_router(personas_router, prefix="/sigme")
api_router.include_router(usuarios_router, prefix="/sigme")
api_router.include_router(seguridad_router, prefix="/sigme")
api_router.include_router(catalogo_router, prefix="/sigme")
api_router.include_router(mesas_router, prefix="/sigme")  # convocatorias (T1)
api_router.include_router(grupos_router, prefix="/sigme")  # grupos (T3)
api_router.include_router(examenes_router, prefix="/sigme")  # mesas (T4)
api_router.include_router(ventanas_router, prefix="/sigme")
# SDD-4: inscripciones y consultas de alumno SIN prefijo de dispositivo
# (L2): a raíz bajo /api/v1/, autorización por sesión o permiso.
api_router.include_router(inscripciones_router)  # ventanas (T2)
# SDD-4 T6: dispositivos (push notifications) SIN prefijo de dispositivo
# (L2): a raíz bajo /api/v1/, gate por sesión válida.
api_router.include_router(dispositivos_router)
# SDD-5: reportes de cierre SIN prefijo de dispositivo (L2).
# Permiso `reporte.exportar` (secretario, director, admin, superadmin).
api_router.include_router(reportes_router)
