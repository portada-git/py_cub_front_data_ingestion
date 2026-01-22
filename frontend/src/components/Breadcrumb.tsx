/**
 * Breadcrumb navigation component
 * Provides hierarchical navigation context
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items }) => {
  const location = useLocation();

  // Generate breadcrumb items from current path if not provided
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Inicio', href: '/dashboard' }
    ];

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === pathSegments.length - 1;
      
      let label = segment;
      // Convert path segments to readable labels
      switch (segment) {
        case 'dashboard':
          label = 'Dashboard';
          break;
        case 'ingestion':
          label = 'Ingestión';
          break;
        case 'analysis':
          label = 'Análisis';
          break;
        case 'pending-files':
          label = 'Archivos Pendientes';
          break;
        case 'missing-dates':
          label = 'Fechas Faltantes';
          break;
        case 'duplicates':
          label = 'Duplicados';
          break;
        case 'daily-entries':
          label = 'Entradas Diarias';
          break;
        case 'known-entities':
          label = 'Entidades Conocidas';
          break;
        case 'storage-metadata':
          label = 'Metadatos de Almacenaje';
          break;
        case 'process-metadata':
          label = 'Metadatos de Procesos';
          break;
        default:
          label = segment.charAt(0).toUpperCase() + segment.slice(1);
      }

      breadcrumbs.push({
        label,
        href: isLast ? undefined : currentPath,
        current: isLast
      });
    });

    return breadcrumbs;
  };

  const breadcrumbItems = items || generateBreadcrumbs();

  if (breadcrumbItems.length <= 1) {
    return null; // Don't show breadcrumb for single items
  }

  return (
    <nav className="flex mb-6" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {breadcrumbItems.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-gray-400 mx-2" />
            )}
            
            {index === 0 && (
              <Home className="w-4 h-4 text-gray-400 mr-2" />
            )}
            
            {item.href && !item.current ? (
              <Link
                to={item.href}
                className="text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={`text-sm font-medium ${
                  item.current 
                    ? 'text-gray-900' 
                    : 'text-gray-500'
                }`}
                aria-current={item.current ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default Breadcrumb;