import { create } from 'zustand';
import { notificationsAPI } from '../services/api';
import type { Notification } from '../types';

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;

  fetchNotifications: () => Promise<void>;
  markRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
  addNotification: (notification: Notification) => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,

  fetchNotifications: async () => {
    set({ loading: true });
    try {
      const response = await notificationsAPI.getNotifications();
      const notifications = response.data;
      const unreadCount = notifications.filter((n) => !n.is_read).length;
      set({ notifications, unreadCount, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  markRead: async (id: number) => {
    try {
      await notificationsAPI.markRead(id);
      set((state) => {
        const notifications = state.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true } : n
        );
        const unreadCount = notifications.filter((n) => !n.is_read).length;
        return { notifications, unreadCount };
      });
    } catch {
      // Silently fail
    }
  },

  markAllRead: async () => {
    try {
      await notificationsAPI.markAllRead();
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
        unreadCount: 0,
      }));
    } catch {
      // Silently fail
    }
  },

  addNotification: (notification: Notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + (notification.is_read ? 0 : 1),
    }));
  },
}));
