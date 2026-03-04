import subprocess


def generate_keypair() -> tuple[str, str]:
    """Generate a WireGuard keypair via wg genkey/pubkey. Returns (private_key, public_key)."""
    result = subprocess.run(
        ["wg", "genkey"],
        capture_output=True, text=True, check=True,
    )
    private_key = result.stdout.strip()

    result = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        capture_output=True, text=True, check=True,
    )
    public_key = result.stdout.strip()

    return private_key, public_key
