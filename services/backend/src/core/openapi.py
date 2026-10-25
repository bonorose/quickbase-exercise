#!/usr/bin/env python3
# ******************************************************************************
# * @file    openapi.py
# * @author  Simeon Marlokov
# * @brief   OpenAPI schema: bearer auth on every operation except the public ones
# * @date    25.10.2026
# ******************************************************************************
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def install_openapi(app: FastAPI, public_routes: frozenset[tuple[str, str]]) -> None:
    def openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        schema.setdefault("components", {})["securitySchemes"] = {
            "BearerAuth": {"type": "http", "scheme": "bearer"},
        }
        schema["security"] = [{"BearerAuth": []}]
        for method, path in public_routes:
            operation = schema["paths"].get(path, {}).get(method.lower())
            if operation is not None:
                operation["security"] = []
        app.openapi_schema = schema
        return schema

    app.openapi = openapi
