import subprocess
import tempfile
from pathlib import Path

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=10",
]


def ssh_run(host: str, command: str, user: str = "root") -> str:
    """Run a command on a remote host via SSH. Returns stdout."""
    result = subprocess.run(
        ["ssh", *SSH_OPTS, f"{user}@{host}", "bash", "-c", command],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def scp_to_host(host: str, content: str, remote_path: str, user: str = "root") -> None:
    """Write content to a temporary file and SCP it to the remote host."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(content)
        local_path = f.name

    try:
        subprocess.run(
            ["scp", *SSH_OPTS, local_path, f"{user}@{host}:{remote_path}"],
            check=True,
        )
    finally:
        Path(local_path).unlink(missing_ok=True)
