"""Platform detection and tool installation dispatch for Porthole setup."""
import platform
import shutil
from enum import Enum, auto
from typing import Optional


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


# Map tool name → install command per OS.
# Commands are lists ready for subprocess.
INSTALL_COMMANDS: dict[str, dict[OS, list[str]]] = {
    "wireguard-tools": {
        OS.LINUX: ["apt-get", "install", "-y", "wireguard"],
        OS.MACOS: ["brew", "install", "wireguard-tools"],
    },
    "sops": {
        OS.LINUX: ["bash", "-c",
            'SOPS_VERSION=$(curl -s https://api.github.com/repos/getsops/sops/releases/latest | grep tag_name | cut -d\\" -f4) && '
            'curl -Lo /usr/local/bin/sops https://github.com/getsops/sops/releases/download/$SOPS_VERSION/sops-$SOPS_VERSION.linux.amd64 && '
            'chmod +x /usr/local/bin/sops'],
        OS.MACOS: ["brew", "install", "sops"],
    },
    "age": {
        OS.LINUX: ["apt-get", "install", "-y", "age"],
        OS.MACOS: ["brew", "install", "age"],
    },
    "terraform": {
        OS.LINUX: ["bash", "-c",
            'wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && '
            'echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list && '
            'apt-get update && apt-get install -y terraform'],
        OS.MACOS: ["brew", "install", "terraform"],
    },
    "ansible": {
        OS.LINUX: ["bash", "-c", "pipx install ansible"],
        OS.MACOS: ["bash", "-c", "pipx install ansible"],
    },
}


def get_install_command(tool: str, os: OS) -> Optional[list[str]]:
    """Return the install command for `tool` on `os`, or None if unknown."""
    return INSTALL_COMMANDS.get(tool, {}).get(os)
