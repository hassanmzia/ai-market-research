import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  CheckCircle,
  Activity,
  Eye,
  Search,
  ArrowRight,
  Loader,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAuthStore } from '../store/authStore';
import { dashboardAPI } from '../services/api';
import StatsCard from '../components/StatsCard';
import { formatRelativeTime, getStatusColor, getStatusLabel, truncateText } from '../utils/helpers';
import type { DashboardStats } from '../types';

const CHART_COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await dashboardAPI.getStats();
        setStats(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-error">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Welcome back, {user?.first_name || 'User'}</h1>
          <p className="page-subtitle">Here's what's happening with your market research</p>
        </div>
        <Link to="/research/new" className="btn btn-primary">
          <Search size={18} />
          New Research
        </Link>
      </div>

      {/* Stats cards */}
      <div className="stats-grid">
        <StatsCard
          icon={BarChart3}
          label="Total Researches"
          value={stats?.total_researches || 0}
          color="#2563EB"
        />
        <StatsCard
          icon={CheckCircle}
          label="Completed"
          value={stats?.completed_researches || 0}
          color="#10B981"
        />
        <StatsCard
          icon={Activity}
          label="Active"
          value={stats?.active_researches || 0}
          color="#F59E0B"
        />
        <StatsCard
          icon={Eye}
          label="Watchlist"
          value={stats?.watchlist_count || 0}
          color="#8B5CF6"
        />
      </div>

      {/* Charts row */}
      <div className="dashboard-charts">
        {/* Top sectors pie chart */}
        <div className="card">
          <div className="card-header">
            <h3>Top Sectors</h3>
          </div>
          <div className="card-body chart-container">
            {stats?.top_sectors && stats.top_sectors.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats.top_sectors}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ sector, percent }) =>
                      `${truncateText(sector, 15)} (${(percent * 100).toFixed(0)}%)`
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="sector"
                  >
                    {stats.top_sectors.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">
                <p>No sector data yet. Start your first research!</p>
              </div>
            )}
          </div>
        </div>

        {/* Monthly activity bar chart */}
        <div className="card">
          <div className="card-header">
            <h3>Monthly Activity</h3>
          </div>
          <div className="card-body chart-container">
            {stats?.monthly_activity && stats.monthly_activity.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.monthly_activity}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" stroke="#6B7280" fontSize={12} />
                  <YAxis stroke="#6B7280" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} name="Researches" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">
                <p>No activity data yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent research */}
      <div className="card">
        <div className="card-header">
          <h3>Recent Research</h3>
          <Link to="/research" className="card-header-link">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="card-body">
          {stats?.recent_researches && stats.recent_researches.length > 0 ? (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Started</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_researches.map((task) => (
                    <tr key={task.id}>
                      <td className="font-medium">{task.company_name}</td>
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
                                width: `${task.progress}%`,
                                backgroundColor: getStatusColor(task.status),
                              }}
                            />
                          </div>
                          <span>{task.progress}%</span>
                        </div>
                      </td>
                      <td className="text-muted">
                        {task.created_at ? formatRelativeTime(task.created_at) : 'N/A'}
                      </td>
                      <td>
                        <Link to={`/research/${task.task_id}`} className="btn btn-sm btn-outline">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <Search size={48} className="empty-state-icon" />
              <h4>No research yet</h4>
              <p>Start your first company research to see results here.</p>
              <Link to="/research/new" className="btn btn-primary">
                Start Research
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
