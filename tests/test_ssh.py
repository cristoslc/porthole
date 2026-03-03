from unittest.mock import patch, MagicMock, call

from wgmesh.ssh import ssh_run, scp_to_host


class TestSSHRun:
    @patch("wgmesh.ssh.subprocess.run")
    def test_runs_command_on_host(self, mock_run):
        mock_run.return_value = MagicMock(stdout="output\n")
        result = ssh_run("hub.example.com", "wg show")

        assert result == "output\n"
        args = mock_run.call_args[0][0]
        assert "ssh" in args
        assert "root@hub.example.com" in args
        assert "StrictHostKeyChecking=accept-new" in " ".join(args)
        assert "ConnectTimeout=10" in " ".join(args)

    @patch("wgmesh.ssh.subprocess.run")
    def test_custom_user(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        ssh_run("host", "ls", user="admin")
        args = mock_run.call_args[0][0]
        assert "admin@host" in args


class TestSCPToHost:
    @patch("wgmesh.ssh.subprocess.run")
    def test_scps_content_to_host(self, mock_run):
        scp_to_host("hub.example.com", "file content", "/etc/test.conf")

        args = mock_run.call_args[0][0]
        assert "scp" in args
        assert "root@hub.example.com:/etc/test.conf" in args
        assert "StrictHostKeyChecking=accept-new" in " ".join(args)
