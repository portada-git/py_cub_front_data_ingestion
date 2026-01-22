/**
 * Authentication guard hook
 * Handles route protection and authentication state validation
 */

import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';

interface UseAuthGuardOptions {
  redirectTo?: string;
  requiredPermission?: string;
  requiredRole?: string;
}

export const useAuthGuard = (options: UseAuthGuardOptions = {}) => {
  const { redirectTo = '/login', requiredPermission, requiredRole } = options;
  const { isAuthenticated, checkAuthStatus, hasPermission, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const validateAuth = async () => {
      setIsLoading(true);

      // Check if user is authenticated
      if (!isAuthenticated) {
        navigate(redirectTo, { 
          state: { from: location.pathname },
          replace: true 
        });
        setIsLoading(false);
        return;
      }

      // Verify authentication status with backend
      const isValid = await checkAuthStatus();
      if (!isValid) {
        navigate(redirectTo, { 
          state: { from: location.pathname },
          replace: true 
        });
        setIsLoading(false);
        return;
      }

      // Check permissions if required
      if (requiredPermission && !hasPermission(requiredPermission)) {
        navigate('/unauthorized', { replace: true });
        setIsLoading(false);
        return;
      }

      // Check role if required
      if (requiredRole && !hasRole(requiredRole)) {
        navigate('/unauthorized', { replace: true });
        setIsLoading(false);
        return;
      }

      setIsAuthorized(true);
      setIsLoading(false);
    };

    validateAuth();
  }, [
    isAuthenticated,
    checkAuthStatus,
    hasPermission,
    hasRole,
    requiredPermission,
    requiredRole,
    navigate,
    redirectTo,
    location.pathname
  ]);

  return {
    isLoading,
    isAuthorized,
    isAuthenticated,
  };
};