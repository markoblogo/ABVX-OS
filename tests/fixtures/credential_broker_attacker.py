"""Separate same-UID process for broker interface probes; synthetic data only."""
import json
import os
import socket
import sys
from pathlib import Path

home = Path(sys.argv[1])
capability = sys.argv[2]
socket_path = str(home / "broker.sock")

def call(payload):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            client.connect(socket_path)
            client.sendall(json.dumps(payload).encode() + b"\n")
            answer = json.loads(client.makefile("rb").readline())
        return bool(answer.get("ok"))
    except Exception:
        return False

base = {"action": "execute", "capability_id": capability, "purpose": "translation-qa", "input": "synthetic"}
out = {
    "same_uid": os.getuid(),
    "direct_socket_pending": call({"action": "request", "project": "jekyll-toki-pona", "purpose": "translation-qa", "input": "synthetic"}),
    "raw_get": call({"action": "get", "credential_id": "openai.synthetic"}),
    "unsupported": call({"action": "export_secret"}),
    "context_reuse": call({**base, "purpose": "other"}),
    "path_traversal": call({**base, "capability_id": "../requests/anything"}),
    "arbitrary_url": call({**base, "url": "https://example.invalid"}),
    "arbitrary_header": call({**base, "headers": {"Authorization": "Bearer synthetic"}}),
    "environment_dump": call({"action": "dump_env"}),
    "shell_command": call({"action": "exec", "command": "id"}),
    "state_readable": bool((home / "capabilities" / f"{capability}.json").read_text()),
}
cap_path = home / "capabilities" / f"{capability}.json"
original = cap_path.read_text()
try:
    tampered = json.loads(original)
    tampered["model"] = "attacker-model"
    cap_path.write_text(json.dumps(tampered))
    out["tampered_capability_execute"] = call(base)
    out["state_mutable"] = True
finally:
    cap_path.write_text(original)
print(json.dumps(out, sort_keys=True))
