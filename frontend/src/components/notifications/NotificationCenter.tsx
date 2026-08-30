import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  CheckCheck,
  FileText,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  AlertCircle,
  Clock,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { apiService } from '../../services/api';
import { NotificationItem, NotificationSeverity } from '../../types/application';

export const NotificationCenter: React.FC = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [filterUnread, setFilterUnread] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const [listRes, count] = await Promise.all([
        apiService.getNotifications(filterUnread, 30),
        apiService.getUnreadNotificationCount(),
      ]);
      setNotifications(listRes.items);
      setUnreadCount(count);
    } catch (err) {
      console.warn('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(() => {
      apiService.getUnreadNotificationCount().then(setUnreadCount).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, [filterUnread]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleToggle = () => {
    if (!isOpen) {
      fetchNotifications();
    }
    setIsOpen(!isOpen);
  };

  const handleItemClick = async (notif: NotificationItem) => {
    if (!notif.read) {
      await apiService.markNotificationRead(notif.id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    }
    setIsOpen(false);
    if (notif.application_id) {
      navigate(`/applications/${notif.application_id}`);
    }
  };

  const handleMarkAllRead = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiService.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.warn('Failed to mark all as read:', err);
    }
  };

  const getSeverityBadge = (severity: NotificationSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'WARNING':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'SUCCESS':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'INFO':
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getSeverityIcon = (severity: NotificationSeverity, type: string) => {
    if (type === 'RETRY_RECEIVED') {
      return <RefreshCw className="w-4 h-4 text-blue-600" />;
    }
    switch (severity) {
      case 'CRITICAL':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'SUCCESS':
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      case 'INFO':
      default:
        return <FileText className="w-4 h-4 text-blue-600" />;
    }
  };

  const formatTimeAgo = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={handleToggle}
        aria-label="Department Notifications"
        className="relative p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex items-center justify-center min-w-[1.25rem] h-5 px-1 text-xs font-bold text-white bg-red-600 rounded-full border-2 border-white shadow-sm">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Popover Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-[95vw] bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Header */}
          <div className="px-4 py-3 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-primary-400" />
              <span className="font-semibold text-sm">Department Alerts</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 text-xs font-medium bg-red-600/90 text-white rounded-full">
                  {unreadCount} new
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-slate-300 hover:text-white flex items-center space-x-1 underline hover:no-underline transition-colors"
                title="Mark all notifications as read"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          {/* Filter Bar */}
          <div className="px-4 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs">
            <div className="flex space-x-2">
              <button
                onClick={() => setFilterUnread(false)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  !filterUnread
                    ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterUnread(true)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  filterUnread
                    ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Unread Only
              </button>
            </div>
            <span className="text-slate-600 font-mono text-[11px]">
              {notifications.length} {notifications.length === 1 ? 'alert' : 'alerts'}
            </span>
          </div>

          {/* Notification List */}
          <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-100">
            {loading && notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-600">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary-600" />
                <p className="text-xs">Loading departmental alerts...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-600">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <p className="text-sm font-medium text-slate-700">All caught up!</p>
                <p className="text-xs text-slate-600 mt-0.5">No unread alerts pending scrutiny.</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => handleItemClick(notif)}
                  className={`p-3.5 transition-colors cursor-pointer hover:bg-slate-50 flex items-start space-x-3 ${
                    !notif.read ? 'bg-blue-50/40' : 'bg-white'
                  }`}
                >
                  <div className="mt-0.5 flex-shrink-0 p-1.5 rounded-lg bg-slate-100">
                    {getSeverityIcon(notif.severity, notif.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <p
                        className={`text-xs font-semibold truncate ${
                          !notif.read ? 'text-slate-900' : 'text-slate-700'
                        }`}
                      >
                        {notif.title}
                      </p>
                      <span className="text-[10px] text-slate-600 whitespace-nowrap flex items-center">
                        <Clock className="w-2.5 h-2.5 mr-0.5" />
                        {formatTimeAgo(notif.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-2 mb-1.5 leading-relaxed">
                      {notif.message}
                    </p>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="inline-flex items-center text-primary-700 font-mono font-medium hover:underline">
                        {notif.application_id}
                        <ExternalLink className="w-2.5 h-2.5 ml-1 inline" />
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-semibold border ${getSeverityBadge(
                          notif.severity
                        )}`}
                      >
                        {notif.severity}
                      </span>
                    </div>
                  </div>
                  {!notif.read && (
                    <div className="w-2 h-2 rounded-full bg-blue-600 mt-1 flex-shrink-0" />
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-center">
            <button
              onClick={() => {
                setIsOpen(false);
                navigate('/applications/action-required');
              }}
              className="text-xs text-primary-700 hover:text-primary-800 font-medium inline-flex items-center space-x-1"
            >
              <span>View Action Required Queue</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
