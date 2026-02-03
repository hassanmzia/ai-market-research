'use strict';

const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');

/**
 * Create an http-proxy-middleware proxy for a target service.
 *
 * @param {string} target  - Full base URL of the target service, e.g. "http://django-api:8063"
 * @param {object} [options] - Additional proxy options
 * @returns Express middleware
 */
function createProxy(target, options = {}) {
  return createProxyMiddleware({
    target,
    changeOrigin: true,
    // Pass through the original path by default
    pathRewrite: options.pathRewrite || undefined,
    // Forward auth headers
    on: {
      proxyReq: (proxyReq, req) => {
        // Guard: skip if headers were already sent (e.g. error path)
        if (proxyReq.headersSent) return;
        // Forward the original IP so the downstream knows the real client
        proxyReq.setHeader('X-Forwarded-For', req.ip || '127.0.0.1');
        if (req.user) {
          proxyReq.setHeader('X-User-Id', String(req.user.id));
          if (req.user.email) {
            proxyReq.setHeader('X-User-Email', req.user.email);
          }
        }
      },
      proxyRes: (proxyRes, req) => {
        // Add gateway timing header
        proxyRes.headers['X-Gateway'] = 'amr-api-gateway';
      },
      error: (err, req, res) => {
        console.error(`[Proxy] Error proxying ${req.method} ${req.originalUrl}:`, err.message);
        if (!res.headersSent) {
          res.status(502).json({
            success: false,
            error: {
              code: 'BAD_GATEWAY',
              message: 'Upstream service is unavailable',
            },
          });
        }
      },
    },
    ...options,
  });
}

/**
 * Manually forward an HTTP request to a target service using axios.
 * Useful when you need to transform the request/response before forwarding.
 *
 * @param {string} targetUrl - Full base URL, e.g. "http://a2a-orchestrator:7063"
 * @param {string} method    - HTTP method (GET, POST, etc.)
 * @param {string} path      - Path to append, e.g. "/a2a/agents"
 * @param {object} [body]    - Request body (for POST/PUT/PATCH)
 * @param {object} [headers] - Additional headers to forward
 * @returns {Promise<{status: number, data: any, headers: object}>}
 */
async function forwardRequest(targetUrl, method, path, body = null, headers = {}) {
  const url = `${targetUrl.replace(/\/+$/, '')}${path}`;

  // Strip hop-by-hop headers that shouldn't be forwarded
  const forwardHeaders = { ...headers };
  delete forwardHeaders.host;
  delete forwardHeaders.connection;
  delete forwardHeaders['content-length'];
  delete forwardHeaders['transfer-encoding'];

  try {
    const response = await axios({
      method: method.toLowerCase(),
      url,
      data: body,
      headers: {
        'Content-Type': 'application/json',
        ...forwardHeaders,
      },
      timeout: parseInt(process.env.PROXY_TIMEOUT || '30000', 10),
      validateStatus: () => true, // Don't throw on non-2xx
    });

    return {
      status: response.status,
      data: response.data,
      headers: response.headers,
    };
  } catch (err) {
    if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
      return {
        status: 502,
        data: {
          success: false,
          error: {
            code: 'BAD_GATEWAY',
            message: `Upstream service at ${targetUrl} is unavailable`,
          },
        },
        headers: {},
      };
    }
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
      return {
        status: 504,
        data: {
          success: false,
          error: {
            code: 'GATEWAY_TIMEOUT',
            message: 'Upstream service timed out',
          },
        },
        headers: {},
      };
    }
    throw err;
  }
}

module.exports = { createProxy, forwardRequest };
