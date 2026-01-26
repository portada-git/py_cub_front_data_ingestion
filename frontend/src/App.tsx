/**
 * Main App component with routing and layout
 * Modern React implementation with proper error boundaries and authentication
 */

import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/useStore';
import { useUploadStore } from './store/useUploadStore';
import { useSession } from './hooks/useSession';
import Layout from './components/Layout';
import LoginView from './views/LoginView';
import DashboardView from './views/DashboardView';
import IngestionView from './views/IngestionView';
import AnalysisView from './views/AnalysisView';
import ProcessDashboardView from './views/ProcessDashboardView';
import ProtectedRoute from './components/ProtectedRoute';
import NotificationContainer from './components/NotificationContainer';
import UploadMonitor from './components/UploadMonitor';
import ErrorBoundary from './components/ErrorBoundary';

// Initialize i18n
import './i18n';
import './styles/upload.css';

// Protected Route component
const ProtectedRouteWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
};

const App: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const { getStats } = useUploadStore();
  
  // Initialize session management for authenticated users with longer intervals
  useSession({
    refreshThreshold: 10, // Refresh 10 minutes before expiry
    warningThreshold: 5, // Show warning 5 minutes before expiry
    checkInterval: 10, // Check every 10 minutes instead of 1
  });

  // Initialize authentication state from localStorage only once
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !isAuthenticated) {
      // Token exists but user is not authenticated, validate token
      console.log('Token found in localStorage');
      // Don't make API call here, let the session hook handle it
    }
  }, []); // Remove isAuthenticated dependency to prevent re-runs

  const uploadStats = getStats();

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/login" element={<LoginView />} />
          <Route
            path="/*"
            element={
              <ProtectedRouteWrapper>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<DashboardView />} />
                    <Route path="/ingestion" element={<IngestionView />} />
                    <Route path="/analysis/*" element={<AnalysisView />} />
                    <Route path="/processes" element={<ProcessDashboardView />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Layout>
              </ProtectedRouteWrapper>
            }
          />
        </Routes>
        
        {/* Global notification container */}
        <NotificationContainer />
        
        {/* Upload Monitor - Always visible when there are tasks */}
        {isAuthenticated && uploadStats.totalTasks > 0 && (
          <UploadMonitor position="bottom-right" />
        )}
      </div>
    </ErrorBoundary>
  );
};

export default App;