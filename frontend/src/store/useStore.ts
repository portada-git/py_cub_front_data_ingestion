/**
 * Global state management using Zustand
 * Modern implementation with TypeScript support and persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserSession, IngestionResponse } from '../types';
import { apiService } from '../services/api';

interface AuthState {
  user: UserSession | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: UserSession) => void;
}

interface IngestionState {
  currentTask: IngestionResponse | null;
  isUploading: boolean;
  uploadProgress: number;
  setCurrentTask: (task: IngestionResponse | null) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number | ((prev: number) => number)) => void;
}

interface UIState {
  sidebarOpen: boolean;
  currentView: string;
  setSidebarOpen: (open: boolean) => void;
  setCurrentView: (view: string) => void;
}

interface NotificationState {
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    timestamp: Date;
  }>;
  addNotification: (notification: Omit<NotificationState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// Auth store with persistence
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      
      login: async (username: string, password: string) => {
        try {
          const response = await apiService.login({ username, password });
          const user: UserSession = {
            ...response.user_info,
            isAuthenticated: true,
            access_token: response.access_token,
            expires_in: response.expires_in,
          };
          
          set({ user, isAuthenticated: true });
          
          // Add success notification
          useNotificationStore.getState().addNotification({
            type: 'success',
            title: 'Inicio de sesión exitoso',
            message: `Bienvenido, ${user.full_name}`,
          });
        } catch (error) {
          // Add error notification
          useNotificationStore.getState().addNotification({
            type: 'error',
            title: 'Error de autenticación',
            message: error instanceof Error ? error.message : 'Error desconocido',
          });
          throw error;
        }
      },
      
      logout: async () => {
        try {
          await apiService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({ user: null, isAuthenticated: false });
          
          // Add info notification
          useNotificationStore.getState().addNotification({
            type: 'info',
            title: 'Sesión cerrada',
            message: 'Has cerrado sesión correctamente',
          });
        }
      },
      
      setUser: (user: UserSession) => {
        set({ user, isAuthenticated: true });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Ingestion store
export const useIngestionStore = create<IngestionState>((set) => ({
  currentTask: null,
  isUploading: false,
  uploadProgress: 0,
  
  setCurrentTask: (task) => set({ currentTask: task }),
  setUploading: (uploading) => set({ isUploading: uploading }),
  setUploadProgress: (progress) => set((state) => ({ 
    uploadProgress: typeof progress === 'function' ? progress(state.uploadProgress) : progress 
  })),
}));

// UI store
export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentView: 'dashboard',
  
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentView: (view) => set({ currentView: view }),
}));

// Notification store
export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  
  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = {
      ...notification,
      id,
      timestamp: new Date(),
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      get().removeNotification(id);
    }, 5000);
  },
  
  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },
  
  clearNotifications: () => {
    set({ notifications: [] });
  },
}));