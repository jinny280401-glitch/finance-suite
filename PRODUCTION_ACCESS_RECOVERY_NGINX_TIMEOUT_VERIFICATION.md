# Production Access Recovery — nginx Timeout Read-Only Verification

**Date:** 2026-08-03 (Asia/Shanghai)  
**Mode:** Production access recovery / nginx READ-ONLY  
**Production modification:** None  
**nginx reload or configuration change:** Not executed

## 1. Access Recovery

### Claim

The production change channel was unavailable because direct SSH closed the connection before key exchange.

### Evidence

- A single direct SSH probe established TCP/22 and was then closed before SSH key exchange completed.
- The repository history contained an established, authorized jump-host route to the production host.
- The jump route successfully authenticated with the existing key and executed a read-only `ACCESS_OK` command on production.

### Evidence Gap

- Direct SSH closure was initially attributed to fail2ban, but current production fail2ban status reports `Currently banned: 0` for the SSH jail.
- No current evidence proves that fail2ban caused the direct-path closure. A network ACL, bastion-only policy, or another SSH control remains possible.

### Risk

Treating the direct-path closure as an active fail2ban ban could lead to unnecessary security-control changes.

### Capability Verdict

**PROVEN** — Production command access is restored through the existing authorized jump route. Direct SSH remains unavailable, but it is not required for the recovered change channel.

## 2. Service Health

At `2026-08-03T10:25:48+08:00`:

| Component | Evidence | Verdict |
|---|---|---|
| nginx | systemd state `active` | PROVEN |
| Production FastAPI service | systemd state `active` | PROVEN |
| Backend process | Uvicorn master plus four workers running | PROVEN |
| Static/API public availability | Previously observed live responses; not reclassified by this timeout audit | PARTIAL |

## 3. Effective nginx Timeout

The authoritative effective configuration was read using `sudo nginx -T` without writing or reloading nginx.

Effective `/api/` location:

```nginx
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    add_header Cache-Control "no-store" always;

    proxy_pass         http://backend;
    proxy_http_version 1.1;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_set_header   Upgrade           $http_upgrade;
    proxy_set_header   Connection        $connection_upgrade;
    proxy_read_timeout 120s;
}
```

### Claim

Production `/api/` requests have a 120-second nginx upstream response-header/read timeout.

### Evidence

- `nginx -T` shows `proxy_read_timeout 120s` in the effective `/api/` block.
- The enabled site configuration contains the same 120-second read timeout.
- No explicit `proxy_connect_timeout` or `proxy_send_timeout` is present in this location.

### Evidence Gap

- No approved target timeout value has been supplied for comparison.
- This audit does not claim that 120 seconds is operationally correct or incorrect by itself.

### Risk

Any backend request that does not return response headers within 120 seconds is terminated by nginx even if Uvicorn continues processing.

### Capability Verdict

**PROVEN**

## 4. Backend Timeout Boundary

### Claim

The production FastAPI launch command has no explicit request timeout aligned to nginx's 120-second read timeout.

### Evidence

- The effective systemd `ExecStart` launches Uvicorn with four workers.
- No Uvicorn/Gunicorn request-timeout argument is present in the service command.
- No relevant systemd runtime/start timeout was observed in the service definition output.

### Evidence Gap

- Application-internal provider or coroutine timeouts were outside this read-only nginx scope and were not re-audited.
- Absence of a process-manager timeout does not prove absence of all application-level timeouts.

### Risk

nginx can abandon the client response while backend work continues, creating a client-visible 504 and wasted backend work.

### Capability Verdict

**PARTIALLY PROVEN** — The nginx/Uvicorn process boundary is mismatched; internal application timing remains outside this verification.

## 5. Incident Correlation

Production nginx logs contain two auction-page requests with the following evidence:

| Time | Request | nginx event | HTTP result |
|---|---|---|---|
| 2026-08-03 09:33:10 +08:00 | `POST /api/analyze` from the auction page | `upstream timed out ... while reading response header from upstream` | `504`, response length `578` |
| 2026-08-03 09:35:21 +08:00 | `POST /api/analyze` from the auction page | `upstream timed out ... while reading response header from upstream` | `504`, response length `578` |

The backend journal does not show a completed `POST /api/analyze` response in the correlated window. Other API and page requests completed normally during the same period.

### Claim

nginx, not the frontend or provider, produced the client-visible non-JSON response after its upstream read timeout expired.

### Evidence

- nginx explicitly logged an upstream response-header timeout for the exact auction endpoint and referrer.
- nginx access logging records HTTP `504` for both requests.
- The effective timeout is 120 seconds.
- The production frontend calls `resp.json()` without first validating Content-Type, so an nginx HTML 504 response produces `Unexpected token '<'`.

### Evidence Gap

- The exact original response body and Content-Type were not preserved in a HAR.
- The logs prove nginx generated the 504 boundary; they do not prove which backend/provider operation consumed the 120 seconds.

### Risk

Provider attribution remains unsupported. The proven incident layer is nginx; the slow backend sub-operation remains unclassified.

### Capability Verdict

**PROVEN** — nginx returned the timeout response instead of the expected JSON contract.

## 6. Change Authorization

**nginx Change Authorized:** NO  
**nginx Reload Executed:** NO  
**Python / Auction / Provider / Trust Gate / Frontend Modified:** NO

No timeout value was changed. A future nginx change requires an approved timeout budget and a separate change window.

## Final Verdict

```text
PRODUCTION_ACCESS_RECOVERY_NGINX_TIMEOUT_VERIFICATION
Production Access:
RESTORED VIA AUTHORIZED JUMP ROUTE
Direct SSH Cause:
NOT PROVEN AS FAIL2BAN; CURRENT SSH JAIL HAS ZERO ACTIVE BANS
Effective nginx API Read Timeout:
120 SECONDS
Timeout Mismatch:
PROVEN AT NGINX / UVICORN PROCESS BOUNDARY
Auction HTML Response Layer:
NGINX 504 UPSTREAM TIMEOUT
Evidence Confidence:
HIGH
Production Change Performed:
NO
Next Action:
Submit the 120-second timeout evidence and backend duration trace for approval; do not reload or change nginx until a target timeout budget is authorized.
```
