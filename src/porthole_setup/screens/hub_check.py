"""Hub check screen — placeholder (not yet implemented).

Blocked by: SPEC-008 acceptance test (iac-remote-desktop-node-4i1).
See SPEC-009 task iac-remote-desktop-node-ioy for implementation details.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class HubCheckScreen(Screen):
    """Check whether the hub VPS is reachable; offer to spin it up if not."""

    TITLE = "Step 3 of 5: Hub Check"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(
            "[bold yellow]Hub Check screen not yet implemented.[/]\n\n"
            "This screen will be available once the SPEC-008 Ansible playbook "
            "has been validated on a live hub (task iac-remote-desktop-node-4i1).",
            markup=True,
        )
        yield Button("← Back", id="back-btn", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
