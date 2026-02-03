import React from 'react';
import { CheckCircle, Circle, Loader, XCircle } from 'lucide-react';
import { useResearchProgress } from '../hooks/useResearchProgress';
import clsx from 'clsx';

interface ResearchProgressProps {
  taskId: string | null;
  onComplete?: () => void;
}

const STAGES = [
  { key: 'validation', label: 'Validation', description: 'Validating company information' },
  { key: 'sector_identification', label: 'Sector Analysis', description: 'Identifying industry sector' },
  { key: 'competitor_discovery', label: 'Competitor Discovery', description: 'Finding key competitors' },
  { key: 'financial_research', label: 'Financial Research', description: 'Gathering financial data' },
  { key: 'deep_research', label: 'Deep Research', description: 'In-depth market analysis' },
  { key: 'sentiment_analysis', label: 'Sentiment Analysis', description: 'Analyzing market sentiment' },
  { key: 'trend_analysis', label: 'Trend Analysis', description: 'Identifying market trends' },
  { key: 'report_generation', label: 'Report Generation', description: 'Compiling final report' },
];

const ResearchProgressComponent: React.FC<ResearchProgressProps> = ({ taskId, onComplete }) => {
  const { progress, stage, message, agentName, isConnected, isComplete, isFailed } =
    useResearchProgress(taskId);

  React.useEffect(() => {
    if (isComplete && onComplete) {
      onComplete();
    }
  }, [isComplete, onComplete]);

  const getStageIndex = (currentStage: string): number => {
    const idx = STAGES.findIndex((s) => s.key === currentStage);
    return idx >= 0 ? idx : -1;
  };

  const currentStageIndex = getStageIndex(stage);

  const getStepStatus = (index: number): 'completed' | 'active' | 'pending' | 'failed' => {
    if (isFailed && index === currentStageIndex) return 'failed';
    if (isComplete) return 'completed';
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'active';
    return 'pending';
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={20} className="step-icon-completed" />;
      case 'active':
        return <Loader size={20} className="step-icon-active spinning" />;
      case 'failed':
        return <XCircle size={20} className="step-icon-failed" />;
      default:
        return <Circle size={20} className="step-icon-pending" />;
    }
  };

  return (
    <div className="research-progress">
      <div className="research-progress-header">
        <h3>Research Progress</h3>
        <div className={clsx('connection-indicator', { connected: isConnected })}>
          <span className="connection-dot" />
          {isConnected ? 'Live' : 'Connecting...'}
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div
            className={clsx('progress-bar-fill', {
              'progress-complete': isComplete,
              'progress-failed': isFailed,
            })}
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="progress-percentage">{Math.round(progress)}%</span>
      </div>

      {/* Current status message */}
      <div className="progress-message">
        {agentName && <span className="agent-badge">{agentName}</span>}
        <span className="status-message">{message}</span>
      </div>

      {/* Stepper */}
      <div className="research-stepper">
        {STAGES.map((s, index) => {
          const status = getStepStatus(index);
          return (
            <div key={s.key} className={clsx('stepper-step', status)}>
              <div className="stepper-icon">{getStepIcon(status)}</div>
              <div className="stepper-content">
                <span className="stepper-label">{s.label}</span>
                <span className="stepper-description">{s.description}</span>
              </div>
              {index < STAGES.length - 1 && <div className="stepper-connector" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ResearchProgressComponent;
