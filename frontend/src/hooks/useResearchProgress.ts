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
    // Handle initial_state message from orchestrator WebSocket
    if (data.type === 'initial_state') {
      if (typeof data.progress === 'number') {
        setProgress(data.progress);
      }
      if (data.status === 'completed') {
        setIsComplete(true);
        setProgress(100);
      } else if (data.status === 'failed') {
        setIsFailed(true);
      }
      // Determine current stage from stages array
      if (data.stages) {
        const running = data.stages.find((s) => s.status === 'running');
        const lastCompleted = [...data.stages].reverse().find((s) => s.status === 'completed');
        if (running) {
          setStage(running.name);
        } else if (lastCompleted) {
          setStage(lastCompleted.name);
        }
      }
      return;
    }

    // Ignore non-progress messages (e.g. connection, pong, keepalive, error)
    const stageName = data.stage || data.stage_name;
    if (typeof data.progress !== 'number' && !stageName) {
      return;
    }

    if (typeof data.progress === 'number') {
      setProgress(data.progress);
    }
    if (data.message) {
      setMessage(data.message);
    }
    if (data.agent_name) {
      setAgentName(data.agent_name);
    }

    // Handle overall pipeline completion/failure from orchestrator
    // Orchestrator sends stage_name="pipeline" with status="completed"
    if (stageName === 'pipeline' && data.status === 'completed') {
      setIsComplete(true);
      setProgress(100);
      return;
    }

    // For individual stage updates, set the current stage name
    if (stageName && stageName !== 'pipeline') {
      setStage(stageName);
    }

    // Check for stage-level failure
    if (data.status === 'failed') {
      setIsFailed(true);
    }

    // Also support legacy format where stage itself is 'completed'/'failed'
    if (stageName === 'completed') {
      setIsComplete(true);
      setProgress(100);
    } else if (stageName === 'failed') {
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
