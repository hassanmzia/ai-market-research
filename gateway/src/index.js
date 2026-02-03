'use strict';

const http = require('http');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

const { authenticate } = require('./middleware/auth');
const { authLimiter, generalLimiter, closeRedis } = require('./middleware/rateLimiter');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { createProxy } = require('./services/proxyService');
const wsService = require('./services/wsService');
const agentsRouter = require('./routes/agents');
const mcpRouter = require('./routes/mcp');

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const PORT = parseInt(process.env.PORT || '4063', 10);
const DJANGO_URL = process.env.DJANGO_API_URL || process.env.DJANGO_URL || 'http://django-api:8063';
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';
const DJANGO_PATHS = ['/api/auth/', '/api/research/', '/api/reports/', '/api/notifications/', '/api/dashboard/'];

// ---------------------------------------------------------------------------
// Express application
// ---------------------------------------------------------------------------
const app = express();

// Trust proxy (for correct IP detection behind Docker / nginx)
app.set('trust proxy', 1);

// ---------------------------------------------------------------------------
// Global middleware
// ---------------------------------------------------------------------------
app.use(helmet({
  contentSecurityPolicy: false, // Let frontend handle CSP
}));

app.use(cors({
  origin: CORS_ORIGIN === '*' ? true : CORS_ORIGIN.split(','),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
}));

app.use(compression());
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// Parse JSON only for non-proxied routes (agents, mcp, etc.)
// Django-proxied routes must NOT go through body parsing so that
// http-proxy-middleware can forward the raw stream without fixRequestBody.
const jsonParser = express.json({ limit: '10mb' });
const urlencodedParser = express.urlencoded({ extended: true, limit: '10mb' });

app.use((req, res, next) => {
  // Skip body parsing for paths that will be proxied to Django
  if (DJANGO_PATHS.some((p) => req.originalUrl.startsWith(p))) {
    return next();
  }
  jsonParser(req, res, (err) => {
    if (err) return next(err);
    urlencodedParser(req, res, next);
  });
});

// ---------------------------------------------------------------------------
// Health check (no auth, no rate limit)
// ---------------------------------------------------------------------------
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'amr-api-gateway',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

// ---------------------------------------------------------------------------
// Django proxy – path-filtered at root level to preserve full URL path
// ---------------------------------------------------------------------------
const djangoProxy = createProxy(DJANGO_URL, {
  changeOrigin: true,
  pathFilter: (path) => DJANGO_PATHS.some((p) => path.startsWith(p)),
});

// Apply per-path middleware before the proxy.
// Django handles its own JWT authentication via SimpleJWT, so the gateway
// must NOT verify tokens locally (different signing secret). We only
// apply rate-limiting here and let Django enforce auth.
app.use((req, res, next) => {
  const url = req.originalUrl;

  // Only intercept Django-bound paths
  if (!DJANGO_PATHS.some((p) => url.startsWith(p))) {
    return next();
  }

  // Auth endpoints: stricter rate limit
  if (url.startsWith('/api/auth/')) {
    return authLimiter(req, res, next);
  }

  // All other Django paths: general rate limit only, Django handles auth
  return generalLimiter(req, res, next);
});

// Mount proxy at root – original path is preserved
app.use(djangoProxy);

// ---------------------------------------------------------------------------
// A2A orchestrator routes (agents)
// ---------------------------------------------------------------------------
app.use('/api/agents', agentsRouter);

// ---------------------------------------------------------------------------
// MCP server routes
// ---------------------------------------------------------------------------
app.use('/api/mcp', mcpRouter);

// ---------------------------------------------------------------------------
// Catch-all & error handling
// ---------------------------------------------------------------------------
app.use(notFoundHandler);
app.use(errorHandler);

// ---------------------------------------------------------------------------
// HTTP + WebSocket server
// ---------------------------------------------------------------------------
const server = http.createServer(app);

// Attach WebSocket handling
wsService.attach(server);

server.listen(PORT, () => {
  console.log(`[Gateway] AI Market Research API Gateway listening on port ${PORT}`);
  console.log(`[Gateway] Environment: ${process.env.NODE_ENV || 'development'}`);
});

// ---------------------------------------------------------------------------
// Graceful shutdown
// ---------------------------------------------------------------------------
function shutdown(signal) {
  console.log(`[Gateway] Received ${signal}. Starting graceful shutdown...`);

  // Stop accepting new connections
  server.close((err) => {
    if (err) {
      console.error('[Gateway] Error closing HTTP server:', err.message);
    } else {
      console.log('[Gateway] HTTP server closed');
    }

    // Close WebSocket connections
    wsService.shutdown();

    // Close Redis connection
    closeRedis();

    console.log('[Gateway] Shutdown complete');
    process.exit(err ? 1 : 0);
  });

  // Force exit after 15 seconds
  setTimeout(() => {
    console.error('[Gateway] Forceful shutdown after timeout');
    process.exit(1);
  }, 15_000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

// Handle uncaught errors
process.on('uncaughtException', (err) => {
  console.error('[Gateway] Uncaught exception:', err);
  shutdown('uncaughtException');
});

process.on('unhandledRejection', (reason) => {
  console.error('[Gateway] Unhandled rejection:', reason);
});

module.exports = app;
