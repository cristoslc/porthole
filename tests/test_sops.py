from pathlib import Path
from unittest.mock import patch, MagicMock

from wgmesh.sops import create_sops_config, encrypt_file, decrypt_file


class TestCreateSopsConfig:
    def test_creates_config_file(self, tmp_path):
        path = tmp_path / ".sops.yaml"
        result = create_sops_config("age1abc123xyz", path)

        assert result == path
        content = path.read_text()
        assert "age1abc123xyz" in content
        assert "encrypted_regex" in content
        assert "^private_key$" in content
        assert "network\\.sops\\.yaml$" in content

    def test_default_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = create_sops_config("age1test")
        assert result == Path(".sops.yaml")
        assert result.exists()


class TestEncryptFile:
    @patch("wgmesh.sops.subprocess.run")
    def test_calls_sops_encrypt(self, mock_run):
        encrypt_file(Path("test.yaml"))
        mock_run.assert_called_once_with(
            ["sops", "--encrypt", "--in-place", "test.yaml"],
            check=True,
        )


class TestDecryptFile:
    @patch("wgmesh.sops.subprocess.run")
    def test_calls_sops_decrypt(self, mock_run):
        mock_run.return_value = MagicMock(stdout="decrypted content")
        result = decrypt_file(Path("test.sops.yaml"))
        assert result == "decrypted content"
        mock_run.assert_called_once_with(
            ["sops", "--decrypt", "test.sops.yaml"],
            capture_output=True, text=True, check=True,
        )
