import subprocess
from pathlib import Path

SOPS_CONFIG_TEMPLATE = """\
creation_rules:
  - path_regex: network\\.sops\\.yaml$
    encrypted_regex: "^private_key$"
    age: "{age_key}"
"""


def create_sops_config(age_key: str, path: Path | None = None) -> Path:
    """Create .sops.yaml configuration file."""
    if path is None:
        path = Path(".sops.yaml")
    content = SOPS_CONFIG_TEMPLATE.format(age_key=age_key)
    path.write_text(content)
    return path


def encrypt_file(plaintext_path: Path) -> None:
    """Encrypt a file in-place using sops."""
    subprocess.run(
        ["sops", "--encrypt", "--in-place", str(plaintext_path)],
        check=True,
    )


def decrypt_file(encrypted_path: Path) -> str:
    """Decrypt a sops-encrypted file and return its contents."""
    result = subprocess.run(
        ["sops", "--decrypt", str(encrypted_path)],
        capture_output=True, text=True, check=True,
    )
    return result.stdout
