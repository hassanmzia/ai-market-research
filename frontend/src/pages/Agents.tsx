import React, { useEffect, useState } from 'react';
import { Bot, Loader, RefreshCw, Wifi, WifiOff, Activity } from 'lucide-react';
import { agentsAPI } from '../services/api';
import type { AgentCard } from '../types';
import clsx from 'clsx';
import toast from 'react-hot-toast';

const DEFAULT_AGENTS: AgentCard[] = [
  {
    name: 'Orchestrator Agent',
    description: 'Coordinates all research agents and manages workflow execution.',
    capabilities: ['Task orchestration', 'Agent coordination', 'Progress tracking', 'Error recovery'],
    status: 'active',
  },
  {
    name: 'Company Validation Agent',
    description: 'Validates company information and identifies the business sector.',
    capabilities: ['Company verification', 'Sector identification', 'Data validation'],
    status: 'active',
  },
  {
    name: 'Competitor Discovery Agent',
    description: 'Discovers and analyzes key competitors in the market.',
    capabilities: ['Competitor identification', 'Market mapping', 'Competitive landscape analysis'],
    status: 'active',
  },
  {
    name: 'Financial Research Agent',
    description: 'Gathers and analyzes financial data and market metrics.',
    capabilities: ['Financial data collection', 'Revenue analysis', 'Market cap tracking', 'Growth metrics'],
    status: 'active',
  },
  {
    name: 'Sentiment Analysis Agent',
    description: 'Analyzes market sentiment from news, social media, and analyst reports.',
    capabilities: ['News sentiment', 'Social media analysis', 'Analyst opinion tracking', 'Mood scoring'],
    status: 'active',
  },
  {
    name: 'Trend Analysis Agent',
    description: 'Identifies emerging and declining market trends and opportunities.',
    capabilities: ['Trend detection', 'Pattern recognition', 'Opportunity identification', 'Market forecasting'],
    status: 'active',
  },
  {
    name: 'Report Generation Agent',
    description: 'Compiles all research data into comprehensive market research reports.',
    capabilities: ['Report compilation', 'SWOT generation', 'Executive summary', 'Recommendations'],
    status: 'active',
  },
];

const Agents: React.FC = () => {
  const [agents, setAgents] = useState<AgentCard[]>(DEFAULT_AGENTS);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAgents = async () => {
    try {
      const response = await agentsAPI.getAgents();
      if (response.data && response.data.length > 0) {
        setAgents(response.data);
      }
    } catch {
      // Use default agents if API is unavailable
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAgents();
    toast.success('Agent statuses refreshed');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#10B981';
      case 'busy':
        return '#F59E0B';
      case 'offline':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Wifi size={14} />;
      case 'busy':
        return <Activity size={14} />;
      case 'offline':
        return <WifiOff size={14} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading agent statuses...</p>
      </div>
    );
  }

  const activeCount = agents.filter((a) => a.status === 'active').length;
  const busyCount = agents.filter((a) => a.status === 'busy').length;
  const offlineCount = agents.filter((a) => a.status === 'offline').length;

  return (
    <div className="agents-page">
      <div className="page-header">
        <div>
          <h1>AI Agent Status</h1>
          <p className="page-subtitle">
            Monitor the multi-agent system powering your market research
          </p>
        </div>
        <button
          className="btn btn-outline"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={18} className={refreshing ? 'spinning' : ''} />
          Refresh
        </button>
      </div>

      {/* Summary stats */}
      <div className="agent-summary">
        <div className="agent-summary-item">
          <span className="agent-summary-dot" style={{ backgroundColor: '#10B981' }} />
          <span className="agent-summary-count">{activeCount}</span>
          <span className="agent-summary-label">Active</span>
        </div>
        <div className="agent-summary-item">
          <span className="agent-summary-dot" style={{ backgroundColor: '#F59E0B' }} />
          <span className="agent-summary-count">{busyCount}</span>
          <span className="agent-summary-label">Busy</span>
        </div>
        <div className="agent-summary-item">
          <span className="agent-summary-dot" style={{ backgroundColor: '#EF4444' }} />
          <span className="agent-summary-count">{offlineCount}</span>
          <span className="agent-summary-label">Offline</span>
        </div>
      </div>

      {/* Architecture diagram */}
      <div className="card agent-architecture">
        <div className="card-header">
          <h3>Multi-Agent Architecture</h3>
        </div>
        <div className="card-body">
          <div className="architecture-flow">
            <div className="architecture-node architecture-orchestrator">
              <Bot size={24} />
              <span>Orchestrator</span>
            </div>
            <div className="architecture-arrows">
              {agents
                .filter((a) => a.name !== 'Orchestrator Agent')
                .map((agent, i) => (
                  <div key={i} className="architecture-arrow">
                    <div className="arrow-line" />
                    <div
                      className="architecture-node architecture-agent"
                      style={{ borderColor: getStatusColor(agent.status) }}
                    >
                      <span
                        className="agent-status-dot"
                        style={{ backgroundColor: getStatusColor(agent.status) }}
                      />
                      <span>{agent.name.replace(' Agent', '')}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Agent cards grid */}
      <div className="agents-grid">
        {agents.map((agent, index) => (
          <div key={index} className="agent-card card">
            <div className="card-body">
              <div className="agent-card-header">
                <div className="agent-card-icon">
                  <Bot size={24} />
                </div>
                <div
                  className={clsx('agent-status-indicator', agent.status)}
                  style={{ color: getStatusColor(agent.status) }}
                >
                  {getStatusIcon(agent.status)}
                  <span>{agent.status}</span>
                </div>
              </div>

              <h3 className="agent-card-name">{agent.name}</h3>
              <p className="agent-card-description">{agent.description}</p>

              <div className="agent-capabilities">
                <h4>Capabilities</h4>
                <div className="capability-tags">
                  {agent.capabilities.map((cap, i) => (
                    <span key={i} className="capability-tag">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Agents;
