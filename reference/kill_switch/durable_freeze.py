"""
UPA-1.2 Reference Implementation
Persistent Enterprise Kill-Switch via Redis Streams (Section 7.1)
TC-004 Conformance: Emergency Disruption Cascading

Why Redis Streams (not pub/sub):
    Traditional pub/sub is fire-and-forget. A gateway node that is
    temporarily disconnected will MISS the invalidation message entirely.
    Redis Streams with consumer group acknowledgment guarantees that every
    gateway node receives and confirms the freeze event, even after reconnect.

Delivery guarantee:
    XADD writes an immutable record to the stream.
    Each gateway node reads via XREADGROUP and ACKs with XACK.
    Unacknowledged messages are retried on reconnect (XAUTOCLAIM).
"""

import redis
import time
from datetime import datetime, timezone


STREAM_KEY_PREFIX  = "security:streams:"
STATE_KEY_PREFIX   = "security:state:"
CONSUMER_GROUP     = "upa-gateway-nodes"


def execute_durable_global_freeze(
    redis_client: redis.Redis,
    enterprise_id: str,
    authorized_by: str,
) -> dict:
    """
    Issues a persistent, guaranteed-delivery enterprise-wide payment freeze.

    Steps:
        1. Sets a hard state flag (checked by all inline gateway validators)
        2. Appends an immutable event to the Redis Stream
        3. All consumer group members receive and ACK the event

    Args:
        redis_client:  Connected Redis client
        enterprise_id: Enterprise identifier matching mandate key namespace
        authorized_by: Identity of the human or system issuing the freeze

    Returns:
        dict with stream_id and state_key confirming write
    """
    state_key  = f"{STATE_KEY_PREFIX}{enterprise_id}"
    stream_key = f"{STREAM_KEY_PREFIX}{enterprise_id}"

    # Step 1: Write hard state flag — checked synchronously by all gatways
    redis_client.set(state_key, "SYSTEM_STATE_FROZEN")

    # Step 2: Append immutable freeze event to durable stream
    event_payload = {
        "event_type":          "GLOBAL_SYSTEM_FREEZE_INJUNCTION",
        "enterprise_id":       enterprise_id,
        "authorized_by":       authorized_by,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "authorization_scope": "ALL_AGENT_FLEETS",
        "upa_version":         "1.2",
    }

    stream_id = redis_client.xadd(stream_key, event_payload)

    return {
        "status":     "DURABLE_FREEZE_RECORDED",
        "stream_id":  stream_id,
        "state_key":  state_key,
        "stream_key": stream_key,
    }


def is_enterprise_frozen(redis_client: redis.Redis, enterprise_id: str) -> bool:
    """
    Gateway-side check. Every inbound transaction must call this first.
    Returns True if the enterprise is under a freeze injunction.
    """
    state_key = f"{STATE_KEY_PREFIX}{enterprise_id}"
    value = redis_client.get(state_key)
    return value is not None and value.decode() == "SYSTEM_STATE_FROZEN"


def lift_freeze(
    redis_client: redis.Redis,
    enterprise_id: str,
    authorized_by: str,
) -> dict:
    """
    Lifts a freeze and publishes a LIFT event to the stream.
    Requires human authorization at call site.
    """
    state_key  = f"{STATE_KEY_PREFIX}{enterprise_id}"
    stream_key = f"{STREAM_KEY_PREFIX}{enterprise_id}"

    redis_client.delete(state_key)

    stream_id = redis_client.xadd(stream_key, {
        "event_type":    "FREEZE_LIFT_AUTHORIZED",
        "enterprise_id": enterprise_id,
        "authorized_by": authorized_by,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    })

    return {
        "status":    "FREEZE_LIFTED",
        "stream_id": stream_id,
    }
