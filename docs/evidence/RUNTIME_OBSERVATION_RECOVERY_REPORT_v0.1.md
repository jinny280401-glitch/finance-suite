# Runtime Observation Recovery Report v0.1

**Date:** 2026-08-10  
**Authority:** Task Card A — CC, Architecture / Runtime Boundary Owner  
**Window:** OPEN — Diagnostic Only  
**Scope:** SSH connection recovery, runtime observation entry recovery, evidence-collection chain confirmation  

---

## Status

```text
[ ] RESTORED (direct path)
[x] RESTORED (observation capability via alternate path)
[ ] NOT RESTORED
[ ] ROOT CAUSE UNKNOWN
```

**Verdict:** Runtime observation capability is **available** via the jumpbox path. The direct SSH path from the operator workstation remains blocked upstream of the production host. No code, governance, provider, or capability state was changed.

---

## Current Evidence

### Network Layer

```text
Target:   119.28.156.125:22 (production web source, Tencent Cloud Lighthouse Seoul)
TCP 22:   REACHABLE — nc -vz succeeded
Direct SSH (212.107.28.53 → 119.28.156.125):
          FAIL at kex_exchange_identification: Connection closed by remote host
Jumpbox SSH (8.138.2.55 → 119.28.156.125):
          SUCCESS — publickey auth, session established
```

### SSH Daemon

```text
systemctl status ssh: active (running) since 2026-08-05 16:27:57 CST
sshd:     OpenSSH_9.6p1 Ubuntu-3ubuntu13.14
Listener: 0.0.0.0:22, [::]:22
Active sessions: 2
```

### fail2ban

```text
Jail sshd:
  Currently failed: 0
  Total failed:     6953
  Currently banned: 0
  Total banned:     122
  Banned IP list:   (empty)
```

fail2ban is **not** currently banning the operator IP. Logs show continuous global brute-force attempts but no active ban.

### Host Firewall

```text
ufw:      inactive
iptables: INPUT policy ACCEPT → jumps to YJ-FIREWALL-INPUT
YJ-FIREWALL-INPUT: 465 REJECT rules (single /32 sources)
Operator IP 212.107.28.53: NOT present in any iptables table (filter/nat/mangle/raw/security)
ip6tables: empty
```

### TCP Wrappers

```text
/etc/hosts.allow:  no sshd restrictions
/etc/hosts.deny:   no sshd restrictions (ALL PARANOID commented out)
```

### sshd Configuration

```text
Effective values (sshd -T):
  logingracetime      120
  maxauthtries        6
  maxsessions         10
  clientaliveinterval 0
  clientalivecountmax 3
  permitrootlogin     no
  passwordauthentication yes
  maxstartups         50:30:200
  persourcemaxstartups 30
```

MaxStartups is not the constraint (50:30:200, load 0.04, only 2 active SSH sessions).

---

## Root Cause Analysis

### What is NOT the cause

| Candidate | Finding |
|---|---|
| sshd down | Active and listening |
| fail2ban active ban | 0 currently banned; operator IP not in jail |
| Host firewall (iptables/ufw) | ufw inactive; operator IP absent from all tables |
| TCP wrappers | No sshd restrictions |
| MaxStartups limit | 50:30:200 with low load |
| Authentication failure | Handshake fails before version exchange |

### What IS the cause

The direct SSH connection from operator workstation `212.107.28.53` is dropped **after TCP handshake but before SSH version exchange**. Because:

1. TCP 22 is reachable (`nc` succeeds).
2. sshd logs show no entry for `212.107.28.53` during direct attempts.
3. No host-level firewall rule matches the operator IP.
4. The same target accepts SSH from jumpbox `8.138.2.55`.

**Conclusion:** An upstream network control (Tencent Cloud security group / ACL / DDoS protection / IPS) is dropping or resetting SSH handshakes from the operator IP range. The block is **outside the production host**, not on the host itself.

---

## Recovery Action Taken

**No production configuration was changed.**

The runtime observation path was restored by routing through the known trusted jumpbox:

```text
Operator Workstation
        ↓  SSH (fails at kex_exchange_identification)
119.28.156.125:22

Operator Workstation
        ↓  SSH (success)
8.138.2.55 (jumpbox)
        ↓  SSH via ProxyCommand (success)
119.28.156.125:22
```

Validated observation commands executed through the recovered path:

```text
whoami    → ubuntu
hostname  → VM-0-4-ubuntu
pwd       → /home/ubuntu
runtime   → uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
            (working directory /home/ubuntu/finance-suite-web)
nginx     → proxy_pass to backend for touziagent.com / www.touziagent.com / api.touziagent.com
```

---

## Explicitly NOT Done

```text
❌ Modified Trust Gate rules
❌ Modified Evidence Governance
❌ Deployed business code
❌ Modified Provider
❌ Claimed Validation PASS
❌ Claimed Production Capability
```

---

## Claim Boundary

This report establishes only:

```text
"Runtime observation path to 119.28.156.125 is available via 8.138.2.55 jumpbox."
```

It does **not** establish:

```text
"Direct SSH from operator workstation is restored."
"Trust Gate is validated."
"Any production capability is proven."
```

---

## Recommended Next Steps

1. **For continued diagnostics:** Use the jumpbox route as the stable observation path.
2. **For direct-path restoration:** Investigate Tencent Cloud console security group / ACL / DDoS protection rules for source IP `212.107.28.53` toward `119.28.156.125:22`.
3. **For Trust Gate window:** The recovered path satisfies the P0 observability prerequisite. P1a Baseline Identity and P1b Production Artifact Reconciliation may now proceed via the jumpbox route, subject to separate authorization.

---

**Reported by:** Claude Code (Architecture / Runtime Boundary Owner)  
**Window status:** Diagnostic task complete; no capability upgrade
