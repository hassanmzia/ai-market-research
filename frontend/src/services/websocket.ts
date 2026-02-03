import type { ResearchProgress } from '../types';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://172.168.1.95:4063';

interface WebSocketConnection {
  disconnect: () => void;
}

export function connectToResearch(
  taskId: string,
  onProgress: (progress: ResearchProgress) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocketConnection {
  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000;
  let isDisconnected = false;

  function connect() {
    if (isDisconnected) return;

    const token = localStorage.getItem('access_token');
    const wsUrl = `${WS_URL}/ws/research/${taskId}${token ? `?token=${token}` : ''}`;

    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      console.error('WebSocket connection error:', err);
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      console.log(`WebSocket connected for task: ${taskId}`);
      reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ResearchProgress;
        onProgress(data);

        // If task is completed or failed, don't reconnect
        if (data.stage === 'completed' || data.stage === 'failed') {
          isDisconnected = true;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      if (onError) onError(event);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      if (onClose) onClose();
      if (!isDisconnected) {
        scheduleReconnect();
      }
    };
  }

  function scheduleReconnect() {
    if (isDisconnected || reconnectAttempts >= maxReconnectAttempts) return;

    const delay = Math.min(baseReconnectDelay * Math.pow(2, reconnectAttempts), 30000);
    reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);

    reconnectTimer = setTimeout(() => {
      connect();
    }, delay);
  }

  function disconnect() {
    isDisconnected = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  connect();

  return { disconnect };
}
