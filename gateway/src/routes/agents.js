'use strict';

const { Router } = require('express');
const { authenticate } = require('../middleware/auth');
const { researchLimiter } = require('../middleware/rateLimiter');
const { forwardRequest } = require('../services/proxyService');

const router = Router();

const A2A_BASE_URL = process.env.A2A_BASE_URL || 'http://a2a-orchestrator:7063';

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
 * GET /api/agents
 * List all available agents from the A2A orchestrator.
 */
router.get('/', authenticate, async (req, res, next) => {
  try {
    const result = await forwardRequest(
      A2A_BASE_URL,
      'GET',
      '/a2a/agents',
      null,
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/agents/research
 * Start a new research task via the A2A orchestrator.
 */
router.post('/research', authenticate, researchLimiter, async (req, res, next) => {
  try {
    const result = await forwardRequest(
      A2A_BASE_URL,
      'POST',
      '/a2a/research',
      req.body,
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/agents/research/:taskId/status
 * Get the status of a research task.
 */
router.get('/research/:taskId/status', authenticate, async (req, res, next) => {
  try {
    const { taskId } = req.params;
    const result = await forwardRequest(
      A2A_BASE_URL,
      'GET',
      `/a2a/research/${taskId}/status`,
      null,
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/agents/research/:taskId/result
 * Get the result of a completed research task.
 */
router.get('/research/:taskId/result', authenticate, async (req, res, next) => {
  try {
    const { taskId } = req.params;
    const result = await forwardRequest(
      A2A_BASE_URL,
      'GET',
      `/a2a/research/${taskId}/result`,
      null,
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/agents/:agentName/invoke
 * Directly invoke a specific agent by name.
 */
router.post('/:agentName/invoke', authenticate, researchLimiter, async (req, res, next) => {
  try {
    const { agentName } = req.params;
    const result = await forwardRequest(
      A2A_BASE_URL,
      'POST',
      `/a2a/agents/${agentName}/invoke`,
      req.body,
      forwardHeaders(req)
    );
    res.status(result.status).json(result.data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
