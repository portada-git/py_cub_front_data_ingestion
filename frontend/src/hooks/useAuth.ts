/**
 * Custom authentication hook
 * Provides authentication utilities and state management
 */

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useStore';
import { apiService } from '../services/api';

export const useAuth = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, login, logout, setUser } = useAuthStore();

  const handleLogin = useCallback(async (username: string) => {
    try {
      await login(username);
      navigate('/dashboard');
    } catch (error) {
      throw error; // Re-throw to let the component handle the error
    }
  }, [login, navigate]);

  const handleLogout = useCallback(async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, redirect to login
      navigate('/login');
    }
  }, [logout, navigate]);

  const checkAuthStatus = useCallback(async () => {
    if (!isAuthenticated || !user) {
      return false;
    }

    try {
      // Verify token is still valid by making a request to the backend
      const currentUser = await apiService.getCurrentUser();
      if (currentUser) {
        setUser({ ...user, ...currentUser });
        return true;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      await handleLogout();
      return false;
    }

    return false;
  }, [isAuthenticated, user, setUser, handleLogout]);

  const hasPermission = useCallback((permission: string) => {
    return user?.permissions?.includes(permission) || false;
  }, [user]);

  const hasRole = useCallback((role: string) => {
    return user?.role === role;
  }, [user]);

  return {
    user,
    isAuthenticated,
    login: handleLogin,
    logout: handleLogout,
    checkAuthStatus,
    hasPermission,
    hasRole,
  };
};