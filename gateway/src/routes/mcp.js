'use strict';

const { Router } = require('express');
const { authenticate } = require('../middleware/auth');
const { generalLimiter } = require('../middleware/rateLimiter');
const { forwardRequest } = require('../services/proxyService');

const router = Router();

const MCP_BASE_URL = process.env.MCP_BASE_URL || 'http://mcp-server:9063';

/**
 * Helper to build forwarding headers from an incoming request.
 */
function forwardHeaders(req) {
  const headers = {};
  if (req.headers.authorization) {
    headers.authorization = req.headers.authorization;
  }
  if (req.user) {
    headers['X-User-Id'] = String(req.user.id);
    if (req.user.email) headers['X-User-Email'] = req.user.email;
  }
  headers['X-Forwarded-For'] = req.ip;
  return headers;
}

/**
 * GET /api/mcp/tools
 * List all available MCP tools.
 * The MCP server uses JSON-RPC style: POST /mcp/tools/list
 */
router.get('/tools', authenticate, generalLimiter, async (req, res, next) => {
  try {
    const result = await forwardRequest(
      MCP_BASE_URL,
      'POST',
      '/mcp/tools/list',
      {},
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/mcp/tools/:toolName
 * Call a specific MCP tool by name.
 * Proxies to POST /mcp/tools/call on the MCP server.
 */
router.post('/tools/:toolName', authenticate, generalLimiter, async (req, res, next) => {
  try {
    const { toolName } = req.params;
    const result = await forwardRequest(
      MCP_BASE_URL,
      'POST',
      '/mcp/tools/call',
      {
        name: toolName,
        arguments: req.body,
      },
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
