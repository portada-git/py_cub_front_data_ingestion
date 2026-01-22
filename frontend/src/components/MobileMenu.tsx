/**
 * Mobile navigation menu component
 * Provides responsive navigation for mobile devices with accessibility features
 */

import React, { useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { X, Home, Upload, BarChart3, LogOut, ChevronDown, ChevronRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../store/useStore';
import clsx from 'clsx';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();
  const { expandedMenus, toggleMenuExpansion } = useUIStore();
  const location = useLocation();
  const menuRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus management
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // Trap focus within the menu
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        const focusableElements = menuRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements && focusableElements.length > 0) {
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

          if (event.shiftKey) {
            if (document.activeElement === firstElement) {
              event.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              event.preventDefault();
              firstElement.focus();
            }
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

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
    onClose();
  };

  const handleMenuToggle = (menuName: string) => {
    toggleMenuExpansion(menuName);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Menu Panel */}
      <div 
        ref={menuRef}
        className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl transform transition-transform"
        role="dialog"
        aria-modal="true"
        aria-label="Menú de navegación móvil"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <div className="flex items-center">
              <div 
                className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center"
                role="img"
                aria-label="Logo de PortAda"
              >
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-gray-900">PortAda</h1>
              </div>
            </div>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="p-1 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Cerrar menú"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          {/* Navigation */}
          <nav 
            className="flex-1 px-4 py-4 space-y-2 overflow-y-auto"
            role="navigation"
            aria-label="Navegación principal móvil"
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
                        'flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                        isActive 
                          ? 'bg-primary-100 text-primary-700' 
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      )}
                      aria-expanded={isExpanded}
                      aria-controls={`mobile-submenu-${item.name}`}
                    >
                      <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />
                      <span className="flex-1 text-left">{item.name}</span>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 ml-2" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="w-4 h-4 ml-2" aria-hidden="true" />
                      )}
                    </button>
                  ) : (
                    <Link
                      to={item.href}
                      onClick={onClose}
                      className={clsx(
                        'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                        isActive 
                          ? 'bg-primary-100 text-primary-700' 
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
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
                      id={`mobile-submenu-${item.name}`}
                      className="ml-8 mt-2 space-y-1"
                      role="menu"
                      aria-label={`Submenú móvil de ${item.name}`}
                    >
                      {item.children.map((child) => {
                        const childIsActive = location.pathname === child.href.split('?')[0] || 
                                            (child.href.includes('?') && location.search.includes(child.href.split('?')[1]));
                        
                        return (
                          <Link
                            key={child.name}
                            to={child.href}
                            onClick={onClose}
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
              <div 
                className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center"
                role="img"
                aria-label={`Avatar de ${user?.full_name || user?.username}`}
              >
                <span className="text-sm font-medium text-gray-700">
                  {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                </span>
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
    </div>
  );
};

export default MobileMenu;