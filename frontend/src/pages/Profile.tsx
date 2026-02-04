import React, { useState, useEffect } from 'react';
import { User, Building, Lock, Bell, Loader, Save, Check } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const Profile: React.FC = () => {
  const { user, updateProfile, loadFromStorage } = useAuthStore();

  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    company: '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [preferences, setPreferences] = useState({
    email_notifications: true,
    research_complete_alerts: true,
    watchlist_alerts: true,
    weekly_digest: false,
  });

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        company: user.company || '',
      });
      if (user.preferences) {
        setPreferences((prev) => ({ ...prev, ...user.preferences }));
      }
    } else {
      loadFromStorage();
    }
  }, [user, loadFromStorage]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await updateProfile(profileData);
      toast.success('Profile updated successfully');
    } catch (err: any) {
      toast.error(err.message || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setSavingPassword(true);
    try {
      await authAPI.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
      toast.success('Password changed successfully');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setSavingPassword(false);
    }
  };

  const handlePreferencesSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPreferences(true);
    try {
      await updateProfile({ preferences } as any);
      toast.success('Preferences saved');
    } catch (err: any) {
      toast.error(err.message || 'Failed to save preferences');
    } finally {
      setSavingPreferences(false);
    }
  };

  return (
    <div className="profile-page">
      <div className="page-header">
        <div>
          <h1>Profile Settings</h1>
          <p className="page-subtitle">Manage your account and preferences</p>
        </div>
      </div>

      <div className="profile-sections">
        {/* Profile info */}
        <div className="card">
          <div className="card-header">
            <h3>
              <User size={20} /> Personal Information
            </h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleProfileSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="first_name">First Name</label>
                  <input
                    id="first_name"
                    type="text"
                    className="form-input"
                    value={profileData.first_name}
                    onChange={(e) =>
                      setProfileData((prev) => ({ ...prev, first_name: e.target.value }))
                    }
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="last_name">Last Name</label>
                  <input
                    id="last_name"
                    type="text"
                    className="form-input"
                    value={profileData.last_name}
                    onChange={(e) =>
                      setProfileData((prev) => ({ ...prev, last_name: e.target.value }))
                    }
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  className="form-input"
                  value={user?.email || ''}
                  disabled
                />
                <span className="form-help">Email cannot be changed</span>
              </div>

              <div className="form-group">
                <label htmlFor="company">
                  <Building size={16} /> Company
                </label>
                <input
                  id="company"
                  type="text"
                  className="form-input"
                  value={profileData.company}
                  onChange={(e) =>
                    setProfileData((prev) => ({ ...prev, company: e.target.value }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Role</label>
                <input
                  type="text"
                  className="form-input"
                  value={user?.role || ''}
                  disabled
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={savingProfile}>
                {savingProfile ? (
                  <Loader size={16} className="spinning" />
                ) : (
                  <Save size={16} />
                )}
                Save Changes
              </button>
            </form>
          </div>
        </div>

        {/* Change password */}
        <div className="card">
          <div className="card-header">
            <h3>
              <Lock size={20} /> Change Password
            </h3>
          </div>
          <div className="card-body">
            <form onSubmit={handlePasswordSubmit}>
              <div className="form-group">
                <label htmlFor="current_password">Current Password</label>
                <input
                  id="current_password"
                  type="password"
                  className="form-input"
                  value={passwordData.current_password}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      current_password: e.target.value,
                    }))
                  }
                  autoComplete="current-password"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="new_password">New Password</label>
                  <input
                    id="new_password"
                    type="password"
                    className="form-input"
                    value={passwordData.new_password}
                    onChange={(e) =>
                      setPasswordData((prev) => ({
                        ...prev,
                        new_password: e.target.value,
                      }))
                    }
                    autoComplete="new-password"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="confirm_new_password">Confirm New Password</label>
                  <input
                    id="confirm_new_password"
                    type="password"
                    className="form-input"
                    value={passwordData.confirm_password}
                    onChange={(e) =>
                      setPasswordData((prev) => ({
                        ...prev,
                        confirm_password: e.target.value,
                      }))
                    }
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary" disabled={savingPassword}>
                {savingPassword ? (
                  <Loader size={16} className="spinning" />
                ) : (
                  <Lock size={16} />
                )}
                Change Password
              </button>
            </form>
          </div>
        </div>

        {/* Notification preferences */}
        <div className="card">
          <div className="card-header">
            <h3>
              <Bell size={20} /> Notification Preferences
            </h3>
          </div>
          <div className="card-body">
            <form onSubmit={handlePreferencesSubmit}>
              <div className="preference-list">
                <label className="preference-item">
                  <div className="preference-info">
                    <span className="preference-name">Email Notifications</span>
                    <span className="preference-description">
                      Receive notifications via email
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle-input"
                    checked={preferences.email_notifications}
                    onChange={(e) =>
                      setPreferences((prev) => ({
                        ...prev,
                        email_notifications: e.target.checked,
                      }))
                    }
                  />
                </label>

                <label className="preference-item">
                  <div className="preference-info">
                    <span className="preference-name">Research Complete Alerts</span>
                    <span className="preference-description">
                      Get notified when research tasks are completed
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle-input"
                    checked={preferences.research_complete_alerts}
                    onChange={(e) =>
                      setPreferences((prev) => ({
                        ...prev,
                        research_complete_alerts: e.target.checked,
                      }))
                    }
                  />
                </label>

                <label className="preference-item">
                  <div className="preference-info">
                    <span className="preference-name">Watchlist Alerts</span>
                    <span className="preference-description">
                      Receive alerts for watchlist company updates
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle-input"
                    checked={preferences.watchlist_alerts}
                    onChange={(e) =>
                      setPreferences((prev) => ({
                        ...prev,
                        watchlist_alerts: e.target.checked,
                      }))
                    }
                  />
                </label>

                <label className="preference-item">
                  <div className="preference-info">
                    <span className="preference-name">Weekly Digest</span>
                    <span className="preference-description">
                      Receive a weekly summary of your research activity
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle-input"
                    checked={preferences.weekly_digest}
                    onChange={(e) =>
                      setPreferences((prev) => ({
                        ...prev,
                        weekly_digest: e.target.checked,
                      }))
                    }
                  />
                </label>
              </div>

              <button type="submit" className="btn btn-primary" disabled={savingPreferences}>
                {savingPreferences ? (
                  <Loader size={16} className="spinning" />
                ) : (
                  <Check size={16} />
                )}
                Save Preferences
              </button>
            </form>
          </div>
        </div>


      </div>
    </div>
  );
};

export default Profile;
