import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Loader, ExternalLink } from 'lucide-react';
import { useResearchStore } from '../store/researchStore';
import {
  getStatusColor,
  getStatusLabel,
  formatRelativeTime,
  formatDateTime,
  calculateProgress,
} from '../utils/helpers';

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
];

const ResearchList: React.FC = () => {
  const { tasks, fetchTasks, loading } = useResearchStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch = task.company_name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesStatus = !statusFilter || task.status === statusFilter ||
      (statusFilter === 'active' && !['pending', 'completed', 'failed'].includes(task.status));
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="research-list-page">
      <div className="page-header">
        <div>
          <h1>Research History</h1>
          <p className="page-subtitle">View and manage all your market research tasks</p>
        </div>
        <Link to="/research/new" className="btn btn-primary">
          <Search size={18} />
          New Research
        </Link>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-input-wrapper">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search by company name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <Filter size={18} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="page-loading">
          <Loader size={40} className="spinning" />
          <p>Loading research tasks...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="empty-state card">
          <Search size={48} className="empty-state-icon" />
          <h4>No research tasks found</h4>
          <p>
            {searchQuery || statusFilter
              ? 'Try adjusting your search or filters.'
              : 'Start your first company research to see results here.'}
          </p>
          {!searchQuery && !statusFilter && (
            <Link to="/research/new" className="btn btn-primary">
              Start Research
            </Link>
          )}
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.map((task) => {
                  const progress = calculateProgress(task.status, task.progress);
                  return (
                    <tr key={task.id}>
                      <td>
                        <span className="font-medium">{task.company_name}</span>
                      </td>
                      <td>
                        <span
                          className="status-badge"
                          style={{
                            backgroundColor: `${getStatusColor(task.status)}20`,
                            color: getStatusColor(task.status),
                          }}
                        >
                          {getStatusLabel(task.status)}
                        </span>
                      </td>
                      <td>
                        <div className="table-progress">
                          <div className="table-progress-bar">
                            <div
                              className="table-progress-fill"
                              style={{
                                width: `${progress}%`,
                                backgroundColor: getStatusColor(task.status),
                              }}
                            />
                          </div>
                          <span>{progress}%</span>
                        </div>
                      </td>
                      <td className="text-muted">
                        {task.started_at
                          ? formatRelativeTime(task.started_at)
                          : task.created_at
                          ? formatRelativeTime(task.created_at)
                          : 'N/A'}
                      </td>
                      <td className="text-muted">
                        {task.completed_at ? formatDateTime(task.completed_at) : '--'}
                      </td>
                      <td>
                        <Link
                          to={`/research/${task.task_id}`}
                          className="btn btn-sm btn-outline"
                        >
                          <ExternalLink size={14} />
                          View
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchList;
