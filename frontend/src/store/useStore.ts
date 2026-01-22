import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserSession } from '../types';
import { apiService } from '../services/api';

type AuthStatus = 'authenticated' | 'unauthenticated' | 'loading';

interface AppState {
  authStatus: AuthStatus;
  user: UserSession | null;
  isProcessing: boolean;
  
  setAuthStatus: (status: AuthStatus) => void;
  setUser: (user: UserSession | null) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      authStatus: 'loading',
      user: null,
      isProcessing: false,

      setAuthStatus: (status) => set({ authStatus: status }),
      setUser: (user) => set({ user }),
      setIsProcessing: (isProcessing) => set({ isProcessing }),
      
      login: async (username: string, password: string) => {
        try {
          set({ authStatus: 'loading' });
          
          const response = await apiService.login({ username, password });
          
          const userSession: UserSession = {
            ...response.user_info,
            isAuthenticated: true,
            access_token: response.access_token,
            expires_in: response.expires_in,
          };
          
          set({ 
            authStatus: 'authenticated', 
            user: userSession 
          });
        } catch (error) {
          set({ authStatus: 'unauthenticated', user: null });
          throw error;
        }
      },
      
      logout: async () => {
        try {
          await apiService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({ 
            authStatus: 'unauthenticated', 
            user: null 
          });
        }
      },
      
      checkAuth: () => {
        const isAuthenticated = apiService.isAuthenticated();
        if (isAuthenticated) {
          // Verify token is still valid by making a request
          apiService.getCurrentUser()
            .then((userInfo) => {
              const userSession: UserSession = {
                ...userInfo,
                isAuthenticated: true,
                access_token: localStorage.getItem('access_token') || '',
                expires_in: 0, // Will be refreshed on next login
              };
              set({ 
                authStatus: 'authenticated', 
                user: userSession 
              });
            })
            .catch(() => {
              // Token is invalid
              apiService.clearToken();
              set({ 
                authStatus: 'unauthenticated', 
                user: null 
              });
            });
        } else {
          set({ authStatus: 'unauthenticated' });
        }
      },
    }),
    {
      name: 'portada-auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        authStatus: state.authStatus === 'authenticated' ? 'authenticated' : 'unauthenticated'
      }),
    }
  )
);
