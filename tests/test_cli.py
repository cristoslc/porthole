from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from wgmesh.cli import cli
from wgmesh.models import HubConfig, Network, Peer


@pytest.fixture
def runner():
    return CliRunner()


def _make_network(*extra_peers):
    peers = [
        Peer(
            name="hub", ip="10.100.0.1",
            public_key="hub-pub=", private_key="hub-priv=",
            dns_name="hub", role="hub",
        ),
        *extra_peers,
    ]
    return Network(
        hub=HubConfig(endpoint="hub.example.com:51820"),
        peers=peers,
    )


class TestInit:
    @patch("wgmesh.commands.init.state.save_state")
    @patch("wgmesh.commands.init.keys.generate_keypair", return_value=("priv=", "pub="))
    @patch("wgmesh.commands.init.sops.create_sops_config")
    def test_init_creates_network(self, mock_sops, mock_keys, mock_save, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--endpoint", "hub.example.com:51820", "--age-key", "age1test"])
            assert result.exit_code == 0
            assert "Initialized" in result.output

    def test_init_fails_if_state_exists(self, runner):
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("existing")
            result = runner.invoke(cli, ["init", "--endpoint", "hub.example.com:51820", "--age-key", "age1test"])
            assert result.exit_code != 0
            assert "already exists" in result.output


class TestAdd:
    @patch("wgmesh.commands.add.render.render_peer_config", return_value="[Interface]\n...")
    @patch("wgmesh.commands.add.state.save_state")
    @patch("wgmesh.commands.add.state.load_state")
    @patch("wgmesh.commands.add.keys.generate_keypair", return_value=("priv=", "pub="))
    def test_add_peer(self, mock_keys, mock_load, mock_save, mock_render, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["add", "laptop"])
            assert result.exit_code == 0
            assert "Added peer 'laptop'" in result.output

    @patch("wgmesh.commands.add.state.load_state")
    def test_add_duplicate_fails(self, mock_load, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["add", "hub"])
            assert result.exit_code != 0
            assert "already exists" in result.output


class TestRemove:
    @patch("wgmesh.commands.remove.state.save_state")
    @patch("wgmesh.commands.remove.state.load_state")
    def test_remove_peer(self, mock_load, mock_save, runner):
        extra = Peer(
            name="laptop", ip="10.100.0.2",
            public_key="pub=", private_key="priv=",
            dns_name="laptop", role="workstation",
            reverse_ssh_port=2202,
        )
        mock_load.return_value = _make_network(extra)
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["remove", "laptop"])
            assert result.exit_code == 0
            assert "Removed peer 'laptop'" in result.output

    @patch("wgmesh.commands.remove.state.load_state")
    def test_remove_hub_fails(self, mock_load, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["remove", "hub"])
            assert result.exit_code != 0
            assert "Cannot remove the hub" in result.output

    @patch("wgmesh.commands.remove.state.load_state")
    def test_remove_nonexistent_fails(self, mock_load, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["remove", "ghost"])
            assert result.exit_code != 0
            assert "not found" in result.output


class TestList:
    @patch("wgmesh.commands.list_cmd.state.load_state")
    def test_list_table(self, mock_load, runner):
        extra = Peer(
            name="laptop", ip="10.100.0.2",
            public_key="pub=", private_key="priv=",
            dns_name="laptop", role="workstation",
            reverse_ssh_port=2202,
        )
        mock_load.return_value = _make_network(extra)
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 0
            assert "hub" in result.output
            assert "laptop" in result.output
            assert "10.100.0.2" in result.output

    @patch("wgmesh.commands.list_cmd.state.load_state")
    def test_list_json(self, mock_load, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["list", "--json"])
            assert result.exit_code == 0
            import json
            data = json.loads(result.output)
            assert isinstance(data, list)
            assert data[0]["name"] == "hub"


class TestSync:
    @patch("wgmesh.commands.sync.render.render_nftables", return_value="nft rules")
    @patch("wgmesh.commands.sync.render.render_dns_zone", return_value="zone data")
    @patch("wgmesh.commands.sync.render.render_hub_config", return_value="wg config")
    @patch("wgmesh.commands.sync.state.load_state")
    def test_sync_dry_run(self, mock_load, mock_hub, mock_dns, mock_nft, runner):
        mock_load.return_value = _make_network()
        with runner.isolated_filesystem():
            Path("network.sops.yaml").write_text("placeholder")
            result = runner.invoke(cli, ["sync", "--dry-run"])
            assert result.exit_code == 0
            assert "hub wg0.conf" in result.output
            assert "wg config" in result.output
            assert "coredns" in result.output
            assert "nftables" in result.output
