import requests
from typing import Optional, List

try:
    import httpx  # optional dependency for async client
except Exception:  # pragma: no cover
    httpx = None


class SandboxProxy:
    """Proxy object for sandbox operations."""

    def __init__(self, name: str, namespace: str, client: "Client"):
        self.name = name
        self.namespace = namespace
        self._client = client

    def exec(self, code: str) -> dict:
        """Execute code in the sandbox."""
        return self._client._exec_command(self.name, code, self.namespace)

    def delete(self) -> dict:
        """Delete this sandbox."""
        return self._client.delete(self.name, self.namespace)


class Client:
    """K7 Python SDK Client."""

    def __init__(self, endpoint: str, api_key: str, verify_ssl: bool = True):
        self.base_url = endpoint.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})
        self.session.verify = verify_ssl

    def _unwrap(self, response) -> dict:
        data = response.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    def create(self, sandbox_config: dict) -> SandboxProxy:
        """Create a new sandbox and return a proxy object."""
        response = self.session.post(
            f"{self.base_url}/api/v1/sandboxes", json=sandbox_config
        )
        response.raise_for_status()

        name = sandbox_config.get("name")
        namespace = sandbox_config.get("namespace", "default")

        return SandboxProxy(name, namespace, self)

    def list(self, namespace: Optional[str] = None) -> List[dict]:
        """List all sandboxes."""
        params = {"namespace": namespace} if namespace else {}
        response = self.session.get(f"{self.base_url}/api/v1/sandboxes", params=params)
        response.raise_for_status()
        return self._unwrap(response)

    def delete(self, name: str, namespace: str = "default") -> dict:
        """Delete a sandbox."""
        response = self.session.delete(
            f"{self.base_url}/api/v1/sandboxes/{name}", params={"namespace": namespace}
        )
        response.raise_for_status()
        return self._unwrap(response)

    def delete_all(self, namespace: str = "default") -> dict:
        """Delete all sandboxes in a namespace."""
        response = self.session.delete(
            f"{self.base_url}/api/v1/sandboxes", params={"namespace": namespace}
        )
        response.raise_for_status()
        return self._unwrap(response)

    def install(
        self,
        playbook: Optional[str] = None,
        inventory: Optional[str] = None,
        verbose: bool = False,
    ) -> dict:
        """Install K7 on target hosts."""
        response = self.session.post(
            f"{self.base_url}/api/v1/install",
            json={"playbook": playbook, "inventory": inventory, "verbose": verbose},
        )
        response.raise_for_status()
        return self._unwrap(response)

    def get_metrics(self, namespace: Optional[str] = None) -> dict:
        """Get resource usage metrics for sandboxes."""
        params = {"namespace": namespace} if namespace else {}
        response = self.session.get(
            f"{self.base_url}/api/v1/sandboxes/metrics", params=params
        )
        response.raise_for_status()
        return self._unwrap(response)

    def _exec_command(self, name: str, command: str, namespace: str) -> dict:
        """Internal method to execute command in sandbox."""
        response = self.session.post(
            f"{self.base_url}/api/v1/sandboxes/{name}/exec",
            json={"command": command},
            params={"namespace": namespace},
        )
        response.raise_for_status()
        return self._unwrap(response)


class AsyncClient:
    """K7 Python SDK Async Client."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        verify_ssl: bool = True,
        timeout: float = 30.0,
    ):
        if httpx is None:
            raise RuntimeError(
                "httpx is required for AsyncClient. Install with `pip install httpx`."
            )
        self.base_url = endpoint.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": api_key},
            verify=verify_ssl,
            timeout=timeout,
        )

    async def create(self, sandbox_config: dict) -> dict:
        r = await self._client.post("/api/v1/sandboxes", json=sandbox_config)
        r.raise_for_status()
        return r.json()

    async def list(self, namespace: Optional[str] = None) -> List[dict]:
        params = {"namespace": namespace} if namespace else {}
        r = await self._client.get("/api/v1/sandboxes", params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def delete(self, name: str, namespace: str = "default") -> dict:
        r = await self._client.delete(
            f"/api/v1/sandboxes/{name}", params={"namespace": namespace}
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def delete_all(self, namespace: str = "default") -> dict:
        r = await self._client.delete(
            "/api/v1/sandboxes", params={"namespace": namespace}
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def exec(self, name: str, command: str, namespace: str = "default") -> dict:
        r = await self._client.post(
            f"/api/v1/sandboxes/{name}/exec",
            json={"command": command},
            params={"namespace": namespace},
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def get_metrics(self, namespace: Optional[str] = None) -> dict:
        params = {"namespace": namespace} if namespace else {}
        r = await self._client.get("/api/v1/sandboxes/metrics", params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def aclose(self):
        await self._client.aclose()
