from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


MODELS = {
    "opencode-go/glm-5.2",
    "opencode-go/kimi-k2.7-code",
}
MAX_PACKET_BYTES = 32 * 1024
PACKET_SCHEMA = "x9-sidecar-packet-v1"
PACKET_FIELDS = {
    "schema",
    "owner_requirement",
    "claims",
    "relevant_diff",
    "proof",
    "failure",
    "question",
}
DEFAULT_PROMPT = (
    "Read only the attached bounded packet. Return concise plan or review advice. "
    "Do not run commands, edit files, deploy, or claim proof you did not inspect."
)
SAFE_ENV_NAMES = {
    "appdata",
    "home",
    "lang",
    "lc_all",
    "localappdata",
    "path",
    "ssl_cert_dir",
    "ssl_cert_file",
    "systemroot",
    "temp",
    "tmp",
    "userprofile",
    "windir",
}
TOOLS_DENIED_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "permission": {"*": "deny"},
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(
        r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret)"
        r"\s*[:=]\s*[^\s]{6,}",
        re.I,
    ),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", re.I),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b", re.I),
    re.compile(r"\b(?:cookie|set-cookie)\s*:\s*\S+", re.I),
    re.compile(r"\bauthorization\s*:\s*bearer\s+\S+", re.I),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+\w+)?|redis|mssql|sqlserver|oracle)"
        r"://[^\s/:@]+:[^@\s/]+@",
        re.I,
    ),
)


def _result(status: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": status,
        "attempts": extra.pop("attempts", 0),
        "blocks_worker": False,
        **extra,
    }


def _secret_labels(text: str) -> list[str]:
    labels: list[str] = []
    for index, pattern in enumerate(SECRET_PATTERNS, start=1):
        if pattern.search(text):
            labels.append(f"pattern-{index}")
    return labels


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _approved_sidecar_roots(repo: Path) -> tuple[Path, ...]:
    candidates = [repo / ".devad" / "manager" / "sidecar"]
    feature_root = repo / ".devad" / "features"
    if feature_root.is_dir():
        try:
            candidates.extend(path / "sidecar" for path in feature_root.iterdir())
        except OSError:
            return ()

    roots: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved.is_dir() and _is_within(resolved, repo):
            roots.append(resolved)
    return tuple(roots)


def _packet_sidecar_directory(packet: Path, repo: Path) -> Path | None:
    for sidecar in _approved_sidecar_roots(repo):
        if packet.parent == sidecar:
            return sidecar
    return None


def _valid_packet_payload(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != PACKET_FIELDS:
        return False
    if payload["schema"] != PACKET_SCHEMA:
        return False
    for field in ("owner_requirement", "failure", "question"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            return False
    for field in ("claims", "relevant_diff", "proof"):
        value = payload[field]
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item.strip() for item in value)
        ):
            return False
    return True


def _validated_output(output: Path, sidecar: Path) -> Path | None:
    try:
        resolved = output.resolve(strict=False)
    except (OSError, RuntimeError):
        return None
    return resolved if resolved.parent == sidecar else None

def _safe_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.casefold() in SAFE_ENV_NAMES
    }
    environment["NO_COLOR"] = "1"
    return environment


def _real_windows_executable(executable: str) -> str | None:
    requested = Path(executable)
    if requested.suffix:
        if requested.suffix.casefold() != ".exe":
            return None
        candidate = (
            requested
            if requested.is_absolute()
            else Path(shutil.which(executable) or "")
        )
        try:
            return str(candidate.resolve(strict=True)) if candidate.is_file() else None
        except (OSError, RuntimeError):
            return None

    direct = shutil.which(f"{executable}.exe")
    if direct:
        try:
            candidate = Path(direct).resolve(strict=True)
            if candidate.is_file():
                return str(candidate)
        except (OSError, RuntimeError):
            pass

    npm_roots: list[Path] = []
    shim = shutil.which(f"{executable}.cmd")
    if shim:
        npm_roots.append(Path(shim).parent)
    appdata = os.environ.get("APPDATA")
    if appdata:
        npm_roots.append(Path(appdata) / "npm")
    for npm_root in npm_roots:
        candidate = (
            npm_root
            / "node_modules"
            / "opencode-ai"
            / "bin"
            / "opencode.exe"
        )
        try:
            candidate = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if candidate.is_file():
            return str(candidate)
    return None


def resolve_executable(executable: str) -> str | None:
    """Resolve a real binary; Windows command shims are never executed."""
    if os.name == "nt":
        return _real_windows_executable(executable)
    resolved = shutil.which(executable)
    return str(Path(resolved).resolve()) if resolved else None


def _failure_class(stderr: str, stdout: str) -> str:
    text = f"{stderr}\n{stdout}".lower()
    classes = (
        ("model", "MODEL_UNAVAILABLE"),
        ("auth", "AUTH_UNAVAILABLE"),
        ("quota", "QUOTA_UNAVAILABLE"),
        ("credit", "CREDIT_UNAVAILABLE"),
        ("timeout", "TIMEOUT"),
        ("provider", "PROVIDER_UNAVAILABLE"),
    )
    for needle, label in classes:
        if needle in text:
            return label
    return "PROCESS_FAILED"


def run_request(
    *,
    packet: Path,
    model: str,
    repo: Path,
    timeout: int = 120,
    executable: str = "opencode",
    output: Path | None = None,
) -> dict[str, Any]:
    repo = repo.resolve()
    if model not in MODELS:
        return _result("MODEL_NOT_ALLOWED", model=model)
    try:
        packet = packet.resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        return _result("PACKET_MISSING", model=model)
    if not packet.is_file():
        return _result("PACKET_MISSING", model=model)
    sidecar = _packet_sidecar_directory(packet, repo)
    if sidecar is None:
        return _result("PACKET_PATH_BLOCKED", model=model)
    size = packet.stat().st_size
    if size > MAX_PACKET_BYTES:
        return _result(
            "PACKET_TOO_LARGE", model=model, packet_bytes=size, limit=MAX_PACKET_BYTES
        )
    text = packet.read_text(encoding="utf-8-sig", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _result("PACKET_SCHEMA_INVALID", model=model)
    if not _valid_packet_payload(payload):
        return _result("PACKET_SCHEMA_INVALID", model=model)
    labels = _secret_labels(text)
    if labels:
        return _result("PACKET_SECRET_BLOCKED", model=model, findings=labels)
    if output is not None:
        output = _validated_output(output, sidecar)
        if output is None:
            return _result("OUTPUT_PATH_BLOCKED", model=model)

    resolved = resolve_executable(executable)
    if not resolved:
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, model=model, failure_class="EXECUTABLE_UNAVAILABLE"
        )
    try:
        with tempfile.TemporaryDirectory(prefix="x9-opencode-") as temporary:
            sandbox = Path(temporary).resolve()
            sandbox_packet = sandbox / "packet.json"
            sandbox_packet.write_bytes(packet.read_bytes())
            (sandbox / "opencode.json").write_text(
                json.dumps(
                    TOOLS_DENIED_CONFIG,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            command = [
                resolved,
                "run",
                "--pure",
                "--model",
                model,
                "--dir",
                str(sandbox),
                "--file",
                str(sandbox_packet),
                "--title",
                f"X9 bounded review {model}",
                DEFAULT_PROMPT,
            ]
            process = subprocess.run(
                command,
                cwd=sandbox,
                env=_safe_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=max(1, timeout),
            )
    except (FileNotFoundError, PermissionError):
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, model=model, failure_class="EXECUTABLE_UNAVAILABLE"
        )
    except subprocess.TimeoutExpired:
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, model=model, failure_class="TIMEOUT"
        )

    if process.returncode:
        return _result(
            "TOOL_UNAVAILABLE",
            attempts=1,
            model=model,
            failure_class=_failure_class(process.stderr, process.stdout),
            exit_code=process.returncode,
        )

    response = process.stdout.strip()
    if output is not None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=sidecar,
                prefix=f".{output.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(response + "\n")
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, output)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
    return _result(
        "PASS",
        attempts=1,
        model=model,
        output_path=str(output) if output else None,
        output_sha256=__import__("hashlib").sha256(response.encode("utf-8")).hexdigest(),
    )

def doctor(*, executable: str = "opencode", timeout: int = 20) -> dict[str, Any]:
    resolved = resolve_executable(executable)
    if not resolved:
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, available_models=[], failure_class="EXECUTABLE_UNAVAILABLE"
        )
    try:
        with tempfile.TemporaryDirectory(
            prefix="x9-opencode-doctor-"
        ) as temporary:
            process = subprocess.run(
                [resolved, "--pure", "models"],
                cwd=temporary,
                env=_safe_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=max(1, timeout),
            )
    except (FileNotFoundError, PermissionError):
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, available_models=[], failure_class="EXECUTABLE_UNAVAILABLE"
        )
    except subprocess.TimeoutExpired:
        return _result(
            "TOOL_UNAVAILABLE", attempts=1, available_models=[], failure_class="TIMEOUT"
        )

    output = f"{process.stdout}\n{process.stderr}"
    available = sorted(model for model in MODELS if model in output)
    if process.returncode or len(available) != len(MODELS):
        return _result(
            "TOOL_UNAVAILABLE",
            attempts=1,
            available_models=available,
            missing_models=sorted(MODELS - set(available)),
            failure_class=(
                _failure_class(process.stderr, process.stdout)
                if process.returncode
                else "MODEL_NOT_CONFIGURED"
            ),
        )
    return _result("PASS", attempts=1, available_models=available)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Secret-safe one-shot OpenCode sidecar")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("doctor", help="Check configured sidecar models once")
    check.add_argument("--executable", default="opencode")
    check.add_argument("--timeout", type=int, default=20)

    request = sub.add_parser("request", help="Run one bounded model request")
    request.add_argument("--packet", required=True, type=Path)
    request.add_argument("--repo", required=True, type=Path)
    request.add_argument("--model", required=True, choices=sorted(MODELS))
    request.add_argument("--output", type=Path)
    request.add_argument("--executable", default="opencode")
    request.add_argument("--timeout", type=int, default=120)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "doctor":
        result = doctor(executable=args.executable, timeout=args.timeout)
    else:
        result = run_request(
            packet=args.packet,
            model=args.model,
            repo=args.repo,
            timeout=args.timeout,
            executable=args.executable,
            output=args.output,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
