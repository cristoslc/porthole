"""Porthole setup Textual application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label


class PortholeApp(App):
    """Interactive node enrollment wizard for the Porthole fleet."""

    TITLE = "Porthole Setup"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Welcome to Porthole Setup. (Screens not yet implemented.)")
        yield Footer()
