import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Download, Share2, Loader, AlertCircle, Copy, Check } from 'lucide-react';
import { reportsAPI } from '../services/api';
import ReportRenderer from '../components/ReportRenderer';
import { formatDateTime } from '../utils/helpers';
import type { SavedReport } from '../types';
import toast from 'react-hot-toast';

const ReportDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<SavedReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id) return;

    const fetchReport = async () => {
      try {
        const response = await reportsAPI.getReport(Number(id));
        setReport(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [id]);

  const handleDownload = async (format: string) => {
    if (!report) return;
    try {
      const response = await reportsAPI.downloadReport(report.id, format);
      const blob = new Blob([response.data], {
        type: format === 'markdown' ? 'text/markdown' : 'text/html',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/\s+/g, '_')}.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download report');
    }
  };

  const handleShare = async () => {
    if (!report) return;
    try {
      const response = await reportsAPI.shareReport(report.id);
      const url =
        response.data.share_url ||
        `${window.location.origin}/shared/${response.data.share_token}`;
      setShareUrl(url);
    } catch {
      toast.error('Failed to generate share link');
    }
  };

  const handleCopyLink = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast.success('Link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy link');
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-error">
        <AlertCircle size={48} />
        <h3>Error</h3>
        <p>{error || 'Report not found'}</p>
        <Link to="/reports" className="btn btn-primary">
          Back to Reports
        </Link>
      </div>
    );
  }

  const reportContent =
    (report.report_data as any)?.report_markdown ||
    (report.report_data as any)?.content ||
    '';

  return (
    <div className="report-detail-page">
      <div className="page-header">
        <div>
          <Link to="/reports" className="back-link">
            <ArrowLeft size={16} />
            Back to Reports
          </Link>
          <h1>{report.title}</h1>
          <div className="research-meta">
            <span className="text-muted">Created {formatDateTime(report.created_at)}</span>
            <span className="text-muted">{report.download_count} downloads</span>
            <span className="report-format-badge">{report.format}</span>
          </div>
        </div>

        <div className="page-actions">
          <button
            className="btn btn-outline"
            onClick={() => handleDownload('markdown')}
          >
            <Download size={16} />
            Markdown
          </button>
          <button className="btn btn-outline" onClick={() => handleDownload('html')}>
            <Download size={16} />
            HTML
          </button>
          <button className="btn btn-primary" onClick={handleShare}>
            <Share2 size={16} />
            Share
          </button>
        </div>
      </div>

      {/* Share URL display */}
      {shareUrl && (
        <div className="share-url-bar card">
          <div className="card-body">
            <div className="share-url-content">
              <span className="share-url-label">Share Link:</span>
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="share-url-input"
                onClick={(e) => (e.target as HTMLInputElement).select()}
              />
              <button className="btn btn-sm btn-primary" onClick={handleCopyLink}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Report description */}
      {report.description && (
        <div className="card">
          <div className="card-body">
            <p className="report-description">{report.description}</p>
          </div>
        </div>
      )}

      {/* Report content */}
      <div className="card">
        <div className="card-body report-content-wrapper">
          {reportContent ? (
            <ReportRenderer markdown={reportContent} />
          ) : (
            <div className="empty-state">
              <p>No report content available.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportDetail;
