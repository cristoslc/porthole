"""Subprocess runner with live output streaming for Porthole setup."""
import subprocess
from collections.abc import Generator
from dataclasses import dataclass


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_streaming(cmd: list[str], *, cwd: str | None = None) -> Generator[str, None, CommandResult]:
    """
    Run `cmd` and yield output lines as they arrive.

    Usage (in a Textual worker or async context):
        result = yield from run_streaming(["terraform", "apply", "-auto-approve"])
        if not result.success:
            ...

    Yields each line (stdout + stderr interleaved) as it is produced.
    Returns a CommandResult with the final returncode and accumulated output.
    """
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # merge stderr into stdout
        text=True,
        bufsize=1,
        cwd=cwd,
    ) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            stdout_lines.append(line)
            yield line
        proc.wait()

    return CommandResult(
        returncode=proc.returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
    )


def run(cmd: list[str], *, cwd: str | None = None, check: bool = False) -> CommandResult:
    """
    Run `cmd` and return a CommandResult. Blocks until completion.
    If check=True, raises subprocess.CalledProcessError on non-zero exit.
    """
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
