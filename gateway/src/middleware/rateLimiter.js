'use strict';

const Redis = require('ioredis');

const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/0';

let redis = null;

function getRedis() {
  if (!redis) {
    redis = new Redis(REDIS_URL, {
      maxRetriesPerRequest: 1,
      enableReadyCheck: false,
      lazyConnect: true,
      retryStrategy(times) {
        if (times > 3) return null; // stop retrying
        return Math.min(times * 200, 2000);
      },
    });
    redis.on('error', (err) => {
      console.warn('[RateLimiter] Redis connection error, falling back to in-memory:', err.message);
    });
    redis.connect().catch(() => {});
  }
  return redis;
}

// Simple in-memory fallback when Redis is unavailable
const memoryStore = new Map();

function cleanMemoryStore() {
  const now = Date.now();
  for (const [key, entry] of memoryStore) {
    if (entry.expiresAt <= now) {
      memoryStore.delete(key);
    }
  }
}

// Periodically clean memory store
setInterval(cleanMemoryStore, 60_000).unref();

/**
 * Create a rate limiter middleware.
 *
 * @param {object} options
 * @param {number} options.windowMs  - Time window in milliseconds (default 60000)
 * @param {number} options.max       - Maximum requests per window (default 60)
 * @param {string} options.prefix    - Redis key prefix
 */
function createRateLimiter({ windowMs = 60_000, max = 60, prefix = 'rl:general' } = {}) {
  const windowSec = Math.ceil(windowMs / 1000);

  return async function rateLimiterMiddleware(req, res, next) {
    const identifier = req.user?.id || req.ip || 'anonymous';
    const key = `${prefix}:${identifier}`;

    try {
      const client = getRedis();

      if (client.status === 'ready') {
        // ---- Redis-backed limiting ----
        const multi = client.multi();
        multi.incr(key);
        multi.ttl(key);
        const results = await multi.exec();

        const count = results[0][1];
        const ttl = results[1][1];

        // Set expiry on first request in window
        if (ttl === -1 || count === 1) {
          await client.expire(key, windowSec);
        }

        res.set('X-RateLimit-Limit', String(max));
        res.set('X-RateLimit-Remaining', String(Math.max(0, max - count)));

        if (count > max) {
          const retryAfter = ttl > 0 ? ttl : windowSec;
          res.set('Retry-After', String(retryAfter));
          return res.status(429).json({
            success: false,
            error: {
              code: 'RATE_LIMIT_EXCEEDED',
              message: `Too many requests. Please retry after ${retryAfter} seconds.`,
              retryAfter,
            },
          });
        }

        return next();
      }
    } catch {
      // Redis error - fall through to in-memory
    }

    // ---- In-memory fallback ----
    const now = Date.now();
    let entry = memoryStore.get(key);

    if (!entry || entry.expiresAt <= now) {
      entry = { count: 0, expiresAt: now + windowMs };
      memoryStore.set(key, entry);
    }

    entry.count += 1;

    res.set('X-RateLimit-Limit', String(max));
    res.set('X-RateLimit-Remaining', String(Math.max(0, max - entry.count)));

    if (entry.count > max) {
      const retryAfter = Math.ceil((entry.expiresAt - now) / 1000);
      res.set('Retry-After', String(retryAfter));
      return res.status(429).json({
        success: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: `Too many requests. Please retry after ${retryAfter} seconds.`,
          retryAfter,
        },
      });
    }

    return next();
  };
}

// Pre-built limiters for common route groups
const authLimiter = createRateLimiter({
  windowMs: 60_000,
  max: parseInt(process.env.AUTH_RATE_LIMIT || '5', 10),
  prefix: 'rl:auth',
});

const researchLimiter = createRateLimiter({
  windowMs: 60_000,
  max: parseInt(process.env.RESEARCH_RATE_LIMIT || '20', 10),
  prefix: 'rl:research',
});

const generalLimiter = createRateLimiter({
  windowMs: 60_000,
  max: parseInt(process.env.RATE_LIMIT_PER_MINUTE || '60', 10),
  prefix: 'rl:general',
});

function closeRedis() {
  if (redis) {
    redis.disconnect();
    redis = null;
  }
}

module.exports = {
  createRateLimiter,
  authLimiter,
  researchLimiter,
  generalLimiter,
  closeRedis,
};
