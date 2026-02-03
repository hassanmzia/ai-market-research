import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Loader,
  ArrowLeft,
  Save,
  Download,
  Eye,
  AlertCircle,
  FileText,
  Users,
  BarChart3,
  Grid,
  BookOpen,
} from 'lucide-react';
import { useResearchStore } from '../store/researchStore';
import { reportsAPI, watchlistAPI } from '../services/api';
import ResearchProgressComponent from '../components/ResearchProgress';
import CompetitorTable from '../components/CompetitorTable';
import SwotChart from '../components/SwotChart';
import SentimentGauge from '../components/SentimentGauge';
import TrendList from '../components/TrendList';
import ReportRenderer from '../components/ReportRenderer';
import {
  getStatusColor,
  getStatusLabel,
  formatDateTime,
  calculateProgress,
} from '../utils/helpers';
import toast from 'react-hot-toast';
import type { ResearchTask, ResearchResult } from '../types';

type TabKey = 'overview' | 'competitors' | 'analysis' | 'swot' | 'report';

const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ size?: number | string }> }[] = [
  { key: 'overview', label: 'Overview', icon: FileText },
  { key: 'competitors', label: 'Competitors', icon: Users },
  { key: 'analysis', label: 'Analysis', icon: BarChart3 },
  { key: 'swot', label: 'SWOT', icon: Grid },
  { key: 'report', label: 'Full Report', icon: BookOpen },
];

const ResearchDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { fetchTaskStatus, fetchTaskResult } = useResearchStore();
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [savingReport, setSavingReport] = useState(false);

  const isInProgress =
    task &&
    !['completed', 'failed', 'pending'].includes(task.status);

  useEffect(() => {
    if (!id) return;

    const loadData = async () => {
      try {
        const taskData = await fetchTaskStatus(id);
        setTask(taskData);

        if (taskData.status === 'completed') {
          try {
            const resultData = await fetchTaskResult(id);
            setResult(resultData);
          } catch {
            // Result may not exist yet
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load research details');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, fetchTaskStatus, fetchTaskResult]);

  const handleResearchComplete = async () => {
    if (!id) return;
    try {
      const taskData = await fetchTaskStatus(id);
      setTask(taskData);
      const resultData = await fetchTaskResult(id);
      setResult(resultData);
    } catch {
      // Retry after a delay
      setTimeout(async () => {
        try {
          const resultData = await fetchTaskResult(id);
          setResult(resultData);
        } catch {
          toast.error('Failed to load results. Please refresh the page.');
        }
      }, 2000);
    }
  };

  const handleSaveReport = async () => {
    if (!id || !task) return;
    setSavingReport(true);
    try {
      await reportsAPI.saveReport({
        task_id: id,
        title: `Market Research: ${task.company_name}`,
        description: result?.executive_summary || '',
      });
      toast.success('Report saved successfully!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to save report');
    } finally {
      setSavingReport(false);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!task) return;
    try {
      await watchlistAPI.addToWatchlist({
        company_name: task.company_name,
        alert_on_news: true,
        alert_on_competitor_change: true,
      });
      toast.success(`${task.company_name} added to watchlist`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add to watchlist');
    }
  };

  const handleDownload = () => {
    if (!result?.report_markdown || !task) return;
    const blob = new Blob([result.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${task.company_name.replace(/\s+/g, '_')}_research_report.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading research details...</p>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="page-error">
        <AlertCircle size={48} />
        <h3>Error</h3>
        <p>{error || 'Research task not found'}</p>
        <Link to="/research" className="btn btn-primary">
          Back to Research List
        </Link>
      </div>
    );
  }

  return (
    <div className="research-detail-page">
      <div className="page-header">
        <div>
          <Link to="/research" className="back-link">
            <ArrowLeft size={16} />
            Back to Research
          </Link>
          <h1>{task.company_name}</h1>
          <div className="research-meta">
            <span
              className="status-badge"
              style={{
                backgroundColor: `${getStatusColor(task.status)}20`,
                color: getStatusColor(task.status),
              }}
            >
              {getStatusLabel(task.status)}
            </span>
            {task.started_at && (
              <span className="text-muted">Started {formatDateTime(task.started_at)}</span>
            )}
            {task.completed_at && (
              <span className="text-muted">Completed {formatDateTime(task.completed_at)}</span>
            )}
          </div>
        </div>

        {result && (
          <div className="page-actions">
            <button
              className="btn btn-outline"
              onClick={handleSaveReport}
              disabled={savingReport}
            >
              <Save size={16} />
              {savingReport ? 'Saving...' : 'Save Report'}
            </button>
            <button className="btn btn-outline" onClick={handleDownload}>
              <Download size={16} />
              Export
            </button>
            <button className="btn btn-outline" onClick={handleAddToWatchlist}>
              <Eye size={16} />
              Watchlist
            </button>
          </div>
        )}
      </div>

      {/* Show progress if in progress */}
      {isInProgress && (
        <ResearchProgressComponent taskId={task.task_id} onComplete={handleResearchComplete} />
      )}

      {/* Show error if failed */}
      {task.status === 'failed' && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <div>
            <strong>Research Failed</strong>
            <p>{task.error_message || 'An unexpected error occurred during research.'}</p>
          </div>
        </div>
      )}

      {/* Results with tabs */}
      {result && (
        <>
          <div className="tabs">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="tab-content">
            {activeTab === 'overview' && (
              <div className="research-overview">
                <div className="card">
                  <div className="card-header">
                    <h3>Company Information</h3>
                  </div>
                  <div className="card-body">
                    <div className="info-grid">
                      <div className="info-item">
                        <span className="info-label">Company</span>
                        <span className="info-value">{task.company_name}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Sector</span>
                        <span className="info-value">
                          {result.company_sector || 'N/A'}
                        </span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Validated</span>
                        <span className="info-value">
                          {result.company_validated ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Competitors Found</span>
                        <span className="info-value">
                          {result.competitors?.length || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {result.executive_summary && (
                  <div className="card">
                    <div className="card-header">
                      <h3>Executive Summary</h3>
                    </div>
                    <div className="card-body">
                      <p className="executive-summary">{result.executive_summary}</p>
                    </div>
                  </div>
                )}

                {result.recommendations && result.recommendations.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <h3>Key Recommendations</h3>
                    </div>
                    <div className="card-body">
                      <ul className="recommendations-list">
                        {result.recommendations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'competitors' && (
              <CompetitorTable
                competitors={result.competitors || []}
                companyName={task.company_name}
              />
            )}

            {activeTab === 'analysis' && (
              <div className="analysis-grid">
                {result.sentiment_data && (
                  <SentimentGauge sentimentData={result.sentiment_data} />
                )}
                {result.trend_data && <TrendList trendData={result.trend_data} />}
              </div>
            )}

            {activeTab === 'swot' && result.swot_analysis && (
              <SwotChart swot={result.swot_analysis} />
            )}

            {activeTab === 'report' && (
              <div className="card">
                <div className="card-body">
                  <ReportRenderer markdown={result.report_markdown || ''} />
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ResearchDetail;
