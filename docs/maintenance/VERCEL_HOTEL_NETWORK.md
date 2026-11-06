# Vercel CLI from filtered hotel DNS

Use the existing CLI through this local wrapper from the target project's directory:

```sh
python3 /Volumes/Work/Work/ABVX-OS/scripts/vercel_hotel.py -- project inspect --non-interactive --scope <existing-team-id>
python3 /Volumes/Work/Work/ABVX-OS/scripts/vercel_hotel.py -- <the-authorized-vercel-command-and-arguments>
```

Diagnostic without credentials: `python3 /Volumes/Work/Work/ABVX-OS/scripts/vercel_hotel.py --probe`.

On 2026-10-28 the active hotel DNS returned 198.153.192.51 for api.vercel.com, including queries explicitly addressed to 1.1.1.1. TLS correctly rejected the unrelated certificate. Cloudflare DNS-over-HTTPS reached via its official bootstrap IP returned the current public Vercel address. The wrapped existing CLI then authenticated and inspected abvcreative/abv-xsite successfully from the same network.

The wrapper resolves api.vercel.com afresh using curl, HTTPS, Cloudflare's hostname and normal certificate checks. It accepts only public IPv4 answers for that exact hostname and injects a temporary Node DNS lookup override into that one child CLI process. Other destinations use their existing resolution. No system DNS, hosts file, VPN, proxy, credentials, project configuration or TLS setting is changed. No credentials are sent to the resolver. Nothing is installed. It refuses an environment that disables Node TLS validation and fails closed if secure DNS is unavailable. Temporary loaders are removed when the command finishes; IPs are never a persistent fixed cache.

This is a scoped workaround for incorrect DNS, not permission to ignore certificate errors, disable TLS, modify network policy or expand account access. It does not add a scheduler or alter deployment authority. It supports the existing CLI's API calls; separately filtered upload/storage hosts remain outside its scope and must fail normally. Use a valid network for such hosts rather than broadening this override without evidence.

Verified: unauthenticated API probe with `tlsAuthorized=true`, then authenticated read-only project inspection. No new production deployment is required for this local operator helper. Tests: `python3 -m unittest discover -s tests -p test_vercel_hotel.py`.
