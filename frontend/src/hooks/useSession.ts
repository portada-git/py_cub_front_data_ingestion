/**
 * Session management hook
 * Handles token refresh, session timeout, and automatic logout
 */

import { useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { useNotificationStore } from '../store/useStore';

interface UseSessionOptions {
  refreshThreshold?: number; // Minutes before expiry to refresh
  warningThreshold?: number; // Minutes before expiry to show warning
  checkInterval?: number; // Minutes between session checks
}

export const useSession = (options: UseSessionOptions = {}) => {
  const {
    refreshThreshold = 5,
    warningThreshold = 2,
    checkInterval = 1
  } = options;

  const { user, isAuthenticated, logout, checkAuthStatus } = useAuth();
  const { addNotification } = useNotificationStore();
  const intervalRef = useRef<number | null>(null);
  const warningShownRef = useRef(false);

  const getTokenExpiryTime = useCallback(() => {
    if (!user?.access_token) return null;
    
    try {
      // Decode JWT token to get expiry time
      const payload = JSON.parse(atob(user.access_token.split('.')[1]));
      return payload.exp ? new Date(payload.exp * 1000) : null;
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }, [user?.access_token]);

  const getMinutesUntilExpiry = useCallback(() => {
    const expiryTime = getTokenExpiryTime();
    if (!expiryTime) return null;
    
    const now = new Date();
    const diffMs = expiryTime.getTime() - now.getTime();
    return Math.floor(diffMs / (1000 * 60));
  }, [getTokenExpiryTime]);

  const handleSessionExpiry = useCallback(async () => {
    addNotification({
      type: 'warning',
      title: 'Sesión expirada',
      message: 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.',
    });
    await logout();
  }, [addNotification, logout]);

  const showExpiryWarning = useCallback(() => {
    if (warningShownRef.current) return;
    
    warningShownRef.current = true;
    addNotification({
      type: 'warning',
      title: 'Sesión por expirar',
      message: `Tu sesión expirará en ${warningThreshold} minutos. Guarda tu trabajo.`,
    });
  }, [addNotification, warningThreshold]);

  const checkSession = useCallback(async () => {
    if (!isAuthenticated) return;

    const minutesLeft = getMinutesUntilExpiry();
    
    if (minutesLeft === null) {
      // Can't determine expiry, check with backend
      const isValid = await checkAuthStatus();
      if (!isValid) {
        await handleSessionExpiry();
      }
      return;
    }

    if (minutesLeft <= 0) {
      // Token expired
      await handleSessionExpiry();
    } else if (minutesLeft <= warningThreshold) {
      // Show warning
      showExpiryWarning();
    } else if (minutesLeft <= refreshThreshold) {
      // Try to refresh token (if backend supports it)
      try {
        const isValid = await checkAuthStatus();
        if (!isValid) {
          await handleSessionExpiry();
        } else {
          // Reset warning flag if session was refreshed
          warningShownRef.current = false;
        }
      } catch (error) {
        console.error('Session refresh failed:', error);
        await handleSessionExpiry();
      }
    }
  }, [
    isAuthenticated,
    getMinutesUntilExpiry,
    checkAuthStatus,
    handleSessionExpiry,
    showExpiryWarning,
    refreshThreshold,
    warningThreshold
  ]);

  // Start session monitoring
  useEffect(() => {
    if (!isAuthenticated) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      warningShownRef.current = false;
      return;
    }

    // Initial check
    checkSession();

    // Set up periodic checks
    intervalRef.current = setInterval(checkSession, checkInterval * 60 * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAuthenticated, checkSession, checkInterval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    minutesUntilExpiry: getMinutesUntilExpiry(),
    isSessionValid: isAuthenticated,
    checkSession,
  };
};