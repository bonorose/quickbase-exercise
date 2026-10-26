import pytest

pytestmark = pytest.mark.api

FORBIDDEN = {"organization_id", "organization", "tenant_id", "tenant"}


def _properties(schema: dict, components: dict, seen: set[str]) -> list[str]:
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        if name in seen:
            return []
        seen.add(name)
        return _properties(components.get(name, {}), components, seen)
    found = []
    for key, value in schema.get("properties", {}).items():
        found.append(key)
        if isinstance(value, dict):
            found.extend(_properties(value, components, set(seen)))
    for key in ("items", "additionalProperties"):
        nested = schema.get(key)
        if isinstance(nested, dict):
            found.extend(_properties(nested, components, set(seen)))
    for key in ("anyOf", "oneOf", "allOf"):
        for variant in schema.get(key, []):
            if isinstance(variant, dict):
                found.extend(_properties(variant, components, set(seen)))
    return found


async def test_openapi_has_no_organization_request_fields(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    components = schema.get("components", {}).get("schemas", {})
    offenders = []
    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            names = [parameter["name"] for parameter in operation.get("parameters", [])]
            body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if isinstance(body, dict):
                names.extend(_properties(body, components, set()))
            hit = FORBIDDEN.intersection(names)
            if hit:
                offenders.append(f"{method.upper()} {path}: {sorted(hit)}")
    assert offenders == []
