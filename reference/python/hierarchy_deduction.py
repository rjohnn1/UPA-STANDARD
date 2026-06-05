"""
UPA-1.2 Reference Implementation
Atomic Hierarchical Budget Deduction — Python Wrapper (Section 6.2)
TC-003 Conformance: Hierarchical Concurrency Stress Isolation

Requires:
    pip install redis

Redis Cluster Mandate (Section 6.1):
    All three mandate keys MUST share the same hash slot via Redis Hash Tags.
    The {enterprise_prefix} tag guarantees single-shard execution.
    Without hash tag colocation, multi-key Lua scripts will fail in cluster mode.
"""

import redis

# Load the Lua script once at module level
LUA_ATOMIC_BUDGET = """
local agent_bal      = tonumber(redis.call('get', KEYS[1]))
local manager_pool   = tonumber(redis.call('get', KEYS[2]))
local global_ceiling = tonumber(redis.call('get', KEYS[3]))
local requested      = tonumber(ARGV[1])

if not agent_bal or not manager_pool or not global_ceiling then
    return -1
end

if agent_bal >= requested and manager_pool >= requested and global_ceiling >= requested then
    redis.call('decrby', KEYS[1], requested)
    redis.call('decrby', KEYS[2], requested)
    redis.call('decrby', KEYS[3], requested)
    return 1
else
    return 0
end
"""


def build_mandate_keys(enterprise_prefix: str, agent_id: str, manager_id: str) -> list:
    """
    Constructs Redis hash-tagged mandate keys.
    Hash tags ensure all three keys map to the same cluster shard,
    enabling atomic multi-key Lua execution (Section 6.1).
    """
    tag = f"{{{enterprise_prefix}}}"
    return [
        f"{tag}:mandate:agent:{agent_id}",
        f"{tag}:mandate:manager:{manager_id}",
        f"{tag}:mandate:global:ceiling",
    ]


def evaluate_and_deduct_hierarchy_atomic(
    redis_client: redis.Redis,
    enterprise_prefix: str,
    agent_id: str,
    manager_id: str,
    amount_in_cents: int,
) -> str:
    """
    Executes a single-cycle atomic deduction across the three-level mandate hierarchy.

    Args:
        redis_client:      Connected Redis client (cluster or standalone)
        enterprise_prefix: Shared hash tag prefix (e.g. "enterprise_101")
        agent_id:          Agent-level mandate identifier
        manager_id:        Manager fleet pool identifier
        amount_in_cents:   Transaction amount in smallest currency unit (integer)

    Returns:
        "ALLOCATION_SUCCESS"          — funds deducted across all three levels
        "ALLOCATION_REJECTED"         — one or more levels insufficient
        "CONTEXT_FAILURE"             — mandate key(s) not initialised

    Raises:
        RuntimeError: On Redis connectivity or cluster routing failure
    """
    keys = build_mandate_keys(enterprise_prefix, agent_id, manager_id)

    try:
        result = redis_client.eval(LUA_ATOMIC_BUDGET, 3,
                                   keys[0], keys[1], keys[2],
                                   amount_in_cents)
        if result == 1:
            return "ALLOCATION_SUCCESS"
        elif result == 0:
            return "ALLOCATION_REJECTED"
        elif result == -1:
            return "CONTEXT_FAILURE"
        else:
            raise RuntimeError(f"Unexpected Lua return value: {result}")

    except redis.exceptions.RedisError as e:
        raise RuntimeError(f"Fiduciary atomicity failure: {e}") from e


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    r = redis.Redis(host="localhost", port=6379, db=0)

    # Initialise mandate balances (in cents)
    prefix = "enterprise_101"
    r.set(f"{{{prefix}}}:mandate:agent:agent_A",      500_000)   # $5,000.00
    r.set(f"{{{prefix}}}:mandate:manager:mgr_1",    2_000_000)   # $20,000.00
    r.set(f"{{{prefix}}}:mandate:global:ceiling",  10_000_000)   # $100,000.00

    # Attempt a $840.00 payment
    status = evaluate_and_deduct_hierarchy_atomic(
        redis_client=r,
        enterprise_prefix=prefix,
        agent_id="agent_A",
        manager_id="mgr_1",
        amount_in_cents=84_000,
    )
    print(f"Result: {status}")  # ALLOCATION_SUCCESS
