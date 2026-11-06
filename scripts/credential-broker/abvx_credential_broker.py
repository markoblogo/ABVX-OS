#!/usr/bin/env python3
"""Local, bounded OpenAI Responses broker. No secret retrieval CLI/API exists."""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable

from macos_secitem import SecItemStore

ROOT = Path(__file__).resolve().parent
DEFAULT_HOME = Path.home() / ".abvx" / "credential-broker"
POLICY = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
MODEL = POLICY["openai"]["default_model"]
ALLOWED_MODELS = set(POLICY["openai"]["allowed_models"])
PROJECT = POLICY["project"]
SMOKE_PROJECT = "abvx-credential-broker-smoke"
SMOKE_PURPOSE = "minimal-live-provider-validation"
SMOKE_BUDGET_USD = 0.01
SMOKE_TTL_SECONDS = 15 * 60
SMOKE_MAX_CALLS = 1
SMOKE_MAX_RETRIES = 0
SMOKE_MAX_OUTPUT_TOKENS = 64
SERVICE = "ABVX Credential Broker"
MAX_INPUT_BYTES = POLICY["openai"]["max_input_bytes"]
MAX_RESPONSE_BYTES = 1_000_000
SOCKET_MODE = 0o600
ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")


def checked_id(value: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError("invalid broker identifier")
    return value


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def stamp() -> str:
    return utcnow().isoformat(timespec="seconds")


def secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def write_json(path: Path, value: Any) -> None:
    secure_dir(path.parent)
    temp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)
    os.chmod(path, 0o600)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def append_audit(home: Path, event: dict[str, Any]) -> None:
    secure_dir(home)
    path = home / "audit.jsonl"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(json.dumps({"schema_version": "1.0", "timestamp": stamp(), **event}, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


TOKEN_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(://[^:/\s]+:)[^@/\s]+(@)"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
]


def redact(value: str, secrets: tuple[str, ...] = ()) -> tuple[str, list[str]]:
    events: list[str] = []
    for secret in secrets:
        if secret and secret in value:
            value = value.replace(secret, "[REDACTED]")
            events.append("exact_secret")
    labels = ("authorization_header", "bearer_token", "credential_url", "provider_token_pattern")
    for pattern, label in zip(TOKEN_PATTERNS, labels):
        value, n = pattern.subn(lambda m: (m.group(1) if m.lastindex and m.lastindex >= 2 else "") + "[REDACTED]" + (m.group(2) if m.lastindex and m.lastindex >= 2 else ""), value)
        if n:
            events.append(label)
    return value, events


class Keychain:
    """Broker-internal Security.framework access; no subprocess credential helper."""
    def __init__(self, home: Path | None = None, test_keychain: str | None = None):
        self.store = SecItemStore(SERVICE, test_keychain=test_keychain)

    def _read_for_provider(self, account: str) -> str:
        return self.store._read_for_provider(account)

    def exists(self, account: str) -> bool:
        return self.store.exists(account)


class SanitizedProviderError(RuntimeError):
    def __init__(self, message: str, redaction_events: list[str]):
        super().__init__(message)
        self.redaction_events = redaction_events


class Broker:
    def __init__(self, home: Path, keychain: Any, provider: Callable[[dict[str, Any], str], dict[str, Any]], clock: Callable[[], dt.datetime] = utcnow):
        self.home, self.keychain, self.provider, self.clock = home, keychain, provider, clock
        secure_dir(home)
        self.lock = threading.Lock()

    def _event(self, name: str, **fields: Any) -> None:
        append_audit(self.home, {
            "event": name, "agent": "local-unverified", "request_id": None,
            "approval_id": None, "capability_id": None, "project": PROJECT,
            "credential_id": "openai.primary", "provider": "openai",
            "operation": "responses.create", "execution_class": "A",
            "policy_id": "openai-pilot-v1", "model": None, "request_count": 0,
            "usage": None, "estimated_cost_usd": None,
            "cumulative_run_cost_usd": None, "budget_remaining_usd": None,
            "status": None, "duration_ms": None, "secret_exposed": False,
            "redaction_events": [], "error_class": None, **fields
        })

    def request(self, req: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
        allowed = {"project", "purpose", "input", "max_output_tokens", "model", "budget_usd"}
        smoke = req.get("project") == SMOKE_PROJECT and req.get("purpose") == SMOKE_PURPOSE
        ordinary = req.get("project") == PROJECT and req.get("purpose") in POLICY["openai"]["allowed_purposes"]
        if set(req) - allowed or not (ordinary or smoke) or req.get("model", MODEL) not in ALLOWED_MODELS or not isinstance(req.get("input"), str) or not req["input"].strip() or len(req["input"].encode()) > MAX_INPUT_BYTES:
            self._event("policy_denial", request_id=uuid.uuid4().hex, reason="invalid_request")
            raise ValueError("request denied by schema or project policy")
        tokens = req.get("max_output_tokens", POLICY["openai"]["max_output_tokens_default"])
        if type(tokens) is not int or not 1 <= tokens <= (SMOKE_MAX_OUTPUT_TOKENS if smoke else POLICY["openai"]["max_output_tokens_max"]):
            raise ValueError("request denied by token policy")
        budget = req.get("budget_usd", POLICY["openai"]["default_budget_usd"])
        if type(budget) not in (int, float) or not 0 < budget <= (SMOKE_BUDGET_USD if smoke else POLICY["openai"]["absolute_budget_usd"]):
            raise ValueError("request denied by budget policy")
        rid = uuid.uuid4().hex
        model = req.get("model", MODEL)
        digest_input = {"project": req["project"], "purpose": req["purpose"], "model": model, "max_output_tokens": tokens, "budget_usd": budget}
        record = {"request_id": rid, "project": req["project"], "purpose": req["purpose"], "model": model, "max_output_tokens": tokens, "budget_usd": budget, "identity": identity, "status": "pending", "created_at": self.clock().isoformat(), "scope_digest": hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode()).hexdigest()}
        write_json(self.home / "requests" / f"{rid}.json", record)
        self._event("capability_requested", request_id=rid, project=req["project"], operation="openai.responses.create", caller=identity)
        return {"request_id": rid, "status": "pending_owner_approval"}

    def approve(self, request_id: str, approved: bool, budget_usd: float | None = None) -> dict[str, Any]:
        request_id = checked_id(request_id)
        path = self.home / "requests" / f"{request_id}.json"
        record = read_json(path)
        if not record or record.get("status") != "pending":
            raise ValueError("request is not pending")
        record["status"] = "approved" if approved else "denied"
        cap = None
        if approved:
            smoke = record["project"] == SMOKE_PROJECT and record["purpose"] == SMOKE_PURPOSE
            budget_usd = record["budget_usd"] if budget_usd is None else budget_usd
            if type(budget_usd) not in (int, float) or not 0 < budget_usd <= min(record["budget_usd"], SMOKE_BUDGET_USD if smoke else POLICY["openai"]["absolute_budget_usd"]):
                raise ValueError("approval budget exceeds requested or absolute limit")
            now = self.clock()
            cap = {"capability_id": uuid.uuid4().hex, "approval_id": uuid.uuid4().hex, "request_id": request_id, "scope_digest": record["scope_digest"], "project": record["project"], "credential_id": "openai.primary", "operation": "openai.responses.create", "model": record["model"], "purpose": record["purpose"], "max_output_tokens": record["max_output_tokens"], "budget_usd": float(budget_usd), "absolute_budget_usd": SMOKE_BUDGET_USD if smoke else POLICY["openai"]["absolute_budget_usd"], "warning_fraction": POLICY["openai"]["warning_fraction"], "max_calls": SMOKE_MAX_CALLS if smoke else POLICY["openai"]["max_calls_per_run"], "max_retries": SMOKE_MAX_RETRIES if smoke else POLICY["openai"]["max_retries"], "calls": 0, "spent_usd": 0.0, "reserved_usd": 0.0, "expires_at": (now + dt.timedelta(seconds=SMOKE_TTL_SECONDS if smoke else POLICY["openai"]["capability_ttl_seconds"])).isoformat(), "revoked": False, "identity": record["identity"]}
            write_json(self.home / "capabilities" / f"{cap['capability_id']}.json", cap)
            record["capability_id"] = cap["capability_id"]
        write_json(path, record)
        self._event("capability_approved" if approved else "capability_denied", request_id=request_id, project=record["project"], approval_id=cap["approval_id"] if cap else None, capability_id=cap["capability_id"] if cap else None)
        return {"status": record["status"], "approval_id": cap["approval_id"] if cap else None, "capability_id": cap["capability_id"] if cap else None}

    def revoke(self, capability_id: str) -> None:
        capability_id = checked_id(capability_id)
        p = self.home / "capabilities" / f"{capability_id}.json"
        cap = read_json(p)
        if not cap:
            raise ValueError("unknown capability")
        cap["revoked"] = True
        write_json(p, cap)
        self._event("capability_revoked", capability_id=capability_id, request_id=cap["request_id"])

    def expire(self, capability_id: str) -> None:
        capability_id = checked_id(capability_id)
        p = self.home / "capabilities" / f"{capability_id}.json"
        cap = read_json(p)
        if cap and self.clock() >= dt.datetime.fromisoformat(cap["expires_at"]):
            self._event("capability_expired", capability_id=capability_id, request_id=cap["request_id"])
            raise PermissionError("capability expired")

    def execute(self, capability_id: str, req: dict[str, Any], identity: dict[str, Any] | None = None) -> dict[str, Any]:
        capability_id = checked_id(capability_id)
        identity = identity or {"identity_strength": "not_available"}
        operation_request_id = uuid.uuid4().hex
        with self.lock:
            p = self.home / "capabilities" / f"{capability_id}.json"
            cap = read_json(p)
            if not cap or cap.get("revoked"):
                self._event("policy_denial", request_id=operation_request_id, capability_id=capability_id, reason="missing_or_revoked")
                raise PermissionError("capability unavailable")
            smoke = cap.get("project") == SMOKE_PROJECT and cap.get("purpose") == SMOKE_PURPOSE
            ordinary = cap.get("project") == PROJECT and cap.get("purpose") in POLICY["openai"]["allowed_purposes"]
            if (cap.get("capability_id") != capability_id or not (ordinary or smoke)
                or cap.get("credential_id") != "openai.primary" or cap.get("operation") != "openai.responses.create"
                or cap.get("model") not in ALLOWED_MODELS
                or type(cap.get("budget_usd")) not in (int, float)
                or not 0 < cap["budget_usd"] <= (SMOKE_BUDGET_USD if smoke else POLICY["openai"]["absolute_budget_usd"])
                or type(cap.get("max_calls")) is not int or not 1 <= cap["max_calls"] <= (SMOKE_MAX_CALLS if smoke else POLICY["openai"]["max_calls_per_run"])
                or type(cap.get("max_retries")) is not int or not 0 <= cap["max_retries"] <= (SMOKE_MAX_RETRIES if smoke else POLICY["openai"]["max_retries"])
                or type(cap.get("max_output_tokens")) is not int or not 1 <= cap["max_output_tokens"] <= (SMOKE_MAX_OUTPUT_TOKENS if smoke else POLICY["openai"]["max_output_tokens_max"])
                or (identity.get("os_uid") is not None and identity.get("os_uid") != cap.get("identity", {}).get("os_uid"))):
                self._event("policy_denial", request_id=operation_request_id, capability_id=capability_id, reason="capability_integrity_or_peer_mismatch")
                raise PermissionError("capability scope unavailable")
            if self.clock() >= dt.datetime.fromisoformat(cap["expires_at"]):
                self._event("capability_expired", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id)
                raise PermissionError("capability expired")
            if set(req) - {"input", "max_output_tokens", "purpose"} or not isinstance(req.get("input"), str) or not req["input"].strip() or len(req["input"].encode()) > MAX_INPUT_BYTES or req.get("purpose") != cap["purpose"]:
                self._event("policy_denial", request_id=operation_request_id, capability_id=capability_id, reason="request_scope_mismatch")
                raise ValueError("request denied by capability scope")
            tokens = req.get("max_output_tokens", POLICY["openai"]["max_output_tokens_default"])
            if type(tokens) is not int or not 1 <= tokens <= cap["max_output_tokens"]:
                raise ValueError("request denied by token policy")
            price = read_json(ROOT / "pricing.json")
            model = price.get("models", {}).get(cap["model"])
            if not model or price.get("context_class") != "short" or price.get("service_tier") != "standard":
                self._event("policy_denial", request_id=operation_request_id, capability_id=capability_id, reason="unknown_price")
                raise PermissionError("model pricing unavailable")
            conservative_input_tokens = len(req["input"].encode()) + 512
            estimate = (conservative_input_tokens * model["input_usd_per_million"] + tokens * model["output_usd_per_million"]) / 1_000_000
            if cap["calls"] >= cap["max_calls"] or cap["spent_usd"] + cap["reserved_usd"] + estimate > cap["budget_usd"]:
                self._event("budget_exhausted", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, estimated_cost_usd=estimate)
                raise PermissionError("capability budget exhausted")
            cap["calls"] += 1
            cap["reserved_usd"] += estimate
            write_json(p, cap)
            self._event("operation_started", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, project=cap["project"], credential_id="openai.primary", provider="openai", operation="responses.create", execution_class="A", policy_id="openai-pilot-v1", model=cap["model"], request_count=cap["calls"], caller=identity, status="started")
        try:
            secret = self.keychain._read_for_provider("openai.primary")
        except Exception:
            with self.lock:
                cap = read_json(p)
                cap["reserved_usd"] = max(0.0, cap["reserved_usd"] - estimate)
                write_json(p, cap)
            self._event("operation_failed", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, status="failed", duration_ms=0, error_class="credential_unavailable", redaction_events=[])
            raise RuntimeError("credential unavailable") from None
        result = None
        error = None
        started = time.monotonic()
        attempts = 0
        reserved_total = estimate
        try:
            while attempts <= cap["max_retries"]:
                attempts += 1
                try:
                    result = self.provider({"model": cap["model"], "input": req["input"], "max_output_tokens": tokens, "store": False}, secret)
                    break
                except (TimeoutError, urllib.error.URLError) as e:
                    if attempts > cap["max_retries"]:
                        error = e
                    else:
                        with self.lock:
                            cap = read_json(p)
                            if cap["calls"] >= cap["max_calls"] or cap["spent_usd"] + cap["reserved_usd"] + estimate > min(cap["budget_usd"], cap["absolute_budget_usd"]):
                                error = PermissionError("retry denied by capability budget")
                                break
                            cap["calls"] += 1
                            cap["reserved_usd"] += estimate
                            reserved_total += estimate
                            write_json(p, cap)
                        time.sleep(min(0.05 * (2 ** (attempts - 1)), 0.2))
                except Exception as e:
                    error = e
                    break
        finally:
            pass
        if error is not None or result is None:
            raw = str(error or "provider failure")[:2000]
            safe, redactions = redact(raw, (secret,))
            redactions.extend(getattr(error, "redaction_events", []))
            del secret
            with self.lock:
                cap = read_json(p)
                cap["reserved_usd"] = max(0.0, cap["reserved_usd"] - reserved_total)
                cap["spent_usd"] += estimate * attempts
                write_json(p, cap)
            self._event("operation_failed", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, status="failed", duration_ms=int((time.monotonic() - started) * 1000), error_class=type(error).__name__ if error else "provider_error", redaction_events=redactions, caller=identity)
            if redactions:
                self._event("redaction_event", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, redaction_events=redactions)
            raise RuntimeError(safe)
        output = result.get("output_text", "")
        usage = result.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
        actual = None
        if all(type(n) is int and n >= 0 for n in (input_tokens, output_tokens, cached)) and cached <= input_tokens:
            actual = ((input_tokens - cached) * model["input_usd_per_million"] + cached * model["cached_input_usd_per_million"] + output_tokens * model["output_usd_per_million"]) / 1_000_000
        if actual is None:
            actual = estimate
        safe_output, redactions = redact(str(output)[:MAX_RESPONSE_BYTES], (secret,))
        del secret
        with self.lock:
            cap = read_json(p)
            cap["reserved_usd"] = max(0.0, cap["reserved_usd"] - reserved_total)
            cap["spent_usd"] += actual + estimate * (attempts - 1)
            write_json(p, cap)
        remaining = max(0.0, cap["budget_usd"] - cap["spent_usd"] - cap["reserved_usd"])
        if cap["spent_usd"] >= cap["budget_usd"] * cap["warning_fraction"]:
            self._event("budget_warning", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, cumulative_run_cost_usd=cap["spent_usd"], budget_remaining_usd=remaining)
        if remaining <= 0:
            self._event("budget_exhausted", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, cumulative_run_cost_usd=cap["spent_usd"], budget_remaining_usd=0.0)
        self._event("operation_completed", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, project=cap["project"], credential_id="openai.primary", provider="openai", operation="responses.create", execution_class="A", policy_id="openai-pilot-v1", model=cap["model"], request_count=cap["calls"], usage={"input_tokens": input_tokens, "cached_input_tokens": cached, "output_tokens": output_tokens}, estimated_cost_usd=actual, cumulative_run_cost_usd=cap["spent_usd"], budget_remaining_usd=remaining, status="succeeded", duration_ms=int((time.monotonic() - started) * 1000), redaction_events=redactions, caller=identity)
        if redactions:
            self._event("redaction_event", request_id=operation_request_id, capability_request_id=cap["request_id"], approval_id=cap["approval_id"], capability_id=capability_id, redaction_events=redactions)
        return {"output_text": safe_output, "usage": {"input_tokens": input_tokens, "cached_input_tokens": cached, "output_tokens": output_tokens}, "estimated_cost_usd": actual, "cumulative_run_cost_usd": cap["spent_usd"], "budget_remaining_usd": remaining, "model": cap["model"]}


def openai_provider(payload: dict[str, Any], key: str) -> dict[str, Any]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.openai.com/v1/responses", data=data, method="POST", headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=POLICY["openai"]["timeout_seconds"]) as res:
            raw = res.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as e:
        raw = e.read(8192).decode("utf-8", "replace")
        safe, redactions = redact(raw, (key,))
        raise SanitizedProviderError("provider returned HTTP " + str(e.code) + ": " + safe[:500], redactions) from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("provider response too large")
    obj = json.loads(raw)
    texts = []
    for item in obj.get("output", []):
        if item.get("type") == "message":
            texts.extend(c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text")
    return {"output_text": "".join(texts), "usage": obj.get("usage")}


def peer_identity(conn: socket.socket) -> dict[str, Any]:
    uid = os.getuid()
    pid = None
    try:
        uid, gid = conn.getpeereid()
    except (AttributeError, OSError):
        gid = os.getgid()
    if sys.platform == "darwin":
        try:
            pid = int.from_bytes(conn.getsockopt(0, 2, 4), byteorder=sys.byteorder)
        except OSError:
            pass
    executable = None
    if pid:
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib")
        buf = ctypes.create_string_buffer(4096)
        if libproc.proc_pidpath(pid, buf, len(buf)) > 0:
            executable = os.path.basename(buf.value.decode(errors="replace"))
    return {"os_uid": uid, "os_gid": gid, "pid": pid, "executable": executable, "identity_strength": "same_user_peer" if pid else "same_user_only"}


def make_broker(home: Path) -> Broker:
    return Broker(home, Keychain(home=home), openai_provider)


def serve(home: Path) -> None:
    # This affects only the broker process; it leaves the invoking agent/session untouched.
    safe_env = {name: os.environ[name] for name in ("HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "DEVELOPER_DIR") if name in os.environ}
    os.environ.clear()
    os.environ.update(safe_env)
    secure_dir(home)
    lock_fd = os.open(home / "daemon.lock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sock_path = home / "broker.sock"
    try:
        sock_path.unlink()
    except FileNotFoundError:
        pass
    broker = make_broker(home)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(sock_path))
        os.chmod(sock_path, SOCKET_MODE)
        server.listen(16)
        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    ident = peer_identity(conn)
                    if ident["os_uid"] != os.getuid():
                        raise PermissionError("peer user denied")
                    chunks = bytearray()
                    while b"\n" not in chunks and len(chunks) <= MAX_INPUT_BYTES + 8192:
                        chunk = conn.recv(min(4096, MAX_INPUT_BYTES + 8193 - len(chunks)))
                        if not chunk: break
                        chunks.extend(chunk)
                    raw = bytes(chunks).split(b"\n", 1)[0]
                    if len(raw) > MAX_INPUT_BYTES + 8192:
                        raise ValueError("request too large")
                    req = json.loads(raw)
                    if not isinstance(req, dict):
                        raise ValueError("invalid request")
                    action = req.pop("action", None)
                    if action == "request":
                        result = broker.request(req, ident)
                    elif action == "execute":
                        cid = req.pop("capability_id", None)
                        result = broker.execute(cid, req, ident)
                    else:
                        raise ValueError("unsupported operation")
                    response = {"ok": True, "result": result}
                except Exception as e:
                    response = {"ok": False, "error": str(e)[:500]}
                try:
                    conn.sendall(json.dumps(response).encode() + b"\n")
                except (BrokenPipeError, ConnectionResetError):
                    pass


def client(home: Path, obj: dict[str, Any]) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect(str(home / "broker.sock"))
        s.sendall(json.dumps(obj).encode() + b"\n")
        stream = s.makefile("rb")
        return json.loads(stream.readline(MAX_RESPONSE_BYTES + 8192))


def main() -> int:
    parser = argparse.ArgumentParser(prog="abvx-secrets")
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("ABVX_BROKER_HOME", DEFAULT_HOME)))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve")
    sub.add_parser("list")
    status = sub.add_parser("status"); status.add_argument("credential_id")
    request = sub.add_parser("request"); request.add_argument("--project", required=True); request.add_argument("--purpose", required=True); request.add_argument("--input-file", required=True); request.add_argument("--max-output-tokens", type=int, default=POLICY["openai"]["max_output_tokens_default"]); request.add_argument("--model", default=MODEL); request.add_argument("--budget-usd", type=float, default=POLICY["openai"]["default_budget_usd"])
    approve = sub.add_parser("approve"); approve.add_argument("request_id"); approve.add_argument("--deny", action="store_true"); approve.add_argument("--budget-usd", type=float)
    revoke = sub.add_parser("revoke"); revoke.add_argument("capability_id")
    run = sub.add_parser("run"); run.add_argument("capability_id"); run.add_argument("--purpose", required=True); run.add_argument("--input-file", required=True); run.add_argument("--max-output-tokens", type=int, default=POLICY["openai"]["max_output_tokens_default"])
    sub.add_parser("audit")
    args = parser.parse_args()
    home = args.home
    if args.command == "serve":
        serve(home); return 0
    if args.command == "list":
        try: state = "configured" if Keychain(home=home).exists("openai.primary") else "not_configured"
        except Exception: state = "status_unknown"
        print(json.dumps({"credentials": [{"credential_id": "openai.primary", "provider": "openai", "status": state}]})); return 0
    if args.command == "status":
        if args.credential_id != "openai.primary": parser.error("unknown credential id")
        try: state = "configured" if Keychain(home=home).exists(args.credential_id) else "not_configured"
        except Exception: state = "status_unknown"
        print(json.dumps({"credential_id": args.credential_id, "status": state})); return 0
    if args.command == "approve":
        checked_id(args.request_id)
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            parser.error("owner approval requires an interactive terminal")
        pending = read_json(home / "requests" / f"{args.request_id}.json")
        if not pending or pending.get("status") != "pending": parser.error("request is not pending")
        cap_usd = min(pending["budget_usd"], args.budget_usd if args.budget_usd is not None else pending["budget_usd"])
        caller = pending["identity"]
        answer = input(f"Approve {args.request_id}: {pending['project']}, {pending['purpose']}, {pending['model']}, max {pending['max_output_tokens']} output tokens, ${cap_usd:.2f}, caller uid={caller.get('os_uid')} executable={caller.get('executable') or 'unknown'}, {15 if pending['project'] == SMOKE_PROJECT else 240}min? [y/N] ")
        if args.deny or answer.strip().lower() != "y":
            broker = make_broker(home); print(json.dumps(broker.approve(args.request_id, False))); return 0
        broker = make_broker(home); print(json.dumps(broker.approve(args.request_id, True, cap_usd))); return 0
    if args.command == "revoke":
        make_broker(home).revoke(args.capability_id); return 0
    if args.command == "audit":
        p = home / "audit.jsonl"
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines(): print(line)
        return 0
    if args.command == "request":
        obj = {"action": "request", "project": args.project, "purpose": args.purpose, "input": Path(args.input_file).read_text(encoding="utf-8"), "max_output_tokens": args.max_output_tokens, "model": args.model, "budget_usd": args.budget_usd}
    else:
        obj = {"action": "execute", "capability_id": args.capability_id, "purpose": args.purpose, "input": Path(args.input_file).read_text(encoding="utf-8"), "max_output_tokens": args.max_output_tokens}
    result = client(home, obj)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
