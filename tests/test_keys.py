from unittest.mock import patch, MagicMock
import subprocess

from porthole.keys import generate_keypair


class TestGenerateKeypair:
    @patch("porthole.keys.subprocess.run")
    def test_returns_keypair(self, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout="cHJpdmF0ZWtleQ==\n"),  # genkey
            MagicMock(stdout="cHVibGlja2V5YQ==\n"),  # pubkey
        ]

        private, public = generate_keypair()

        assert private == "cHJpdmF0ZWtleQ=="
        assert public == "cHVibGlja2V5YQ=="

    @patch("porthole.keys.subprocess.run")
    def test_calls_wg_genkey_then_pubkey(self, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout="privkey\n"),
            MagicMock(stdout="pubkey\n"),
        ]

        generate_keypair()

        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0][0] == ["wg", "genkey"]
        assert mock_run.call_args_list[1][0][0] == ["wg", "pubkey"]
        assert mock_run.call_args_list[1][1]["input"] == "privkey"

    @patch("porthole.keys.subprocess.run")
    def test_raises_on_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "wg genkey")

        try:
            generate_keypair()
            assert False, "Should have raised"
        except subprocess.CalledProcessError:
            pass
