from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class ExperimentalProvider(Protocol):
    def prepare(self, context: dict[str, Any]) -> dict[str, Any]: ...
    def run(self, prepared: dict[str, Any], fixture: dict[str, Any]) -> "ProviderResult": ...
    def collect(self, prepared: dict[str, Any], result: "ProviderResult") -> "ProviderResult": ...
    def cleanup(self, prepared: dict[str, Any]) -> None: ...


@dataclass
class ProviderResult:
    exit_status: int | None
    duration_ms: int
    stdout: bytes
    stderr: bytes
    timed_out: bool = False


class LocalCommandProvider:
    """Baseline provider: execute one fixture-owned local argv, once bounded."""

    def prepare(self, context: dict[str, Any]) -> dict[str, Any]:
        return context

    def run(self, prepared: dict[str, Any], fixture: dict[str, Any]) -> ProviderResult:
        import subprocess
        import time

        started = time.monotonic()
        try:
            completed = subprocess.run(
                fixture["command"],
                cwd=prepared["root"],
                capture_output=True,
                timeout=prepared["timeout_seconds"],
                check=False,
            )
            return ProviderResult(completed.returncode, int((time.monotonic() - started) * 1000), completed.stdout, completed.stderr)
        except subprocess.TimeoutExpired as exc:
            return ProviderResult(None, int((time.monotonic() - started) * 1000), exc.stdout or b"", exc.stderr or b"", True)

    def collect(self, prepared: dict[str, Any], result: ProviderResult) -> ProviderResult:
        return result

    def cleanup(self, prepared: dict[str, Any]) -> None:
        return None
