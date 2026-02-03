import { useState, useEffect, useRef, useCallback } from 'react';
import { connectToResearch } from '../services/websocket';
import type { ResearchProgress } from '../types';

interface UseResearchProgressReturn {
  progress: number;
  stage: string;
  message: string;
  agentName: string;
  isConnected: boolean;
  isComplete: boolean;
  isFailed: boolean;
}

export function useResearchProgress(taskId: string | null): UseResearchProgressReturn {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('pending');
  const [message, setMessage] = useState('Waiting to start...');
  const [agentName, setAgentName] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isFailed, setIsFailed] = useState(false);
  const disconnectRef = useRef<(() => void) | null>(null);

  const handleProgress = useCallback((data: ResearchProgress) => {
    // Ignore non-progress messages (e.g. connection, pong, error, raw)
    if (typeof data.progress !== 'number' && !data.stage) {
      return;
    }

    if (typeof data.progress === 'number') {
      setProgress(data.progress);
    }
    if (data.stage) {
      setStage(data.stage);
    }
    if (data.message) {
      setMessage(data.message);
    }
    if (data.agent_name) {
      setAgentName(data.agent_name);
    }

    if (data.stage === 'completed') {
      setIsComplete(true);
      setProgress(100);
    } else if (data.stage === 'failed') {
      setIsFailed(true);
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;

    // Reset state
    setProgress(0);
    setStage('pending');
    setMessage('Connecting...');
    setAgentName('');
    setIsConnected(false);
    setIsComplete(false);
    setIsFailed(false);

    const connection = connectToResearch(
      taskId,
      (data) => {
        setIsConnected(true);
        handleProgress(data);
      },
      () => {
        // on error
        setIsConnected(false);
      },
      () => {
        // on close
        setIsConnected(false);
      }
    );

    disconnectRef.current = connection.disconnect;
    setIsConnected(true);

    return () => {
      if (disconnectRef.current) {
        disconnectRef.current();
        disconnectRef.current = null;
      }
    };
  }, [taskId, handleProgress]);

  return { progress, stage, message, agentName, isConnected, isComplete, isFailed };
}
