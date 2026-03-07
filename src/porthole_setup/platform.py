"""Platform detection for Porthole setup."""
from __future__ import annotations

import platform
import shutil
from enum import Enum, auto


class OS(Enum):
    LINUX = auto()
    MACOS = auto()
    UNSUPPORTED = auto()


def detect_os() -> OS:
    """Return the current OS as an OS enum value."""
    system = platform.system()
    if system == "Linux":
        return OS.LINUX
    elif system == "Darwin":
        return OS.MACOS
    return OS.UNSUPPORTED


def is_installed(tool: str) -> bool:
    """Return True if `tool` is on PATH."""
    return shutil.which(tool) is not None


# Human-readable description of what each tool does in this project.
TOOL_DESCRIPTIONS: dict[str, str] = {
    "uv": "Fast Python package manager used to run porthole CLI tools",
    "wireguard-tools": "WireGuard VPN utilities (wg, wg-quick) for mesh networking",
    "sops": "Mozilla SOPS — encrypts/decrypts network state secrets",
    "age": "Modern file encryption, used as the SOPS key backend",
    "porthole": "Porthole CLI — manages peers, generates WireGuard configs",
    "terraform": "Infrastructure-as-code for provisioning the hub VPS",
    "ansible": "Configuration management for hub server setup",
}


def get_tool_description(tool: str) -> str:
    """Return a human-readable description of the tool."""
    return TOOL_DESCRIPTIONS.get(tool, "")
