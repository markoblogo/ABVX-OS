"""Read-only Docker storage receipt; no start, prune, run, inspect env or changes."""
import json
from pathlib import Path
import subprocess
import time
from .mac_operator import STATE, save


def error_kind(stderr):
    text = stderr.lower()
    if 'permission denied' in text or 'operation not permitted' in text:
        return 'PERMISSION_DENIED'
    if 'cannot connect' in text or 'is the docker daemon running' in text or 'connection refused' in text or 'is docker desktop running' in text:
        return 'ENGINE_UNREACHABLE'
    if 'no such file or directory' in text:
        return 'SOCKET_OR_COMMAND_MISSING'
    return 'DOCKER_ACCESS_OR_ENGINE_ERROR'


def collect():
    result = {'schema_version': 'v1', 'time': time.time(), 'mode': 'READ_ONLY',
              'commands': {}, 'status': 'COMPLETE'}
    specs = {'context': ['docker', 'context', 'show'],
             'usage': ['docker', 'system', 'df', '-v'],
             'containers': ['docker', 'ps', '-a', '--format', '{{.Names}}\t{{.Status}}\t{{.Image}}']}
    for key, command in specs.items():
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=20)
            result['commands'][key] = {'code': p.returncode, 'stdout': p.stdout[:80000],
                'error': error_kind(p.stderr) if p.returncode else None,
                'truncated': len(p.stdout) > 80000}
            if p.returncode or len(p.stdout) > 80000:
                result['status'] = 'PARTIAL_OR_BLOCKED'
        except (OSError, subprocess.TimeoutExpired) as exc:
            result['commands'][key] = {'error': type(exc).__name__}
            result['status'] = 'PARTIAL_OR_BLOCKED'
    disk = Path.home() / 'Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw'
    if disk.exists() and not disk.is_symlink():
        st = disk.stat()
        result['host_disk'] = {'allocated_bytes': st.st_blocks*512, 'logical_bytes': st.st_size}
    result['note'] = 'Engine sizes and host APFS allocations are different. No reclaimable byte guarantee.'
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    save(STATE / 'docker-storage-report.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(collect(), ensure_ascii=False, indent=2))
