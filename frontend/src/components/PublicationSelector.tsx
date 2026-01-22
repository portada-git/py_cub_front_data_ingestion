/**
 * Publication selector component
 * Handles selection of newspaper publications for extraction data
 */

import React from 'react';
import { Newspaper, ChevronDown } from 'lucide-react';
import clsx from 'clsx';

export interface Publication {
  id: string;
  name: string;
  fullName: string;
  description?: string;
  editions?: string[];
}

interface PublicationSelectorProps {
  selectedPublication: string;
  onPublicationChange: (publicationId: string) => void;
  publications?: Publication[];
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

const PublicationSelector: React.FC<PublicationSelectorProps> = ({
  selectedPublication,
  onPublicationChange,
  publications = [
    {
      id: 'db',
      name: 'DB',
      fullName: 'Diario de Barcelona',
      description: 'Periódico histórico de Barcelona',
      editions: ['M', 'T', 'U']
    },
    {
      id: 'dm',
      name: 'DM',
      fullName: 'Diario Mercantil',
      description: 'Periódico comercial y mercantil',
      editions: ['M', 'T']
    },
    {
      id: 'sm',
      name: 'SM',
      fullName: 'Semanario Mercantil',
      description: 'Semanario de información comercial',
      editions: ['U']
    }
  ],
  disabled = false,
  required = false,
  className = ''
}) => {
  const selectedPub = publications.find(pub => pub.id === selectedPublication);

  return (
    <div className={clsx('space-y-3', className)}>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Publicación {required && <span className="text-red-500">*</span>}
        </label>
        <p className="text-xs text-gray-600 mb-3">
          Selecciona el periódico del cual provienen los datos de extracción
        </p>
      </div>

      <div className="relative">
        <select
          value={selectedPublication}
          onChange={(e) => onPublicationChange(e.target.value)}
          disabled={disabled}
          required={required}
          className={clsx(
            'input pr-10 appearance-none',
            disabled && 'bg-gray-50 cursor-not-allowed'
          )}
        >
          <option value="">Selecciona una publicación</option>
          {publications.map((publication) => (
            <option key={publication.id} value={publication.id}>
              {publication.name} - {publication.fullName}
            </option>
          ))}
        </select>
        
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </div>
      </div>

      {/* Publication cards for visual selection */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {publications.map((publication) => (
          <button
            key={publication.id}
            type="button"
            onClick={() => !disabled && onPublicationChange(publication.id)}
            disabled={disabled}
            className={clsx(
              'p-3 border rounded-lg text-left transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
              {
                'border-primary-500 bg-primary-50': selectedPublication === publication.id,
                'border-gray-200 hover:border-gray-300 hover:bg-gray-50': 
                  selectedPublication !== publication.id && !disabled,
                'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60': disabled,
              }
            )}
          >
            <div className="flex items-start">
              <Newspaper className={clsx(
                'w-5 h-5 mr-2 mt-0.5 flex-shrink-0',
                selectedPublication === publication.id ? 'text-primary-600' : 'text-gray-400'
              )} />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center">
                  <span className={clsx(
                    'text-sm font-medium',
                    selectedPublication === publication.id ? 'text-primary-900' : 'text-gray-900'
                  )}>
                    {publication.name}
                  </span>
                  {publication.editions && (
                    <span className={clsx(
                      'ml-2 text-xs px-1.5 py-0.5 rounded',
                      selectedPublication === publication.id 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'bg-gray-100 text-gray-600'
                    )}>
                      {publication.editions.join(', ')}
                    </span>
                  )}
                </div>
                
                <p className={clsx(
                  'text-xs mt-1',
                  selectedPublication === publication.id ? 'text-primary-700' : 'text-gray-600'
                )}>
                  {publication.fullName}
                </p>
                
                {publication.description && (
                  <p className={clsx(
                    'text-xs mt-1',
                    selectedPublication === publication.id ? 'text-primary-600' : 'text-gray-500'
                  )}>
                    {publication.description}
                  </p>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Selected publication info */}
      {selectedPub && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-start">
            <Newspaper className="w-4 h-4 text-blue-500 mr-2 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-900">
                {selectedPub.fullName} ({selectedPub.name})
              </p>
              {selectedPub.description && (
                <p className="text-xs text-blue-700 mt-1">
                  {selectedPub.description}
                </p>
              )}
              {selectedPub.editions && (
                <p className="text-xs text-blue-600 mt-1">
                  Ediciones disponibles: {selectedPub.editions.join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PublicationSelector;