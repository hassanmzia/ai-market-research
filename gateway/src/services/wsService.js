'use strict';

const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const A2A_WS_URL = process.env.A2A_WS_URL || 'ws://a2a-orchestrator:7063';

/**
 * Manages WebSocket connections between frontend clients and the A2A orchestrator.
 *
 * For each taskId, we maintain:
 *   - A set of frontend client connections
 *   - A single upstream connection to the A2A orchestrator
 *
 * Progress messages from A2A are broadcast to all connected frontend clients
 * for that task.
 */
class WebSocketService {
  constructor() {
    /** @type {Map<string, Set<WebSocket>>} taskId -> frontend clients */
    this.taskClients = new Map();
    /** @type {Map<string, WebSocket>} taskId -> upstream A2A connection */
    this.upstreamConnections = new Map();
    /** @type {Map<string, NodeJS.Timeout>} taskId -> reconnect timer */
    this.reconnectTimers = new Map();
    this.maxReconnectAttempts = 5;
    /** @type {Map<string, number>} taskId -> reconnect attempt count */
    this.reconnectAttempts = new Map();
  }

  /**
   * Attach the WebSocket server to an HTTP server.
   * Handles upgrade requests with path matching /ws/research/:taskId.
   *
   * @param {import('http').Server} server
   */
  attach(server) {
    this.wss = new WebSocket.Server({ noServer: true });

    server.on('upgrade', (req, socket, head) => {
      const match = req.url.match(/^\/ws\/research\/([a-zA-Z0-9_-]+)/);
      if (!match) {
        socket.destroy();
        return;
      }

      const taskId = match[1];

      this.wss.handleUpgrade(req, socket, head, (ws) => {
        this._handleClientConnection(ws, taskId);
      });
    });

    console.log('[WS] WebSocket service attached to server');
  }

  /**
   * Handle a new frontend client connection for a given taskId.
   */
  _handleClientConnection(ws, taskId) {
    const clientId = uuidv4();
    console.log(`[WS] Client ${clientId} connected for task ${taskId}`);

    // Track client
    if (!this.taskClients.has(taskId)) {
      this.taskClients.set(taskId, new Set());
    }
    this.taskClients.get(taskId).add(ws);

    // Send welcome message
    this._sendToClient(ws, {
      type: 'connected',
      taskId,
      clientId,
      message: 'Connected to research progress stream',
    });

    // Ensure we have an upstream connection for this task
    if (!this.upstreamConnections.has(taskId)) {
      this._connectUpstream(taskId);
    }

    // Handle messages from the client (e.g., control messages)
    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        console.log(`[WS] Message from client ${clientId}:`, msg.type || 'unknown');

        if (msg.type === 'ping') {
          this._sendToClient(ws, { type: 'pong', timestamp: Date.now() });
        }
      } catch {
        // Ignore malformed messages
      }
    });

    ws.on('close', () => {
      console.log(`[WS] Client ${clientId} disconnected from task ${taskId}`);
      const clients = this.taskClients.get(taskId);
      if (clients) {
        clients.delete(ws);
        // If no more clients for this task, clean up upstream
        if (clients.size === 0) {
          this.taskClients.delete(taskId);
          this._disconnectUpstream(taskId);
        }
      }
    });

    ws.on('error', (err) => {
      console.error(`[WS] Client ${clientId} error:`, err.message);
    });
  }

  /**
   * Connect to the A2A orchestrator WebSocket for a specific task.
   */
  _connectUpstream(taskId) {
    if (this.upstreamConnections.has(taskId)) return;

    const url = `${A2A_WS_URL}/ws/research/${taskId}`;
    console.log(`[WS] Connecting upstream to ${url}`);

    const upstream = new WebSocket(url);

    upstream.on('open', () => {
      console.log(`[WS] Upstream connected for task ${taskId}`);
      this.reconnectAttempts.set(taskId, 0);
    });

    upstream.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        // Broadcast to all frontend clients for this task
        this._broadcastToTask(taskId, msg);
      } catch {
        // Forward raw message if not JSON
        this._broadcastToTask(taskId, {
          type: 'raw',
          data: data.toString(),
        });
      }
    });

    upstream.on('close', (code, reason) => {
      console.log(`[WS] Upstream closed for task ${taskId}: ${code} ${reason}`);
      this.upstreamConnections.delete(taskId);

      // Attempt reconnection if clients are still listening
      if (this.taskClients.has(taskId) && this.taskClients.get(taskId).size > 0) {
        this._scheduleReconnect(taskId);
      }
    });

    upstream.on('error', (err) => {
      console.error(`[WS] Upstream error for task ${taskId}:`, err.message);
      // Notify connected clients about the error
      this._broadcastToTask(taskId, {
        type: 'error',
        message: 'Connection to research service interrupted',
        recoverable: true,
      });
    });

    this.upstreamConnections.set(taskId, upstream);
  }

  /**
   * Schedule a reconnection attempt for an upstream connection.
   */
  _scheduleReconnect(taskId) {
    const attempts = this.reconnectAttempts.get(taskId) || 0;

    if (attempts >= this.maxReconnectAttempts) {
      console.warn(`[WS] Max reconnect attempts reached for task ${taskId}`);
      this._broadcastToTask(taskId, {
        type: 'error',
        message: 'Unable to reconnect to research service',
        recoverable: false,
      });
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, attempts), 30_000); // Exponential backoff, max 30s
    console.log(`[WS] Reconnecting upstream for task ${taskId} in ${delay}ms (attempt ${attempts + 1})`);

    this.reconnectAttempts.set(taskId, attempts + 1);

    const timer = setTimeout(() => {
      this.reconnectTimers.delete(taskId);
      this._connectUpstream(taskId);
    }, delay);

    // Store timer so we can cancel on cleanup
    if (this.reconnectTimers.has(taskId)) {
      clearTimeout(this.reconnectTimers.get(taskId));
    }
    this.reconnectTimers.set(taskId, timer);
  }

  /**
   * Disconnect the upstream connection for a task.
   */
  _disconnectUpstream(taskId) {
    // Cancel any pending reconnect
    if (this.reconnectTimers.has(taskId)) {
      clearTimeout(this.reconnectTimers.get(taskId));
      this.reconnectTimers.delete(taskId);
    }
    this.reconnectAttempts.delete(taskId);

    const upstream = this.upstreamConnections.get(taskId);
    if (upstream) {
      upstream.close(1000, 'No more clients');
      this.upstreamConnections.delete(taskId);
      console.log(`[WS] Upstream disconnected for task ${taskId}`);
    }
  }

  /**
   * Broadcast a message to all frontend clients subscribed to a task.
   */
  _broadcastToTask(taskId, message) {
    const clients = this.taskClients.get(taskId);
    if (!clients) return;

    const payload = typeof message === 'string' ? message : JSON.stringify(message);

    for (const client of clients) {
      this._sendToClient(client, payload);
    }
  }

  /**
   * Send a message to a single client.
   */
  _sendToClient(ws, message) {
    if (ws.readyState === WebSocket.OPEN) {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      ws.send(payload, (err) => {
        if (err) {
          console.error('[WS] Send error:', err.message);
        }
      });
    }
  }

  /**
   * Gracefully shut down all connections.
   */
  shutdown() {
    console.log('[WS] Shutting down WebSocket service');

    // Close all upstream connections
    for (const [taskId, upstream] of this.upstreamConnections) {
      upstream.close(1001, 'Server shutting down');
      this.upstreamConnections.delete(taskId);
    }

    // Cancel all reconnect timers
    for (const [taskId, timer] of this.reconnectTimers) {
      clearTimeout(timer);
      this.reconnectTimers.delete(taskId);
    }

    // Close all client connections
    for (const [taskId, clients] of this.taskClients) {
      for (const client of clients) {
        client.close(1001, 'Server shutting down');
      }
      this.taskClients.delete(taskId);
    }

    // Close the WebSocket server
    if (this.wss) {
      this.wss.close();
    }
  }
}

module.exports = new WebSocketService();
