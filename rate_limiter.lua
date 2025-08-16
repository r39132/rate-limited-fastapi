-- Token Bucket with Retry-After support
--
-- KEYS[1] - bucket key
-- ARGV[1] - capacity (int)
-- ARGV[2] - refill rate (tokens per second, may be fractional)
-- ARGV[3] - now (milliseconds)
-- ARGV[4] - requested tokens (int)
--
-- Returns (in this order to preserve existing Python tuple unpacking):
-- 1) allowed (1/0)
-- 2) remaining tokens after evaluation (may be fractional)
-- 3) retry_after (seconds; 0 if allowed; -1 means "cannot ever be satisfied")
--
-- NOTE: We return tokens as the second value (rather than after retry_after)
-- to keep compatibility with existing Python code that unpacked as:
-- allowed, tokens_after, retry = ...

local capacity     = tonumber(ARGV[1])
local refill_rate  = tonumber(ARGV[2])
local now_ms       = tonumber(ARGV[3])
local requested    = tonumber(ARGV[4])

local bucket       = redis.call("HMGET", KEYS[1], "tokens", "timestamp")
local tokens       = tonumber(bucket[1])
local last_refill  = tonumber(bucket[2])

if tokens == nil then
  tokens = capacity
  last_refill = now_ms
end

-- Refill
local delta_secs = math.max(0, now_ms - last_refill) / 1000.0
local filled = tokens + (delta_secs * refill_rate)
if filled > capacity then
  filled = capacity
end

local allowed = filled >= requested
local retry_after = 0

if allowed then
  filled = filled - requested
else
  if requested > capacity or refill_rate <= 0 then
    retry_after = -1
  else
    local deficit = requested - filled
    retry_after = math.ceil(deficit / refill_rate)
  end
end

-- Persist
redis.call("HMSET", KEYS[1], "tokens", filled, "timestamp", now_ms)
-- Optional: expire after one full refill horizon (capacity / rate)
if refill_rate > 0 then
  local ttl = math.ceil(capacity / refill_rate)
  redis.call("EXPIRE", KEYS[1], ttl)
end

return { allowed and 1 or 0, filled, retry_after }
