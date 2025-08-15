
-- Token Bucket in Redis (atomic, hardened)
-- KEYS[1] = bucket key
-- ARGV[1] = capacity (tokens)
-- ARGV[2] = rate tokens/sec (float allowed)
--
-- Returns array:
--   [1] allowed (1 or 0)
--   [2] tokens_after (float)
--   [3] retry_after_ms (int) -- 0 if allowed
--
-- State is stored as hash with fields: 'tokens' (float), 'last_ts' (ms).

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])

if capacity == nil or rate == nil or capacity < 0 or rate <= 0 then
  return {0, 0, 0}
end

-- Server time to avoid client clock skew
local t = redis.call("TIME")
local now_ms = t[1] * 1000 + math.floor(t[2] / 1000)

local data = redis.call("HMGET", key, "tokens", "last_ts")
local tokens = tonumber(data[1])
local last_ts = tonumber(data[2])

if tokens == nil or last_ts == nil then
  tokens = capacity
  last_ts = now_ms
end

local elapsed = now_ms - last_ts
if elapsed < 0 then
  elapsed = 0
end

-- Refill fractionally
local refill = (elapsed * rate) / 1000.0
tokens = math.min(capacity, tokens + refill)
last_ts = now_ms

local allowed = 0
local retry_after_ms = 0
if tokens >= 1.0 then
  allowed = 1
  tokens = tokens - 1.0
else
  -- how long until next token?
  local needed = 1.0 - tokens
  retry_after_ms = math.ceil((needed / rate) * 1000.0)
end

redis.call("HMSET", key, "tokens", tokens, "last_ts", last_ts)
-- expire after time-to-full + small buffer
local ttf_ms = math.ceil(((capacity - tokens) / rate) * 1000.0) + 2000
if ttf_ms < 5000 then ttf_ms = 5000 end
redis.call("PEXPIRE", key, ttf_ms)

return {allowed, tokens, retry_after_ms}
