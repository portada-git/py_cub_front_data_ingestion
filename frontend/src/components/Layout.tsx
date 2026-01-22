/**
 * Main layout component with sidebar navigation
 * Implements the UI requirements from the specification
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Upload, 
  BarChart3, 
  Database, 
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../store/useStore';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { 
      name: 'Ingestión', 
      href: '/ingestion', 
      icon: Upload,
      children: [
        { name: 'Carga de datos de extracción', href: '/ingestion?type=extraction' },
        { name: 'Carga de entidades conocidas', href: '/ingestion?type=entities' },
      ]
    },
    { 
      name: 'Análisis', 
      href: '/analysis', 
      icon: BarChart3,
      children: [
        { name: 'Ficheros de ingestión por procesar', href: '/analysis/pending-files' },
        { name: 'Fechas faltantes', href: '/analysis/missing-dates' },
        { name: 'Duplicados', href: '/analysis/duplicates' },
        { name: 'Cantidad de entradas diarias', href: '/analysis/daily-entries' },
        { name: 'Entidades conocidas subidas', href: '/analysis/known-entities' },
        { name: 'Metadatos de almacenaje', href: '/analysis/storage-metadata' },
        { name: 'Metadatos de procesos ejecutados', href: '/analysis/process-metadata' },
      ]
    },
  ];

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-gray-900">PortAda</h1>
                <p className="text-xs text-gray-500">Sistema de Ingestión</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href);
              
              return (
                <div key={item.name}>
                  <Link
                    to={item.href}
                    className={clsx(
                      'sidebar-item',
                      isActive ? 'sidebar-item-active' : 'sidebar-item-inactive'
                    )}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                  
                  {/* Sub-navigation */}
                  {item.children && isActive && (
                    <div className="ml-8 mt-2 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.name}
                          to={child.href}
                          className={clsx(
                            'block px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors',
                            location.pathname === child.href.split('?')[0] && 'text-primary-700 bg-primary-50'
                          )}
                        >
                          {child.name}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* User info and logout */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center mb-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-700">
                    {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                  </span>
                </div>
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.role}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4 mr-3" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        {/* Top bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900">PortAda</h1>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;