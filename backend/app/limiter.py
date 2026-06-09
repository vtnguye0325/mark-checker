from __future__ import annotations

import os

from slowapi import Limiter
from starlette.requests import Request


def _client_ip(request: Request) -> str:
    """Resolve the real client IP for rate-limiting, honoring nginx's forwarded header.

    Behind the nginx proxy, ``request.client.host`` is the proxy's container IP, so
    ``get_remote_address`` would put every user in one shared bucket. nginx sets
    ``X-Forwarded-For`` via ``proxy_add_x_forwarded_for``, which appends the real
    socket peer ($remote_addr) as the LAST entry. Any earlier entries are
    client-supplied and therefore spoofable, so we trust the rightmost one.

    Assumes a single trusted proxy hop (the bundled nginx). If more proxies are
    added in front (e.g. a cloud load balancer), adjust the hop count here.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    client = request.client
    return client.host if client else "127.0.0.1"


# Per-IP limits. /analyze spends money on a paid LLM, so it is throttled harder
# than the local-inference endpoints. Both are env-overridable for deployment.
DEFAULT_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
ANALYZE_LIMIT = os.getenv("RATE_LIMIT_ANALYZE", "20/hour")

limiter = Limiter(key_func=_client_ip, default_limits=[DEFAULT_LIMIT])
