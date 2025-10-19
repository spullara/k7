from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, fields
import yaml


@dataclass
class SandboxConfig:
    """Data model for sandbox configuration"""

    name: str
    image: str
    namespace: str = "default"
    env_file: Optional[str] = None
    egress_whitelist: Optional[List[str]] = None
    limits: Optional[Dict[str, str]] = None
    before_script: str = ""
    # Security toggles (default off) and capabilities configuration
    pod_non_root: bool = False
    container_non_root: bool = False
    cap_drop: Optional[List[str]] = None  # default behavior handled in core: drop ALL
    cap_add: Optional[List[str]] = None
    # Note: ingress isolation is enforced by core with a hardcoded NetworkPolicy

    def __post_init__(self):
        if self.limits is None:
            self.limits = {}

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SandboxConfig":
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "SandboxConfig":
        # Be forward/backward compatible with API by ignoring unknown keys
        allowed = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in (data or {}).items() if k in allowed}
        return cls(**filtered)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SandboxInfo:
    name: str
    namespace: str
    status: str
    ready: str
    restarts: int
    age: str
    image: str
    error_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OperationResult:
    success: bool
    message: str = ""
    error: str = ""
    data: Any = None

    def to_dict(self) -> dict:
        return asdict(self)
