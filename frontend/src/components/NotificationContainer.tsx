/**
 * Notification container component
 * Displays toast notifications with accessibility features
 */

import React, { useEffect } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { useNotificationStore } from '../store/useStore';
import { ApiErrorHandler } from '../utils/apiErrorHandler';
import clsx from 'clsx';

const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();

  // Set up the error handler callback
  useEffect(() => {
    ApiErrorHandler.setNotificationCallback((notification) => {
      useNotificationStore.getState().addNotification(notification);
    });
  }, []);

  if (notifications.length === 0) {
    return null;
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" aria-hidden="true" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-400" aria-hidden="true" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" aria-hidden="true" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-400" aria-hidden="true" />;
    }
  };

  const getBackgroundColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div 
      className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full"
      role="region"
      aria-label="Notificaciones"
      aria-live="polite"
    >
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={clsx(
            'rounded-lg border p-4 shadow-lg transition-all duration-300 ease-in-out',
            getBackgroundColor(notification.type)
          )}
          role="alert"
          aria-live={notification.type === 'error' ? 'assertive' : 'polite'}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {getIcon(notification.type)}
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-gray-900">
                {notification.title}
              </h3>
              <p className="mt-1 text-sm text-gray-600">
                {notification.message}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={() => removeNotification(notification.id)}
                className="inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500 focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 rounded transition-colors"
                aria-label={`Cerrar notificación: ${notification.title}`}
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationContainer;