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

# Manual install hints shown when no auto-install command is available.
MANUAL_INSTALL_HINTS: dict[str, dict[OS, str]] = {
    "uv": {
        OS.LINUX: "curl -LsSf https://astral.sh/uv/install.sh | sh",
        OS.MACOS: "curl -LsSf https://astral.sh/uv/install.sh | sh",
    },
    "porthole": {
        OS.LINUX: "uv tool install porthole   (from this repo, after uv is installed)",
        OS.MACOS: "uv tool install porthole   (from this repo, after uv is installed)",
    },
}

# Map tool name -> install command per OS.
# Commands are lists ready for subprocess.
INSTALL_COMMANDS: dict[str, dict[OS, list[str]]] = {
    "uv": {
        OS.LINUX: ["bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
        OS.MACOS: ["bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
    },
    "wireguard-tools": {
        OS.LINUX: ["sudo", "apt-get", "install", "-y", "wireguard"],
        OS.MACOS: ["brew", "install", "wireguard-tools"],
    },
    "sops": {
        OS.LINUX: ["bash", "-c",
            'SOPS_VERSION=$(curl -s https://api.github.com/repos/getsops/sops/releases/latest | grep tag_name | cut -d\\" -f4) && '
            'sudo curl -Lo /usr/local/bin/sops https://github.com/getsops/sops/releases/download/$SOPS_VERSION/sops-$SOPS_VERSION.linux.amd64 && '
            'sudo chmod +x /usr/local/bin/sops'],
        OS.MACOS: ["brew", "install", "sops"],
    },
    "age": {
        OS.LINUX: ["sudo", "apt-get", "install", "-y", "age"],
        OS.MACOS: ["brew", "install", "age"],
    },
    "porthole": {
        OS.LINUX: ["bash", "-c", "uv tool install porthole"],
        OS.MACOS: ["bash", "-c", "uv tool install porthole"],
    },
    "terraform": {
        OS.LINUX: ["bash", "-c",
            'wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && '
            'echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list && '
            'sudo apt-get update && sudo apt-get install -y terraform'],
        OS.MACOS: ["bash", "-c", "brew tap hashicorp/tap && brew install hashicorp/tap/terraform"],
    },
    "ansible": {
        OS.LINUX: ["bash", "-c", "pipx install ansible || uv tool install ansible"],
        OS.MACOS: ["bash", "-c", "pipx install ansible || uv tool install ansible"],
    },
}

# Tools whose install commands require sudo (shown as a warning in the UI).
NEEDS_SUDO: set[str] = {"wireguard-tools", "sops", "age", "terraform"}


def get_install_command(tool: str, os: OS) -> Optional[list[str]]:
    """Return the install command for `tool` on `os`, or None if unknown."""
    return INSTALL_COMMANDS.get(tool, {}).get(os)


def get_tool_description(tool: str) -> str:
    """Return a human-readable description of the tool."""
    return TOOL_DESCRIPTIONS.get(tool, "")


def get_manual_hint(tool: str, os: OS) -> str | None:
    """Return a manual install hint when auto-install isn't available."""
    return MANUAL_INSTALL_HINTS.get(tool, {}).get(os)
