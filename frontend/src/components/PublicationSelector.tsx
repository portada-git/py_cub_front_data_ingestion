/**
 * Publication Selector Component
 * Reutilizable selector for publications with dynamic data loading
 */

import React, { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { apiService } from '../services/api';
import { useNotificationStore } from '../store/useStore';
import { Publication } from '../types';
import clsx from 'clsx';

interface PublicationSelectorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  includeAll?: boolean;
  allLabel?: string;
  className?: string;
  disabled?: boolean;
  required?: boolean;
}

const PublicationSelector: React.FC<PublicationSelectorProps> = ({
  value,
  onChange,
  placeholder = "Selecciona una publicación",
  includeAll = true,
  allLabel = "Todas las publicaciones",
  className = "",
  disabled = false,
  required = false
}) => {
  const [publications, setPublications] = useState<Publication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { addNotification } = useNotificationStore();

  useEffect(() => {
    loadPublications();
  }, []);

  const loadPublications = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getPublications();
      setPublications(response.publications);
    } catch (error) {
      console.error('Error loading publications:', error);
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'No se pudieron cargar las publicaciones'
      });
      // Fallback to default publications
      setPublications([
        { code: "db", name: "Diario de Barcelona", full_name: "Diario de Barcelona" },
        { code: "dm", name: "Diario de la Marina", full_name: "Diario de la Marina" },
        { code: "sm", name: "Le semaphore de Marseille", full_name: "Le semaphore de Marseille" },
        { code: "gm", name: "Gaceta Mercantil", full_name: "Gaceta Mercantil" },
        { code: "bp", name: "British Packet", full_name: "British Packet" },
        { code: "en", name: "El Nacional", full_name: "El Nacional" },
        { code: "lp", name: "La Prensa", full_name: "La Prensa" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || isLoading}
        required={required}
        className={clsx(
          'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
          'bg-white text-gray-900',
          'disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed',
          className
        )}
      >
        {includeAll && (
          <option value="">{allLabel}</option>
        )}
        
        {!includeAll && !value && (
          <option value="" disabled>{placeholder}</option>
        )}
        
        {isLoading ? (
          <option disabled>Cargando publicaciones...</option>
        ) : (
          publications.map((publication) => (
            <option key={publication.code} value={publication.code}>
              {publication.name}
            </option>
          ))
        )}
      </select>
      
      {/* Custom dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </div>
    </div>
  );
};

export default PublicationSelector;