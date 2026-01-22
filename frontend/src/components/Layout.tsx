/**
 * Main layout component with sidebar navigation
 * Implements responsive design and accessibility features
 */

import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Upload, 
  BarChart3, 
  Database, 
  LogOut,
  Menu,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../store/useStore';
import MobileMenu from './MobileMenu';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const { sidebarOpen, setSidebarOpen, expandedMenus, toggleMenuExpansion } = useUIStore();
  const location = useLocation();

  // Close mobile menu on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname, setSidebarOpen]);

  // Handle escape key to close mobile menu
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen, setSidebarOpen]);

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

  const handleMenuToggle = (menuName: string) => {
    toggleMenuExpansion(menuName);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <div className={clsx(
        'hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white shadow-lg'
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div 
                  className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center"
                  role="img"
                  aria-label="Logo de PortAda"
                >
                  <Database className="w-5 h-5 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-gray-900">PortAda</h1>
                <p className="text-xs text-gray-500">Sistema de Ingestión</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav 
            className="flex-1 px-4 py-4 space-y-2 overflow-y-auto"
            role="navigation"
            aria-label="Navegación principal"
          >
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href);
              const isExpanded = expandedMenus.includes(item.name);
              const hasChildren = item.children && item.children.length > 0;
              
              return (
                <div key={item.name}>
                  {hasChildren ? (
                    <button
                      onClick={() => handleMenuToggle(item.name)}
                      className={clsx(
                        'sidebar-item w-full text-left',
                        isActive ? 'sidebar-item-active' : 'sidebar-item-inactive'
                      )}
                      aria-expanded={isExpanded}
                      aria-controls={`submenu-${item.name}`}
                    >
                      <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />
                      <span className="flex-1">{item.name}</span>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 ml-2" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="w-4 h-4 ml-2" aria-hidden="true" />
                      )}
                    </button>
                  ) : (
                    <Link
                      to={item.href}
                      className={clsx(
                        'sidebar-item',
                        isActive ? 'sidebar-item-active' : 'sidebar-item-inactive'
                      )}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />
                      {item.name}
                    </Link>
                  )}
                  
                  {/* Sub-navigation */}
                  {hasChildren && isExpanded && (
                    <div 
                      id={`submenu-${item.name}`}
                      className="ml-8 mt-2 space-y-1"
                      role="menu"
                      aria-label={`Submenú de ${item.name}`}
                    >
                      {item.children.map((child) => {
                        const childIsActive = location.pathname === child.href.split('?')[0] || 
                                            (child.href.includes('?') && location.search.includes(child.href.split('?')[1]));
                        
                        return (
                          <Link
                            key={child.name}
                            to={child.href}
                            className={clsx(
                              'block px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                              childIsActive && 'text-primary-700 bg-primary-50'
                            )}
                            role="menuitem"
                            aria-current={childIsActive ? 'page' : undefined}
                          >
                            {child.name}
                          </Link>
                        );
                      })}
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
                <div 
                  className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center"
                  role="img"
                  aria-label={`Avatar de ${user?.full_name || user?.username}`}
                >
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
              className="flex items-center w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Cerrar sesión"
            >
              <LogOut className="w-4 h-4 mr-3" aria-hidden="true" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-64">
        {/* Mobile top bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Abrir menú de navegación"
            >
              <Menu className="w-6 h-6" aria-hidden="true" />
            </button>
            <div className="flex items-center">
              <div 
                className="w-6 h-6 bg-primary-600 rounded flex items-center justify-center mr-2"
                role="img"
                aria-label="Logo de PortAda"
              >
                <Database className="w-4 h-4 text-white" aria-hidden="true" />
              </div>
              <h1 className="text-lg font-semibold text-gray-900">PortAda</h1>
            </div>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </header>

        {/* Page content */}
        <main 
          className="flex-1 overflow-y-auto"
          role="main"
          aria-label="Contenido principal"
        >
          <div className="p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Menu */}
      <MobileMenu 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />
    </div>
  );
};

export default Layout;