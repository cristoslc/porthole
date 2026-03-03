"""Entry point for porthole_setup TUI."""

import sys


def main() -> None:
    """Parse flags and launch the Textual app."""
    # TODO: parse --check flag
    from porthole_setup.app import PortholeApp
    app = PortholeApp()
    app.run()


if __name__ == "__main__":
    main()
