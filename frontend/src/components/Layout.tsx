import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  History,
  FileText,
  Eye,
  Bot,
  User,
  LogOut,
  Menu,
  X,
  ChevronLeft,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import NotificationBell from './NotificationBell';

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/research/new', icon: Search, label: 'New Research' },
  { to: '/research', icon: History, label: 'Research History' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/watchlist', icon: Eye, label: 'Watchlist' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/profile', icon: User, label: 'Profile' },
];

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`app-layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          {!sidebarCollapsed && (
            <div className="sidebar-brand">
              <Bot size={28} />
              <span>AI Market Research</span>
            </div>
          )}
          <button
            className="sidebar-collapse-btn desktop-only"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            aria-label="Toggle sidebar"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            className="sidebar-close-btn mobile-only"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <item.icon size={20} />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {!sidebarCollapsed && user && (
            <div className="sidebar-user">
              <div className="sidebar-user-avatar">
                {user.first_name?.[0]}
                {user.last_name?.[0]}
              </div>
              <div className="sidebar-user-info">
                <span className="sidebar-user-name">
                  {user.first_name} {user.last_name}
                </span>
                <span className="sidebar-user-role">{user.role}</span>
              </div>
            </div>
          )}
          <button className="sidebar-logout-btn" onClick={handleLogout} title="Logout">
            <LogOut size={18} />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-wrapper">
        <header className="main-header">
          <button
            className="mobile-menu-btn mobile-only"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu size={24} />
          </button>

          <div className="header-spacer" />

          <div className="header-actions">
            <NotificationBell />
            {user && (
              <div className="header-user">
                <span className="header-user-name">
                  {user.first_name} {user.last_name}
                </span>
              </div>
            )}
          </div>
        </header>

        <main className="main-content">{children}</main>
      </div>
    </div>
  );
};

export default Layout;
