import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Eye,
  Trash2,
  Search,
  Bell,
  BellOff,
  Edit3,
  Save,
  X,
  Loader,
  RefreshCw,
} from 'lucide-react';
import { watchlistAPI } from '../services/api';
import { formatDate } from '../utils/helpers';
import type { WatchlistItem } from '../types';
import toast from 'react-hot-toast';

const Watchlist: React.FC = () => {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editNotes, setEditNotes] = useState('');
  const [addCompany, setAddCompany] = useState('');
  const [addNotes, setAddNotes] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      const response = await watchlistAPI.getWatchlist();
      setItems(response.data);
    } catch {
      toast.error('Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addCompany.trim()) return;

    setAdding(true);
    try {
      const response = await watchlistAPI.addToWatchlist({
        company_name: addCompany.trim(),
        alert_on_news: true,
        alert_on_competitor_change: true,
        notes: addNotes,
      });
      setItems((prev) => [...prev, response.data]);
      setAddCompany('');
      setAddNotes('');
      setShowAddForm(false);
      toast.success('Company added to watchlist');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add to watchlist');
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id: number) => {
    if (!window.confirm('Remove from watchlist?')) return;
    try {
      await watchlistAPI.removeFromWatchlist(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      toast.success('Removed from watchlist');
    } catch {
      toast.error('Failed to remove');
    }
  };

  const handleToggleAlert = async (
    id: number,
    field: 'alert_on_news' | 'alert_on_competitor_change',
    currentValue: boolean
  ) => {
    try {
      const response = await watchlistAPI.updateWatchlistItem(id, {
        [field]: !currentValue,
      } as any);
      setItems((prev) =>
        prev.map((item) => (item.id === id ? response.data : item))
      );
    } catch {
      toast.error('Failed to update alert setting');
    }
  };

  const handleSaveNotes = async (id: number) => {
    try {
      const response = await watchlistAPI.updateWatchlistItem(id, {
        notes: editNotes,
      } as any);
      setItems((prev) =>
        prev.map((item) => (item.id === id ? response.data : item))
      );
      setEditingId(null);
      toast.success('Notes saved');
    } catch {
      toast.error('Failed to save notes');
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <Loader size={40} className="spinning" />
        <p>Loading watchlist...</p>
      </div>
    );
  }

  return (
    <div className="watchlist-page">
      <div className="page-header">
        <div>
          <h1>Watchlist</h1>
          <p className="page-subtitle">Monitor companies and receive alerts</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>
          <Eye size={18} />
          Add Company
        </button>
      </div>

      {/* Add form */}
      {showAddForm && (
        <div className="card watchlist-add-card">
          <div className="card-body">
            <form onSubmit={handleAdd} className="watchlist-add-form">
              <div className="form-row">
                <div className="form-group" style={{ flex: 2 }}>
                  <label>Company Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter company name"
                    value={addCompany}
                    onChange={(e) => setAddCompany(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="form-group" style={{ flex: 3 }}>
                  <label>Notes (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Add notes..."
                    value={addNotes}
                    onChange={(e) => setAddNotes(e.target.value)}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={adding}>
                  {adding ? <Loader size={16} className="spinning" /> : 'Add to Watchlist'}
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Watchlist items */}
      {items.length === 0 ? (
        <div className="empty-state card">
          <Eye size={48} className="empty-state-icon" />
          <h4>Your watchlist is empty</h4>
          <p>Add companies to monitor market changes and receive alerts.</p>
          <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>
            Add Your First Company
          </button>
        </div>
      ) : (
        <div className="watchlist-grid">
          {items.map((item) => (
            <div key={item.id} className="watchlist-card card">
              <div className="card-body">
                <div className="watchlist-card-header">
                  <div>
                    <h3 className="watchlist-company-name">{item.company.name}</h3>
                    {item.company.sector && (
                      <span className="sector-badge">{item.company.sector}</span>
                    )}
                  </div>
                  <span className="text-muted text-sm">
                    Added {formatDate(item.created_at)}
                  </span>
                </div>

                {/* Notes */}
                <div className="watchlist-notes">
                  {editingId === item.id ? (
                    <div className="watchlist-notes-edit">
                      <textarea
                        className="form-textarea"
                        value={editNotes}
                        onChange={(e) => setEditNotes(e.target.value)}
                        rows={2}
                        placeholder="Add notes..."
                      />
                      <div className="watchlist-notes-actions">
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => handleSaveNotes(item.id)}
                        >
                          <Save size={14} /> Save
                        </button>
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => setEditingId(null)}
                        >
                          <X size={14} /> Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className="watchlist-notes-display"
                      onClick={() => {
                        setEditingId(item.id);
                        setEditNotes(item.notes || '');
                      }}
                    >
                      {item.notes ? (
                        <p>{item.notes}</p>
                      ) : (
                        <p className="text-muted">Click to add notes...</p>
                      )}
                      <Edit3 size={14} className="edit-icon" />
                    </div>
                  )}
                </div>

                {/* Alert toggles */}
                <div className="watchlist-alerts">
                  <button
                    className={`alert-toggle ${item.alert_on_news ? 'active' : ''}`}
                    onClick={() =>
                      handleToggleAlert(item.id, 'alert_on_news', item.alert_on_news)
                    }
                  >
                    {item.alert_on_news ? <Bell size={14} /> : <BellOff size={14} />}
                    News Alerts
                  </button>
                  <button
                    className={`alert-toggle ${item.alert_on_competitor_change ? 'active' : ''}`}
                    onClick={() =>
                      handleToggleAlert(
                        item.id,
                        'alert_on_competitor_change',
                        item.alert_on_competitor_change
                      )
                    }
                  >
                    {item.alert_on_competitor_change ? (
                      <Bell size={14} />
                    ) : (
                      <BellOff size={14} />
                    )}
                    Competitor Alerts
                  </button>
                </div>

                {/* Actions */}
                <div className="watchlist-card-actions">
                  <Link
                    to={`/research/new?company=${encodeURIComponent(item.company.name)}`}
                    className="btn btn-sm btn-primary"
                  >
                    <RefreshCw size={14} />
                    Research
                  </Link>
                  <button
                    className="btn btn-sm btn-danger-outline"
                    onClick={() => handleRemove(item.id)}
                  >
                    <Trash2 size={14} />
                    Remove
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

export default Watchlist;
