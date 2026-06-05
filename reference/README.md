# Universal Payment Agent (UPA-1.2) — Reference Implementation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2--RELEASE-green.svg)]()
[![Standard](https://img.shields.io/badge/standard-UPA--1.2-orange.svg)]()

---

## What Is UPA?

The **Universal Payment Agent (UPA)** standard defines an open, platform-agnostic framework for secure machine-to-machine commerce. It specifies the cryptographic identity, deterministic enforcement, and multi-rail settlement architecture required for autonomous AI agents to move enterprise money safely.

UPA solves a specific architectural problem: **the gap between probabilistic AI reasoning and deterministic financial execution.** Without a protocol layer between them, autonomous agents that spend company money have no enforceable mandate boundary, no immutable audit trail, and no kill-switch.

UPA provides all three.

---

## The Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│  1. COGNITIVE RUNTIME LAYER  (Probabilistic)            │
│     LLM orchestrators, multi-agent chains               │
│     Intent formulation, semantic tool calling           │
└──────────────────────────┬──────────────────────────────┘
                           │ Payment Intent
                           ▼
┌─────────────────────────────────────────────────────────┐
│  2. FIDUCIARY PERIMETER LAYER  (Deterministic)          │
│     Cryptographic agent identity (KYA)                  │
│     Atomic CAS budget enforcement                       │
│     Mandate hierarchy validation                        │
│     Jurisdiction-aware policy routing                   │
└──────────────────────────┬──────────────────────────────┘
                           │ Approved Payload
                           ▼
┌─────────────────────────────────────────────────────────┐
│  3. SETTLEMENT INTERFACE LAYER  (Structured Message)    │
│     ISO 20022 pacs.008 compilation                      │
│     On-chain stablecoin gas-retry                       │
│     camt.056 counter-transaction recovery               │
└─────────────────────────────────────────────────────────┘
```

**Key principle:** The Cognitive Layer is treated as untrusted. Every payment intent is stripped of prose and evaluated against an unalterable, machine-readable ledger of authority before any money moves.

---

## This Repository

This is the official reference implementation for **UPA-1.2-RELEASE** (June 2026).

| File | Purpose | Conformance Test |
|---|---|---|
| `lua/atomic_budget.lua` | Atomic multi-key CAS budget deduction | TC-003 |
| `python/hierarchy_deduction.py` | Python wrapper + Redis hash tag key builder | TC-003 |
| `kill_switch/durable_freeze.py` | Persistent Redis Stream enterprise kill-switch | TC-004 |
| `conformance/TC-001-through-TC-007.md` | Full conformance test definitions | All |

---

## Quick Start

### Prerequisites

```bash
pip install redis
redis-server   # local Redis instance for testing
```

### Test the Atomic Budget Engine (TC-003)

```python
import redis
from python.hierarchy_deduction import evaluate_and_deduct_hierarchy_atomic

r = redis.Redis(host="localhost", port=6379, db=0)

# Initialise mandate balances (in cents)
prefix = "enterprise_101"
r.set(f"{{{prefix}}}:mandate:agent:agent_A",     500_000)   # $5,000
r.set(f"{{{prefix}}}:mandate:manager:mgr_1",   2_000_000)   # $20,000
r.set(f"{{{prefix}}}:mandate:global:ceiling", 10_000_000)   # $100,000

# Attempt a $840.00 payment
result = evaluate_and_deduct_hierarchy_atomic(
    redis_client=r,
    enterprise_prefix=prefix,
    agent_id="agent_A",
    manager_id="mgr_1",
    amount_in_cents=84_000,
)
print(result)   # ALLOCATION_SUCCESS
```

### Test the Kill-Switch (TC-004)

```python
import redis
from kill_switch.durable_freeze import execute_durable_global_freeze, is_enterprise_frozen

r = redis.Redis(host="localhost", port=6379, db=0)

# Issue freeze
result = execute_durable_global_freeze(r, "enterprise_101", "CFO-override")
print(result["status"])   # DURABLE_FREEZE_RECORDED

# Gateway check — every inbound transaction calls this first
frozen = is_enterprise_frozen(r, "enterprise_101")
print(frozen)   # True — all payments blocked
```

---

## Conformance

A platform can claim **UPA-1.2 Conformance** only after passing TC-001 through TC-007.

See [`conformance/TC-001-through-TC-007.md`](conformance/TC-001-through-TC-007.md) for full test definitions and pass conditions.

Summary:

| Test | What It Verifies | SLA |
|---|---|---|
| TC-001 | KYA cryptographic identity + TEE attestation | ≤ 5ms |
| TC-002 | Intent → ISO 20022 transformation, ERP conflict handling | — |
| TC-003 | 10,000 concurrent requests, zero budget leakage | 10ms window |
| TC-004 | Kill-switch cascade, durable delivery | ≤ 5ms regional / ≤ 180ms global |
| TC-005 | JWKS key rotation, 24-hour overlap window | — |
| TC-006 | Adversarial token replay + circular delegation detection | ≤ 5ms |
| TC-007 | Malformed gas oracle, fail-secure circuit stop | — |

---

## Scope

**UPA-1.x (this repository):** Enterprise and institutional principals — B2B treasury, procurement, programmatic AP.

**UPA-2.x (planned):** SME principals — lightweight JSON whitelist model, non-ERP deployments.

**UPA-3.x (planned):** Consumer and retail agent implementations — individual biometric attestation, retail banking rails.

---

## Related

- **JSON Schema definitions:** [schemas.upa-standard.org](https://schemas.upa-standard.org)
- **Lightweight whitelist schema:** [schemas.upa-standard.org/v1/lightweight-whitelist.json](https://schemas.upa-standard.org/v1/lightweight-whitelist.json)
- **Full specification document:** UPA-1.2-RELEASE (June 2026), available from the Fintech Architecture Working Group

---

## Governance

This implementation is maintained under the **UPA Open Community Registry**.

Version increments follow a public RFC process. Contributions, conformance reports, and implementation feedback are welcomed via GitHub Issues.

**Primary Rapporteur / Chair:** Rajesh Johnny  
**Working Group:** Fintech Architecture Working Group  
**Classification:** Public Reference Architecture & Interoperability Specification

---

## License

MIT License — see [LICENSE](LICENSE) for details.

The UPA standard itself is published as an open community specification. This reference implementation is provided to accelerate adoption and conformance testing. It is not a production-hardened deployment; implementers are responsible for security review, load testing, and compliance validation in their environments.
