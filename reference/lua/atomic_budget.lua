-- UPA-1.2 Reference Implementation
-- Atomic Hierarchical Budget Deduction Engine (Section 6.2)
-- TC-003 Conformance: Hierarchical Concurrency Stress Isolation
--
-- Usage: EVAL atomic_budget.lua 3 AGENT_KEY MANAGER_KEY GLOBAL_KEY AMOUNT
--
-- KEYS[1] = {enterprise_prefix}:mandate:agent:{agent_id}
-- KEYS[2] = {enterprise_prefix}:mandate:manager:{manager_id}
-- KEYS[3] = {enterprise_prefix}:mandate:global:ceiling
-- ARGV[1] = requested_amount (integer, in smallest currency unit e.g. cents)
--
-- Returns:
--   1  = ALLOCATION_SUCCESS - all three levels decremented atomically
--   0  = ALLOCATION_REJECTED - one or more levels would go negative
--  -1  = CONTEXT_FAILURE - one or more mandate keys not found

local agent_bal       = tonumber(redis.call('get', KEYS[1]))
local manager_pool    = tonumber(redis.call('get', KEYS[2]))
local global_ceiling  = tonumber(redis.call('get', KEYS[3]))
local requested       = tonumber(ARGV[1])

-- Validate all mandate contexts exist
if not agent_bal or not manager_pool or not global_ceiling then
  return -1  -- CONTEXT_FAILURE: mandate reference missing
end

-- Atomic compare-and-swap: all three must have sufficient balance
if agent_bal      >= requested and
   manager_pool   >= requested and
   global_ceiling >= requested
then
  redis.call('decrby', KEYS[1], requested)  -- agent level
  redis.call('decrby', KEYS[2], requested)  -- manager fleet pool
  redis.call('decrby', KEYS[3], requested)  -- global corporate ceiling
  return 1  -- ALLOCATION_SUCCESS
else
  return 0  -- ALLOCATION_REJECTED: boundary exceeded
end
