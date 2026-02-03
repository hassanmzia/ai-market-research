import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  FileText,
  Download,
  Share2,
  Trash2,
  Loader,
  ExternalLink,
} from 'lucide-react';
import { reportsAPI } from '../services/api';
import { formatDate, truncateText } from '../utils/helpers';
import type { SavedReport } from '../types';
import toast from 'react-hot-toast';

const Reports: React.FC = () => {
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await reportsAPI.getReports();
      setReports(response.data);
    } catch {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    setDeletingId(id);
    try {
      await reportsAPI.deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
      toast.success('Report deleted');
    } catch {
      toast.error('Failed to delete report');
    } finally {
      setDeletingId(null);
    }
  };

  const handleShare = async (id: number) => {
    try {
      const response = await reportsAPI.shareReport(id);
      const shareUrl = response.data.share_url || `${window.location.origin}/shared/${response.data.share_token}`;
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Share link copied to clipboard!');
    } catch {
      toast.error('Failed to generate share link');
    }
  };

  const handleDownload = async (id: number, title: string) => {
    try {
      const response = await reportsAPI.downloadReport(id, 'markdown');
      const blob = new Blob([response.data], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download report');
    }
  };

  const filteredReports = reports.filter(
    (report) =>
      report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading reports...</p>
      </div>
    );
  }

  return (
    <div className="reports-page">
      <div className="page-header">
        <div>
          <h1>Saved Reports</h1>
          <p className="page-subtitle">Manage and share your market research reports</p>
        </div>
      </div>

      <div className="filters-bar">
        <div className="search-input-wrapper">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {filteredReports.length === 0 ? (
        <div className="empty-state card">
          <FileText size={48} className="empty-state-icon" />
          <h4>No reports found</h4>
          <p>
            {searchQuery
              ? 'Try adjusting your search.'
              : 'Complete a research to save reports.'}
          </p>
        </div>
      ) : (
        <div className="reports-grid">
          {filteredReports.map((report) => (
            <div key={report.id} className="report-card card">
              <div className="card-body">
                <div className="report-card-header">
                  <FileText size={24} className="report-card-icon" />
                  <div className="report-card-meta">
                    <span className="report-format-badge">{report.format}</span>
                    {report.is_public && <span className="report-public-badge">Public</span>}
                  </div>
                </div>

                <h3 className="report-card-title">
                  <Link to={`/reports/${report.id}`}>{report.title}</Link>
                </h3>

                {report.description && (
                  <p className="report-card-description">
                    {truncateText(report.description, 150)}
                  </p>
                )}

                <div className="report-card-footer">
                  <span className="text-muted">{formatDate(report.created_at)}</span>
                  <span className="text-muted">{report.download_count} downloads</span>
                </div>

                <div className="report-card-actions">
                  <Link
                    to={`/reports/${report.id}`}
                    className="btn btn-sm btn-outline"
                    title="View"
                  >
                    <ExternalLink size={14} />
                  </Link>
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => handleDownload(report.id, report.title)}
                    title="Download"
                  >
                    <Download size={14} />
                  </button>
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => handleShare(report.id)}
                    title="Share"
                  >
                    <Share2 size={14} />
                  </button>
                  <button
                    className="btn btn-sm btn-danger-outline"
                    onClick={() => handleDelete(report.id)}
                    disabled={deletingId === report.id}
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Reports;
