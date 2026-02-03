'use strict';

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';

/**
 * JWT authentication middleware.
 *
 * Usage:
 *   router.get('/secure', authenticate, handler);          // required
 *   router.get('/public', authenticate({ optional: true }), handler); // optional
 */
function authenticate(optionsOrReq, res, next) {
  // If called with (req, res, next) it is used directly as middleware (required mode).
  // If called with an options object it returns a middleware function.
  if (optionsOrReq && typeof optionsOrReq === 'object' && !optionsOrReq.headers) {
    const options = optionsOrReq;
    return function _optionalAuth(req, _res, _next) {
      return _authenticate(req, _res, _next, options);
    };
  }
  return _authenticate(optionsOrReq, res, next, { optional: false });
}

function _authenticate(req, res, next, options = {}) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    if (options.optional) {
      req.user = null;
      return next();
    }
    return res.status(401).json({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Missing or invalid Authorization header. Expected: Bearer <token>',
      },
    });
  }

  const token = authHeader.slice(7); // strip "Bearer "

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = {
      id: decoded.user_id || decoded.sub || decoded.id,
      email: decoded.email || null,
      username: decoded.username || null,
      role: decoded.role || 'user',
      // Keep full decoded payload available
      _token: decoded,
    };
    return next();
  } catch (err) {
    if (options.optional) {
      req.user = null;
      return next();
    }

    const message =
      err.name === 'TokenExpiredError'
        ? 'Token has expired'
        : err.name === 'JsonWebTokenError'
          ? 'Invalid token'
          : 'Authentication failed';

    return res.status(401).json({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message,
      },
    });
  }
}

module.exports = { authenticate };
