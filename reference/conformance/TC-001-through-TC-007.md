# UPA-1.2 Conformance Test Definitions

A platform claims **UPA-1.2 Conformance** only after passing all seven tests.
Run against the reference implementation in this repository.

---

## TC-001: Cryptographic KYA Validation

**Target:** Section 4 KYA lifecycle  
**Pass Condition:**  
The harness ingests an Ed25519 signature payload combined with a simulated TEE
attestation block. The gateway must validate the signature, verify the identity
manifest against:

```
Manifest_identity = SHA-256(AgentInstanceID || ParentPrincipalID || RootSystemPromptString || Timestamp)
```

and confirm the exchange completes within **5 milliseconds** with zero state leakage.

---

## TC-002: Intent Transformation Compliance

**Target:** Section 5.1 Fiduciary Translation Engine  
**Pass Condition:**  
Input: unstructured text (`"Pay the monthly SaaS fee for cloud analytics"`).  
The engine must cross-reference the internal whitelist, map to ISO 20022
purpose code `COMP`, and output a structurally valid pacs.008 XML payload.  
On duplicate LEI input, must return `AMBIGUOUS_VENDOR_MATCH` and route to
human review — must NOT fail open.

---

## TC-003: Hierarchical Concurrency Stress Isolation

**Target:** Section 6.1-6.2 Atomic CAS engine  
**Pass Condition:**  
Fire **10,000 concurrent overlapping transaction requests** within a **10ms window**.  
All keys must use Redis Hash Tags (`{enterprise_prefix}`) to guarantee
single-shard execution.  
Result: zero budget balance leakage, zero shard routing errors.  
Reference: `python/hierarchy_deduction.py` + `lua/atomic_budget.lua`

---

## TC-004: Emergency Disruption Cascading

**Target:** Section 7.1 Kill-Switch  
**Pass Condition:**  
Fire global freeze injunction mid-execution.  
Consumer group acknowledgment must invalidate all active tokens:
- **Regional deployment:** ≤ 5 milliseconds
- **Multi-region (e.g. Mumbai → Frankfurt):** ≤ 180 milliseconds

Reference: `kill_switch/durable_freeze.py`

---

## TC-005: Overlapping JWKS Lifecycle Rotation

**Target:** Section 4.3 JWKS Management  
**Pass Condition:**  
Execute active transactions while simultaneously rotating public keys.  
Gateway must maintain both prior and rotated keys via `kid` matching per
RFC 7517 for a minimum **24-hour overlap window** without stalling
in-flight transactions.

---

## TC-006: Adversarial Token Replay Resilience

**Target:** Section 9.1 Graph Traversal + Section 4.1 KYA  
**Pass Condition:**  
Inject a previously captured valid transaction token (replay attack).  
The Fiduciary Perimeter must detect the invalid nonce and block within **5ms**.  
Also inject a circular delegation chain (A → B → C → A).  
The graph cycle detector must throw a hard stop and demand
human re-authentication.

---

## TC-007: Malformed Gas Oracle Response Handling

**Target:** Section 5.3 On-Chain Gas Retry  
**Pass Condition:**  
Feed corrupted / delayed / null response from the gas oracle.  
System must:
1. Skip direct broadcast
2. Enter exponential backoff queue (max 4 retries, 300s ceiling)
3. On timeout: hard circuit stop, unlock budget state,
   flush `GAS_THRESHOLD_EXCEEDED` to metrics registry

Must NOT fail open under any oracle failure mode.

---

## Running the Tests

```bash
# Install dependencies
pip install redis pytest

# Start a local Redis instance
redis-server

# Run reference implementation smoke tests
cd reference/
python python/hierarchy_deduction.py   # TC-003 smoke test
python kill_switch/durable_freeze.py   # TC-004 smoke test
```

Full automated harness: forthcoming in `conformance/harness/` (UPA-1.2 RELEASE milestone).
