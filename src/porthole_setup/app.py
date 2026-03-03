"""Porthole setup Textual application."""

from textual.app import App

from porthole_setup.screens.hub_check import HubCheckScreen
from porthole_setup.screens.hub_spinup import HubSpinupScreen
from porthole_setup.screens.prerequisites import PrerequisitesScreen
from porthole_setup.screens.secrets import SecretsScreen


class PortholeApp(App):
    """Interactive node enrollment wizard for the Porthole fleet."""

    TITLE = "Porthole Setup"

    SCREENS = {
        "prerequisites": PrerequisitesScreen,
        "secrets": SecretsScreen,
        "hub_check": HubCheckScreen,
        "hub_spinup": HubSpinupScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("prerequisites")
