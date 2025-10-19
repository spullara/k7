from fastapi import FastAPI, HTTPException, Depends, Header, status, Request
from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict
import os
import json
import hashlib
import secrets
import time
from pathlib import Path

from ..core.core import K7Core
from ..core.models import SandboxConfig
from .. import __version__

app = FastAPI(title="K7 Sandbox API", version=__version__)

API_KEYS_FILE = Path(os.getenv("K7_API_KEYS_FILE", "/etc/k7/api_keys.json"))


def load_api_keys() -> dict:
    """Load API keys from file."""
    if not API_KEYS_FILE.exists():
        return {}
    try:
        with open(API_KEYS_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return {}
    # Purge expired keys opportunistically
    now_ts = int(time.time())
    changed = False
    for h, v in list(data.items()):
        exp = v.get("expires")
        if isinstance(exp, int) and now_ts > exp:
            del data[h]
            changed = True
    if changed:
        save_api_keys(data)
    return data


def save_api_keys(keys: dict):
    """Save API keys to file with proper permissions."""
    API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)
    os.chmod(API_KEYS_FILE, 0o600)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """Verify API key via X-API-Key or Authorization: Bearer header.

    Uses timing-attack-resistant comparison and updates last_used on success.
    """
    token: Optional[str] = None
    if x_api_key and x_api_key.strip():
        token = x_api_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing API key")

    api_keys = load_api_keys()
    key_hash = hashlib.sha256(token.encode()).hexdigest()

    valid_hash = None
    valid_data = None
    for stored_hash, key_data in api_keys.items():
        if secrets.compare_digest(key_hash, stored_hash):
            valid_hash = stored_hash
            valid_data = key_data
            break

    if valid_data is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Enforce expiry if present
    now_ts = int(time.time())
    expires_ts = valid_data.get("expires")
    if isinstance(expires_ts, int) and now_ts > expires_ts:
        raise HTTPException(status_code=401, detail="API key expired")

    api_keys[valid_hash]["last_used"] = now_ts
    save_api_keys(api_keys)

    return valid_data


def success_response(data: Any, status_code: int = status.HTTP_200_OK, headers: Dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(content={"data": data}, status_code=status_code, headers=headers)


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(content={"error": {"code": code, "message": message}}, status_code=status_code)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # type: ignore[override]
    # Map common status codes to generic error codes
    code_map = {
        400: "BadRequest",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        409: "Conflict",
        422: "UnprocessableEntity",
        500: "InternalServerError",
    }
    code = code_map.get(exc.status_code, "Error")
    # FastAPI often sets detail to str or dict; normalize to str
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return error_response(code, detail, exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[override]
    return error_response("InternalServerError", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "K7 Sandbox API", "version": __version__}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/sandboxes", dependencies=[Depends(verify_api_key)])
async def create_sandbox(config: dict):
    """Create a new sandbox."""
    try:
        sandbox_config = SandboxConfig.from_dict(config)
        core = K7Core()
        result = core.create_sandbox(sandbox_config)

        if result.success:
            resource = {
                "name": sandbox_config.name,
                "namespace": sandbox_config.namespace,
                "image": sandbox_config.image,
            }
            location = f"/api/v1/sandboxes/{sandbox_config.name}?namespace={sandbox_config.namespace}"
            return success_response(resource, status_code=status.HTTP_201_CREATED, headers={"Location": location})
        else:
            raise HTTPException(status_code=400, detail=result.error)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/sandboxes", dependencies=[Depends(verify_api_key)])
async def list_sandboxes(namespace: Optional[str] = None):
    """List all sandboxes."""
    core = K7Core()
    sandboxes = core.list_sandboxes(namespace)
    return success_response([sandbox.to_dict() for sandbox in sandboxes])


@app.get("/api/v1/sandboxes/{name}", dependencies=[Depends(verify_api_key)])
async def get_sandbox(name: str, namespace: str = "default"):
    """Get a single sandbox by name."""
    core = K7Core()
    items = core.list_sandboxes(namespace)
    for s in items:
        if s.name == name:
            return success_response(s.to_dict())
    raise HTTPException(status_code=404, detail=f"Sandbox {name} not found in namespace {namespace}")


@app.delete("/api/v1/sandboxes/{name}", dependencies=[Depends(verify_api_key)])
async def delete_sandbox(name: str, namespace: str = "default"):
    """Delete a sandbox."""
    core = K7Core()
    result = core.delete_sandbox(name, namespace)

    if result.success:
        return success_response({"message": result.message})
    else:
        raise HTTPException(status_code=400, detail=result.error)


@app.delete("/api/v1/sandboxes", dependencies=[Depends(verify_api_key)])
async def delete_all_sandboxes(namespace: str = "default"):
    """Delete all sandboxes in a namespace."""
    core = K7Core()
    result = core.delete_all_sandboxes(namespace)

    if result.success:
        return success_response({"message": result.message, "results": result.data})
    else:
        raise HTTPException(status_code=400, detail=result.error)


@app.post("/api/v1/sandboxes/{name}/exec", dependencies=[Depends(verify_api_key)])
async def exec_command(name: str, command_data: dict, namespace: str = "default"):
    """Execute a command in a sandbox."""
    command = command_data.get("command", "")
    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    core = K7Core()
    result = core.exec_command(name, command, namespace)
    return success_response(result.to_dict())


@app.post("/api/v1/install", dependencies=[Depends(verify_api_key)])
async def install_node(install_data: dict):
    """Install K7 on target hosts."""
    core = K7Core()
    result = core.install_node(
        install_data.get("playbook"),
        install_data.get("inventory"),
        install_data.get("verbose", False),
    )

    if result.success:
        return success_response({"message": result.message})
    else:
        raise HTTPException(status_code=400, detail=result.error)


@app.get("/api/v1/sandboxes/metrics", dependencies=[Depends(verify_api_key)])
async def get_sandbox_metrics(namespace: Optional[str] = None):
    """Get resource usage metrics for sandboxes."""
    core = K7Core()
    metrics = core.get_sandbox_metrics(namespace)
    return success_response(metrics)
