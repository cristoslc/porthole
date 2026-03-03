#!/usr/bin/env bash
set -euo pipefail

# Porthole setup -- bash shim
# Ensures uv is installed, then delegates to the Textual TUI.
# Usage: ./setup.sh [--check] [--help]

if ! command -v uv &>/dev/null; then
    echo "uv not found -- installing via the official uv installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # The installer adds uv to ~/.cargo/bin (or ~/.local/bin on some systems).
    # Source the cargo env so uv is available in this shell session.
    if [ -f "$HOME/.cargo/env" ]; then
        # shellcheck source=/dev/null
        source "$HOME/.cargo/env"
    fi

    # If uv is still not on PATH after sourcing, the user may need to open a
    # new shell or manually add the install directory to PATH.
    if ! command -v uv &>/dev/null; then
        echo ""
        echo "NOTE: uv was installed but is not yet on your PATH."
        echo "Please open a new shell session and re-run this script, or run:"
        echo "  source \"\$HOME/.cargo/env\""
        exit 1
    fi

    echo "uv installed successfully."
fi

exec uv run python -m porthole_setup "$@"
