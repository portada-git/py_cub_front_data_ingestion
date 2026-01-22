/**
 * Entity configuration component
 * Handles configuration for known entities ingestion
 */

import React from 'react';
import { Database, Info } from 'lucide-react';
import clsx from 'clsx';

interface EntityConfigurationProps {
  entityName: string;
  onEntityNameChange: (name: string) => void;
  dataPath?: string;
  onDataPathChange?: (path: string) => void;
  disabled?: boolean;
  className?: string;
}

const EntityConfiguration: React.FC<EntityConfigurationProps> = ({
  entityName,
  onEntityNameChange,
  dataPath,
  onDataPathChange,
  disabled = false,
  className = ''
}) => {
  const commonEntityNames = [
    {
      name: 'known_entities',
      description: 'Entidades generales conocidas',
      example: 'Nombres de personas, lugares, organizaciones'
    },
    {
      name: 'ship_entities',
      description: 'Entidades relacionadas con embarcaciones',
      example: 'Nombres de barcos, puertos, compañías navieras'
    },
    {
      name: 'location_entities',
      description: 'Entidades de ubicación geográfica',
      example: 'Ciudades, países, regiones, puertos'
    },
    {
      name: 'person_entities',
      description: 'Entidades de personas',
      example: 'Nombres de capitanes, comerciantes, autoridades'
    }
  ];

  return (
    <div className={clsx('space-y-4', className)}>
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Configuración de Entidades
        </h3>
        <p className="text-sm text-gray-600">
          Configura el nombre y tipo de entidades que se van a ingerir
        </p>
      </div>

      {/* Entity Name Input */}
      <div>
        <label htmlFor="entityName" className="block text-sm font-medium text-gray-700 mb-2">
          Nombre de Entidad
        </label>
        <input
          type="text"
          id="entityName"
          value={entityName}
          onChange={(e) => onEntityNameChange(e.target.value)}
          disabled={disabled}
          className={clsx(
            'input',
            disabled && 'bg-gray-50 cursor-not-allowed'
          )}
          placeholder="Ej: known_entities, ship_entities"
        />
        <p className="text-xs text-gray-500 mt-1">
          Identificador único para el tipo de entidades (usar snake_case)
        </p>
      </div>

      {/* Common Entity Types */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Tipos Comunes de Entidades
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {commonEntityNames.map((entity) => (
            <button
              key={entity.name}
              type="button"
              onClick={() => !disabled && onEntityNameChange(entity.name)}
              disabled={disabled}
              className={clsx(
                'p-3 border rounded-lg text-left transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                {
                  'border-primary-500 bg-primary-50': entityName === entity.name,
                  'border-gray-200 hover:border-gray-300 hover:bg-gray-50': 
                    entityName !== entity.name && !disabled,
                  'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60': disabled,
                }
              )}
            >
              <div className="flex items-start">
                <Database className={clsx(
                  'w-4 h-4 mr-2 mt-0.5 flex-shrink-0',
                  entityName === entity.name ? 'text-primary-600' : 'text-gray-400'
                )} />
                
                <div className="flex-1 min-w-0">
                  <p className={clsx(
                    'text-sm font-medium',
                    entityName === entity.name ? 'text-primary-900' : 'text-gray-900'
                  )}>
                    {entity.name}
                  </p>
                  <p className={clsx(
                    'text-xs mt-1',
                    entityName === entity.name ? 'text-primary-700' : 'text-gray-600'
                  )}>
                    {entity.description}
                  </p>
                  <p className={clsx(
                    'text-xs mt-1',
                    entityName === entity.name ? 'text-primary-600' : 'text-gray-500'
                  )}>
                    {entity.example}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Data Path (Optional) */}
      {onDataPathChange && (
        <div>
          <label htmlFor="dataPath" className="block text-sm font-medium text-gray-700 mb-2">
            Ruta de Datos (Opcional)
          </label>
          <input
            type="text"
            id="dataPath"
            value={dataPath || ''}
            onChange={(e) => onDataPathChange(e.target.value)}
            disabled={disabled}
            className={clsx(
              'input',
              disabled && 'bg-gray-50 cursor-not-allowed'
            )}
            placeholder="Ej: entities/known_entities"
          />
          <p className="text-xs text-gray-500 mt-1">
            Ruta específica en el Delta Lake donde se almacenarán las entidades
          </p>
        </div>
      )}

      {/* Information Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <Info className="w-5 h-5 text-blue-400 mr-3 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-2">
              Información sobre Entidades Conocidas
            </h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Las entidades deben estar en formato YAML válido</li>
              <li>• Cada entidad debe tener un identificador único</li>
              <li>• Se pueden incluir metadatos adicionales para cada entidad</li>
              <li>• Las entidades se utilizan para mejorar la precisión del análisis</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Current Configuration Summary */}
      {entityName && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Configuración Actual
          </h4>
          <div className="space-y-1 text-sm text-gray-600">
            <p><span className="font-medium">Nombre:</span> {entityName}</p>
            {dataPath && (
              <p><span className="font-medium">Ruta:</span> {dataPath}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityConfiguration;